# TABLEBASE_FEASIBILITY — Opening Book & Endgame Tablebase Probe

**Author:** tablebase-probe agent
**Date:** 2026-04-16
**Scope:** Feasibility of (A) opening book and (B) endgame tablebase for RattleBot, before the 2026-04-19 submission deadline.

**TL;DR — Recommendation: SHIP NEITHER.** Opening book is technically feasible but low-value (~10–30 ELO ceiling, 1–2 hits/game, integration risk > gain 3 days from deadline). Endgame tablebase reduces to "increase α-β depth in last 6 plies" — no new data structure, just a `time_mgr` tweak.

---

## Part A — Opening Book

### A.1 State-space count

Turn-0 board state is fully determined by:
- **Corner blockers.** 4 corners × 3 shapes (2×3, 3×2, 2×2) = **81 layouts**. `engine/gameplay.py:254-262`.
- **Spawn pair.** A at `x ∈ {2,3}, y ∈ {2..5}` (8 cells); B at `(7-x, y)` (mirrored). **8 spawn pairs**. `engine/board_utils.py:186-190`.
- Total turn-0 positions: **81 × 8 = 648**.
- The transition matrix `T` is drawn per-game with ±10% multiplicative noise per entry (`engine/gameplay.py:22-24`). Opening-book entries would have to be keyed on `T` too — but `T` has 4096 real-valued entries, so we **cannot index by `T`**. Workaround: build the book assuming a nominal `T` (mean of the 4 pickled tables). This is tolerable for ply-0 moves because they are positional (PRIME direction) and largely `T`-independent — the rat's stationary distribution matters only once the belief is sharp.

Symmetry reductions:
- **Vertical reflection** (`y → 7-y`) is a true game symmetry — player ordering is preserved, just relabels TL↔BL and TR↔BR corners. Halves the space to **~324 canonical positions**.
- **Horizontal reflection** (`x → 7-x`) is NOT a game symmetry: A is always at `x ∈ {2,3}` (left half) and moves first. Reflecting would put A on the right, reversing move-order semantics. No reduction.
- Diagonal / 90° rotations: not symmetries (break the A-left / B-right invariant).

So: **~324 distinct turn-0 positions after symmetry.**

### A.2 Scoping the book: how deep can it go?

The book is only useful while **both** players follow it. As soon as the opponent deviates, subsequent book entries are stale. Realistic coverage:

| Ply | Book hits? | Reason |
|-----|------------|--------|
| 0 (A ply 1) | Yes (100%) | Always at root book state |
| 1 (B ply 1) | Yes, keyed on A's book move | B is in a child state of A's choice |
| 2 (A ply 2) | Only if B stayed in book | B is not running RattleBot; they may diverge immediately |
| 3 (B ply 2) | Requires both plies followed book | Very low hit rate |
| 4+ | Essentially 0 | Tree fan-out explodes, B is adversarial |

So practical book scope: **plies 0–1 + a partial ply-2 table**. That's 324 (ply-0) + ~324 × (branching-factor ≈ 6) (ply-1) ≈ **~2300 entries**. Ply-2 adds another ~6x multiplier → ~14k entries (still tractable).

### A.3 Time to solve each position

To compute the best opening move at depth 10+ expectiminimax with rat-chance nodes:

- **Branching factor.** At turn 0 each worker has 4 PLAIN + 4 PRIME = ~8 non-SEARCH moves (CARPET impossible — no primes yet, SEARCH usually −EV at ply 0 because belief is the known `T^1000` prior, which is not peaked enough to clear 1/3). SEARCH candidates: 64, but only cells with `belief > 0.333` are +EV; at ply 0 this is typically 0–2 cells. So effective b ≈ **8–10**.
- **Rat chance nodes.** Each ply has a rat-move chance node with up to 5 outcomes, plus a sensor observation (3 × 4 = 12 outcomes). In a full expectiminimax, this fans out ~60× per ply. Standard technique is to collapse to an **expected** value over the rat distribution (one belief-update chance node per ply, not 60 branches). With this collapse, b ≈ 8–10 per decision ply.
- **Depth 10** (5 plies per side) with b=9 → **~3.5B leaves**. With α-β the typical reduction is ~b^(d/2) = 9^5 ≈ 60k leaves. With good move ordering (book candidates first) and zobrist caching: likely **under 10 seconds per position on a mid-range CPU**. RattleBot's existing α-β at depth 6 already runs in a few seconds per move; depth 10 offline with no time pressure is ~10–60s.

**Offline compute estimate:**
- 324 ply-0 positions × 30s/solve = **~2.7 hours** (single-threaded)
- + 2000 ply-1 positions × 20s/solve (shallower needed since we're deeper in tree) = 11 hours
- Total: ~14 hours single-threaded; **< 2 hours with 8-way parallelism**.

This is **within budget** if we use the tournament's 8-core headroom and run the solver overnight.

### A.4 Expected ELO gain

- **Hit rate:** 1 guaranteed hit for A's ply-0, 1 for B's ply-0 response. Ply-1 probably 0.2 hits/game since opponent won't follow. Call it **~2 hits/game out of 40 turns**.
- **Quality delta per hit:** at ply 0, the RattleBot's existing depth-6 α-β already picks near-optimal PRIME directions. The book move (depth 10) might differ from depth-6 in maybe 20% of positions, and among those, the quality delta is typically small (picking a slightly better prime ray). Expected value per hit: **+0.3 points over a 40-turn game** generously.
- **Total expected point swing:** ~2 hits × 0.3 = **~0.6 points per game**.
- Against reference bots scoring 30–50 points, this is **~1–2% win-rate shift**. In ELO terms: **~10–20 ELO**.

Additionally, saving 2 × ~3s = 6s of live-search time reallocated to midgame gives perhaps one more depth ply on one critical move. Generously, another **~10 ELO**.

**Total ceiling: ~20–30 ELO.** Non-trivial but small vs. the existing tasks in flight (heuristic weight tuning — T-20d — could easily find 50+ ELO).

### A.5 Integration risk

- The runtime book lookup is simple: hash `(blocker_mask, spawn_a, spawn_b, move_history_first_2_plies)` → `Move`. ~10 LoC.
- Risk: book move might be **invalid** in the actual game state (e.g., if we canonicalized wrong, or the vertical-reflection lookup returns a move that needs un-reflecting and we bungle the coordinate flip). An invalid move = instant loss. This is the dominant risk given 3 days to deadline.
- Mitigation: always validate book move with `board.is_valid_move` before playing; fall back to α-β on mismatch. This makes the book "safe but only a speedup".

### A.6 Part A Verdict

**Feasible, but not worth shipping with 3 days left.** ~20–30 ELO upside is dominated by:
- Weight-tuning pipeline (T-20d) — estimated 50+ ELO
- Heuristic features F8/F13 (T-20c) — estimated 30–50 ELO
- Audit corrections from T-18

**Defer indefinitely** unless the above tasks land well ahead of schedule and there is remaining budget.

---

## Part B — Endgame Tablebase

### B.1 State-space analysis for last M=6 plies

For a "realistic late-game board" (hand-constructed: ~30 SPACE, ~15 PRIMED, ~10 CARPET, ~8 BLOCKED, 1 of each worker in mid-8×8):

**What can evolve in 6 plies:**
- Each ply, one of 4 move types for the acting worker:
  - PLAIN: moves worker, no cell change
  - PRIME: +1 cell becomes PRIMED, worker moves
  - CARPET k: k cells PRIMED→CARPET, worker moves
  - SEARCH: no cell change, worker unchanged, +4 or −2 points
- Effective branching factor in late-game with many primes: ~15 (more carpet options) + ~5 high-EV searches = **~20 legal moves per ply**.

**Reachable states in 6 plies:** ~20^6 ≈ **64M** unpruned. With α-β pruning and zobrist dedup, typically **~100k–1M unique states**.

**Key problem: rat belief is state-dependent and continuous.** The belief distribution over 64 cells is a function of the full history of noise + distance observations, not just the current board. Two paths to the same cell-mask configuration have different beliefs. The tablebase cannot key on cell state alone — it must also key on belief, which has 64 real-valued components. **No static lookup table possible.**

### B.2 Retrograde analysis attempt

The classical chess-tablebase approach:
1. Enumerate all terminal states (turns_left = 0).
2. Label each with winner based on points.
3. Walk backward, propagating min/max values.

**Breaks here because:**
- Terminal "winner" depends on `player_worker.points` and `opponent_worker.points`. Two paths to the same cell/worker config will have different scores. So the "same" cell-configuration is actually many states.
- **Fix:** store *point-delta* from current state, not absolute winner. Then tablebase gives "best achievable point delta from this state in M plies". That's just a **min-max game-value function** — exactly what α-β computes.
- **So the "tablebase" is just memoized α-β at depth M.** No new algorithm.

### B.3 Comparison with live α-β at depth 6

The RattleBot's existing α-β (`3600-agents/RattleBot/search.py`) already does iterative-deepening expectiminimax with transposition-table caching (`zobrist.py`) and heuristic leaf eval. At depth 6 in the endgame with ~15 effective branching, a reasonable α-β completes in ~2–6s.

**What "endgame tablebase" would add:**
1. **Exhaustive depth to true horizon.** If 6 plies from end, go to depth 6 exactly with no heuristic cutoff. Replace heuristic eval at leaves with actual point-count + residual-prime-potential estimate.
2. **More time budget.** Spend all remaining clock on the last few plies.

These are both **time-management tweaks**, not new data structures. They collapse into a 5-line change to `time_mgr.py`: "when `turns_left ≤ 6`, allow 2× the normal per-move time cap." No offline precompute, no tablebase file, no new search code.

### B.4 Offline precompute?

Could we enumerate all **plausible** endgame boards and cache solutions?
- Number of distinct mid-game boards: effectively unbounded (the cell configuration has ~4^50 possibilities, most unreachable but still enormous).
- Reachable boards from a given starting board by turn 34 depend on both players' entire move history. Sampling games to build a realistic endgame corpus would take as long as just playing more games.
- **Not feasible.**

### B.5 Part B Verdict

**Not a tablebase — just a time-allocation knob.** The "endgame solver" reduces to "let α-β run deeper in the last 6 plies" which is a trivial `time_mgr` change (estimated <1 hour of work, <20 LoC). This is a legitimate improvement but belongs in the **heuristic/search task track**, not as a separate solver.

**Recommendation: fold this into `time_mgr`.** Suggested rule: for the last 8 plies of the game, allow up to 1.8× the average remaining-time budget per move, and set the α-β depth cap to max(6, remaining_time ÷ 1s). Confirm the current ceiling in `T-20a` (lift time ceiling 3→6s) is already compatible.

---

## Part C — Prototype status

**No prototypes written.** Both solvers landed on "do not ship":
- Opening book: feasible but low-ROI given deadline pressure; building the book eats time that T-20c/T-20d would convert to more ELO.
- Endgame tablebase: reduces to a `time_mgr` tweak; no separate solver.

If leadership overrides and wants the opening book shipped anyway, the prototype shape is:

```
tools/opening_book_solver.py
├── Enumerate 81 blocker layouts × 8 spawn pairs = 648 positions (324 after y-reflection dedup)
├── For each: run depth-10 expectiminimax with nominal T (mean of 4 pkl files)
│   └── Reuse RattleBot's search.py with a higher depth_cap
├── Extract best move per (blocker, spawn) canonical key
├── Also enumerate ply-1 responses for each of B's ~6 replies to A's book move
└── Serialize to 3600-agents/RattleBot/opening_book.json
    Key format: {"blocker_mask_hex": str, "spawn_a": [x,y], "spawn_b": [x,y], "move_history": [[type, dir, roll?], ...]}
    Value: {"move_type": int, "direction": int, "roll_length": int, "search_loc": [x,y]|null}
```

Runtime integration: `agent.py::play` checks the book before calling search; if hit, validates via `board.is_valid_move` and returns; else falls through to α-β.

**Estimated dev time: ~4–6 hours** (solver + canonicalization + runtime hook + validation tests). **Estimated ELO: ~20–30.** Not worth the opportunity cost vs. T-20c/T-20d.

---

## Summary of Recommendation

| Proposal | Verdict | Reasoning |
|----------|---------|-----------|
| Opening book | **Do not ship** | Feasible in ~2h offline compute + ~5h dev, but ~20–30 ELO ceiling; T-20c/T-20d have higher ROI with same dev budget 3 days from deadline |
| Endgame tablebase | **Do not ship as tablebase; fold into time_mgr** | Reduces to "spend more time in last 6 plies + deeper α-β" — no new data structure needed. Recommend a 20-LoC time_mgr change owned by whoever is finishing T-20a. |

**Next steps for the team:**
1. **Confirm** that T-20a's time ceiling change includes a late-game boost rule (deeper search in last 6–8 plies). If not, add a ticket.
2. **Deprioritize** any opening-book work until post-deadline (e.g., a v2 experiment).

---

## Sources

- `engine/gameplay.py:254-262` — corner blocker generation
- `engine/gameplay.py:22-24` — transition matrix ±10% noise
- `engine/board_utils.py:186-190` — spawn generation
- `engine/game/board.py:130-197` — `get_valid_moves`, branching factor
- `engine/game/rat.py:127-131` — `HEADSTART_MOVES=1000`
- `docs/GAME_SPEC.md` §1–§5 — authoritative spec cross-reference
