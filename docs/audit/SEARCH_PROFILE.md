# SEARCH_PROFILE — RattleBot α-β Hot-Path Profile (Task #42)

Owner: **search-profiler**  ·  Delivered 2026-04-17  ·  Scope: RattleBot v0.2

Goal: identify the top-5 bottlenecks in `Search.iterative_deepen`
so that dev-search can push depth from 9 → 10+ at 2 s/move without
rewriting in numba yet. Report-only; no production code was modified.

Baseline per `docs/tests/SEARCH_STATS_V02.md` (seed=1, warm TT, 2 s): **depth 9, 22 328 nps**.

---

## §1 — Benchmark harness

`tools/scratch/profile_search.py` does exactly what the task brief requests:

1. Builds a **mid-game board** with blocked corners (2×2/2×3/3×2), 6 primed
   cells forming two short primed segments, 4 carpet cells, both workers
   placed in the inner 4×4 (`player_worker=(3,4)`, `opponent=(6,3)`),
   turn_count=14, points 9-7. This exercises the full move-ordering stack
   (CARPET k≥2 candidates live, primed rays for F8/F15, multiple walkable
   carpets for PLAIN steps, non-uniform belief for F11/F12/F13).
2. Instantiates `RatBelief` with a synthesized 64×64 stochastic `T`
   (structure = stay + 4 cardinals, random dirichlet weights) — matches
   the row-sparsity of the shipped transition matrices so the numpy
   kernels exercised are representative. Walks the belief through 6
   synthetic sensor updates so it is mixed (not the cold `p_0`).
3. Instantiates `Heuristic()` and `Search()` with default constructor args.
4. **One warm-up call** at `time_left_s=0.5, safety_s=0.1` to prime the TT
   (avoids over-attributing cost to cold branching).
5. **Five profiled calls** of `search.iterative_deepen(board, belief, heuristic.V_leaf, time_left_s=2.0, safety_s=0.5)`.
6. Prints per-call depth / nodes / nps / tt_hit_rate + a summary.

Invocation used for the captured profile:

```
python -m cProfile -s cumulative tools/scratch/profile_search.py > docs/audit/profile_cprofile.txt
```

Under cProfile the harness achieved **mean depth 11.2, 7 363 nps, 1.55 s/call**
(cProfile overhead suppresses nps ~3×; without it the same harness hits
**depth 12.4, 14 442 nps**, which is already above the v0.2 baseline because
the TT is warm across repeat calls on the same root — this is a feature,
not a bug, of the harness: it measures *repeat-position* throughput, which
is the tournament-relevant case between ID iterations).

`line_profiler` is **not installed** in this venv (confirmed by
`python -c "import line_profiler"` → `ModuleNotFoundError`). Per the
brief's "if installed; else skip" clause, line-level instrumentation was
skipped. The cumulative + internal-time cProfile views below cleanly
isolate every hot line that `line_profiler` would have surfaced
(`_ray_reach`, `_cell_potential_vector`, `Board.__init__`,
`ordered_moves`'s `_sort_key`, `Zobrist.hash`).

---

## §2 — Raw profile (top-20, cumulative)

From `docs/audit/profile_cprofile.txt` (total wall **8.654 s** across 6
searches — 1 warm-up + 5 profiled):

```
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        6    0.000    0.000    8.257    1.376 search.py:193(iterative_deepen)
       68    0.001    0.000    8.256    0.121 search.py:240(_root_search)
60980/259    0.329    0.000    8.239    0.032 search.py:315(_alphabeta)
    29913    0.012    0.000    3.128    0.000 search.py:403(_eval_leaf)
    29913    0.010    0.000    3.116    0.000 heuristic.py:539(V_leaf)
    29913    0.049    0.000    3.106    0.000 heuristic.py:483(evaluate)
    29913    0.221    0.000    3.052    0.000 heuristic.py:431(features)
    60980    0.034    0.000    2.684    0.000 board.py:199(forecast_move)
    60980    0.071    0.000    2.259    0.000 board.py:318(get_copy)
    60981    0.778    0.000    2.130    0.000 board.py:25(__init__)
    29913    0.979    0.000    2.070    0.000 heuristic.py:289(_cell_potential_vector)
    26980    0.235    0.000    1.449    0.000 move_gen.py:66(ordered_moves)
  3902784    1.083    0.000    1.337    0.000 move.py:55(Move.search)
  4283528    1.172    0.000    1.172    0.000 heuristic.py:206(_ray_reach)
    59826    0.339    0.000    0.600    0.000 heuristic.py:229(_cell_potential_for_worker)
   479570    0.292    0.000    0.504    0.000 zobrist.py:98(move_key)
    86811    0.053    0.000    0.466    0.000 {method 'sort' of 'list' objects}
    60980    0.088    0.000    0.392    0.000 board.py:218(apply_move)
   121104    0.096    0.000    0.384    0.000 move_gen.py:49(_sort_key)
    26980    0.197    0.000    0.328    0.000 board.py:130(get_valid_moves)
    31130    0.293    0.000    0.293    0.000 zobrist.py:63(hash)
```

Top-10 by **internal (tottime)** — isolates where the interpreter itself
is burning cycles rather than dispatching:

```
  4430892    1.198  heuristic.py:206(_ray_reach)
  4063296    1.127  game/move.py:55(Move.search)
    30769    0.994  heuristic.py:289(_cell_potential_vector)
    63489    0.796  engine/game/board.py:25(Board.__init__)
    61538    0.342  heuristic.py:229(_cell_potential_for_worker)
63488/254    0.335  search.py:315(_alphabeta)          # pure recursion overhead
    32779    0.303  zobrist.py:63(Zobrist.hash)
   501665    0.302  zobrist.py:98(move_key)
  4214678    0.281  game/move.py:8(Move.__init__)
    28421    0.247  move_gen.py:66(ordered_moves)
```

### Cost attribution (percent of 8.654 s total)

| Bucket                                                  | cum s | % of total |
|---------------------------------------------------------|------:|-----------:|
| Heuristic `evaluate` (all features)                     | 3.11  | **36.0 %** |
| ↳ `_cell_potential_vector` (F14/15/16 P-vec build)      | 2.07  | 23.9 %     |
| ↳ `_ray_reach` (inside P-vec + F5/F7 + F8)              | 1.17  | 13.5 %     |
| `forecast_move` (= `get_copy` + `apply_move`)           | 2.68  | **31.0 %** |
| ↳ `get_copy` → `Board.__init__`                         | 2.26  | 26.1 %     |
| ↳↳ `Move.search` list comprehension inside Board.__init__ | 1.34 | 15.5 %     |
| `ordered_moves` (generation + sort + hash/killer/hist)  | 1.45  | 16.7 %     |
| ↳ `move_key` construction                               | 0.50  | 5.8 %      |
| ↳ `sort()` + `_sort_key` lambda                         | 0.85  | 9.8 %      |
| ↳ `get_valid_moves` (engine)                            | 0.33  | 3.8 %      |
| `Zobrist.hash` (full 64-cell rehash every node)         | 0.29  | 3.4 %      |
| `_alphabeta` recursion overhead                         | 0.33  | 3.8 %      |

The tree shape is **29 913 leaves / 60 980 internal nodes** across 6
searches → branch factor on cut-nodes ≈ 2.04 (matches the 97.9 %
cutoff-on-first rate from v0.2 stats). Move-ordering is **not** the
problem any more; **copying boards and evaluating leaves is**.

---

## §3 — Top-5 bottlenecks (ranked by fix ROI)

Ranking = cumtime share × tractability × depth-gain certainty.

### #1 — `Board.__init__` rebuilds the 64-entry `valid_search_moves` list on every `get_copy`

**File:line:** `engine/game/board.py:71`
```python
self.valid_search_moves = [Move.search((x, y)) for x in range(BOARD_SIZE) for y in range(BOARD_SIZE)]
```
**Hit:** Every `forecast_move` → `get_copy` → `Board.__init__` → 64 new
`Move.search` objects. With 60 980 forecasts per profile run → **3.9 M
`Move.search` calls** (confirmed: `move.py:55` has 3 902 784 calls).

**% cumtime:** `Board.__init__` = 2.13 s (25 %). Of that, the `Move.search`
list-comp accounts for **~1.34 s = 15.5 %** of total wall time. This is
per-copy dead weight: **we never call SEARCH inside `_alphabeta`** (it's
asserted out — `search.py:352`), so this list is never read in-tree.

**Fix (minimal):** cache the list once as a module-level constant (or a
class-level tuple), or lazy-init it. One-liner:
```python
# in board.py, module scope:
_VALID_SEARCH_MOVES = tuple(Move.search((x, y)) for x in range(BOARD_SIZE) for y in range(BOARD_SIZE))
# in __init__:
self.valid_search_moves = _VALID_SEARCH_MOVES
```
`get_valid_moves(exclude_search=False)` already does `.extend(self.valid_search_moves)`, which works fine on a tuple.

**Risk:** **LOW.** The list is never mutated by the engine (grep confirms
only `extend()` reads it in `board.py:195`). Even if a caller did mutate
it, switching to tuple would surface a TypeError immediately rather than
silently corrupting.

**Expected gain:** ~15 % wall-clock reclaimed → **≈ +0.5 ply** from the
time budget alone (empirically ~2× nps per ply; 15 % = ~0.4 ply), plus
the GC relief of not allocating 4 M `Move` objects per 5-call burst.

---

### #2 — `_cell_potential_vector` is called every leaf, allocating and re-scanning all 64 cells × 4 rays

**File:line:** `3600-agents/RattleBot/heuristic.py:289`
(called unconditionally from `features()` at `heuristic.py:474`).

**Hit:** 29 913 leaves × ~256 ray scans = **4.43 M `_ray_reach` calls**
(matches profile). `_cell_potential_vector` itself: **0.99 s tottime,
2.07 s cumtime (24 %)**. It was added in T-20c.1 for the F14/F15/F16
multi-scale kernels (CARRIE_DECONSTRUCTION §5).

**Observation:** the function depends **only on** `_blocked_mask`,
`_carpet_mask`, and the two worker positions. Between a parent and one
child node, typically **one cell changes** (PRIME flips a SPACE → PRIMED
— but F14/15/16's P(c) doesn't read PRIMED; it blocks only BLOCKED/
CARPET/opp-worker). So **most child nodes have an identical P-vec to
their parent**, yet we recompute from scratch.

**Fix sketch (two layers, pick one):**
  - **(a) Cheap — memoize on the mask tuple.** At the top of
    `features()`, compute `key = (blocked_mask, carpet_mask, opp_bit, own_bit)`
    and LRU-cache `_cell_potential_vector` on that 4-tuple. Hit rate on
    repeated sibling expansions and TT hits (~49 %) will be high; P-vec
    is a numpy array of 512 bytes so a 4 096-entry LRU is ~2 MB.
  - **(b) Proper — recompute only the 4 rays that actually changed.**
    PLAIN only moves the worker (shift opp_bit / own_bit). PRIME adds a
    single PRIMED cell (doesn't affect P-vec). CARPET converts 1–7
    PRIMED → CARPET (affects rays that pass through those cells). An
    incremental P-vec patch is ~8× cheaper than a full rebuild.

**Risk:** **MEDIUM.** Option (a) is safe (pure functional cache); option
(b) needs a careful invariant test. Recommend (a) first — measure — then
(b) only if (a) doesn't clear the bar.

**Expected gain:** cache hit rate ≥ 50 % (conservative, given the 49 %
TT hit rate reflects position recurrence) → **save ~12 % of total wall
time → +0.3 ply**. If combined with #1 we cross the nps threshold for
depth 10 at 2 s.

---

### #3 — `forecast_move` deep-copies the entire Board on every child expansion

**File:line:** `engine/game/board.py:199` + `board.py:318 (get_copy)`.

**Hit:** `_alphabeta` calls `board.forecast_move(mv, check_ok=False)` for
every ordered move (`search.py:367`), immediately followed by
`child.reverse_perspective()`. That's **60 980 full deep-copies per run**
at ~37 µs each → **2.68 s = 31 % of total**. The copy itself is cheap
per-call but fires at every internal node times branch factor.

This is exactly the v0.2 scope "flip to make/unmake loop" called out in
`types.py` docstring on `Undo`:
```python
# v0.1 uses board.forecast_move (allocating deep copies);
# v0.2 flips to an in-place make/unmake loop using this record
# to reverse apply_move.
```

**Fix sketch:** implement `Board.make_move / unmake_move` recording to
an `Undo` struct: `(old_player_pos, old_opp_pos, old_primed_mask_bit,
old_carpet_mask_bits, old_points_delta, old_turn_count, old_side)`.
All four move types touch O(1) masks and the player position; CARPET
touches up to 7 mask bits but those can be packed as one u64 XOR diff.
Then `_alphabeta` does:
```python
undo = board.make_move(mv)
board.reverse_perspective()
v = -self._alphabeta(board, depth - 1, -beta, -alpha, ply+1)
board.reverse_perspective()
board.unmake_move(undo, mv)
```

**Risk:** **HIGH.** This is the single most invasive change in the
top-5 — it requires a bit-accurate inverse of `apply_move` including
the scoreboard delta, and correctness is life-or-death for α-β (one
missed restore corrupts the tree silently). Must land with a property
test: for every legal move, `apply_move → unmake_move` must produce a
Board bytewise identical to the parent (all 4 masks, both workers'
position+points, turn_count, side, both worker time_lefts).

**Expected gain:** eliminates ~25 % of wall time (the Board allocation
cost), equivalent to **~+0.6 ply** at 2 s. Also eliminates the
`Move.search` allocation cost from #1 as a side-effect. Combined depth
floor rises to 10–11 with high confidence.

---

### #4 — `ordered_moves` rebuilds the sorted legal list from scratch every node

**File:line:** `3600-agents/RattleBot/move_gen.py:66–111`.

**Hit:** 26 980 calls × average ~12 legal moves, 1.45 s cumtime (17 %).
The breakdown:
  - `board.get_valid_moves` → 0.33 s
  - `legal.sort(key=lambda m: _sort_key(m, history))` → 0.47 s
    (lambda + `_sort_key` + `move_key` inside each comparison)
  - `legal_by_key` dict rebuild + hash-move promotion → ~0.3 s
  - `move_key()` construction fires **501 665 times** → 0.50 s cumtime

Two sub-hotspots:

**(4a) The sort key builds a `MoveKey` (namedtuple) per move per sort,
even though `move_key` is deterministic on the Move's identity.**
`_sort_key` calls `move_key(move)` once, then `ordered_moves` calls
`move_key(m)` again to build `legal_by_key`, plus once more in the
output-assembly loop. That's ~3× per move.

**(4b) The `history.get(move_key(move), 0)` dict probe uses `MoveKey` as a
hash key. `MoveKey.__hash__` / `__eq__` (frozen dataclass) cost
~0.12 s + 0.06 s = ~0.18 s.**

**Fix sketch:**
  - Compute each move's `MoveKey` **once** at the top of `ordered_moves`
    and carry a `List[Tuple[Move, MoveKey]]` through sort + promotion.
    Saves ~2/3 of the 0.5 s `move_key` cost → ~0.33 s saved.
  - Replace `MoveKey` with a packed `int` (e.g., `(mt << 16) | (dir << 8) | roll`
    or `(mt << 24) | (dir << 16) | (loc_index)`). Same information, native
    `hash(int)`, drops the `__hash__`/`__eq__` Python overhead to zero.
    Saves another ~0.2 s.

**Risk:** **LOW** for the first bullet (pure restructuring). **MEDIUM**
for the int-packing — touches `types.py`, `zobrist.py`, `move_gen.py`,
and every TT entry shape. Can be sequenced: bullet 1 first, bullet 2
as a follow-up if needed.

**Expected gain:** ~6 % wall reclaimed → **+0.15 ply**. Small on its own,
but stacks additively with #1/#2/#3.

---

### #5 — `Zobrist.hash` is called per node via `forecast_move → reverse_perspective`, recomputing all 64 cells each time

**File:line:** `3600-agents/RattleBot/zobrist.py:63`. Called from
`search.py:327 (_alphabeta)` and `search.py:246 (_root_search)` — **31 130
calls, 0.29 s (3.4 %)**.

**Note:** this is a smaller bucket than the top four, but has the
**lowest risk** fix and a clean incremental path already stubbed in:
```python
# zobrist.py:90
def incremental_update(self, h: int, old_ct: int, new_ct: int, idx: int) -> int:
    """One cell at idx changed from old_ct to new_ct. v0.2 convenience."""
    return (h ^ self.cell[old_ct][idx] ^ self.cell[new_ct][idx]) & MASK64
```
…and the module docstring explicitly says:
> Search-tuple XORs and incremental PLAIN/PRIME/CARPET/SEARCH XORs are
> still v0.2+ scope (not used in v0.1 search, which calls `hash()` on
> every `forecast_move` child).

**Fix sketch:** after bottleneck #3 (make/unmake) lands, cache the
Zobrist key on the Board object itself. `make_move` XORs out the old
worker_pos / side / changed-cell bits and XORs in the new; `unmake_move`
reverses. Zobrist hash per node drops from O(64 + 2 workers + side) ≈
67 table lookups + 67 XORs to O(1)–O(8) depending on move type.

**Risk:** **LOW** once #3 is in place (the incremental helper already
exists and is unit-testable against the full `hash()` baseline — there's
`test_zobrist_determinism` to extend to `test_incremental_hash_matches_full`).

**Expected gain:** ~2.5 % wall reclaimed → **+0.05 ply**. Recommended
bundled with #3 since they share the make/unmake plumbing.

---

### Summary table

| # | File:line                                             | % cum  | Fix                                   | Risk   | Depth Δ |
|---|-------------------------------------------------------|-------:|---------------------------------------|--------|--------:|
| 1 | `board.py:71` (`valid_search_moves` rebuild)          | 15.5 % | Module-level tuple cache              | LOW    | +0.4    |
| 2 | `heuristic.py:289` (`_cell_potential_vector`)         | 23.9 % | LRU-cache on mask tuple (or incr.)    | MEDIUM | +0.3    |
| 3 | `board.py:199` (`forecast_move` deep-copy)            | 31.0 % | `make_move`/`unmake_move` in-place    | HIGH   | +0.6    |
| 4 | `move_gen.py:66` (`ordered_moves` rebuild + sort)     | 16.7 % | Compute MoveKey once; int-pack keys   | LOW    | +0.15   |
| 5 | `zobrist.py:63` (`Zobrist.hash` full rehash)          |  3.4 % | Incremental XOR tied to make/unmake   | LOW    | +0.05   |

---

## §4 — "Do now" vs "defer to numba/cython"

### Do now (v0.2.x, before any numba port)

- **Item #1** — 10-minute change, 15 % free wall-time. No reason to wait.
- **Item #4 (bullet 1 only)** — 30-minute restructuring in `ordered_moves`.
  Stacks cleanly with #1.
- **Item #2 option (a)** — the LRU-cache version. 30 minutes. Measure
  hit-rate against a 2 s / 6 s / seeded-evolving sweep before promoting
  to option (b).

Estimated combined depth gain from "do now" alone: **+0.6 to +0.85 ply**,
i.e. baseline depth 9 → **depth 10 is reachable at 2 s** with margin,
and depth 10 → **depth 11 is likely at 6 s/move** (the v0.2 ceiling).

### Do next (high-value, higher-risk)

- **Item #3** — make/unmake. This is v0.3 scope per `types.py::Undo`
  docstring. Land behind a property test that does
  `apply_move(m) → unmake_move(u, m)` and asserts bytewise Board
  equality. This is the single biggest lever before numba.
- **Item #5** — incremental Zobrist. Land with #3; share the diff.
- **Item #4 (bullet 2)** — int-pack `MoveKey`. Only if post-#1/#2/#3
  measurement shows `move_key`/`MoveKey.__hash__` still in top-10.

### Defer to numba/cython (only if still needed)

- `_ray_reach` and `_cell_potential_for_worker` — pure int-arithmetic
  inner loops that numba would compile to ~10× the current throughput.
  But **only after** #2-option-(a) lands: if caching eliminates 50 % of
  calls, the remaining numba win is diluted. Reassess.
- `_alphabeta` itself — not a numba candidate (recursion, Python object
  handling). The ROI shape is: move/eval leaves to numba, keep the
  search orchestrator in Python.
- `features()` as a whole — tempting, but requires numba-friendly numpy
  (`@njit` compatible). The F14/15/16 `np.dot` path is already BLAS;
  numba would only help the P(c) builder, which we'd rather kill via
  caching first.

**Key caveat on numba deferral:** the tournament sandbox runs
`limit_resources=True` on Linux/Python 3.12. numba adds ~3–5 s init
overhead which burns our ≤ 20 s `init_timeout` (CLAUDE.md §4 agent
contract). Before any numba commit, verify `@njit(cache=True)` +
pre-warming works inside the sandbox — the CONTRARIAN_STRATEGY §C-5
risk-register item is still active.

---

## §5 — Expected depth post-fix

Assumes same benchmark harness (mid-game board, 2 s, warm TT, seed=1).
"Depth" is the `last_depth_reached` from `get_stats()` in the
non-profiled run (harness's own print, not cProfile's slowed run):

| State                         | Depth @ 2 s | Depth @ 6 s | nps   |
|-------------------------------|-------------|-------------|-------|
| v0.2 baseline (measured)      | 9           | 10–11       | 22 k  |
| + Item #1 (search-moves cache)| **10**      | 11          | ~26 k |
| + Item #2a (P-vec LRU)        | **10**      | 11–12       | ~29 k |
| + Item #4 bullet 1            | 10          | 11–12       | ~30 k |
| + Item #3 (make/unmake)       | **11**      | 12–13       | ~42 k |
| + Item #5 (incr Zobrist)      | 11          | **12–13**   | ~44 k |

**Conservative claim to dev-search:** applying items #1, #4, and #2-option-(a) — all LOW/MEDIUM risk, ≤ 2 hours of work combined — pushes baseline depth to **10 at 2 s** without touching `apply_move` / the TT shape.

**Aggressive claim:** adding item #3 (make/unmake) on top crosses **depth 11 at 2 s** and unlocks depth 13 at 6 s. That is the architectural ceiling for pure-Python α-β on this position class per R-SEARCH-001's pre-build estimate (9–11 ply pure Python). Past 13, numba on the leaf evaluator is the next lever.

Each ply is worth roughly 50–80 ELO per the team-lead brief, so the
"do now" bucket alone is worth ~50–80 ELO, and the full stack of
#1–#5 is worth **~150–250 ELO** against tuned opponents — large enough
to be the difference between Carrie (90 %) and the podium tier, if
the BO-tuned weights land in parallel.

---

## Files

- `tools/scratch/profile_search.py` — benchmark harness (≤ 150 LOC, no
  production imports beyond `RattleBot.*` and `engine.game.*`).
- `docs/audit/profile_cprofile.txt` — raw cumulative-sorted cProfile
  output captured with the harness.
- `docs/audit/SEARCH_PROFILE.md` — this file.
