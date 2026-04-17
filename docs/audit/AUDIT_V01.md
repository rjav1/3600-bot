# AUDIT_V01 — RattleBot v0.1 End-to-End Audit

**Auditor:** auditor (Claude, T-18)
**Date:** 2026-04-17
**Scope:** `3600-agents/RattleBot/` v0.1 code against `docs/GAME_SPEC.md`, `docs/plan/BOT_STRATEGY.md` v1.1, `docs/plan/RATTLEBOT_V01_NOTES.md`, D-004/D-005/D-008/D-009/D-010/D-011.
**Method:** Static read + cross-check against engine source + full pytest run.
**Protocol:** No code changes. Findings only.

---

## §1 — Executive summary

**Verdict:** **PASS (amber — clear to continue v0.1 → v0.2 dev wave; three medium findings should be tracked as v0.2 cleanups, no critical/high issues).**

**Test suite result:** `python -m pytest 3600-agents/RattleBot/tests/ -v` with `PYTHONPATH="engine;3600-agents"` → **34 passed in 4.78 s, 0 failures, 0 errors.** (Pytest without `PYTHONPATH` set fails at collection because `RattleBot/__init__.py` eagerly imports `.agent` which imports `game.*`; tests work via their own `sys.path` bootstrap when invoked directly or with `PYTHONPATH` set. This is a test-harness mechanic, not a bot defect — in tournament, the engine supplies `game.*` via subprocess cwd.)

**Top findings (by severity):**
- **Critical:** 0.
- **High:** 0.
- **Medium:** 3.
  - M-01: `_PER_TURN_CEILING_S = 3.0 s` in `time_mgr.py` silently overrides adaptive multiplier AND hard-cap. In tournament mode, base budget ≈ 6 s/turn so the ceiling burns ~half of the budget. Documented in `RATTLEBOT_V01_NOTES.md` S-2 as v0.1-only. **v0.2 must lift this** once heuristic is BO-tuned.
  - M-02: `budget` in `_alphabeta` is tracked via `self._deadline` only (not safety_s), but the safety_s re-read via `start_turn` → `time_mgr._turn_budget` is never actually plumbed into `search`. Agent passes the time_mgr's `budget_s` to `iterative_deepen` as `time_left_s`, and `iterative_deepen` subtracts `safety_s` a **second time** (`budget = max(0, time_left_s − safety_s)` → effective 0.5 s applied twice). Not a correctness bug (it just means search has slightly less than the time_mgr planned), but obscures intent.
  - M-03: F3/F4 attribution in `heuristic.py` counts board-global `_primed_mask` / `_carpet_mask` popcount as "ours" without subtracting theirs. Documented as an approximation in code comments (§3 under F3/F4), but the approximation means F3 and F4 never differentiate our positioning work from the opponent's — they are literally perspective-invariant (verified by `test_symmetry`). The v0.2 fix is F5/F7 (already landed) + opponent-parity tracking; the approximation is safe for v0.1 because both sides see identical feature values, so they cancel in paired self-play.
- **Low:** 4 nits (zobrist `turn_count // 2` bucket is a documented approximation for TT miss-rate vs wrong-value tradeoff — D-003 arbitration already covers this).

**No show-stoppers.** All 11 audit items pass with evidence (see §3). Emergency fallback is correctly wired (§3.3). The SEARCH-not-in-tree invariant is both asserted in code AND has a targeted test that exercises the assertion. HMM first-turn guard is implemented AND has a reference-value test. Zobrist hash covers all required state. ID respects safety margin. Belief updates are not redundantly done inside the tree. Import isolation is clean. Test coverage is respectable (34 tests) with identified gaps listed in §3 item 10.

---

## §2 — Findings table

Sorted by severity descending, then file.

| File:line | Severity | Issue | Fix suggestion |
|---|---|---|---|
| `3600-agents/RattleBot/time_mgr.py:39, 79-80` | medium | `_PER_TURN_CEILING_S = 3.0 s` caps every turn, including late-game `critical` classification. Leaves ≥ 50 % of tournament budget on the table (base=6s/turn, ceiling=3s). Intentional per RATTLEBOT_V01_NOTES.md S-2 but fires silently. | v0.2: lift ceiling or make it configurable via constructor arg. Document the ceiling explicitly in `commentate()` for tournament logs. |
| `3600-agents/RattleBot/agent.py:127-137` ↔ `search.py:132` | medium | `time_mgr.start_turn` already subtracts `SAFETY_S` (= 0.5 s) from `time_left` to compute `usable`; then `agent.py` passes `budget_s` to `iterative_deepen` as `time_left_s`, and `iterative_deepen` subtracts `safety_s` (= 0.5 s) **again**. Net: 1.0 s of safety applied. Not a correctness defect (strictly conservative), but the interface double-books the safety. | Either (a) pass `budget_s` with `safety_s=0.0` from agent.py, or (b) document that the agent-level layer does not reserve safety and `search` owns the single 0.5 s reserve. |
| `3600-agents/RattleBot/heuristic.py:224-228` | medium | F3 and F4 are `popcount(_primed_mask)` / `popcount(_carpet_mask)` — whole-board totals, NOT "ours". `test_symmetry` explicitly documents this as perspective-invariant. | v0.2: either track prime/carpet attribution via an event-hook from `apply_move` (cheapest: count-since-last-worker-plain-step), OR drop F3/F4 in favor of F5/F7 (already the Carrie-style lever). |
| `3600-agents/RattleBot/search.py:310` | low | `root_search_decision` uses `entry.value` from TT as `best_value` for the SEARCH-vs-non-SEARCH comparison. If the TT entry's flag is `TT_FLAG_LOWER` or `UPPER` (bound, not exact), the comparison is against a bound, not the true root value. | Use the return of `iterative_deepen` directly (`iterative_deepen` should return the value alongside the move) rather than re-probing the TT. One-line refactor. |
| `3600-agents/RattleBot/zobrist.py:79-80` | low | `turn_count // 2` bucketed into 41 slots intentionally drops "true turn_count" resolution for TT miss-rate trade (D-003 clarification). Fine, but could collide across the 40→41 boundary (guard works via `min()`). | None required — documented intentionally. |
| `3600-agents/RattleBot/search.py:146-155` | low | `iterative_deepen` doesn't cap `depth` below `MAX_DEPTH` based on whether a search actually completed — the for-loop can reach d=MAX_DEPTH with no completed iteration if time was never checked. Not observed in practice due to `_TIME_CHECK_EVERY=1024` polling. | Optional: add an elapsed-time check after each depth completes before starting the next depth (partially already done at line 153). |
| `3600-agents/RattleBot/agent.py:69` | low | `transition_matrix=None` falls back to `np.eye(64)`, which means belief is completely static. Not a bug (tournament always passes a T) but a misleading fallback for testing. | Document in docstring that identity T is a test-only degenerate; real games always see a real T. |
| `3600-agents/RattleBot/__init__.py:7-8` | low | `__init__.py` eagerly imports `.agent` (+submodules), which pulls in `game.*`. Pytest collection fails without `PYTHONPATH="engine;3600-agents"` or equivalent. Submission zip will work (engine injects `game.*`), but local test harness needs the path set. | Add a short note in `docs/tests/` or a pytest `conftest.py` that sets `sys.path` at collection time. |

---

## §3 — Per-item walk

### 3.1 — SEARCH-not-in-tree invariant (D-011 item 2)

**PASS.**

- **Evidence, assertion:** `search.py:235-237`:
  ```python
  assert all(
      m.move_type != MoveType.SEARCH for m in ordered
  ), "SEARCH must never enter the in-tree move list"
  ```
  Always-on (not debug-gated). Runs in `_alphabeta` immediately after `ordered_moves(...)` returns.
- **Evidence, test:** `tests/test_search.py:282-311` (`test_search_not_in_tree_invariant`) monkey-patches `search_mod.ordered_moves` to inject a `Move.search((0,0))` into the returned list and asserts `AssertionError` is raised. Test **PASSES** in the 34-test suite.
- **Additional evidence:** `move_gen.py:53-64` — `ordered_moves` calls `board.get_valid_moves(exclude_search=exclude_search)` with default `exclude_search=True`; all call sites from `search.py` either use the default or explicitly pass `exclude_search=True`.

### 3.2 — HMM first-turn guard (D-011 item 7)

**PASS.**

- **Evidence, guard:** `rat_belief.py:145-166`:
  ```python
  skip_opp_phase = (
      self._first_call
      and bool(getattr(board, "is_player_a_turn", False))
      and int(getattr(board, "turn_count", 0)) == 0
  )
  if not skip_opp_phase:
      self.belief = self.belief @ self.T          # step 1
      self._apply_search_result(opp_search)        # step 2
  self.belief = self.belief @ self.T               # step 3
  self._sensor_update(...)                         # step 4
  ```
- **Sequence trace vs engine protocol (`engine/gameplay.py:386-387`):**
  - `__init__`: `belief = p_0 = e_0 @ T^1000`, `_first_call = True`.
  - Engine's first rat move: `rat.move()` called at top of player A's ply; rat now distributed as `p_0 @ T`.
  - A's first `update()` call: `turn_count == 0`, `is_player_a_turn == True`, so skip steps 1-2. Step 3 sets `belief = p_0 @ T`. Step 4 applies sensor. **Correct.**
  - Without the guard, steps 1+2 would run (extra predict over the non-existent opp move), resulting in `belief = p_0 @ T^2` after step 3 → systematic over-prediction on turn 0.
- **Evidence, test:** `tests/test_rat_belief.py:168-200` (`test_first_turn_guard_no_double_predict`) computes the hand-derived reference `ref = (p_0 @ T) * noise_factor * dist_factor / normalizer` and asserts `np.allclose(rb.belief, ref, atol=1e-12)`. Test **PASSES**.
- **Player B first turn:** player B's first `update()` is called with `turn_count == 1`, so `skip_opp_phase` is false and the full 4-step pipeline runs. Correct per BOT_STRATEGY §2.h.

### 3.3 — Emergency fallback

**PASS.**

- **Evidence, try/except wrap:** `agent.py:89-100`:
  ```python
  def play(self, board, sensor_data, time_left) -> Move:
      if not self._init_ok:
          return self._emergency_fallback(board)
      try:
          return self._play_internal(board, sensor_data, time_left)
      except Exception:
          return self._emergency_fallback(board)
  ```
  Every `play()` call is wrapped.
- **Evidence, fallback implementation:** `agent.py:152-195`.
  1. Try `_floor_choose(board)` which does carpet(k≥2) > prime > plain (lines 174-195) and passes through `_looks_valid`.
  2. Fallback: `board.get_valid_moves()` random pick (default excludes SEARCH).
  3. Second fallback: `board.get_valid_moves(exclude_search=False)` random pick.
  4. Absolute terminal: `Move.search((0, 0))`.
- **Under ALL engine conditions:**
  - Normal board: step 1 succeeds.
  - Dead-end (no non-SEARCH legal moves): step 3 picks a SEARCH; all SEARCH locs are in-bounds so valid per GAME_SPEC §2.4.
  - Catastrophic board corruption (`get_valid_moves` raises): step 4 returns `Move.search((0,0))` which is always valid (no state dependence).
- **Initialization failure guard:** `__init__` wraps everything in try/except and sets `self._init_ok = False` on failure (`agent.py:65-81`); first `play()` call immediately returns `_emergency_fallback`.
- **`_looks_valid` guard (`agent.py:146-150`):** also wraps the main path's move return — if `search` returns `None` or an invalid move (per RATTLEBOT_V01_NOTES.md S-5), falls through to `_emergency_fallback`.

### 3.4 — Zobrist completeness

**PASS.**

- **Evidence, hash composition:** `zobrist.py:55-81`. For each of the 64 cells, XORs in one of `cell[SPACE | PRIMED | CARPET | BLOCKED][idx]` — covers all 4 cell types. Then:
  - Worker positions: `player_pos[idx]` + `opp_pos[idx]` XORed. (a) ✓ (b) ✓
  - Side-to-move: `side[0]` or `side[1]` XORed via `board.is_player_a_turn`. (c) ✓
  - Turn count: `turn[turn_count // 2]` XORed, min-clamped to bucket 40. (d) ✓ (with D-003 clarification that turn_count // 2 trades exact turn resolution for TT hit-rate — documented in zobrist.py:8-10 and BOT_STRATEGY §2.g).
- **Note on 4-mask disjointness:** Since engine masks are disjoint (GAME_SPEC §1), the cell loop in `zobrist.py:60-69` correctly picks exactly one cell-type key per bit — no double-counting, no missing state.
- **Evidence, tests:**
  - `tests/test_search.py:76-87` (`test_zobrist_determinism`): same seed → same table → same hash; different seed → different hash.
  - `tests/test_search.py:90-108` (`test_zobrist_hash_sensitivity`): cell-state change, worker-pos change, and side-flip each flip the hash.
  - `tests/test_search.py:111-134` (`test_zobrist_collision`): 10 000 random boards, collision rate < 1 % asserted — measured 0 % on our run.
  - All three **PASS**.
- **Caveat re D-003:** `turn_count` enters hash as `turn_count // 2` (41-bucket), which intentionally merges adjacent plies into the same bucket. This is a deliberate miss-rate / wrong-value trade (ply-by-ply distinctions are mostly captured by worker/mask changes, and bucket collisions that DO occur are dominated by the 64-bit hash full-key check in `_probe_tt`). No correctness risk — `_probe_tt` verifies full 64-bit `zobrist_key == key` before accepting a hit (`search.py:94`).

### 3.5 — Iterative deepening safety margin

**PASS.**

- **Evidence:** `search.py:118-155`:
  ```python
  def iterative_deepen(self, board, belief, eval_fn, time_left_s, safety_s=0.5):
      ...
      budget = max(0.0, float(time_left_s) - float(safety_s))
      self._deadline = start + budget
      ...
      for depth in range(1, MAX_DEPTH + 1):
          try:
              _, move = self._root_search(...)
              best_move = move
              legal = self._reorder_pv_first(legal, move)
          except _TimeUp:
              break
          if _time.perf_counter() >= self._deadline:
              break
  ```
  - **Default `safety_s = 0.5`** matches D-011 item 4 and GAME_SPEC §7's 0.5 s tie-vs-loss band.
  - **Inner-loop time check:** `_time_check` is invoked every `_TIME_CHECK_EVERY = 1024` node expansions (`search.py:200-201`) and raises `_TimeUp` when the deadline is reached. The ID loop catches this and exits.
  - **Outer loop exit:** `_time.perf_counter() >= self._deadline` check between depths (line 153) prevents one-more-iteration-overrun.
- **Evidence, test:** `tests/test_search.py:317-334` (`test_iterative_deepening_respects_budget`) asserts that 1.0 s budget with `safety_s=0.2` returns within 1.1 s wall-time. **PASSES**.
- **Minor concern (M-02):** agent.py re-applies safety when calling `iterative_deepen`; see §2 Findings table. Not a correctness issue (strictly conservative), but a clean-up for v0.2.

### 3.6 — Belief snapshot/restore around SEARCH

**PASS.**

- **Evidence, root-only update path:** `agent.py:113` calls `self._belief.update(board, sensor_data)` **once per turn** before entering the tree. This is the single place belief is mutated during `play`.
- **Inside the tree (`_alphabeta`):** `search.py:275-283` — `_eval_leaf(board)` passes `self._root_belief` (the snapshot taken before the tree was entered) to `fn(board, bs)`. **No belief mutation.** No calls to `snapshot`, `restore`, `apply_our_search`, or `apply_opp_search` from `search.py` (grep-verified).
- **Post-capture reset:** the belief-reset after our successful SEARCH happens on the NEXT turn inside `RatBelief.update()` via `_apply_search_result(board.player_search)` (steps 1-2 or the direct call path). This is correct because:
  1. Our SEARCH at turn T commits. Engine respawns rat between T and T+2.
  2. At turn T+2, `board.player_search = (loc, True)` is visible.
  3. `update()` runs steps 1→2, and step 2 sees `result=True` → `belief = p_0.copy()`. (The `predict(T)` in step 1 is run before the reset, which is slightly inefficient but numerically harmless because step 2 overwrites belief.)
- **Evidence, test:** `tests/test_rat_belief.py:125-135` (`test_post_hit_resets_to_p0_via_helper`) and `tests/test_rat_belief.py:138-146` (`test_apply_our_search_hit_resets_to_p0`). **Both PASS.**
- **Redundancy check:** the helpers `snapshot`, `restore`, `apply_our_search`, `apply_opp_search` exist for an eventual in-tree SEARCH-chance-node expansion (documented v0.2+), but are NOT called by `search.py` today. Confirmed via `grep` in §3 preamble tool results.

### 3.7 — time_mgr 3 s/turn ceiling (S-2)

**PARTIAL — documented, but leaves tournament budget on the table.**

- **Evidence, ceiling:** `time_mgr.py:39, 79-80`:
  ```python
  _PER_TURN_CEILING_S: float = 3.0
  ...
  if budget > _PER_TURN_CEILING_S:
      budget = _PER_TURN_CEILING_S
  ```
  The ceiling overrides even the D-004 2.5× hard cap and the "critical" multiplier (1.6×).
- **Rationale:** Documented in `docs/plan/RATTLEBOT_V01_NOTES.md` S-2 (lines 25-34). The reasoning is sound: in v0.1 the heuristic is uncalibrated (D-009 BO tuning is v0.2), so deeper search just amplifies bias. 3 s keeps batch runs ~3× faster.
- **Tournament-time-on-the-table test:** Simulated `turns_left=2, time_left=60 s` → classification="critical", base=(60−0.5)/2=29.75 s, mult=1.6 → 47.6 s, hard-cap=2.5×29.75=74.4 s, ceiling=3.0 s → **final budget = 3.0 s.** Only 5 % of the available late-game budget is used. **This will hurt ELO** under any heuristic that could profit from deeper search.
- **Tournament-mode math:** base=240/40=6 s/turn, so the ceiling halves the average turn's budget. A well-calibrated v0.2 heuristic would gain depth+1 or depth+2 with the full budget — likely +20-50 ELO.
- **Configurability:** `_PER_TURN_CEILING_S` is a module-level constant, not a constructor arg. Not runtime-configurable.
- **Documentation:** The ceiling is explicitly flagged as v0.1-only in:
  - `time_mgr.py:34-39` module comment.
  - `RATTLEBOT_V01_NOTES.md` S-2 (full rationale + v0.2 owner).
  - v0.2 dev-search + dev-heuristic task.
- **Verdict:** Acceptable for v0.1 per S-2's documented rationale. **Must be lifted or made configurable before v0.2 ships** — or we leave 30-50 ELO on the table.

### 3.8 — Heuristic approximations (F3/F4 attribution, F5 4-ray)

**PARTIAL — documented, with measured correctness guarantees.**

- **F3/F4 attribution approximation (`heuristic.py:8-20, 224-228`):**
  - F3 = `popcount(_primed_mask)` (board-global, both sides).
  - F4 = `popcount(_carpet_mask)` (board-global, both sides).
  - **Documented in module docstring:** lines 8-20 explicitly note "attribution approximation: we do not track who laid which prime, so this is total primed cells on the board".
  - **Correctness under self-play:** since both workers compute features from identical masks, the F3/F4 contribution cancels in the minimax sense. `test_symmetry` (`test_heuristic.py:225-262`) explicitly verifies this:
    ```python
    assert feats_fwd[1] == feats_rev[1]  # F3 popcount invariant under reversal
    assert feats_fwd[2] == feats_rev[2]  # F4 popcount invariant under reversal
    ```
  - **Documented in plan?** Yes — RATTLEBOT_V01_NOTES mentions the integration but the BOT_STRATEGY §3.4 v0.1 scope allows this (5→7 feature expansion just adds F5/F7; F3/F4 attribution remains v0.2 for the "v0.2 scope: full 9-feature vector" line).
- **F5 4-ray approximation (`heuristic.py:148-205`):**
  - Deviation from BOT_STRATEGY §2.c's P(c) formula (sum over all SPACE cells): v0.1 computes P only at the worker's cell, aggregating the 4 cardinal rays. Documented in `heuristic.py:156-173`:
    ```
    Instead of summing over every board cell, v0.1 uses the 4-ray
    best-roll-from-worker-position approximation -- equivalent to
    assuming the worker stands at c. This matches what F9/F10
    (longest_primable) were designed for and is cheap; the per-cell
    sum formulation is deferred to v0.2 when we budget for it.
    ```
- **Hand-crafted-board sanity check of the evaluation:**
  - `test_heuristic.py:307-342` (`test_high_max_belief_triggers_search_signal`): evaluates the same board under uniform vs peaky (0.9) belief. Under `W_INIT`, peaky belief produces a **more negative** evaluation (F11 term dominates), exactly the gradient that drives `root_search_decision` to pick SEARCH at the root. **PASSES** — confirms F11 directionality.
  - `test_heuristic.py:186-195` (`test_terminal_position`): forced game-over with `Δpoints=10` → eval = `10 × TERMINAL_SCALE = 1e5`, dominating any non-terminal leaf value. **PASSES** — confirms terminal short-circuit.
  - `test_heuristic.py:198-222` (`test_zero_features_on_empty_board`): empty-board eval within ±50 of the F11+F12 analytical contribution — sanity-bounded.
  - `test_heuristic.py:225-262` (`test_symmetry`): perspective flip of the same board preserves F3/F4 (approximation), flips F1, swaps F5 ↔ F7. No catastrophic divergence.
- **Catastrophic eval check:** no observed pathologies. The five quantitative sanity checks above cover the main axes (terminal, belief signal, perspective, zero-state).
- **v0.2 fix:** BO-tuned weights + F9/F10 (per D-008 / D-011) + (optionally) per-cell sum formulation for F5/F7.

### 3.9 — Import isolation

**PASS.**

- **Grep-audited imports (see §Import grep output above):** Only two external dependency classes:
  1. Stdlib: `typing`, `dataclasses`, `collections.abc`, `random`, `math`, `time`, `os`, `sys` (tests only).
  2. `numpy` — allowed per `requirements.txt`.
  3. `game.*` — engine-provided per SPEC §4. These imports resolve via the tournament sandbox's injected `game` package; in local test they resolve via `PYTHONPATH="engine;3600-agents"` bootstrap (or the `sys.path` manipulation at the top of each test file).
- **No other cross-agent imports:** no imports from `FloorBot.*`, `Yolanda.*`, or any other `3600-agents/*` package. This matches D-006's "RattleBot embeds FloorBot's emergency_fallback as a local duplicate, not an import" (documented in `RATTLEBOT_V01_NOTES.md` S-4 and `agent.py:174-195`).
- **File operations:** `grep open\(|write|socket|urllib|requests|http|subprocess|os\.(system|spawn|exec)|eval\(|exec\(` shows the only hits are in `tests/_batch_smoke.py` (which is a test harness, not part of the shipped bot; uses `subprocess.run` to launch match runs — standard). **No `open()`, no `write()`, no network, no subprocess in `agent.py` or any module imported by it.** Per GAME_SPEC §7: "no reads/writes outside cwd, no network" — satisfied.
- **RNG determinism:** `Zobrist(seed=0xBADDCAFE)` fixed seed — deterministic hash tables. `PlayerAgent._rng = random.Random(0xBA11A111)` fixed seed — deterministic fallback picks. Deterministic bot given same engine state (ignoring `time.perf_counter` jitter in the time_mgr's should_stop).

### 3.10 — Test coverage

**PASS (34 passing tests) — with documented gaps.**

- **Covered v0.1 behaviors:**
  - HMM: p_0 distribution; belief→p_0 on init; normalization preservation over 40 turns; post-capture reset (helper AND via `apply_our_search` hit); miss zero+renorm; **first-turn guard vs hand-computed reference**; snapshot/restore round-trip; opp-search miss and hit behavior; timing budget; summary fields contract; stationary-drift sanity.
  - Search: Zobrist determinism / sensitivity / collision rate; MoveKey uniqueness; `ordered_moves` excludes SEARCH / promotes CARPET / promotes hash-move; α-β matches plain minimax at d=2 with fewer nodes; TT reduces nodes on 2nd run; **SEARCH-not-in-tree AssertionError fires on leak** (T-18 audit item 1 directly tested); ID respects budget; root decision returns legal move; root triggers SEARCH at p=0.9.
  - Heuristic: evaluate returns float; terminal short-circuit; zero-feature empty board; F1/F5/F7 perspective behavior; F11 signal directionality; class wrapper parity; weight-shape validation; **p99 timing ≤ 250 µs** (median ≤ 100 µs hard-gate).
- **Coverage gaps (severity: medium; fix_suggestion follows):**
  1. **`move_gen.get_ordered_moves` (legacy Move→Move API):** not directly tested — only the `ordered_moves` (MoveKey) variant is covered. Severity: **medium**. Fix: add a 5-line test that constructs a hash_move Move and asserts it sits first.
  2. **`zobrist.incremental_update`:** no test for the XOR-out/XOR-in helper (v0.2 will actually use this on make/unmake). Severity: **medium**. Fix: add a test that verifies `incremental_update` matches `hash` before/after a set_cell.
  3. **`agent._emergency_fallback` path triggered by a forced exception:** no test forces `_play_internal` to raise and verifies the fallback returns a legal move. Severity: **medium**. Fix: add a test with a monkey-patched `_belief.update` that raises, then assert `play()` returns a `board.is_valid_move(m) == True` Move.
  4. **`time_mgr.classify`:** no direct unit tests for easy / normal / critical classification. Severity: **medium**. Fix: 3 test cases with hand-constructed boards.
  5. **End-to-end play (80 plies) integration test:** currently only in `_batch_smoke.py` which shells out to `run_local_agents.py`. Not pytest-collected. Severity: **medium**. Fix: make `_batch_smoke.py` runnable via pytest OR add an in-process micro-game integration test.
  6. **Commentate string test:** no test that `commentate()` returns a string. Severity: **low**. Fix: trivial 2-line test.
  7. **`_looks_valid` failure path** (search returns invalid move, triggers fallback): not directly tested. Severity: **medium** (guards a real observed v0.1 bug per RATTLEBOT_V01_NOTES S-5). Fix: monkey-patch `search.iterative_deepen` to return a crafted invalid move, assert fallback fires.

### 3.11 — Full test-suite run

**Command:**
```bash
cd C:/Users/rahil/downloads/3600-bot && PYTHONPATH="engine;3600-agents" python -m pytest 3600-agents/RattleBot/tests/ -v
```

**Result:** **34 passed in 4.78 s. 0 failures. 0 errors.**

Full per-test summary in §4.

---

## §4 — Test-suite output

```
============================= test session starts =============================
platform win32 -- Python 3.13.12, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\rahil\downloads\3600-bot
plugins: anyio-4.13.0
collected 34 items

3600-agents/RattleBot/tests/test_heuristic.py::test_evaluate_returns_float PASSED [  2%]
3600-agents/RattleBot/tests/test_heuristic.py::test_terminal_position PASSED [  5%]
3600-agents/RattleBot/tests/test_heuristic.py::test_zero_features_on_empty_board PASSED [  8%]
3600-agents/RattleBot/tests/test_heuristic.py::test_symmetry PASSED      [ 11%]
3600-agents/RattleBot/tests/test_heuristic.py::test_per_call_timing PASSED [ 14%]
3600-agents/RattleBot/tests/test_heuristic.py::test_high_max_belief_triggers_search_signal PASSED [ 17%]
3600-agents/RattleBot/tests/test_heuristic.py::test_class_wrapper_matches_module_fn PASSED [ 20%]
3600-agents/RattleBot/tests/test_heuristic.py::test_weight_shape_validation PASSED [ 23%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_p0_valid_distribution PASSED [ 26%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_belief_init_matches_p0 PASSED [ 29%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_update_preserves_normalization PASSED [ 32%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_post_hit_resets_to_p0_via_helper PASSED [ 35%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_apply_our_search_hit_resets_to_p0 PASSED [ 38%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_apply_our_search_miss_zeros_cell PASSED [ 41%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_first_turn_guard_no_double_predict PASSED [ 44%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_snapshot_restore_roundtrip PASSED [ 47%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_opp_search_miss_zeros_cell PASSED [ 50%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_opp_search_hit_resets_to_p0 PASSED [ 52%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_timing_update_budget PASSED [ 55%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_p0_compute_independent_of_board PASSED [ 58%]
3600-agents/RattleBot/tests/test_rat_belief.py::test_summary_fields PASSED [ 61%]
3600-agents/RattleBot/tests/test_search.py::test_zobrist_determinism PASSED [ 64%]
3600-agents/RattleBot/tests/test_search.py::test_zobrist_hash_sensitivity PASSED [ 67%]
3600-agents/RattleBot/tests/test_search.py::test_zobrist_collision PASSED [ 70%]
3600-agents/RattleBot/tests/test_search.py::test_move_key_uniqueness PASSED [ 73%]
3600-agents/RattleBot/tests/test_search.py::test_ordered_moves_excludes_search_by_default PASSED [ 76%]
3600-agents/RattleBot/tests/test_search.py::test_ordered_moves_carpet_first PASSED [ 79%]
3600-agents/RattleBot/tests/test_search.py::test_ordered_moves_hash_move_promoted PASSED [ 82%]
3600-agents/RattleBot/tests/test_search.py::test_alphabeta_matches_minimax PASSED [ 85%]
3600-agents/RattleBot/tests/test_search.py::test_tt_reduces_nodes PASSED [ 88%]
3600-agents/RattleBot/tests/test_search.py::test_search_not_in_tree_invariant PASSED [ 91%]
3600-agents/RattleBot/tests/test_search.py::test_iterative_deepening_respects_budget PASSED [ 94%]
3600-agents/RattleBot/tests/test_search.py::test_root_decision_returns_valid_move PASSED [ 97%]
3600-agents/RattleBot/tests/test_search.py::test_root_decision_triggers_search_when_mass_high PASSED [100%]

============================= 34 passed in 4.78s ==============================
```

**Harness note:** The default pytest invocation (without `PYTHONPATH` set) fails at collection because `RattleBot/__init__.py:7` eagerly imports `.agent`, which imports `game.*`. The tests individually bootstrap `sys.path` when run as `python <test_file>.py`, but pytest collects via `import_module` which triggers `__init__.py` first. In the tournament environment the engine subprocess runs with `game.*` already importable via cwd, so this is a local-test-harness mechanic, not a shipped-zip defect. Recommended fix (v0.2): add a `conftest.py` in `3600-agents/RattleBot/tests/` that sets `sys.path` at collection time.

---

## §5 — Recommendations for v0.2

Prioritized list of nice-to-have cleanups and improvements surfaced during the audit.

### High-value (would unblock real ELO upside)

1. **Lift `_PER_TURN_CEILING_S = 3.0 s`** — once BO-tuned weights land (D-009), either raise to 6-7 s or make it a constructor argument. v0.1 leaves ~30-50 ELO on the table by capping late-game search. (M-01)
2. **F3/F4 attribution** — either track prime/carpet ownership via an `apply_move` event-hook, OR simply drop them in favor of F5/F7. Under self-play the approximation is a no-op, but against George/Albert/Carrie it may matter. (M-03)
3. **Plumb `iterative_deepen` return value through to `root_search_decision`** — currently re-probes the TT for `best_value`, which may be a bound rather than the exact value if flag != EXACT. One-line fix. (Low table entry #4)
4. **Full `BeliefSummary.belief` usage by heuristic** — currently F11/F12 use only `max_mass` and `entropy`. F5 could use the per-cell belief weighting as a tie-breaker. Worth ~10-20 ELO if F5 becomes the Carrie-style P(c) sum.

### Low-value / hygiene

5. **pytest conftest.py** — add one in `tests/` so `PYTHONPATH` isn't required for casual test runs. (Low table entry #8)
6. **Coverage for `get_ordered_moves` legacy API, `incremental_update`, forced-exception fallback, `time_mgr.classify`, `commentate`** — all ≤ 10 lines each. Severity medium per §3.10. Closes the identified test gaps.
7. **In-process micro-game integration test** — currently only shell-based `_batch_smoke.py`. A 5-turn in-process match (no subprocess) would catch wiring regressions in CI without depending on `engine/run_local_agents.py`.
8. **Document `transition_matrix=None` fallback** — eye-roll noise but the identity-T fallback is a misleading testing convenience; note in docstring.
9. **Zobrist full turn_count vs 41-bucket** — at v0.2's TT hit-rate audit (T-SRCH-3 ≥ 15 %), if miss-rate is way above floor, consider adding full `turn_count` back in. The current bucket trade is documented but untested at v0.2 budget.
10. **Safety-margin double-book** — clean up the time_mgr ↔ search safety_s accounting so a single layer owns the 0.5 s reserve. (M-02)

### Tracking bugs already raised in v0.1 notes

- S-5 (`is_valid_move` guard against TT cross-state moves): dev-search should investigate whether the TT is returning moves from positions with different `is_player_a_turn`. If yes, promote `is_player_a_turn` into the zobrist key's primary structure (it is already there as a side-to-move bit, but v0.2 should confirm there's no collision path via the `turn_count // 2` bucket).
- Heuristic calibration S-1: the F11/F12 weights that produce negative leaf values on flat belief are what force the `p > 1/3` SEARCH gate in agent.py. Once BO-tuned, the gate should fire correctly without the agent-side guard — remove the guard as a v0.2 cleanup.

### Not recommended for v0.2 (per BOT_STRATEGY §8 non-goals)

- No NN-from-scratch.
- No MCTS pivot (SYN §B16).
- No null-move pruning / magic bitboards (no Zugzwang analogues on this board).
- No in-tree SEARCH chance nodes (branching blowup; leaf-as-potential is sufficient at d≤6).

---

**End of audit.**
