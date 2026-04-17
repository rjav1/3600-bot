"""
Pure-Python client for bytefight.org tournament API.

Replaces Chrome MCP dependence. Reverse-engineered from HAR captures of
the logged-in user's session on 2026-04-17.

Endpoints (server.bytefight.org):
  GET    /api/v1/ping                                                    # liveness
  GET    /api/v1/competition/{slug}/teams/my-team                        # team info (may need auth)
  GET    /api/v1/public/leaderboard/{slug}/ranked                        # list all teams
  GET    /api/v1/submission/team/{teamUuid}                              # list own submissions
  GET    /api/v1/submission/team/{teamUuid}/status                       # storage usage
  POST   /api/v1/submission/team/{teamUuid}                              # upload [TURNSTILE]
  PATCH  /api/v1/team/{teamUuid}/current-submission                      # set active submission
  GET    /api/v1/public/game-match?competitionSlug=...&teamUuid=...      # list matches (poll here)
  POST   /api/v1/game-match                                              # create scrimmage [TURNSTILE]
  GET    /files/{fileUuid}?exp=...&sig=...                               # signed PGN download (no auth)

Replay fetch:
  Per-match PGN ("match.json") is not served from a JSON API. The signed `/files/...`
  URL is embedded as an `<a href download>` link inside the server-rendered HTML at
  `https://bytefight.org/match/{matchUuid}`. `get_replay()` scrapes the page, follows
  the signed URL, and returns the parsed PGN (turn-indexed parallel arrays).

Auth:
  - Public endpoints (`/api/v1/public/*`, `/api/v1/ping`) are fully anonymous. This covers
    list-matches, leaderboard, ladder config, team-stats, glicko-history — i.e. EVERYTHING
    needed to poll scrimmage results 24/7 without login.
  - All other endpoints (my-team, list-own-submissions, upload, set-current, scrimmage)
    require `Authorization: Bearer <jwt>`. The JWT lives in bytefight.org's browser
    localStorage / cookies — it's omitted from Chrome HAR exports for security.
    Provide the JWT via tools/bytefight_session.json `{"bearer_token": "..."}` or
    BYTEFIGHT_BEARER env var, or pass --bearer on the CLI.
  - POST /api/v1/submission/team/{teamUuid} (upload) and POST /api/v1/game-match
    (scrimmage) ALSO require a Cloudflare Turnstile token in `cf-turnstile-response`.
    Provide via CAPSOLVER_KEY env var (the client calls CAPSOLVER's
    AntiTurnstileTaskProxyLess API). Without a solver, upload/scrimmage raise
    TurnstileRequired.
  - PATCH /api/v1/team/{teamUuid}/current-submission needs Bearer but NOT Turnstile —
    so set-current is fully scriptable with just the JWT.

Usage (CLI):
    python tools/bytefight_client.py list-submissions
    python tools/bytefight_client.py list-matches
    python tools/bytefight_client.py set-current --submission-id UUID
    python tools/bytefight_client.py poll --match-uuid UUID
    python tools/bytefight_client.py resolve-opponent --name Carrie
    python tools/bytefight_client.py upload --zip PATH [--name X] [--auto-set]
    python tools/bytefight_client.py scrimmage --opponent Carrie [--count 1]
    python tools/bytefight_client.py replay --match-uuid UUID [--save PATH]

All write operations accept --dry-run to print the intended request without
sending it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests


def _load_dotenv() -> None:
    """Auto-load KEY=VALUE pairs from repo-root .env into os.environ (no override)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

# Supabase auth auto-refresh. Local-import-safe if run as script or as package.
try:
    from tools.bytefight_auth import (
        AuthError,
        Session,
        describe_session,
        import_bootstrap,
        load_session,
        refresh_if_needed,
    )
except ImportError:
    _HERE = Path(__file__).resolve().parent
    sys.path.insert(0, str(_HERE))
    from bytefight_auth import (  # type: ignore[no-redef]
        AuthError,
        Session,
        describe_session,
        import_bootstrap,
        load_session,
        refresh_if_needed,
    )


REPO_ROOT = Path(__file__).resolve().parent.parent
SESSION_PATH_DEFAULT = REPO_ROOT / "tools" / "bytefight_session.json"

API_BASE = "https://server.bytefight.org"
SITE_BASE = "https://bytefight.org"
COMPETITION_SLUG = "cs3600_sp2026"

# Match result codes from the match-page JS bundle (entry 7 of view_results HAR).
# `let P=function(e){return e[e.TEAM_A_WIN=0]="TEAM_A_WIN",e[e.TEAM_B_WIN=1]="TEAM_B_WIN",e[e.DRAW=2]="DRAW",e}({});`
RESULT_CODES = {0: "TEAM_A_WIN", 1: "TEAM_B_WIN", 2: "DRAW"}
DEFAULT_TEAM_UUID = "81513423-e93e-4fe5-8a2f-cc0423ccb953"  # Team 15 — override via env/session/flag
# Extracted from https://bytefight.org — widget site key (public by design).
TURNSTILE_SITE_KEY = "0x4AAAAAACq7wjGZKYGP8Yr0"
TURNSTILE_PAGE_URL = "https://bytefight.org/"
DEFAULT_TIMEOUT_S = 30.0
UPLOAD_TIMEOUT_S = 120.0
MAX_RETRIES_5XX = 3

# Chrome UA string from HAR — presented to match the captured session's fingerprint.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
)
BROWSER_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "origin": "https://bytefight.org",
    "referer": "https://bytefight.org/",
    "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": DEFAULT_USER_AGENT,
}


class BytefightError(Exception):
    pass


class TurnstileRequired(BytefightError):
    """Raised when an endpoint needs a Turnstile token but no solver is configured."""


def _load_session(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_session(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _solve_turnstile_capsolver(api_key: str, site_key: str, page_url: str, timeout_s: float = 120.0) -> str:
    """Submit a Turnstile task to CAPSOLVER and poll until solved. Returns the token string."""
    create = requests.post(
        "https://api.capsolver.com/createTask",
        json={
            "clientKey": api_key,
            "task": {
                "type": "AntiTurnstileTaskProxyLess",
                "websiteURL": page_url,
                "websiteKey": site_key,
            },
        },
        timeout=30,
    )
    create.raise_for_status()
    j = create.json()
    if j.get("errorId"):
        raise BytefightError(f"CAPSOLVER createTask failed: {j}")
    task_id = j["taskId"]
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(3)
        poll = requests.post(
            "https://api.capsolver.com/getTaskResult",
            json={"clientKey": api_key, "taskId": task_id},
            timeout=30,
        )
        poll.raise_for_status()
        r = poll.json()
        if r.get("errorId"):
            raise BytefightError(f"CAPSOLVER getTaskResult failed: {r}")
        status = r.get("status")
        if status == "ready":
            return r["solution"]["token"]
        # else "processing" — keep polling
    raise BytefightError("CAPSOLVER timed out")


class BytefightClient:
    def __init__(
        self,
        session_path: Path = SESSION_PATH_DEFAULT,
        *,
        team_uuid: str | None = None,
        bearer_token: str | None = None,
        competition_slug: str = COMPETITION_SLUG,
        turnstile_solver: str | None = None,  # "capsolver" or None
        capsolver_key: str | None = None,
        rate_limit_s: float = 1.0,
        dry_run: bool = False,
    ):
        self.session_path = Path(session_path)
        self.competition_slug = competition_slug
        self.turnstile_solver = turnstile_solver or (
            "capsolver" if os.environ.get("CAPSOLVER_KEY") else None
        )
        self.capsolver_key = capsolver_key or os.environ.get("CAPSOLVER_KEY")
        self.rate_limit_s = rate_limit_s
        self.dry_run = dry_run
        self._last_request_at = 0.0

        session_blob = _load_session(self.session_path)
        self.team_uuid = (
            team_uuid
            or os.environ.get("BYTEFIGHT_TEAM_UUID")
            or session_blob.get("team_uuid")
            or DEFAULT_TEAM_UUID
        )
        # Explicit bearer override (CLI/env) wins. Otherwise we drive auth from
        # the Supabase session file via `bytefight_auth`.
        self.bearer_token = bearer_token or os.environ.get("BYTEFIGHT_BEARER")
        self._session_blob = session_blob
        self._auth_session: Session | None = load_session(self.session_path)
        self.http = requests.Session()
        self.http.headers.update(BROWSER_HEADERS)
        self._apply_auth_header()

    def _apply_auth_header(self) -> None:
        """Sets Authorization header from explicit bearer, else from the loaded Session."""
        token = self.bearer_token
        if not token and self._auth_session is not None:
            token = self._auth_session.access_token
        if token:
            self.http.headers["authorization"] = f"Bearer {token}"
        else:
            self.http.headers.pop("authorization", None)

    def ensure_fresh_auth(self, *, force: bool = False) -> None:
        """If we have a Supabase session, refresh it when expiring soon (or forced)."""
        if self.bearer_token is not None:
            # Explicit override in play — don't touch Supabase flow.
            return
        if not self.session_path.exists():
            return
        try:
            self._auth_session = refresh_if_needed(self.session_path, force=force)
        except AuthError:
            raise
        self._apply_auth_header()

    # --- core ---
    def _rate_limit(self) -> None:
        now = time.monotonic()
        wait = self.rate_limit_s - (now - self._last_request_at)
        if wait > 0:
            time.sleep(wait)
        self._last_request_at = time.monotonic()

    def _request(self, method: str, path: str, *, timeout: float = DEFAULT_TIMEOUT_S, **kwargs) -> requests.Response:
        url = urljoin(API_BASE, path)
        if self.dry_run and method.upper() not in ("GET", "HEAD", "OPTIONS"):
            print(f"[DRY-RUN] would {method} {url}")
            if "json" in kwargs:
                print(f"[DRY-RUN]   json={kwargs['json']}")
            if "files" in kwargs or "data" in kwargs:
                print(f"[DRY-RUN]   multipart present")
            raise SystemExit(0)
        # Opportunistic pre-flight refresh if the current access token is near-expiry.
        try:
            self.ensure_fresh_auth()
        except AuthError:
            # If pre-flight refresh fails, fall through — the request may still be a
            # public endpoint (ping, leaderboard, list-matches) that works without auth.
            pass
        last_exc: Exception | None = None
        did_401_refresh = False
        for attempt in range(MAX_RETRIES_5XX + 1):
            self._rate_limit()
            try:
                resp = self.http.request(method, url, timeout=timeout, **kwargs)
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                if attempt < MAX_RETRIES_5XX:
                    time.sleep(2 ** attempt)  # 1, 2, 4 seconds
                    continue
                raise BytefightError(f"{method} {path}: network error after retries: {exc}")
            if resp.status_code == 401:
                # Try forced refresh exactly once, then retry the same request.
                if not did_401_refresh and self._auth_session is not None and self.bearer_token is None:
                    did_401_refresh = True
                    try:
                        self.ensure_fresh_auth(force=True)
                    except AuthError as exc:
                        raise BytefightError(
                            f"401 Unauthorized on {method} {path}; refresh failed: {exc}. "
                            "Re-run `python tools/bytefight_client.py bootstrap-auth`."
                        )
                    # Re-apply auth header into the per-call headers kwarg if it pinned one.
                    # (We already updated the session default headers in _apply_auth_header.)
                    continue
                raise BytefightError(
                    f"401 Unauthorized on {method} {path} — "
                    "run `python tools/bytefight_client.py bootstrap-auth` to set up Supabase session"
                )
            if resp.status_code == 403:
                raise BytefightError(f"403 Forbidden on {method} {path}")
            if resp.status_code == 429:
                raise BytefightError(f"429 rate limit on {method} {path}")
            if 500 <= resp.status_code < 600 and attempt < MAX_RETRIES_5XX:
                time.sleep(2 ** attempt)
                continue
            return resp
        raise BytefightError(f"{method} {path}: retries exhausted ({last_exc})")

    def _get_turnstile_token(self) -> str:
        if self.turnstile_solver == "capsolver":
            if not self.capsolver_key:
                raise TurnstileRequired("CAPSOLVER_KEY env var required")
            return _solve_turnstile_capsolver(self.capsolver_key, TURNSTILE_SITE_KEY, TURNSTILE_PAGE_URL)
        raise TurnstileRequired(
            "This endpoint requires a Cloudflare Turnstile token. Set CAPSOLVER_KEY "
            "or pass --capsolver-key to enable automated solving."
        )

    # --- read-only endpoints (no Turnstile, no auth) ---
    def ping(self) -> bool:
        resp = self._request("GET", "/api/v1/ping")
        return resp.ok

    def get_ladders(self) -> list[dict]:
        resp = self._request("GET", f"/api/v1/public/ladder/{self.competition_slug}")
        resp.raise_for_status()
        return resp.json()

    def get_my_team(self) -> dict:
        """May fail without auth — but worth probing. Falls back to cached session value."""
        resp = self._request("GET", f"/api/v1/competition/{self.competition_slug}/teams/my-team")
        if resp.status_code == 401 or resp.status_code == 403:
            raise BytefightError("my-team requires auth. Use --team-uuid directly.")
        resp.raise_for_status()
        data = resp.json()
        # Opportunistically cache the team_uuid
        team_uuid = data.get("team", {}).get("uuid") or data.get("teamUuid") or data.get("uuid")
        if team_uuid and not self.team_uuid:
            self.team_uuid = team_uuid
            self._session_blob["team_uuid"] = team_uuid
            _save_session(self.session_path, self._session_blob)
        return data

    def list_submissions(self) -> list[dict]:
        self._require_team()
        resp = self._request("GET", f"/api/v1/submission/team/{self.team_uuid}")
        resp.raise_for_status()
        return resp.json()

    def get_storage_status(self) -> dict:
        self._require_team()
        resp = self._request("GET", f"/api/v1/submission/team/{self.team_uuid}/status")
        resp.raise_for_status()
        return resp.json()

    def list_matches(self, page: int = 0, size: int = 20, team_uuid: str | None = None) -> dict:
        team = team_uuid or self.team_uuid
        self._require_team(team)
        resp = self._request(
            "GET",
            "/api/v1/public/game-match",
            params={
                "competitionSlug": self.competition_slug,
                "teamUuid": team,
                "page": page,
                "size": size,
            },
        )
        resp.raise_for_status()
        return resp.json()

    def get_match(self, match_uuid: str) -> dict | None:
        """Find a match by UUID via list-matches paging. Returns None if not found in first 200."""
        self._require_team()
        for page in range(10):
            data = self.list_matches(page=page, size=20)
            for m in data.get("content", []):
                if m["uuid"] == match_uuid:
                    return m
            if len(data.get("content", [])) < 20:
                break
        return None

    def get_replay(self, match_uuid: str) -> dict:
        """Fetch per-turn replay (PGN) for a finished match.

        The signed `server.bytefight.org/files/<fileUuid>?exp&sig` download URL is not
        served by any JSON API — it is embedded server-side in the HTML at
        `bytefight.org/match/<matchUuid>`. We scrape it, follow the link, parse JSON.

        Returns a dict with:
          - `match_uuid`: the input uuid
          - `signed_url`: the resolved `/files/...` URL we downloaded from
          - `result_code`: 0/1/2
          - `result`: "TEAM_A_WIN" | "TEAM_B_WIN" | "DRAW" (derived from `result_code`)
          - `reason`: str (WinReason — e.g. "max_turns", "illegal_move", "out_of_time")
          - `turn_count`: int
          - `final_score`: {"a": int, "b": int}
          - `pgn`: the full raw PGN (parallel arrays keyed by turn index: a_pos, b_pos,
            a_points, b_points, a_turns_left, b_turns_left, a_time_left, b_time_left,
            rat_position_history, rat_caught, left_behind, new_carpets, blocked_positions,
            errlog_a, errlog_b, ...)

        Raises BytefightError if the match page doesn't embed a signed URL (e.g. the
        match is still running, 404, or the page layout changed).
        """
        import html as _html
        import re

        # Match page is a public anonymous Next.js SSR doc — no Authorization header.
        page_url = f"{SITE_BASE}/match/{match_uuid}"
        self._rate_limit()
        # Bypass the _request auth-refresh flow; this host is bytefight.org not the API.
        r = requests.get(
            page_url,
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "accept-language": BROWSER_HEADERS["accept-language"],
                "user-agent": DEFAULT_USER_AGENT,
            },
            timeout=DEFAULT_TIMEOUT_S,
        )
        if r.status_code == 404:
            raise BytefightError(f"match page 404 for {match_uuid} — does it exist?")
        r.raise_for_status()
        body = r.text

        # Extract the signed `/files/<uuid>?exp=...&sig=...` URL. Appears twice in the
        # HTML: once HTML-entity-encoded (&amp;) in the <a href>, once Unicode-escaped
        # (\u0026) in the RSC stream. Either works; pick the href form and decode.
        m = re.search(
            r'href="(https://server\.bytefight\.org/files/[a-f0-9-]+\?[^"]+)"',
            body,
        )
        if not m:
            # Fallback: look for the \u0026 form in the RSC stream
            m = re.search(
                r'"(https://server\.bytefight\.org/files/[a-f0-9-]+\?exp=\d+\\u0026sig=[A-Za-z0-9_-]+)"',
                body,
            )
        if not m:
            raise BytefightError(
                f"no /files/ signed URL found in match page for {match_uuid}. "
                "Match may still be running, failed to produce a PGN, or page layout changed."
            )
        signed_url = _html.unescape(m.group(1)).replace("\\u0026", "&")

        # Follow the signed URL — also public, no auth needed.
        self._rate_limit()
        r2 = requests.get(
            signed_url,
            headers={
                "accept": "application/json,*/*;q=0.8",
                "accept-language": BROWSER_HEADERS["accept-language"],
                "referer": f"{SITE_BASE}/",
                "user-agent": DEFAULT_USER_AGENT,
            },
            timeout=DEFAULT_TIMEOUT_S,
        )
        if r2.status_code == 403:
            raise BytefightError(
                f"signed URL returned 403 — the `sig` may have expired. Re-fetch the match page "
                "to get a fresh signature."
            )
        r2.raise_for_status()
        pgn = r2.json()

        result_code = pgn.get("result")
        turn_count = pgn.get("turn_count", 0)
        a_points = (pgn.get("a_points") or [0])
        b_points = (pgn.get("b_points") or [0])
        return {
            "match_uuid": match_uuid,
            "signed_url": signed_url,
            "result_code": result_code,
            "result": RESULT_CODES.get(result_code, f"UNKNOWN({result_code})"),
            "reason": pgn.get("reason"),
            "turn_count": turn_count,
            "final_score": {"a": a_points[-1], "b": b_points[-1]},
            "pgn": pgn,
        }

    def list_leaderboard(self, ladder: str = "ranked") -> list[dict]:
        resp = self._request("GET", f"/api/v1/public/leaderboard/{self.competition_slug}/{ladder}")
        resp.raise_for_status()
        return resp.json()

    def resolve_opponent(self, name_or_uuid: str) -> str:
        """Return a team UUID given either a UUID (returned as-is) or a teamName from the leaderboard."""
        # Heuristic: UUID pattern has 36 chars with 4 dashes
        if len(name_or_uuid) == 36 and name_or_uuid.count("-") == 4:
            return name_or_uuid
        lb = self.list_leaderboard()
        for team in lb:
            if team.get("teamName") == name_or_uuid:
                return team["teamUuid"]
        matches = [t for t in lb if t.get("teamName", "").lower() == name_or_uuid.lower()]
        if matches:
            return matches[0]["teamUuid"]
        raise BytefightError(f"Team {name_or_uuid!r} not found on leaderboard")

    # --- mutating endpoints WITHOUT Turnstile ---
    def set_current_submission(self, submission_uuid: str) -> None:
        self._require_team()
        resp = self._request(
            "PATCH",
            f"/api/v1/team/{self.team_uuid}/current-submission",
            json={"submissionUuid": submission_uuid},
            headers={"content-type": "application/json"},
        )
        resp.raise_for_status()

    # --- mutating endpoints WITH Turnstile ---
    def upload_zip(self, zip_path: str | Path, description: str = "Uploaded via bytefight_client", is_auto_set: bool = False) -> dict:
        self._require_team()
        zip_path = Path(zip_path)
        if not zip_path.is_file():
            raise BytefightError(f"zip not found: {zip_path}")
        token = self._get_turnstile_token()
        with open(zip_path, "rb") as f:
            files = {
                "description": (None, description),
                "file": (zip_path.name, f, "application/x-zip-compressed"),
                "isAutoSet": (None, "true" if is_auto_set else "false"),
            }
            resp = self._request(
                "POST",
                f"/api/v1/submission/team/{self.team_uuid}",
                files=files,
                headers={"cf-turnstile-response": token},
                timeout=UPLOAD_TIMEOUT_S,
            )
        resp.raise_for_status()
        return resp.json()

    def start_scrimmage(self, opponent: str, count: int = 1, map_setting: Any = None, ladder: str = "scrimmage") -> list[dict]:
        self._require_team()
        opponent_uuid = self.resolve_opponent(opponent)
        token = self._get_turnstile_token()
        body = {
            "competitionSlug": self.competition_slug,
            "ladder": ladder,
            "teamAUuid": self.team_uuid,
            "teamBUuid": opponent_uuid,
            "count": int(count),
            "matchSettings": {"map": map_setting},
        }
        resp = self._request(
            "POST",
            "/api/v1/game-match",
            json=body,
            headers={
                "content-type": "application/json",
                "cf-turnstile-response": token,
            },
        )
        resp.raise_for_status()
        return resp.json()

    # --- helpers ---
    def poll_match(self, match_uuid: str, *, interval_s: float = 10.0, timeout_s: float = 1200.0) -> dict:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            m = self.get_match(match_uuid)
            if m is None:
                raise BytefightError(f"match {match_uuid} not found")
            status = m.get("status")
            if status and status != "waiting" and status != "running" and m.get("finishedAt"):
                return m
            if status in ("team_a_win", "team_b_win", "draw", "error"):
                return m
            time.sleep(interval_s)
        raise BytefightError(f"poll timed out for match {match_uuid}")

    def _require_team(self, team_uuid: str | None = None) -> None:
        if not (team_uuid or self.team_uuid):
            raise BytefightError(
                "team_uuid not set. Pass --team-uuid, edit tools/bytefight_session.json, "
                "or call get-my-team to populate it."
            )


# --- CLI ---
def _find_bootstrap_file() -> Path | None:
    """Look for `bytefight_session_bootstrap.json` in common Downloads locations."""
    candidates = [
        Path.home() / "Downloads" / "bytefight_session_bootstrap.json",
        Path("C:/Users/rahil/Downloads/bytefight_session_bootstrap.json"),
        REPO_ROOT / "bytefight_session_bootstrap.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _fmt_submissions(subs: list[dict]) -> str:
    rows = ["{:<38}  {:<45}  {:<20}".format("uuid", "name", "validity")]
    for s in subs:
        rows.append("{:<38}  {:<45}  {:<20}".format(s["uuid"], s["name"][:45], s.get("validity", "")))
    return "\n".join(rows)


def _fmt_matches(resp: dict) -> str:
    rows = ["{:<38}  {:<20}  {:<12}  {:<18}  {:<18}".format("uuid", "opp", "status", "scheduled", "finished")]
    for m in resp.get("content", []):
        opp = m.get("teamBName") if m.get("teamAUuid") != m.get("teamBUuid") else "(self)"
        rows.append("{:<38}  {:<20}  {:<12}  {:<18}  {:<18}".format(
            m["uuid"][:38], str(opp)[:20], m.get("status", ""),
            (m.get("scheduledAt") or "")[:16], (m.get("finishedAt") or "")[:16],
        ))
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bytefight tournament API client")
    p.add_argument("--team-uuid", help="override team UUID (else read from tools/bytefight_session.json)")
    p.add_argument("--bearer", help="Bearer JWT (else read from $BYTEFIGHT_BEARER or session.json)")
    p.add_argument("--competition-slug", default=COMPETITION_SLUG)
    p.add_argument("--session-path", default=str(SESSION_PATH_DEFAULT))
    p.add_argument("--capsolver-key", help="CAPSOLVER API key (else read from $CAPSOLVER_KEY)")
    p.add_argument("--dry-run", action="store_true", help="for mutating ops, print intended request and exit")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ping")
    sub.add_parser("my-team")
    sub.add_parser("list-submissions")
    sub.add_parser("list-leaderboard")
    sub.add_parser("storage-status")
    sub.add_parser("auth-status")

    ba = sub.add_parser("bootstrap-auth", help="import a browser-downloaded bootstrap JSON into session.json")
    ba.add_argument("--from", dest="from_path", default=None,
                    help="path to bytefight_session_bootstrap.json (auto-detect Downloads if omitted)")

    ra = sub.add_parser("refresh-auth", help="force a Supabase refresh and persist the new tokens")

    lm = sub.add_parser("list-matches")
    lm.add_argument("--page", type=int, default=0)
    lm.add_argument("--size", type=int, default=20)

    gm = sub.add_parser("get-match")
    gm.add_argument("--match-uuid", required=True)

    ro = sub.add_parser("resolve-opponent")
    ro.add_argument("--name", required=True)

    sc = sub.add_parser("set-current")
    sc.add_argument("--submission-id", required=True)

    up = sub.add_parser("upload")
    up.add_argument("--zip", required=True)
    up.add_argument("--description", default="Uploaded via bytefight_client")
    up.add_argument("--auto-set", action="store_true")

    sg = sub.add_parser("scrimmage")
    sg.add_argument("--opponent", required=True, help="team name or UUID")
    sg.add_argument("--count", type=int, default=1)
    sg.add_argument("--ladder", default="scrimmage")

    po = sub.add_parser("poll")
    po.add_argument("--match-uuid", required=True)
    po.add_argument("--interval", type=float, default=10.0)
    po.add_argument("--timeout", type=float, default=1200.0)

    rp = sub.add_parser("replay", help="fetch per-turn PGN for a finished match")
    rp.add_argument("--match-uuid", required=True)
    rp.add_argument("--save", help="if set, write full PGN JSON to this path")
    rp.add_argument("--full", action="store_true", help="print full PGN to stdout (otherwise just a summary)")

    args = p.parse_args(argv)
    client = BytefightClient(
        session_path=Path(args.session_path),
        team_uuid=args.team_uuid,
        bearer_token=args.bearer,
        competition_slug=args.competition_slug,
        capsolver_key=args.capsolver_key,
        dry_run=args.dry_run,
    )

    try:
        if args.cmd == "bootstrap-auth":
            from_path = Path(args.from_path) if args.from_path else _find_bootstrap_file()
            if not from_path or not from_path.exists():
                print(
                    "[error] bootstrap file not found. Capture steps:\n"
                    "  1. Log into https://bytefight.org in Chrome.\n"
                    "  2. Have an ops agent run `tools/chrome_snippets/bootstrap_bytefight_session.js`\n"
                    "     via the claude-in-chrome MCP javascript_tool; it downloads\n"
                    "     `bytefight_session_bootstrap.json` to your Downloads folder.\n"
                    "  3. Re-run `python tools/bytefight_client.py bootstrap-auth`.",
                    file=sys.stderr,
                )
                return 1
            sess = import_bootstrap(Path(args.session_path), from_path)
            print("imported session:")
            for k, v in describe_session(sess).items():
                print(f"  {k}: {v}")
            return 0
        if args.cmd == "refresh-auth":
            from bytefight_auth import refresh_if_needed as _refresh  # local name
            sess = _refresh(Path(args.session_path), force=True)
            print("refreshed:")
            for k, v in describe_session(sess).items():
                print(f"  {k}: {v}")
            return 0
        if args.cmd == "auth-status":
            if client._auth_session is None:
                print("no session. run `bootstrap-auth`.")
                return 1
            for k, v in describe_session(client._auth_session).items():
                print(f"  {k}: {v}")
            return 0
        if args.cmd == "ping":
            print("OK" if client.ping() else "FAIL")
        elif args.cmd == "my-team":
            print(json.dumps(client.get_my_team(), indent=2))
        elif args.cmd == "list-submissions":
            print(_fmt_submissions(client.list_submissions()))
        elif args.cmd == "list-leaderboard":
            for t in client.list_leaderboard():
                print(f"{t['rank']:>3}  {t['teamUuid']}  {t.get('teamName', ''):<24}  glicko={t.get('glicko', 0):.1f}")
        elif args.cmd == "storage-status":
            print(json.dumps(client.get_storage_status(), indent=2))
        elif args.cmd == "list-matches":
            print(_fmt_matches(client.list_matches(page=args.page, size=args.size)))
        elif args.cmd == "get-match":
            m = client.get_match(args.match_uuid)
            print(json.dumps(m, indent=2) if m else "not found")
        elif args.cmd == "resolve-opponent":
            print(client.resolve_opponent(args.name))
        elif args.cmd == "set-current":
            client.set_current_submission(args.submission_id)
            print(f"set current submission -> {args.submission_id}")
        elif args.cmd == "upload":
            result = client.upload_zip(args.zip, description=args.description, is_auto_set=args.auto_set)
            print(json.dumps(result, indent=2))
        elif args.cmd == "scrimmage":
            result = client.start_scrimmage(args.opponent, count=args.count, ladder=args.ladder)
            for m in result:
                print(f"scrimmage queued: {m['uuid']}  {m.get('teamAName')} vs {m.get('teamBName')}")
        elif args.cmd == "poll":
            m = client.poll_match(args.match_uuid, interval_s=args.interval, timeout_s=args.timeout)
            print(json.dumps(m, indent=2))
        elif args.cmd == "replay":
            rep = client.get_replay(args.match_uuid)
            if args.save:
                save_path = Path(args.save)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_text(json.dumps(rep["pgn"], indent=2), encoding="utf-8")
                print(f"wrote {save_path}")
            if args.full:
                print(json.dumps(rep, indent=2))
            else:
                pgn = rep["pgn"]
                summary = {
                    "match_uuid": rep["match_uuid"],
                    "result": rep["result"],
                    "reason": rep["reason"],
                    "turn_count": rep["turn_count"],
                    "final_score": rep["final_score"],
                    "blocked_positions": pgn.get("blocked_positions"),
                    "signed_url": rep["signed_url"],
                    "pgn_keys": sorted(pgn.keys()),
                    "errlog_a_len": len((pgn.get("errlog_a") or "").strip()),
                    "errlog_b_len": len((pgn.get("errlog_b") or "").strip()),
                }
                print(json.dumps(summary, indent=2))
    except TurnstileRequired as e:
        print(f"[turnstile] {e}", file=sys.stderr)
        return 2
    except BytefightError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1
    except requests.HTTPError as e:
        print(f"[http] {e}  body={e.response.text[:400] if e.response is not None else ''}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
