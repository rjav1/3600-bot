"""
Supabase-backed auto-refresh for bytefight.org authentication.

Bytefight auths via Supabase — project ref `pblznfkajrasiprcohrx`. The browser
stores {access_token, refresh_token, expires_at, user, ...} in a JS-readable
cookie `sb-pblznfkajrasiprcohrx-auth-token` (base64-encoded JSON).

Access tokens are 1hr TTL; refresh tokens are long-lived and rotate on every
use. Once bootstrapped (extract session from Chrome once), this module keeps
the Bearer JWT fresh indefinitely without any browser interaction.

Flow:
  1. Bootstrap (one-time, requires logged-in Chrome): manually run
     `python tools/bytefight_client.py bootstrap-auth` which walks the user
     through a claude-in-chrome MCP snippet to download a
     `bytefight_session_bootstrap.json` file, then imports it into
     `tools/bytefight_session.json`.
  2. Refresh (headless, runs automatically when token near-expiry or on 401):
     POST https://pblznfkajrasiprcohrx.supabase.co/auth/v1/token?grant_type=refresh_token
     Headers: apikey: <SUPABASE_ANON_KEY>, Content-Type: application/json
     Body: {"refresh_token": "..."}
     Response: new access + refresh + expires_at. Saves atomically.
"""
from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

SUPABASE_URL = "https://pblznfkajrasiprcohrx.supabase.co"
SUPABASE_PROJECT_REF = "pblznfkajrasiprcohrx"
REFRESH_MARGIN_S = 60  # refresh if access token expires in less than this
REFRESH_TIMEOUT_S = 15.0


class AuthError(Exception):
    pass


@dataclass
class Session:
    access_token: str
    refresh_token: str
    expires_at: int  # unix seconds
    supabase_anon_key: str
    user_id: str | None = None
    user_email: str | None = None
    team_uuid: str | None = None

    def is_expiring_soon(self, margin_s: int = REFRESH_MARGIN_S) -> bool:
        return time.time() + margin_s >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        d = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "supabase_anon_key": self.supabase_anon_key,
            "supabase_url": SUPABASE_URL,
            "supabase_project_ref": SUPABASE_PROJECT_REF,
        }
        if self.user_id is not None:
            d["user_id"] = self.user_id
        if self.user_email is not None:
            d["user_email"] = self.user_email
        if self.team_uuid is not None:
            d["team_uuid"] = self.team_uuid
        return d


def _mask(s: str, keep: int = 4) -> str:
    if not s:
        return "<empty>"
    return f"{s[:keep]}***{s[-keep:]}" if len(s) > 2 * keep else "***"


def load_session(path: Path) -> Session | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    required = ("access_token", "refresh_token", "expires_at", "supabase_anon_key")
    if not all(k in data for k in required):
        return None
    return Session(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_at=int(data["expires_at"]),
        supabase_anon_key=data["supabase_anon_key"],
        user_id=data.get("user_id"),
        user_email=data.get("user_email"),
        team_uuid=data.get("team_uuid"),
    )


def save_session(path: Path, session: Session, extra: dict | None = None) -> None:
    """Atomic write to session file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = session.to_dict()
    if extra:
        data.update(extra)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)


def import_bootstrap(session_path: Path, bootstrap_path: Path) -> Session:
    """Read the browser-downloaded bootstrap file and write it as session.json."""
    with open(bootstrap_path, encoding="utf-8") as f:
        b = json.load(f)
    required = ("access_token", "refresh_token", "expires_at", "supabase_anon_key")
    missing = [k for k in required if k not in b]
    if missing:
        raise AuthError(f"bootstrap file missing keys: {missing}")
    session = Session(
        access_token=b["access_token"],
        refresh_token=b["refresh_token"],
        expires_at=int(b["expires_at"]),
        supabase_anon_key=b["supabase_anon_key"],
        user_id=b.get("user_id"),
        user_email=b.get("user_email"),
        team_uuid=b.get("team_uuid"),
    )
    # Preserve any other fields already in the session.json (e.g., custom metadata)
    extra = {}
    if session_path.exists():
        with open(session_path, encoding="utf-8") as f:
            existing = json.load(f)
        for k, v in existing.items():
            if k not in session.to_dict():
                extra[k] = v
    save_session(session_path, session, extra=extra)
    return session


def refresh_access_token(session: Session) -> Session:
    """POST to Supabase, return NEW Session with rotated refresh_token."""
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
    headers = {
        "apikey": session.supabase_anon_key,
        "authorization": f"Bearer {session.supabase_anon_key}",
        "content-type": "application/json",
        "accept": "application/json",
    }
    body = {"refresh_token": session.refresh_token}
    resp = requests.post(url, headers=headers, json=body, timeout=REFRESH_TIMEOUT_S)
    if not resp.ok:
        raise AuthError(f"supabase refresh failed {resp.status_code}: {resp.text[:300]}")
    j = resp.json()
    if "access_token" not in j or "refresh_token" not in j:
        raise AuthError(f"supabase refresh response malformed: {list(j.keys())}")
    new_expires_at = int(j.get("expires_at") or (time.time() + int(j.get("expires_in", 3600))))
    return Session(
        access_token=j["access_token"],
        refresh_token=j["refresh_token"],
        expires_at=new_expires_at,
        supabase_anon_key=session.supabase_anon_key,
        user_id=(j.get("user", {}) or {}).get("id") or session.user_id,
        user_email=(j.get("user", {}) or {}).get("email") or session.user_email,
        team_uuid=session.team_uuid,
    )


def refresh_if_needed(session_path: Path, *, force: bool = False) -> Session:
    """Load, refresh-if-expiring-soon (or forced), save, return current Session."""
    session = load_session(session_path)
    if session is None:
        raise AuthError(
            f"no session at {session_path}. Run `python tools/bytefight_client.py bootstrap-auth` first."
        )
    if not force and not session.is_expiring_soon():
        return session
    # Back up the old session before overwriting — single rollback slot.
    backup = session_path.with_suffix(session_path.suffix + ".prev")
    try:
        shutil.copy2(session_path, backup)
    except OSError:
        pass
    new_session = refresh_access_token(session)
    # Preserve extra fields from the existing file
    extra = {}
    with open(session_path, encoding="utf-8") as f:
        existing = json.load(f)
    for k, v in existing.items():
        if k not in new_session.to_dict():
            extra[k] = v
    save_session(session_path, new_session, extra=extra)
    return new_session


def describe_session(session: Session) -> dict[str, str]:
    """Return a JSON-safe, masked summary for logging/debugging."""
    now = int(time.time())
    return {
        "access_token": _mask(session.access_token, 6),
        "refresh_token": _mask(session.refresh_token, 4),
        "expires_at": str(session.expires_at),
        "expires_in_s": str(session.expires_at - now),
        "expiring_soon": str(session.is_expiring_soon()),
        "supabase_anon_key": _mask(session.supabase_anon_key, 6),
        "user_email": session.user_email or "<unknown>",
        "team_uuid": session.team_uuid or "<unknown>",
    }
