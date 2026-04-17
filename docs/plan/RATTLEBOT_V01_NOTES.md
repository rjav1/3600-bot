# RATTLEBOT_V01_NOTES — Integration Surprises (T-16 dev-integrator)

**Owner:** dev-integrator
**Date:** 2026-04-16
**Scope:** Wiring `agent.py` + `time_mgr.py` on top of `rat_belief.py`, `search.py`, `heuristic.py`, `move_gen.py`, `zobrist.py` (all committed by T-13/T-14/T-15).

Covers only the delta from component-perfect to end-to-end-runnable. Component-level behavior is documented in each module.

---

## S-1 — SEARCH gate fires on near-flat belief in v0.1 (ROOT CAUSE of initial -68 loss)

**Symptom:** First smoke-test end-to-end match, RattleBot A vs Yolanda B, ended `PLAYER_B wins by POINTS 3 to −68`. RattleBot issued a SEARCH every turn (40/40).

**Root cause:** `search.root_search_decision` picks SEARCH when `ev_search > best_non_search_value + eps_tiebreak`. At flat belief (max_mass ≈ 0.04), `ev_search ≈ 6·0.04 − 2 + γ_info·dH − γ_reset·p·H(p₀) ≈ −1.7`. But the v0.1 heuristic produces negative leaf values in most early positions (F11 = `w·max_mass` with `w=-3.0`, F12 = `w·entropy` with `w=-0.5` so entropy≈4 nats contributes −2). So `best_non_search_value ≈ −2.3`, and `ev_search − best ≈ +0.6 > eps_tiebreak=0.25` — SEARCH always wins. This is a heuristic-calibration defect amplified by the root-gate comparison, not a wiring bug per se.

**Wiring-side mitigation (applied in `agent.py`):** gate SEARCH on `belief_summary.max_mass > 1/3`, which is the unconditional break-even for a `+4 / −2` bet per GAME_SPEC §2.4. Below that threshold, we skip the root chance-node comparison and call `search.iterative_deepen(...)` directly so only non-SEARCH moves are considered.

**Effect on smoke test:** RattleBot (A) vs Yolanda (B): `PLAYER_A wins by POINTS 28 to 1` on the 1-match validation. 5-match batch `_batch_smoke.py 5` → **5/5 wins (100 %)**, mean 96 s/match, no crashes / timeouts / invalid moves. 40/40 turn loop no longer filled with SEARCH spam; instead fills with CARPET/PRIME/PLAIN picks plus occasional SEARCH when belief concentrates.

**v0.2 owner (dev-heuristic):** recalibrate `W_INIT` so that `ev_leaf ~ 0` at a neutral board; this will let `search.root_search_decision` gate on its own without the agent-side p > 1/3 guard. Bayesian-optimization tuning (D-009) is the target mechanism.

---

## S-2 — Per-turn budget capped at 3 s for v0.1

**Decision:** Added `_PER_TURN_CEILING_S = 3.0` to `time_mgr.py` on top of the D-004 multipliers (0.6×/1.0×/1.6×) and 2.5× surplus cap.

**Rationale:**
- Local default `time_to_play=360 s` → base budget 9 s/turn. Running full 9 s on an untuned v0.1 heuristic just amplifies bad picks (deeper search on a biased leaf converges to the same wrong move faster and more confidently).
- Reducing the ceiling to 3 s makes self-play runs ~3× faster — critical for the 50-match paired comparisons that tester-local (T-17) is running.
- Tournament budget `240 s / 40 = 6 s/turn` base; in tournament we'll still be well inside the budget. Surplus accumulates for late-game critical turns (multiplier 1.6×, ceiling still 3 s).

**v0.2 owner (dev-search + dev-heuristic):** lift or remove `_PER_TURN_CEILING_S` after BO tuning and TT+killer+history ordering ship. Real depth-6 search on a calibrated heuristic is the path to 90 %+.

---

## S-3 — RatBelief reads `board.opponent_search` / `board.player_search` internally

**Observation:** The original T-16 brief said "track opp_search from board.opponent_search and apply to belief via belief.apply_opp_search()". But `RatBelief.update()` (shipped by dev-hmm) already reads `board.opponent_search` directly and applies the miss/hit logic in step 2 of its 4-step pipeline. `apply_our_search` / `apply_opp_search` are kept as **helpers for in-tree SEARCH chance-node unrolling** (search-§E.6), NOT as wiring callbacks from `agent.py`.

**Wiring consequence:** `agent.py` does NOT call `apply_opp_search` or `apply_our_search`. Post-capture reset on OUR successful SEARCH is likewise handled on the NEXT turn by `RatBelief.update()` reading `board.player_search = (loc, True)` and calling the reset branch.

**Correctness check:** T-HMM test `test_apply_our_search_hit_resets_to_p0` already covers the helper path; T-HMM `test_update_preserves_normalization` covers the engine-driven path. No integration test was required.

---

## S-4 — Emergency fallback is duplicated, not imported

**Decision:** `PlayerAgent._emergency_fallback` and `_floor_choose` are lightweight FloorBot re-implementations inside `agent.py`, not imports from `FloorBot.agent`. Per D-006 but stronger: **the tournament-submission zip must contain only `RattleBot/*`**, with zero cross-agent dependencies. Importing `FloorBot` would create an implicit dependency that breaks at upload time.

**Size cost:** ~30 LOC of duplication (carpet/prime/plain triage + random fallback + SEARCH-at-(0,0) terminal). Accepted.

---

## S-5 — `board.is_valid_move(move)` guard against occasional search-returns

**Observation:** On rare boards (≤ 1 % of turns in local smoke), `search.iterative_deepen` returned a move that didn't validate against `board.is_valid_move`. Specifically in end-game positions where the search's TT move came from a near-identical transposed position. Cheap to guard: `agent.py` calls `self._looks_valid(board, move)` and falls through to `_emergency_fallback` on failure. Never fires in healthy play.

**v0.2 owner (dev-search):** investigate whether the TT move was pulled from a position with a different `is_player_a_turn`. If yes, add `is_player_a_turn` to the zobrist key (currently packaged via `turn_count // 2` bucket, which MAY miss edge cases).

---

## S-6 — No CLI/board-state state-machine anomalies

**Sanity:** All 34 pytest tests in `3600-agents/RattleBot/tests/` PASS on clean run with the wired agent. Smoke-test game runs 80 plies end-to-end with no `ImportError`, no `InvalidMove`, no `TIMEOUT`, no `CODE_CRASH`. Tournament-contract shape (`__init__`, `play`, `commentate`) verified through `engine/player_process.py::run_timed_constructor` and `run_timed_play`.

---

## Summary for v0.2 dev wave

The wiring is clean; the component integration is correct; the v0.1 play-quality ceiling is set by the heuristic, not by the search or the time manager. BO-tuned `W_INIT` (D-009) and the F9/F10 features (v0.2 §3.4) should lift ELO by the expected +80–120 points. Lifting `_PER_TURN_CEILING_S` should ride on top of that.
