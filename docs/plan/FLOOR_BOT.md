# FLOOR_BOT — Crash-proof Reactive-Policy Insurance Agent

**Status:** v1 built 2026-04-16. 100% win-rate vs Yolanda on 50 matches each side.
**Path:** `3600-agents/FloorBot/`
**Task:** #9 (per contrarian-scope recommendation #3 in `docs/research/CONTRARIAN_SCOPE.md`).

---

## Design philosophy

FloorBot is not trying to be strong. It is trying to be **unkillable and boring-competent**: to reliably complete a full 40-turn game with no invalid moves, no crashes, and no timeouts, and to beat Yolanda (the random-mover) the vast majority of the time. If the team's high-tier bot regresses or behaves unpredictably close to the deadline, FloorBot is the fallback we can submit to `bytefight.org` with high confidence that it clears the ≥70% floor.

The policy is pure reactive: no lookahead, no HMM, no search, no global mutable state. Every decision is a small set of O(board) scans over the four cardinal directions from the worker's current cell. The whole agent is under 200 lines. This minimalism is intentional — the smaller the surface area, the smaller the failure surface.

Robustness wraps the policy: the entire body of `play` is inside a try/except, with a `random.choice(get_valid_moves())` fallback, itself wrapped in try/except. Even a completely corrupt board state would at worst degrade FloorBot to the Yolanda-equivalent, which we know completes games without crashing.

## Decision priority list

On each `play()` call, in this order — first viable move wins:

1. **Finish a big carpet roll.** Scan `board.get_valid_moves()` for CARPET moves with `roll_length ≥ 2` (since k=1 costs −1 point). Pick the one with the highest point value from `CARPET_POINTS_TABLE`. This is the main point-engine action when a primed line is already in place.

2. **Extend or start a line via PRIME.** For each legal PRIME direction, score it by `line_potential + extension_bonus`:
   - `line_potential(dir)` = count of contiguous SPACE cells in `dir` from our worker, stopping at any non-SPACE cell, out-of-bounds, or the opponent.
   - `extension_bonus(dir)` = +2 per existing PRIMED cell located 2–3 steps ahead in that direction (a reward for stacking on top of a partial line we can later roll).
   - If the top score is 0, skip PRIME entirely (priming into a wall would strand us). Otherwise, prime in the best-scoring direction.

3. **Plain step toward the most open area.** Score each PLAIN by `2 · half_open_area(next_cell) + line_potential(dir)`:
   - `half_open_area(cell)` = count of SPACE cells in the 4×4 quadrant containing `cell`. A crude but cheap proxy for "how much room is over there to prime later". Weighted 2× because open area is the more valuable signal than short-line potential from your current cell.
   - Prefer moves that keep future priming options alive.

4. **Fallback: any valid move.** If we somehow have no PLAIN/PRIME/CARPET≥2 candidates, return `valid_moves[0]` (which can include a CARPET-1 at −1 point — acceptable to stay legal).

5. **Exception fallback (in `_safe_fallback`).** On any raised exception along the primary path, return `random.choice(board.get_valid_moves())`. If even `get_valid_moves()` raises, fall back to `get_valid_moves(exclude_search=False)`. If that raises too, return `Move.search((0, 0))` — SEARCH only needs in-bounds, so this is always legal.

SEARCH is intentionally **never chosen** by the primary policy. The v1 floor-bot does not track the rat belief, so any SEARCH is blind and EV≈−(2·5/6) = −5/3 ≈ −1.67. Not worth it. The fifth-level fallback is the only place SEARCH can occur, and only as a last-ditch way to avoid an invalid-move loss in the presence of a corrupt board.

## Robustness guarantees

- `__init__` wraps all setup in try/except, does zero I/O, never prints, and completes in <1 ms (tested).
- No module-level mutable state. All state is per-instance.
- No file reads or writes anywhere.
- No imports beyond `random`, `typing`, `collections.abc`, and the engine's `game.*` modules.
- Per-move wall time (microbench, 2000 calls across 50 simulated games):
  - mean 0.017 ms
  - p50  0.016 ms
  - p90  0.026 ms
  - p99  0.034 ms
  - max  0.061 ms
- The 50 ms per-move budget is 1000× larger than our observed max. Even on the tournament sandbox (which is CPU-constrained vs local), we have headroom of three orders of magnitude.

## Test results

### Local self-play vs Yolanda

50 matches each side, `python 3600-agents/FloorBot/tests/batch_test.py 50 <A> <B>`:

| FloorBot side | Wins | Losses | Ties | Crashes | Timeouts | Invalid |
|---------------|------|--------|------|---------|----------|---------|
| A (first)     | 50   | 0      | 0    | 0       | 0        | 0       |
| B (second)    | 50   | 0      | 0    | 0       | 0        | 0       |

**Win rate: 100/100 = 100.0%** (observed). Against the 95% target this is a comfortable pass with wide margin. Note: local runs use `limit_resources=False` (360 s vs 240 s tournament budget), but given FloorBot's max observed per-move time is 0.06 ms, the tournament budget is irrelevant — FloorBot uses ≈2 ms of its 240 s.

Logs: `3600-agents/FloorBot/tests/run_A.log`, `run_B.log`.

### Microbench

`python 3600-agents/FloorBot/tests/bench_play.py` — synthetic 50-game sweep:

- 2000 calls to `play()` on 50 randomized board states.
- 0 crashes, 0 invalid moves.
- Latency distribution above.

## Known weaknesses

FloorBot is **not** our top bot. By design:

1. **No rat tracking, no searches.** We leave up to +4 per correct search on the table, and we have no information-gathering plan. Against a bot that searches intelligently we lose the rat-points budget entirely.
2. **No opponent modeling.** If the opponent carpets aggressively through our territory, we have no mechanism to defend or counter-pace. Yolanda's random moves almost never happen to be the best move, so this doesn't show up vs Yolanda, but it will vs Albert/Carrie.
3. **No lookahead.** We cannot see a two-move combo where priming toward a bad-looking cell sets up a big carpet roll two turns from now. This costs ~20-40% of theoretical point maxima per the heuristic research (`docs/research/RESEARCH_HEURISTIC.md` §B).
4. **Greedy carpet rule is shallow.** We take the highest-point CARPET≥2 available *now*, not the one that preserves the most future priming options. A CARPET-2 that uses the only remaining line is worse than holding for CARPET-3 next turn — FloorBot won't see that.
5. **Direction tie-breaking is fixed by enum order** (UP=0, RIGHT=1, DOWN=2, LEFT=3). A smart opponent who knows this could channel us into unfavorable terrain. Not exploitable by Yolanda or George; maybe exploitable by Carrie.
6. **Plain-step heuristic is 4×4-quadrant-level**, not cell-level. It can pick a direction that heads "toward the big empty area" but away from existing primed lines.
7. **No game-end awareness.** We don't recognize "turn 38, opponent has 12-pt carpet line we could block" kinds of moments. This is unfixable without a game tree.

## When to activate FloorBot on bytefight.org

**Use as primary submission only in fallback scenarios.** The default tournament submission is whichever higher-tier bot the team has confidence in (likely `RattleBot` or similar when it lands). Switch to FloorBot if **any** of the following trigger:

1. Primary bot's local win-rate vs George drops below 50% in a 50-match evaluation. Grade tier below 70% is a risk at that point, and FloorBot's ≥95% vs Yolanda gives a modest but non-zero win rate vs George (Yolanda-equivalent opponent floor).
2. Primary bot crashes, times out, or makes an invalid move in any bytefight scrimmage in the 24 hours before the deadline. This is a red flag for systematic failure mode — FloorBot has no such failure modes.
3. < 2 hours before the 2026-04-19 23:59 deadline and the primary bot has an unresolved regression. Do NOT ship broken code; ship FloorBot.
4. Partner handoff conflict: if it is unclear whose code is active and we risk submitting something wrong, submit FloorBot as a deliberate floor and reconcile afterward.

**Do NOT use FloorBot as primary if** the higher-tier bot has passed ≥3 bytefight.org scrimmages vs George/Albert/Carrie without a crash — in that regime the higher-tier bot's expected tier placement dominates FloorBot's tier-floor guarantee.

## Files

- `3600-agents/FloorBot/__init__.py`
- `3600-agents/FloorBot/agent.py` (~180 lines)
- `3600-agents/FloorBot/tests/test_selfplay.py` (one-game smoke)
- `3600-agents/FloorBot/tests/batch_test.py` (N-match evaluator)
- `3600-agents/FloorBot/tests/bench_play.py` (per-move wall-time benchmark)
- `3600-agents/FloorBot/tests/run_A.log`, `run_B.log` (50-match logs)
