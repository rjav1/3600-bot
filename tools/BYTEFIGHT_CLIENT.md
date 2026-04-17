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

**Turnstile site key:** `0x4AAAAAACq7wjGZKYGP8Yr0` (bytefight.org). Page URL: `https://bytefight.org/`.

## Auth setup

### 1. Bearer JWT

The API uses `Authorization: Bearer <jwt>`. The JWT is created when you log in through https://bytefight.org and stored in the browser (localStorage/sessionStorage; not an httpOnly cookie — but Chrome's HAR exporter strips the `authorization` header for security, which is why it's not visible in the recorded HAR).

To extract your JWT:

```
1. Open https://bytefight.org (logged in).
2. DevTools → Application tab → Local Storage → https://bytefight.org
3. Look for a key like `accessToken`, `jwt`, `auth`, or a `supabase.auth.token`-shaped blob.
4. Copy the JWT string (begins with `eyJ...`).
```

Alternatively, in the Network tab, pick any authenticated request (e.g., `GET /api/v1/submission/team/...`), click it, and look at the full Request Headers — the `authorization` header IS actually sent, Chrome just strips it during HAR export.

Store it via any of:

- `tools/bytefight_session.json`: `{"bearer_token": "eyJ..."}`
- env var: `export BYTEFIGHT_BEARER=eyJ...`
- CLI flag: `--bearer eyJ...`

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

**Replay**: `GET https://server.bytefight.org/files/<uuid>?exp=<unix>&sig=<signed>` returns the full match JSON. The signed URL is fetched (via Bearer) from a per-match endpoint that wasn't captured — likely `GET /api/v1/public/game-match/{uuid}` or `GET /api/v1/game-match/{uuid}`. Not implemented yet; extend the client once observed.

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
