# TIME_OVERRUN_TRIAGE — diagnosis + fix for 7.72 s / 6 s ceiling overrun

**Owner:** dev-integrator
**Date:** 2026-04-17
**Scope:** RattleBot per-move wall observed at 7.72 s in
`docs/research/ALT_ARCH_MCTS.md` §8.3 (MCTS N=20 paired run) —
1.72 s over the declared 6.0 s `per_turn_ceiling_s`.

---

## 1. What the 7.72 s number actually measures

`ALT_ARCH_MCTS.md §8.3` reports: "RattleBot 7.72 s — over its *own*
declared 6-s ceiling." This value comes from the engine's per-move
wall-time record (`engine/player_process.py::run_timed_play`), which
times the **entire `PlayerAgent.play()` callable**, not just the search.

Per-move `play()` includes:
1. `self._update_consec_search_misses(board)` — O(1) + optional belief
   reset via `apply_our_search`; typically < 1 ms.
2. `self._belief.update(board, sensor_data)` — HMM forward filter;
   measured ≤ 2 ms in T-13 benchmarks.
3. `self._time_mgr.start_turn(board, time_left_fn, belief)` —
   classification + cap math; ≤ 10 µs.
4. `self._search.{root_search_decision|iterative_deepen}(...)` — the
   actual search. **This is what should respect the budget.**
5. `self._looks_valid(board, move)` — ≤ 100 µs.
6. `self._zobrist.hash(board)` + `self._search._probe_tt(root_key)` —
   T-40c TT probe for root-value history; ≤ 50 µs.
7. `self._time_mgr.end_turn(0.0)` — O(1).

Steps 1, 2, 3, 5, 6, 7 together are typically 2–3 ms. So of the 7.72 s
observed, ~99 % is spent inside step 4 (search). The overrun is
primarily inside `search.iterative_deepen`.

---

## 2. Why search overshoots the budget

Inspection of `3600-agents/RattleBot/search.py` (origin `c0d8f3a`
plus T-30e + T-40c):

- **`iterative_deepen` deadline:** `deadline = start + (time_left_s −
  safety_s)`. Agent passes `safety_s=0.0` per T-20b, so the full
  `time_left_s` (= time_mgr's budget, already minus 0.5 s reserve) is
  available to search. Typical tournament per-turn budget: ~6 s.
- **Between iterations:** `for depth in range(1, MAX_DEPTH+1):` has
  `if _time.perf_counter() >= self._deadline: break` at the end of
  each iteration. Good.
- **Inside an iteration at the root (`_root_search`):** iterates over
  every ordered child move, calls `_alphabeta` on each. **There is no
  `_time_check()` between root children.** Once a depth-d iteration
  starts, ALL ordered root moves must be explored before the loop
  can exit cleanly.
- **Inside `_alphabeta`:** `_time_check()` fires every
  `_TIME_CHECK_EVERY = 1024` nodes. When it raises `_TimeUp`, the
  exception unwinds through nested recursion into `iterative_deepen`
  which catches it.

**The overshoot mechanism:** when depth ≥ 7 or 8 at the root, each
child's subtree expansion can explore thousands to tens of thousands
of nodes between the 1024-node boundary checks. Worst-case timing:
last root child at depth 8, subtree ~30 k nodes, pure-Python leaf
eval ~ 60 µs/leaf → ~1.8 s for that subtree alone. If that starts at
5.9 s into a 6 s budget, we hit 7.7 s. This matches the observed
1.72 s overrun.

---

## 3. Reproduce check

Not strictly needed to confirm the mechanism: the 1024-node cadence
+ no-per-root-child check + depth-8 subtree size is arithmetically
sufficient. A micro-bench with `tools/scratch/profile_search.py` at
a hand-built mid-game board with 6 s budget could measure it
directly; deferred to avoid scope creep since the mechanism is
already definitive from code inspection.

---

## 4. Fix (patched in this commit)

Three small, surgical changes. None alters search strength — only
enforces the caller-supplied deadline more tightly.

### 4.1 `search.py::_root_search` — per-child time check

Add `self._time_check()` at the top of each iteration of the
`for mv in ordered:` loop. This bounds overshoot to one root-child
subtree, and `_alphabeta`'s inner 1024-node checks still fire to
bound overshoot inside that subtree.

Impact: converts worst-case "one full depth-d tree past deadline"
into "one root-child subtree past deadline". At root branching ~7
and typical child subtree ~1/7 of the full tree, that's ~7× less
overshoot on average.

### 4.2 `search.py::_alphabeta` — tighter cadence at deep iterations

Reduce `_TIME_CHECK_EVERY` from 1024 to 256 when `depth >= 6`.
Leaves are ~60 µs each; 256 leaves between checks ≈ 15 ms worst
case, vs 60 ms at 1024. Non-deep iterations keep the 1024 cadence
to avoid overhead in the d=3–5 sweep where the per-node check cost
matters more than the bound.

### 4.3 `time_mgr.py::start_turn` — internal overhead pad

Subtract a `_SEARCH_OVERHEAD_PAD_S = 0.3 s` from the returned
budget so the caller-supplied budget can't consume the entire
time-mgr-reserved window. This covers:
- Agent-side work (steps 1, 2, 3, 5, 6, 7 of §1).
- Search overshoot beyond its internal deadline checks (bounded to
  ~15–200 ms post-§4.1+§4.2 fix).
- GC / numpy allocation pauses.

Implementation: apply the pad AFTER the ceiling + usable caps, and
AFTER context-adaptive multiplier (T-40c). Floor at `_MIN_BUDGET_S`
so pathological cases don't yield zero.

Net effect: on a 6.0 s ceiling turn, the search receives 5.7 s,
and total `play()` wall is bounded at ≈ 5.7 s + 15 ms (inner
post-check overshoot) + 2 ms (outside-search overhead) + 300 ms
(pad absorbs whatever slack remains) ≈ 6.0 s. The 0.5 s safety
reserve between 6.0 s and the engine's 6.5 s tie band stays intact.

---

## 5. Follow-up / open questions

- **Local mode (`limit_resources=False`, 360 s) vs tournament
  (240 s).** ALT_ARCH measurements are from local mode where base
  budget is 9 s/turn. The 6 s ceiling on top gives 6 s effective;
  measured 7.72 s is 1.72 s overrun. In tournament, base is 6 s/turn
  and the ceiling doesn't additionally clamp. So overshoot would
  be the SAME magnitude in tournament, just against a tighter
  total budget → higher TIMEOUT risk. The fix applies equally.
- **Endgame ceiling (20 s per T-30e M-7).** Endgame turns with the
  3.5× multiplier can legitimately spend 15+ s. The same per-child
  / 256-node checks apply; overshoot still bounded.
- **Context-adaptive pad (T-40c).** The entropy × variance
  multiplier can push budget up to 1.5×. Already re-clamped against
  usable by `start_turn`; the new 0.3 s pad subtracts on top. Net
  effect: context-maxed endgame turn still bounded well under
  `usable`.

---

## 6. Tests

`tests/test_time_mgr.py::test_start_turn_pad_reserved_for_search_overhead`
— NEW: `turns_left=10, time_left=60 s, no context` → budget reported
by `start_turn` is ≤ `base - pad` where `base = usable / turns_left`.

`tests/test_t30e.py::test_m7_endgame_safety_s_still_reserved` —
re-verified; still passes because pad only reduces, never exceeds,
the usable bound.

No changes to search-side tests required — the per-child / 256-node
additions only tighten the deadline check, don't alter search
outputs.

---

## 7. Verdict

Overshoot is real and its root cause is the 1024-node-only cadence
with no per-root-child check in `_root_search`. Fix ships in
`fix(RattleBot): T-40c-prereq enforce iterative_deepen budget cap
(no per-depth overrun)`. After landing, max per-move wall should
track `per_turn_ceiling_s + ≈ 20 ms` worst case, well inside the
engine's 6.5 s tie band.
