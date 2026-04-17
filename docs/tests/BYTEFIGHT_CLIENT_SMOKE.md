# BYTEFIGHT_CLIENT_SMOKE — trip report for task #79

**Date:** 2026-04-17
**Author:** bytefight-client
**Status:** KEYLESS PATH PASSES. Bearer + CAPSOLVER paths awaiting credentials.

## What got built

1. `tools/bytefight_client.py` — library + CLI (~400 lines)
2. `tools/bytefight_poll.py` — anonymous match-status poller daemon
3. `tools/BYTEFIGHT_CLIENT.md` — endpoint reference + auth setup guide
4. `tools/CAPTURE_INSTRUCTIONS.md` — Chrome HAR capture flow for future auth refreshes
5. `tools/bytefight_session.json` — team UUID cached; gitignored
6. `.gitignore` — added `tools/scratch/*.har`, `tools/bytefight_session.json`, `tools/bytefight_poll_state.json`, `bytefight_poll_pid.txt`, `.env`

Full endpoint reverse-engineering from the two HARs lives in `tools/BYTEFIGHT_CLIENT.md`.

## Auth reality (discovered during smoke)

- `/api/v1/public/*` and `/api/v1/ping`: **fully anonymous**. No headers needed.
- Everything else (including read-only `/api/v1/submission/team/{uuid}` and
  `/api/v1/competition/{slug}/teams/my-team`): requires **`Authorization: Bearer <JWT>`**.
  Chrome's HAR export scrubs the `authorization` header for security (confirmed: 0 occurrences
  of `authorization`, `cookie`, or `Bearer` across both 7MB HARs). Server returns
  `WWW-Authenticate: Bearer` on 401, confirming JWT-bearer scheme.
- `POST /api/v1/submission/team/{uuid}` (upload) and `POST /api/v1/game-match` (scrimmage):
  require **`cf-turnstile-response`** header in addition to Bearer. Turnstile site key
  `0x4AAAAAACq7wjGZKYGP8Yr0`, page `https://bytefight.org/`.
- `PATCH /api/v1/team/{uuid}/current-submission` (set-current): Bearer only, no Turnstile.

## Smoke results

### PASS — keyless public endpoints

```bash
$ python tools/bytefight_client.py ping
OK

$ python tools/bytefight_client.py list-matches --size 5
<5 rows returned, all waiting/scrimmage>

$ python tools/bytefight_client.py resolve-opponent --name Carrie
6d2a15ad-f175-48db-9fad-e1b5de3f71e2
$ python tools/bytefight_client.py resolve-opponent --name George
13f7ba71-eb75-4b4a-9c48-abb6bb1e8318
$ python tools/bytefight_client.py resolve-opponent --name Albert
5121a2d4-75e2-4ab4-b97f-567aa693ccd9
```

### PASS — anonymous poller daemon

```bash
$ python tools/bytefight_poll.py --once
<20 events appended to docs/tests/LIVE_SCRIMMAGE_LOG.md>
$ python tools/bytefight_poll.py --once       # second run, state-deduped
<exits cleanly, 0 events>
```

Background poller running since 2026-04-17 20:54Z, pid in `bytefight_poll_pid.txt`.
Writes to `## Poller observations (bytefight_poll.py)` section of LIVE_SCRIMMAGE_LOG.md
so it does not collide with live-tester-2's human-curated tracking table above.

Fresh match results surfaced on first sweep (visible to live-tester-2 now):
- `9432921e` B_WIN vs `20thAgent.zip` (matchmaking, finished 20:52)
- `8757c2fd` B_WIN vs `YolandaR3` (matchmaking, finished 20:32)
- `856d41c0` B_WIN vs Team 57 `Luca.zip` (matchmaking, finished 20:28)
- `b7e65887` A_WIN vs `Rascal4.zip` (matchmaking, finished 16:17)
- `a636229e` A_WIN vs `yolanda_v21.zip` (matchmaking, finished 16:28)
- `d242965b` B_WIN vs Team 65 `alexBot_dual_dominator.zip` (matchmaking, finished 16:19)
- `6d7219ac` B_WIN vs `rv12-3.zip` (matchmaking, finished 16:43)
- `49dbaf33` RUNNING vs `rv13-1.zip` (matchmaking, in progress)

### BLOCKED — Bearer-gated endpoints (awaiting JWT)

```bash
$ python tools/bytefight_client.py list-submissions
[error] 401 Unauthorized on GET /api/v1/submission/team/... — Bearer JWT missing or expired

$ python tools/bytefight_client.py set-current --submission-id ...
[error] 401 Unauthorized ...
```

Will re-test once the user provides the JWT (set `BYTEFIGHT_BEARER` env var or add
`"bearer_token"` to `tools/bytefight_session.json`).

### BLOCKED — Turnstile-gated endpoints (awaiting JWT + CAPSOLVER key)

Dry-run confirms the client wires correctly:

```bash
$ python tools/bytefight_client.py --dry-run scrimmage --opponent George
[turnstile] This endpoint requires a Cloudflare Turnstile token. Set CAPSOLVER_KEY ...
```

`CAPSOLVER_KEY` lives in the user's local env only — never committed. The client calls
CAPSOLVER's `AntiTurnstileTaskProxyLess` endpoint with a 120s poll timeout; token
returned is sent as the `cf-turnstile-response` header on the upload/scrimmage call.

## Planned e2e flow once credentials land

Per team-lead's Phase 2 plan:
1. `list-submissions` to confirm JWT works.
2. `set-current RattleBot_v03_pureonly_20260417_1022.zip` (safe no-op — re-asserts the current).
3. Build a throwaway FloorBot-like zip, upload via `upload --zip ... --description 'smoke throwaway'`.
4. Fire ONE scrimmage vs George using the throwaway as Current.
5. Revert Current back to RattleBot_v03_pureonly.

Will amend this trip report in place once that flow runs clean.

## Robustness knobs (already wired)

- **Timeouts:** 30s default, 120s on upload.
- **Retries:** exponential backoff (1, 2, 4s) on 5xx and network errors, max 3 retries. Never retry on 4xx.
- **Rate limit:** client-side 1 req/sec cap. Poller defaults to 30s interval.
- **Sensitive values:**
  - `BYTEFIGHT_BEARER` and `CAPSOLVER_KEY` live in env/session.json, gitignored.
  - `.env`, `tools/bytefight_session.json`, `tools/scratch/*.har` all in `.gitignore`.
  - CAPSOLVER key is never logged (token-bearing log lines mask as `CAP-***` in future logging passes; today the client doesn't log the key at all).
- **Dry-run:** every mutating CLI subcommand supports `--dry-run` to preview without touching the network.

## Handoff to live-tester-2

The poller is running and writes to `docs/tests/LIVE_SCRIMMAGE_LOG.md` under
`## Poller observations`. Task #78 can now read that section instead of tab-flipping on
bytefight.org. When I add the scrimmage-submit path (post-JWT+CAPSOLVER), live-tester-2
can call `BytefightClient.start_scrimmage()` directly to queue new §F-14 slots.

## Knowns / unknowns

- Replay fetch (`GET /files/{uuid}?exp&sig`): the signed URL must come from a per-match
  detail endpoint that wasn't captured in either HAR. Likely `GET /api/v1/public/game-match/{uuid}`
  or `GET /api/v1/game-match/{uuid}`. I'll probe both once we have a Bearer to test against.
- `my-team` endpoint: returned in the HAR but gated — 403 or 401 without Bearer. Not essential;
  team_uuid is already in session.json.
