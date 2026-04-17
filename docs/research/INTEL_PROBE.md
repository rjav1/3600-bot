# INTEL_PROBE — Can we harvest bytefight.org match logs for opponent intel?

**Owner:** live-tester-2
**Date:** 2026-04-17
**Task:** #34
**Scope:** Read-only probe of bytefight.org to assess whether per-match move/board data is exposed to our account. Hypothesis: if logs exist, deploy a "decoy sensor" bot that plays probe positions, scrape opponent responses, reverse-engineer George/Albert/Carrie/strong-team heuristics.

---

## 1. YES/NO: Do logs/replays exist?

**NO (for our account, at this point in the competition).** Replays are 404 across the board:

| Match                                    | Match UUID (captured)                        | /match/<uuid> result |
|------------------------------------------|----------------------------------------------|----------------------|
| George vs Yolanda (scrimmage, RUNNING)   | `d8edf119-783e-462a-9cc7-d1e4bbf81b2f`       | (not tested — RUNNING; LIVE-004 previously showed 404 for other RUNNING matches) |
| Team 15 vs validator (WON, valid)        | `6134f078-1224-404a-802d-30bbcd5975ac`       | **404 "Match Not Found"** |
| Team 15 vs validator (LOST, FloorBot)    | `2fa66018-daf9-4df0-acb0-f7a05fb8ddc7`       | (LIVE-001/002 confirmed 404) |
| Team 15 vs validator (LOST, FloorBot)    | `330386c2-e4d9-4caf-bb93-21481eb82877`       | (LIVE-001/002 confirmed 404) |

Corrects the LIVE-003 assumption "replays may work for valid matches." They do not. The UI renders the same **"Match Not Found"** page for the WON Yolanda validation match.

**UI evidence the feature is planned but disabled or gated.** Every row in Match History has an `<button title="Open replay in new tab">` with a live click handler (`e=>{e.stopPropagation(),window.open(u,"_blank")}` where `u` is a `/match/<uuid>` URL). The feature is wired end-to-end on the frontend but the route itself renders a 404 error page from `app/(match)/match/[matchUuid]/error-770d42dbac22c210.js`. Next.js `error.js` boundary — meaning the match fetch throws on the server.

**Hypothesis:** Replays are deliberately withheld during the active competition to prevent exactly what we would use them for — opponent reverse engineering. They may be turned on post-deadline (2026-04-19 23:59).

## 2. Data catalog (what's NOT available, what IS)

### NOT AVAILABLE (via the UI or same-origin browser probing)

- Per-match move list (our moves, opponent moves, rat moves).
- Per-turn board state / scores / points delta / carpet ownership.
- Per-turn time budget consumed.
- SEARCH outcomes (hit/miss, rat position revealed).
- WinReason (which one of INVALID_TURN / TIMEOUT / CODE_CRASH / FAILED_INIT / POINTS triggered).

### AVAILABLE (binary or aggregate only)

| Source                                                            | Data                                                                                     |
|-------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `/compete/cs3600_sp2026/team` Match History                       | Match UUID, opponent name, our submission filename, match type, age, status (RUNNING/WON/LOST/TIE) |
| `/compete/cs3600_sp2026/leaderboard`                              | All teams' display names, ELO, "quote" field, team UUID; per-row scrimmage crossed-swords icon |
| `/compete/cs3600_sp2026/queue`                                    | Site-wide RUNNING matches with opponent pair + age (saw 343 simultaneous). Useful as a **congestion gauge** only. |
| `/compete/cs3600_sp2026/team/<uuid>` (other teams' public pages)  | Public team name, member list, team-level ELO history. **Not tested this pass** (extension disconnected); LIVE docs imply it does render. |
| Submissions page                                                  | Our uploads only: filename, validity (valid/invalid), date, Current checkbox. No score, no log. |
| `/match/<uuid>` (all tested)                                      | **404 "Match Not Found"** for all our matches regardless of W/L/T status. |

### API surface (server.bytefight.org) — observed via preflights only

Every bytefight page talks to `https://server.bytefight.org/api/v1/...`. Preflight `OPTIONS` requests we observed:

- `/api/v1/public/glicko-history/<teamUuid>/ranked`  → our team's ELO time series (aggregate)
- `/api/v1/competition/cs3600_sp2026/teams/my-team`  → team info

Same-origin `fetch()` from the frontend works because of CORS allow-list; my cross-window `fetch()` from the browser JS console **errored with TypeError: Failed to fetch** for every tried endpoint — either CORS is strict to the exact `Origin` header the frontend sends or there's some other gate. The frontend itself does NOT expose match-log endpoints — the replay button opens a Next.js page route, not an API call, so the server probably has no log endpoint at all (if it did, the error boundary message would differ).

I did **not** discover a `/matches/<uuid>` or `/replays/<uuid>` API endpoint that returns data. If one exists, it is not used by the current UI and not discoverable by passive observation.

## 3. Access pattern / scraper sketch

**There is nothing to scrape.** What we would need:

```
for match in my_team.scrimmages_against(George):
    moves = GET /api/v1/matches/{match.uuid}/moves     # does not exist
    board = GET /api/v1/matches/{match.uuid}/snapshots # does not exist
    analyze(moves, board)
```

What we actually have is the binary result (W/L/T) for each scrimmage, which gives us roughly **1 bit of information per §F-14-budgeted scrimmage**. That's far too thin a signal to reverse-engineer a heuristic in the time remaining.

### Minor passive-scrape opportunity

The leaderboard + queue pages are public-ish. We could poll `/queue` once a minute and record every (TeamA, TeamB, status, age) tuple to build a matrix of "who's scrimmaging whom". That tells us which teams are actively tuning against which reference bots (e.g., 10 copies of `FightAI vs George`, 10 of `team ra vs Albert Lite`). Useful sociology, **useless for heuristic reverse engineering**.

**Verdict: not worth building a scraper.** The intel gain per hour of engineering is near-zero.

## 4. Decoy bot spec (if logs WERE available — preserved for post-deadline follow-up)

Because this might unlock if replays come online after the deadline, here's the sketch we would have built:

### Design goal

A deterministic "sensor" submission whose every `play()` return depends only on **turn number** (not on opponent moves or board state). Each turn it lays a specific probe pattern designed to force a characteristic opponent response. With replays, we would then extract: "when board is state X at turn K, opponent Y chose move M". A few hundred carpet-probes would fit most 9-feature linear heuristics.

### Minimal implementation

```python
# 3600-agents/DecoyBot/agent.py
from engine.game.move import Move, MoveType
from engine.game.move_consts import SEARCH, PRIME, CARPET, PLAIN, CARPETS

PROBE_SEQUENCE = [
    # Turn 0-4: lay a carpet line down the center column
    # Turn 5-9: prime a 3-long vertical line
    # Turn 10-14: idle (PLAIN passes) to give opponent free turns
    # Turn 15-19: issue SEARCH at max-belief cells to observe catch rate
    # Turn 20-39: repeat with column offsets
    ...
]

class PlayerAgent:
    def __init__(self, time_left_ms, board, is_player_a):
        self._turn = 0

    def play(self, board, time_left_ms):
        # Deterministic; ignore board except to pick a nearest legal equivalent.
        try:
            desired = PROBE_SEQUENCE[self._turn]
            move = _nearest_legal(board, desired)
        except Exception:
            move = _first_valid(board)
        self._turn += 1
        return move
```

### Analysis pipeline (post-replay-access)

1. Queue N scrimmages vs each target opponent (George/Albert/Carrie/top students).
2. Scrape move-by-move logs.
3. For each (turn, board-state) → (opponent-move) pair, fit:
   - **F1-F15 linear regression** on the opponent's scored move vs all legal alternatives — reveals their F-weights.
   - **Decision-tree classifier** on same data — reveals rule-based priorities (e.g., "Carrie always primes if longest primable ≥ 4").
   - **SEARCH-frequency histogram by belief-entropy** — reveals their SEARCH threshold.
4. Use fitted opponent models in `3600-agents/RattleBot/opp_model.py`.

### Risks (if we had logs)

- **Decoy consumes §F-14 scrimmage budget.** 10 scrimmages per opponent × 3 opponents = 30 scrimmages, well over our remaining budget.
- **Heuristic-fit overfits to probe positions.** We'd need probes that cover the natural distribution of opponent decision surfaces, not just deterministic lines.
- **Opponents may be stochastic.** Several per-position samples needed; multiplies budget.
- **Decoy is a LOSS every match.** ELO drops from intentional sacrifices.

## 5. Alternative paths (since logs don't exist)

Given verdict §1 = NO, reallocate the engineering hour-budget as follows:

1. **Carrie heuristic enumeration (task #32).** CLAUDE.md §5 describes Carrie's strategy in prose ("prime+roll, opportunistic rat search, no lookahead"). Read the assignment rubric + any reference-bot source in the engine to extract her decision function directly. Zero scrimmage cost.
2. **George/Albert analogs.** Same — both are documented reference bots. If their source is in the engine or assignment.pdf, we have their heuristic without reverse engineering.
3. **Opponent-agnostic depth.** Lift `_PER_TURN_CEILING_S` (task #25 done), Bayesian-opt weights (T-20d), feature expansion F8+F13 (task #27 done). These compound and don't depend on opponent identity.
4. **Wait for post-deadline logs.** If replays come online after 2026-04-19 23:59, use them for a post-mortem / v2.0 iteration. Not for this deadline.
5. **Self-play diversity.** Train RattleBot weights on self-play vs FloorBot + Yolanda + reference-bot reimplementations we code ourselves from §5.1/5.2 above. Effectively free.

## 6. ToS / privacy caveats

- `assignment.pdf §7.2` (per task brief reference — not re-read this pass; committer should verify) — check explicitly before any scraper work touches other teams' data.
- The leaderboard and queue are clearly intentionally public (linked from the main nav, no auth gate beyond competition membership). Observing them is fine.
- Even if we found an unauthenticated match-log endpoint, pulling other teams' data would likely be forbidden. Stop and check ToS before any such use.
- Public team pages (`/team/<uuid>`) presumably expose only what the team chose to show — team name, member list, ELO. No per-match detail observed.
- **Safest posture:** this probe doc itself reports only endpoints and observations, not scraped content.

## 7. Appendix: Match UUIDs captured (for future followups)

Captured by monkeypatching `window.open` and clicking each "Open replay in new tab" button (no actual navigation triggered):

```
George vs Yolanda (scrimmage, RUNNING): d8edf119-783e-462a-9cc7-d1e4bbf81b2f
Team 15 (WON, Yolanda validation):       6134f078-1224-404a-802d-30bbcd5975ac
Team 15 (LOST, FloorBot validation):     2fa66018-daf9-4df0-acb0-f7a05fb8ddc7
Team 15 (LOST, FloorBot validation):     330386c2-e4d9-4caf-bb93-21481eb82877
```

Team UUIDs:

```
Team 15 (ours):      81513423-e93e-4fe5-8a2f-cc0423ccb953
George (reference):  13f7ba71-eb75-4b4a-9c48-abb6bb1e8318
Unknown (DOM):       9de7da14-cdf0-482a-87fb-d7c8553ef052
Unknown (DOM):       619dbc1a-7ae9-4b52-b0f8-65993decc360
Unknown (DOM):       0923cdee-89e3-4e04-9b48-0e2faa3cf64b
```

API host: `https://server.bytefight.org/api/v1/...` (CORS-locked to frontend origin only; cross-origin fetch blocked).

## 8. Conclusions

- **No match logs are available** to our account for any match (validation or scrimmage, W/L/T). `/match/<uuid>` uniformly 404s.
- **No public API endpoint** returns per-turn game data. CORS prevents direct API probing from the browser console; the frontend itself never calls a "get match moves" endpoint, suggesting one doesn't exist.
- **Replay-button plumbing exists** (the `<button title="Open replay in new tab">` elements open `/match/<uuid>` URLs) but the destination is not wired to any working backend route. Plausibly intentional during the active competition.
- **The decoy-bot idea is blocked** on the log availability and on §F-14 scrimmage budget. Preserve the design for post-deadline use.
- **Redirect effort** to opponent-model synthesis from source (task #32 on Carrie) and opponent-agnostic depth gains (tasks #25/#27/#29/#28 already in progress).
- **Soft monitoring:** re-probe `/match/<valid-uuid>` weekly, or immediately after team-lead notices a UI change (e.g., a "Replays available!" banner). A one-line curl: `curl -s https://bytefight.org/match/<uuid>` body != "Match Not Found" would indicate flip.

## 9. What this pass did not accomplish

- Did not browse the George public team page (`/team/13f7ba71-...`). Extension disconnected mid-pass. Unknown whether it reveals George's match history against other teams. **Suggested follow-up for whoever picks up next:** navigate to `https://bytefight.org/compete/cs3600_sp2026/team/13f7ba71-eb75-4b4a-9c48-abb6bb1e8318` and capture the page structure. If George's match history is visible, that's a new data source we haven't exploited.
- Did not verify `/api/v1/competition/cs3600_sp2026/teams/my-team` response body (only saw OPTIONS preflight). Sucessor could click in the DevTools Network tab to record the GET body — it might list all our matches with fields we haven't seen in the UI.
- Did not inspect `assignment.pdf §7.2` on what scraping is permissible.
