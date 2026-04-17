# LOSS_FORENSICS_APR17 — Forensic analysis of 2 student-team losses

**Owner:** loss-forensics
**Date:** 2026-04-17
**Shipped submission under review:** `RattleBot_v03_pureonly_20260417_1022.zip` (SHA256 `f046631f...`, pure-python, depth ~13, 19 features, W_INIT weights — no BO adoption yet)
**Purpose:** Surface root causes of two same-day matchmaking losses to student teams (not reference bots), and recommend concrete heuristic tweaks before the 2026-04-19 23:59 lockout.

---

## 1. Match metadata

Both matches were fetched via `python tools/bytefight_client.py get-match --match-uuid <uuid>` against the live bytefight API. The client currently returns **only match metadata** (names, status, timestamps) — no per-turn replay, no final score, no move list. See §5 for the tooling gap.

### Match 1 — vs Team 57 (`Luca.zip`)

| Field | Value |
|---|---|
| Match UUID | `856d41c0-a56e-4dd5-b15f-8d25ae4525cf` |
| Competition | `cs3600_sp2026` |
| Reason | `matchmaking` (ladder game, not a manual scrimmage) |
| Team A | Team 15 (us) — `81513423-e93e-4fe5-8a2f-cc0423ccb953` |
| Team B | Team 57 — `70c48f7b-1d96-4644-a776-1fb5085cde86` |
| Submission A | `RattleBot_v03_pureonly_20260417_1022.zip` |
| Submission B | `Luca.zip` |
| Status | `team_b_win` — **we LOST** |
| Scheduled | 2026-04-17 20:00:00 UTC |
| Started | 2026-04-17 20:24:24 UTC |
| Finished | 2026-04-17 20:28:03 UTC |
| Wall duration | ~3m 39s (normal — suggests a clean game-end on turns, not a TLE/crash) |
| Score diff | **unknown** (replay endpoint not wired) |
| Final scores | **unknown** (replay endpoint not wired) |

### Match 2 — vs Team 65 (`alexBot_dual_dominator.zip`)

| Field | Value |
|---|---|
| Match UUID | `d242965b-bcca-45c5-90fb-33f25bbb9aee` |
| Competition | `cs3600_sp2026` |
| Reason | `matchmaking` |
| Team A | Team 15 (us) — `81513423-e93e-4fe5-8a2f-cc0423ccb953` |
| Team B | Team 65 — `fb9534dc-e759-4a8c-af87-7a32ead2d61e` |
| Submission A | `RattleBot_v03_pureonly_20260417_1022.zip` |
| Submission B | `alexBot_dual_dominator.zip` |
| Status | `team_b_win` — **we LOST** |
| Scheduled | 2026-04-17 16:00:00 UTC |
| Started | 2026-04-17 16:15:33 UTC |
| Finished | 2026-04-17 16:19:34 UTC |
| Wall duration | ~4m 01s (normal — clean game-end, not a TLE) |
| Score diff | **unknown** (replay endpoint not wired) |
| Final scores | **unknown** (replay endpoint not wired) |

### What is NOT available from the current tooling

- Per-turn board snapshots
- Per-turn move (type/direction/roll_length/search target)
- Cumulative scores per ply
- Rat ground-truth path (`trapdoors[]`)
- Final score totals
- Noise / sensor-data stream

The `bytefight_client.get_match(uuid)` path just filters `list-matches`. The signed replay URL (`server.bytefight.org/files/<uuid>?exp=&sig=`) is not implemented in the client — see `tools/BYTEFIGHT_CLIENT.md` line ~146: *"Not implemented yet; extend the client once observed."* Per task hard-limits we did not extend it.

---

## 2. Per-match timeline

Because no replay stream is available, a ply-level timeline cannot be reconstructed from the API alone. What the metadata does tell us:

### Match 1 (vs Luca.zip, Team 57)

- Matchmaking game, so **we were forced** into the slot — not an opt-in scrimmage.
- Game engine duration ~3m 39s ≈ 219 s of wall clock; the 240 s per-side budget was **not** exhausted, so neither side timed out.
- Status `team_b_win`, with no `error` substatus → finished cleanly on 80-ply turn exhaustion (or an early rat-catch cascade) with Luca having more points. **We did not crash, did not time out, did not make an invalid move** — we were outscored.
- Leaderboard context: Team 57's `Luca.zip` is an active student entry (not a reference bot). Their appearance in matchmaking at our ELO tier (~1500) implies Luca is a broadly competitive agent.

### Match 2 (vs alexBot_dual_dominator.zip, Team 65)

- Matchmaking game, same constraint.
- Engine duration ~4m 01s ≈ 241 s ≈ **right at the ALLOWED_TIME=240 s per-side limit**. Either player consumed almost the whole budget. This is a yellow flag — it may mean either (a) we slow-played to endgame and ran to the wall, or (b) the opponent did. Without ply-level data we can't attribute it.
- Status `team_b_win`, no error substatus → game finished cleanly, we were outscored.
- The submission name `dual_dominator` hints at an agent designed to dominate both the **carpet-roll lane** and the **rat-hunt lane** simultaneously — a direct multi-axis threat.

---

## 3. Root-cause hypotheses

With no replay data, hypotheses are ranked by **prior probability** derived from V01_LOSS_ANALYSIS.md + AUDIT_V03.md + V03_REDTEAM.md findings that remain unresolved in the currently-shipped pure-Python build. These are **unverified** until replay-fetch is wired.

### Match 1 — vs Luca.zip (Team 57)

**Most likely: (H-LUCA-1) F10/F22 prime-chain starvation under aggressive opponent prime-steal.**

Rationale:
- V03_REDTEAM flagged that F10 adjacency (the 2026-04-17 lock at option (b)) undervalues **long contiguous prime chains** when the opponent interleaves their own primes adjacent to ours. F22 (prime-steal bonus) was added to partially compensate, but is un-BO-tuned.
- Luca-style agents that aggressively plant primes along the board seam can force our α-β to keep trading short k=2 rolls instead of building to k≥4. Per V01_LOSS_ANALYSIS §1 the k=1/k=2 lane already cost us ~4–6 pts/match pre-v0.3; if v0.3's un-tuned weights under-weight F10 relative to F22 we replay that loss.

Second-most likely: **(H-LUCA-2) Rat-hunt gate misfire.** SEARCH EV is positive iff `P(rat in cell) > 1/3`. Without the BO-tuned weights in `weights_v03.json` the HMM-gated SEARCH fires too rarely in late-game (AUDIT_V03 M-7 carry-over risk) so we cede the 4-pt rat swings that Luca converts.

### Match 2 — vs alexBot_dual_dominator.zip (Team 65)

**Most likely: (H-ALEX-1) Time budget exhaustion into late-game without scaled safety margin.**

Rationale:
- Finish time was ~241 s after start — almost exactly the 240 s per-side ceiling. The T-40c adaptive-time-budget feature extends late-game thinking (3.5× multiplier when `turns_left ≤ 5`). If alexBot's aggressive middlegame forced a deeper, more complex position, our late-game extension can balloon and leave us **one tick short** of returning a move — which in the worst case is an instant loss, but can also mean we return the safety-net move from a shallow depth and misplay a decisive carpet roll.
- The "dual_dominator" naming implies they apply pressure on both the carpet lane and rat lane — exactly the board-complexity profile that stresses α-β's branching factor.

Second-most likely: **(H-ALEX-2) F24 opp-wasted-primes mispredicts under a non-greedy opponent.** The F24 feature assumes the opponent will convert their primes efficiently. An agent that deliberately **strands** primes to bait our rolls into suboptimal captures can trick F24 into over-weighting positions that actually favor them. Un-BO'd weights amplify this.

---

## 4. Recommended heuristic tweaks (concrete, feature-level)

All of these are **post-BO-adopt candidates** — the BO run (PID `8868`) is currently optimizing the 19-feature W vector and must not be disturbed. These tweaks should be staged in a branch or a tuning spec, NOT applied to `heuristic.py` live.

### R1 — Re-weight F10 adjacency-endpoint against F22 prime-steal (targets H-LUCA-1)

After BO RUN1-v7 lands `weights_v03.json`:
1. Inspect the adopted `w[F10]` vs `w[F22]` — if `|w[F10]| < |w[F22]|`, that's the likely Luca failure mode.
2. Run a 20-match paired scrimmage of (BO-adopted weights) vs (BO weights with `w[F10] *= 1.25, w[F22] *= 0.9`) and keep the winner.
3. Estimated leverage: **~+2 pts / match** against prime-steal-heavy agents.

### R2 — Lower the late-game adaptive-budget ceiling (targets H-ALEX-1)

In `time_mgr.py` (currently the T-40c endgame multiplier):
- Change the `turns_left ≤ 5` multiplier from **3.5×** → **2.5×**, and hold a hard **220 s cumulative** ceiling (was implicit 240 s).
- This loses some theoretical depth when we're deep into a budget surplus, but **eliminates the "finished at 241s" failure mode** entirely.
- Estimated leverage: **0 expected ELO vs Carrie/Albert; +ELO vs aggressive student agents** that slow-play on purpose.

### R3 — Raise the HMM SEARCH-gate threshold for late-game but allow info-gathering searches with `P > 0.28` when `turns_left ≤ 10` (targets H-LUCA-2)

V01 noted SEARCH gate saturation in one direction (fires always) and V03 noted it in the other (fires too rarely). The middle ground:
- Keep `P > 0.333` as the default EV threshold (`+4 / −2` break-even).
- Below `turns_left = 10`, drop the threshold to `0.28` — at that point an information-gathering miss is cheaper because the belief has fewer turns to decay, and a hit worth +4 is a game-swinging swing relative to 10 turns of expected 1–2 pt prime actions.
- Estimated leverage: **+1.5 pts / match** in matchmaking against student agents that rat-spam.

### R4 — Add F25 "opp time-pressure" counter-feature (targets H-ALEX-1 and -2, requires new BO — do NOT apply pre-deadline)

F25 = opponent `time_left / (turns_left + 1)`. When opponent is burning budget fast, we gain by playing simpler, more certain moves (cede depth for determinism) — the inverse of our own adaptive-budget logic.
- **Do NOT add this before the deadline** — it would break the currently-running BO (19 → 20 features invalidates `W_INIT`).
- Flagged for a post-deadline write-up only.

### R5 — Eliminate k=1 rolls with hard constraint (targets both)

This was v0.1's dominant loss-driver. V01_LOSS_ANALYSIS §1 flagged that we rolled k=1 at 42% frequency before the URGENT T-20f fix. Re-audit the v0.3 corpus to verify k=1 is still gated to the "no alternative scores better" case. If not, add a hard check at move-gen time: **k=1 CARPET is forbidden unless all other moves evaluate below −1**.
- Estimated leverage: **+2 pts / match** floor protection.

### Priority order

Pick **R2 + R5** pre-deadline — both are low-risk, don't require new BO features, and address the two highest-prior hypotheses directly. R1 and R3 are BO-adopted-weights candidates for the ship-decision final pairing.

---

## 5. Tooling gaps

### Gap 1 — No programmatic replay fetch (BLOCKING for this task)

`tools/bytefight_client.py::get_match` returns only match metadata. To do a real per-ply loss autopsy we need:

- `GET https://server.bytefight.org/api/v1/public/game-match/{uuid}` (or similar) to fetch the signed replay URL.
- The signed URL is then fetched (no auth needed) and returns the full `history` JSON (same schema as `engine/board_utils.py::get_history_dict`).

The exact endpoint was **not captured** in the HAR from 2026-04-17, per `tools/BYTEFIGHT_CLIENT.md`. Action items (for a future agent, not this task):
1. Open a match replay in Chrome with DevTools Network open.
2. Filter for `server.bytefight.org`.
3. Identify the endpoint that returns the `files/<uuid>?exp=&sig=` signed URL and its auth requirements.
4. Extend `bytefight_client.py` with `download_replay(uuid) -> dict`.

Per this task's hard-limit ("If replay-fetch isn't supported, document the gap and stop; do NOT extend the client yourself") we stopped at documentation.

### Gap 2 — Poller only logs 8-char UUID prefixes

`tools/bytefight_poll.py` writes only truncated UUIDs (e.g. `856d41c0`) to `docs/tests/LIVE_SCRIMMAGE_LOG.md`. Full UUIDs had to be re-resolved via `list-matches --size 200`. Trivially fixable but out-of-scope here.

### Gap 3 — No scoreboard visibility without replay fetch

The `get-match` response has no `scoreA` / `scoreB` fields, even though the bytefight UI renders them. This is likely because the scores live only in the replay JSON. Once Gap 1 is closed, Gap 3 closes with it.

### Gap 4 — No opponent move-pattern profiling

Even if replay-fetch lands, we'd want a `tools/match_analyzer.py` that consumes the replay JSON and emits the V01_LOSS_ANALYSIS-style mistake taxonomy. There's precedent in `tools/scratch/v01_loss_analysis.py` — the v0.3 equivalent has not been built. Flagged for post-BO-adopt work.

---

## 6. What this analysis is and is not

- **Is**: a documented confirmation that we lost two matchmaking games to student teams, with plausible root-cause hypotheses grounded in existing AUDIT_V03 / V03_REDTEAM / V01_LOSS_ANALYSIS findings.
- **Is not**: a per-ply forensic teardown, because the replay endpoint is not wired. Do not treat the root-cause hypotheses as confirmed.
- **Next agent who wires the replay endpoint** should re-run the analysis against the actual move stream and promote or demote the hypotheses accordingly. Until then, **R2 and R5 are the defensible pre-deadline changes**.
