# bytefight_client — programmatic bytefight.org client

Pure-Python client for the tournament API. Replaces Chrome MCP / manual-click UI flows with a small CLI + library.

## Endpoints (from HAR capture 2026-04-17)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET    | /api/v1/ping                                            | none   | liveness |
| GET    | /api/v1/public/ladder/{slug}                            | none   | list ladders for competition |
| GET    | /api/v1/public/leaderboard/{slug}/ranked                | none   | full team list (name→uuid lookup) |
| GET    | /api/v1/public/team-stats/{teamUuid}                    | none   | w/l/d + glicko |
| GET    | /api/v1/public/glicko-history/{teamUuid}/{ladder}       | none   | glicko timeseries |
| GET    | /api/v1/public/game-match?competitionSlug&teamUuid&...  | none   | list matches (POLL HERE) |
| GET    | /api/v1/public/game-match/queue/{slug}?page&size        | none   | global queue |
| GET    | /api/v1/competition/{slug}/teams/my-team                | Bearer | own team info |
| GET    | /api/v1/submission/team/{teamUuid}                      | Bearer | list own submissions |
| GET    | /api/v1/submission/team/{teamUuid}/status               | Bearer | storage usage |
| POST   | /api/v1/submission/team/{teamUuid}                      | Bearer + Turnstile | upload zip (multipart: description, file, isAutoSet) |
| PATCH  | /api/v1/team/{teamUuid}/current-submission              | Bearer | set active submission (JSON: `{submissionUuid}`) |
| POST   | /api/v1/game-match                                      | Bearer + Turnstile | create scrimmage (JSON: `{competitionSlug, ladder:"scrimmage", teamAUuid, teamBUuid, count, matchSettings:{map:null}}`) |
| GET    | https://bytefight.org/match/{matchUuid}                 | none   | HTML match page — embeds signed PGN URL (scrape via `get_replay`) |
| GET    | https://server.bytefight.org/files/{fileUuid}?exp&sig   | none   | signed PGN download (sig expires ~1hr after page render) |

**Turnstile site key:** `0x4AAAAAACq7wjGZKYGP8Yr0` (bytefight.org). Page URL: `https://bytefight.org/`.

## Auto-refresh (Supabase refresh_token)

Bytefight authenticates via **Supabase** (project ref `pblznfkajrasiprcohrx`). The browser
stores the full Supabase session — `{access_token, refresh_token, expires_at, user}` — in a
JS-readable cookie `sb-pblznfkajrasiprcohrx-auth-token` (base64 JSON). Access tokens expire
every ~1hr; refresh tokens are long-lived and rotate on every use.

`tools/bytefight_auth.py` handles this end-to-end. After a **one-time bootstrap**, the client
keeps the JWT fresh indefinitely with zero browser interaction:

- **Pre-flight:** every request calls `ensure_fresh_auth()`, which refreshes when the cached
  access_token has ≤60s of TTL left. The refresh hits
  `POST https://pblznfkajrasiprcohrx.supabase.co/auth/v1/token?grant_type=refresh_token`
  with `{apikey: <anon_key>, content-type: application/json}` and body
  `{"refresh_token": "..."}`. Response = new access_token + rotated refresh_token,
  persisted atomically to `bytefight_session.json`.
- **401 recovery:** if a request still returns 401, client force-refreshes once and retries.
- **Poller inheritance:** `bytefight_poll.py` uses `BytefightClient` and inherits auto-refresh
  (though the public endpoints it hits don't need auth anyway).

### One-time bootstrap

1. Log in at `https://bytefight.org` in Chrome.
2. Have an agent with `claude-in-chrome` MCP run `tools/chrome_snippets/bootstrap_bytefight_session.js`
   via the `javascript_tool` against the bytefight.org tab. It extracts the session + anon key
   and downloads `bytefight_session_bootstrap.json` to your Downloads folder.
3. Run `python tools/bytefight_client.py bootstrap-auth` — auto-detects the Downloads file
   and imports it into gitignored `tools/bytefight_session.json`.

From then on it's fully headless. Re-bootstrap only if:
- the user logs out of all devices (invalidates refresh_token), or
- bytefight changes auth provider.

### CLI auth commands

```bash
python tools/bytefight_client.py bootstrap-auth              # import Downloads/bytefight_session_bootstrap.json
python tools/bytefight_client.py bootstrap-auth --from PATH  # import from explicit path
python tools/bytefight_client.py refresh-auth                # force refresh now (rotates refresh_token)
python tools/bytefight_client.py auth-status                 # masked summary + TTL
```

### Manual override (legacy)

- env var `BYTEFIGHT_BEARER=eyJ...`
- CLI flag `--bearer eyJ...`

When an explicit bearer is set, auto-refresh is disabled.

### 2. Turnstile solver (CAPSOLVER)

Upload and scrimmage-create are gated behind Cloudflare Turnstile. Integrate CAPSOLVER's [AntiTurnstileTaskProxyLess](https://docs.capsolver.com/guide/captcha/turnstile.html):

```
export CAPSOLVER_KEY=CAP-XXXXXXXXXXXXXX...
```

Without it, only set-current + read endpoints work. set-current alone still dramatically improves the workflow (swap active submission between scrimmage windows without clicks).

## CLI reference

```bash
# Read-only (no auth needed)
python tools/bytefight_client.py ping
python tools/bytefight_client.py list-matches --size 20
python tools/bytefight_client.py list-leaderboard
python tools/bytefight_client.py resolve-opponent --name Carrie    # -> UUID
python tools/bytefight_client.py get-match --match-uuid <uuid>
python tools/bytefight_client.py poll --match-uuid <uuid> --interval 10 --timeout 1200
python tools/bytefight_client.py replay --match-uuid <uuid>                  # summary (result, score, turn count, PGN key list)
python tools/bytefight_client.py replay --match-uuid <uuid> --save out.json  # write full PGN JSON to disk
python tools/bytefight_client.py replay --match-uuid <uuid> --full           # print the full PGN JSON to stdout

# Requires Bearer (no Turnstile)
python tools/bytefight_client.py my-team
python tools/bytefight_client.py list-submissions
python tools/bytefight_client.py storage-status
python tools/bytefight_client.py set-current --submission-id <uuid>

# Requires Bearer + Turnstile (CAPSOLVER_KEY)
python tools/bytefight_client.py upload --zip tools/scratch/RattleBot_v03_prebo.zip --description "v0.3 prebo" [--auto-set]
python tools/bytefight_client.py scrimmage --opponent Carrie --count 1

# Dry-run any mutating command to preview the request
python tools/bytefight_client.py --dry-run set-current --submission-id <uuid>
python tools/bytefight_client.py --dry-run scrimmage --opponent George
```

## Library usage

```python
from tools.bytefight_client import BytefightClient

c = BytefightClient()  # reads session.json, env vars
subs = c.list_submissions()
c.set_current_submission(subs[0]["uuid"])
matches = c.start_scrimmage("Carrie", count=3)
for m in matches:
    result = c.poll_match(m["uuid"])
    print(m["uuid"], result["status"])
    if result["status"] in ("team_a_win", "team_b_win", "draw"):
        rep = c.get_replay(m["uuid"])
        print(f"  -> {rep['result']} by {rep['reason']} in {rep['turn_count']} turns")
        print(f"     final: A={rep['final_score']['a']}  B={rep['final_score']['b']}")
        # rep["pgn"] is the full per-turn log — feed to loss-forensics
```

## Response schemas (observed)

**Submission:**
```json
{"uuid": "...", "teamUuid": "...", "name": "Foo.zip",
 "validity": "valid" | "not_evaluated_autoset" | "invalid",
 "timestampsDto": {"createdAt": "...", "updatedAt": "..."}}
```

**Match (list item):**
```json
{"uuid": "...", "competitionSlug": "cs3600_sp2026",
 "teamAName": "...", "teamBName": "...",
 "teamAUuid": "...", "teamBUuid": "...",
 "submissionAName": "...", "submissionBName": "...",
 "matchSettings": {"map": null},
 "status": "waiting" | "team_a_win" | "team_b_win" | "draw" | "error" | ...,
 "reason": "scrimmage" | "matchmaking",
 "scheduledAt": "...", "startedAt": "...", "finishedAt": "...",
 "timestampsDto": {...}}
```

**Replay** (implemented via `get_replay(match_uuid)`):
Per-match PGN is NOT served from a JSON API. The signed `/files/<fileUuid>?exp=...&sig=...`
download URL is embedded as an `<a href download>` link inside the server-rendered HTML
at `https://bytefight.org/match/{matchUuid}`. Both the match page and the signed URL are
fully public (no Bearer, no Turnstile). `get_replay()`:
1. `GET https://bytefight.org/match/{matchUuid}` — public Next.js SSR HTML page.
2. Regex-extract `href="https://server.bytefight.org/files/...?exp=...&amp;sig=..."`,
   unescape HTML entities.
3. `GET` the signed URL → returns `match.json` (schema below).
4. Return `{match_uuid, signed_url, result, result_code, reason, turn_count, final_score, pgn}`.

`sig` is an HMAC over `(fileUuid, exp)` with a ~1hr expiry bound to the page render. If a
cached `signed_url` returns 403, re-call `get_replay()` — the method always re-scrapes for
a fresh signature.

PGN schema (parallel arrays, index = turn; turn 0 is initial state):
```
a_pos[T]                   [[x,y], ...]       — worker A position per turn (length turn_count+1)
b_pos[T]                   [[x,y], ...]       — worker B position
a_points[T], b_points[T]   [int, ...]         — running scores
a_turns_left[T], b_turns_left[T]              — turns remaining
a_time_left[T], b_time_left[T]                — seconds remaining
rat_position_history[T]    [[x,y], ...]       — rat cell per turn (ground truth; bots never see this)
rat_caught[T]              [bool, ...]
left_behind[T]             ["prime"|"none"|...]  — what the mover dropped this turn
new_carpets[T]             [[[x,y], ...], ...]    — cells converted to CARPET this turn
blocked_positions          [[x,y], ...]        — per-game static blocks (not per-turn)
turn_count                 int
result                     0|1|2 (TEAM_A_WIN|TEAM_B_WIN|DRAW)
reason                     WinReason str (e.g. "POINTS", "ILLEGAL_MOVE", "OUT_OF_TIME")
errlog_a, errlog_b         str — stderr captured from each agent's sandboxed process
```

## Refreshing auth

If bytefight rotates auth schemes or your JWT expires:

1. Log into https://bytefight.org in Chrome.
2. Follow the capture flow in `tools/CAPTURE_INSTRUCTIONS.md`.
3. Re-run `_har_find.py` / `_har_auth.py` in `tools/scratch/` to re-verify endpoint shapes.
4. Update `bytefight_session.json` with the new JWT.

## Security notes

- `tools/scratch/*.har` is gitignored — HARs may embed auth fragments, signed URLs, Turnstile tokens.
- `tools/bytefight_session.json` is gitignored — contains the Bearer JWT.
- Rate limit: client caps at 1 req/sec by default. Bytefight uses Cloudflare — burst too fast and you'll see 429s.
- Always use `--dry-run` first when writing new automation around upload/scrimmage.
