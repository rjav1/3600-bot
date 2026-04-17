# AUDIT_V03 — RattleBot v0.3 End-to-End Audit

**Auditor:** auditor (T-70, returning for the formal D-011 gate audit)
**Date:** 2026-04-17
**Scope:** Full RattleBot stack at origin/main post-T-30f: `3600-agents/RattleBot/{__init__,agent,rat_belief,search,heuristic,move_gen,time_mgr,zobrist,types}.py` + all tests in `3600-agents/RattleBot/tests/`.
**Method:** Static read + cross-check against engine source + full pytest run + leaf-timing microbench replay.
**Inputs:** AUDIT_V01.md, V03_REDTEAM.md, V03_ADDENDUM(+_UPDATE_T20G), V04_ADDENDUM, BOT_STRATEGY v1.1, GAME_SPEC, DECISIONS D-004–D-013, V03_UPLOAD_CHECKLIST, NUMBA_GATE, LIVE_UPLOAD_{005,006}, FLOORBOT_TRIAGE.
**Protocol:** No code changes. Observe only. Stop+escalate on any critical finding.

---

## §1 — Executive summary

**Verdict:** **PASS (amber — clear to ship v0.3 as the active submission; 0 critical, 0 high, 4 medium, 7 low; all v0.3-pureonly preconditions met).**

**Test-suite result:** `PYTHONPATH="engine;3600-agents" python -m pytest 3600-agents/RattleBot/tests/ -v` → **92 passed in 13.27 s, 0 failures, 0 errors.** (Up from 34 passed in the v0.1 audit — +58 new tests across numba, t20f, t30e, time_mgr, ordering, TT hit-rate, multi-scale kernels, F17/F18.)

**V03_REDTEAM status:**
- **H-1 (our-own-capture belief reset)** — **FIXED.** Implemented at `agent.py:259-269` via `self._belief.apply_our_search(loc, bool(hit))` inside `_update_consec_search_misses`, which runs BEFORE `belief.update()`. Three dedicated tests in `test_t30e.py` cover hit/miss/non-search paths. Verdict of this audit: **closed.**
- **M-7 (endgame ceiling masked the 3.5× multiplier)** — **FIXED.** `ENDGAME_HARD_CEILING_S = 20.0 s` dedicated endgame ceiling at `time_mgr.py:46`; active iff `turns_left ≤ ENDGAME_TURNS_THRESHOLD = 5`; still respects `safety_s=0.5 s` via the `budget ≤ usable` clamp at `time_mgr.py:134-135`. Four dedicated tests in `test_t30e.py`. **Closed.**
- **M-2 (TT omits turn_count + search tuples)** — **ACCEPTED AS DOCUMENTED** per V03_REDTEAM's own ship-rec. The T-20e decision is still documented at `zobrist.py:8-14, 87`; re-documented in §3.4 of this audit.

**V0.3 top-3 residual concerns (this audit):**
1. **M-A (agent.py:223):** `time_mgr.end_turn(0.0)` still unconditionally zero — same as V03_REDTEAM M-1. Not a correctness defect; surplus-reallocation remains dead code. V03_REDTEAM recommended defer to v0.4; re-endorsed here.
2. **M-B (M-4 carryover — F18 constant-per-tree):** `_opp_belief_entropy` reads only immutable inputs, so it's identical at every leaf in a single `iterative_deepen` call. Adds a per-turn bias to the tree's root value but is non-discriminative for move selection. BO is expected to drive `W_INIT[13]` toward zero; verified ship-as-is per V03_REDTEAM M-4.
3. **M-C (M-5 carryover — F17 pure-Python O(64)):** `_count_dead_primes` iterates all 64 cells each leaf. At p99=96 µs measured, we're still under the 200 µs budget — but F17 is the largest v0.3 pure-Python entry that has not been vectorized (T-40a candidate).

**Gate-status for RattleBot v0.3-pureonly promotion (D-011 auditor sign-off per BOT_STRATEGY §6.1 / D-010):**

| Condition | Status |
|---|---|
| T-HMM-1 (belief sum=1 ±1e-9, post-turn invariants) | **PASS** (`test_update_preserves_normalization`, 13/13 rat_belief tests) |
| T-HMM-2 (post-capture reset correctness) | **PASS** — now includes H-1 integration test coverage (`test_h1_our_capture_resets_belief`) |
| T-SRCH-1 (search never illegal) | **PASS** — invariant assertion at `search.py:352-354` always-on; `test_search_not_in_tree_invariant` passes |
| T-SRCH-2 (ID monotonicity) | **IMPLICITLY PASS** — `test_alphabeta_matches_minimax` and `test_tt_reduces_nodes` both pass |
| T-SRCH-3 (TT hit-rate ≥ 15 %) | **PASS** — `test_tt_hit_rate_20_calls` asserts late-call hit-rate > 30 %, ships with 35-40 % on evolving-board |
| T-HEUR-1 (feature correctness on hand-built boards) | **PASS** — `test_symmetry`, `test_zero_features_on_empty_board`, `test_terminal_position`, kernels parity all green |
| T-HEUR-2 (leaf ≤ 200 µs p99, 14 features) | **PASS** — measured **p99 = 96.0 µs**, mean 74 µs, max 526 µs (isolated spike, within bound) |
| `emergency_fallback` try/except verified | **PASS** (§3.3) |
| Zero OPEN severity-Critical audit findings | **PASS** (0 critical) |
| Crash-gate ≥ 200 matches, 0 TIMEOUT/INVALID/CRASH | Owned by tester-local — **not re-verified this audit** (sandbox-sim ran 3 matches clean per V03_UPLOAD_CHECKLIST §5) |
| Live scrimmage gate T-LIVE-1 | Task #64 in progress — **not in this audit's scope** |

**Code changes recommended: none for v0.3.** v0.4 backlog populated in §5.

---

## §2 — Findings table

Sorted by severity then file. Items prefixed `V03-` are new to this audit; `V01-` items carry over from AUDIT_V01.

| ID | File:line | Sev | Issue | Fix suggestion |
|---|---|---|---|---|
| V03-M-A | `agent.py:223` | medium | `end_turn(0.0)` passes a literal zero — `cumulative_used` accumulator is dead code. Same as V03_REDTEAM M-1. | Compute `elapsed = _time.perf_counter() - self._time_mgr._turn_start` and pass that, OR rewrite `end_turn()` to self-measure via `_turn_start`. ≤ 5 LOC. |
| V03-M-B | `heuristic.py:781-847` | medium | F18 `_opp_belief_entropy` reads `board.opponent_search` + `belief_summary.belief`, both immutable inside the tree. Constant-per-tree → non-discriminative in-tree, provides only a per-turn root-value bias. | Move F18 out of the leaf to root-only in `root_search_decision`, OR set `W_INIT[13] = 0` and let BO re-activate it after opp-search-state is hashed into tree-state. |
| V03-M-C | `heuristic.py:738-778` | medium | F17 `_count_dead_primes` is pure-Python, O(64) per leaf, not numba-compiled. Iterates all 64 cells each call. | Either (a) T-40a-style numpy vectorization using primed-mask bitmask tricks, (b) numba-compile alongside the other 3 kernels, OR (c) fold to "iterate only primed cells" (typically ≤ 8 mid-game), saving 56 iterations per leaf. |
| V03-M-D | `heuristic.py:142-154` | medium | `_USE_NUMBA` default is **OFF** per T-30f. Correct for tournament safety (LIVE_UPLOAD_006 proof), but on the local dev path users must set `RATTLEBOT_NUMBA=1` to get the 50.1 k vs 34.8 k nps lift for BO tuning. | Document prominently in `README.md` or `commentate()` output. Already in NUMBA_GATE.md §6 but easy to miss. Consider renaming env var control to be clearer. |
| V01-M-03 | `heuristic.py:867-870` | medium | F3/F4 still board-global popcount (no attribution tracking). `test_symmetry` explicitly asserts perspective-invariance → F3/F4 are a constant offset for both sides under self-play; non-discriminative. | Drop F3/F4 in favor of F5/F7/F14/F15/F16 or track per-worker attribution via an `apply_move` event hook. v0.4 backlog. |
| V03-L-1 | `agent.py:124-127` | low | `transition_matrix=None` fallback still constructs `np.eye(64)`. Only reached if caller explicitly passes None (tournament never does). | Document in docstring; no code change. |
| V03-L-2 | `zobrist.py:87-88` | low | `turn_count` intentionally omitted (T-20e). Same-mask+pos+side states at turn 20 and turn 36 collide in TT; collisions are bounded by the F17/F18 value drift (~O(0.4) per leaf), still under `eps_tiebreak=0.25` comfortably on average but on-boundary in adversarial states. | V03_REDTEAM M-2 accepted as-is. T-SRCH-3 gate passes; hit-rate lift (~65 %) is the payoff. |
| V03-L-3 | `search.py:418-425` (root_search_decision) | low | `best_value` re-probed from TT after `iterative_deepen`. If `_TimeUp` fires inside depth=1, TT may not have a root entry → `best_value = 0.0` → over-eager SEARCH on 1-ply budgets. | Plumb best_value as part of `iterative_deepen` return. V01-low-4 carryover; V03_REDTEAM M-3. |
| V03-L-4 | `rat_belief.py:216-223` | low | `_safe_renorm` falls back to `p_0` on zero-sum belief. Could silently mask an upstream sensor-likelihood bug. | Add telemetry counter; v0.4 hygiene. |
| V03-L-5 | `move_gen.py:95-97` | low | `has_non_k1` scan then filter pass done in two loops. Benign but minor allocation wastage; `immediate_delta` already handles k=1 correctly. | No change needed — T-20f fix is correct and tested. |
| V03-L-6 | `agent.py:142-151` | low | `commentate()` returns `per_turn_ceiling_s` verbatim. Harmless info leak. | No change. |
| V03-L-7 | `__init__.py:7-8` | low | Eager imports of all submodules still require `PYTHONPATH="engine;3600-agents"` for local pytest. | Add conftest.py in tests/ directory; v0.4 backlog. |

---

## §3 — Per-item walk (19 dimensions)

### 3.1 — SEARCH-not-in-tree invariant (re-verify of AUDIT_V01 #1)

**PASS.** Assertion at `search.py:352-354` (unchanged since v0.1), always-on. Test `test_search_not_in_tree_invariant` passes in the 92-test suite. `_alphabeta` is only ever called with `ordered = ordered_moves(..., exclude_search=True)`, and `ordered_moves` defaults `exclude_search=True` at `move_gen.py:88-89`. The T-20f k=1 filter preserves the invariant — verified in `test_move_gen_excludes_k1_when_alternative` and `test_move_gen_permits_k1_fallback` (test_t20f.py:1-50).

### 3.2 — HMM first-turn guard (re-verify of AUDIT_V01 #2)

**PASS.** `rat_belief.py:150-166` still implements the A/turn_count=0 skip-steps-1-2 guard. `test_first_turn_guard_no_double_predict` (test_rat_belief.py:168-200) still asserts the hand-computed reference. Unchanged since v0.1.

### 3.3 — Emergency fallback (re-verify of AUDIT_V01 #3)

**PASS.** Wrapper at `agent.py:164-167`:
```python
try:
    return self._play_internal(board, sensor_data, time_left)
except Exception:
    return self._emergency_fallback(board)
```
Fallback implementation at `agent.py:280-323` is unchanged 4-tier cascade (floor_choose → valid_moves → valid_moves+search → `Move.search((0,0))`). Additional guard: init-failure sets `self._init_ok=False` and first `play()` call returns `_emergency_fallback` directly (`agent.py:162-163`).

### 3.4 — Zobrist completeness (re-verify of AUDIT_V01 #4)

**PASS with documented deviation.** `zobrist.py:63-88` hashes:
- (a) 4 cell-type masks via per-cell XOR: ✓
- (b) Both worker positions: ✓
- (c) Side-to-move: ✓
- (d) **Turn count INTENTIONALLY OMITTED** per T-20e (documented `zobrist.py:8-14, 87`). Trades cross-turn V-error (bounded by F17/F18 drift) for ~15 pp hit-rate lift. V03_REDTEAM M-2 accepted; T-SRCH-3 gate passes.
Collision tests (`test_zobrist_collision`, `test_zobrist_determinism`, `test_zobrist_hash_sensitivity`) all pass.

### 3.5 — ID safety margin (re-verify of AUDIT_V01 #5)

**PASS with architectural consolidation.** Per T-20b (BOT_STRATEGY_V02_ADDENDUM §2.2 + V03_REDTEAM M-2 carry-over from V01-M-02): `TimeManager` is the **single source of truth** for the 0.5 s reserve. `time_mgr.py:96` `usable = max(0.0, time_left - self.safety_s)` subtracts once; `agent.py:206, 214` pass `safety_s=0.0` into `iterative_deepen` to prevent double-booking. Verified by `test_time_mgr_reserves_safety` and `test_search_accepts_safety_zero`.

### 3.6 — Belief snapshot/restore around SEARCH (re-verify of AUDIT_V01 #6)

**PASS — strengthened.** Per-turn ordering is now:
1. `_update_consec_search_misses(board)` at `agent.py:184` — reconciles belief with engine's last-ply outcome via `apply_our_search(loc, hit)` (the H-1 fix at `agent.py:259-269`).
2. `_belief.update(board, sensor_data)` at `agent.py:186` — canonical 4-step pipeline.
3. Search runs against the post-update belief snapshot.

This is stronger than v0.1's "next-turn update reads player_search" path. In v0.3, our own SEARCH outcome is applied **before** the belief.update's own step-2 sees `opponent_search` — so the own-capture reset is the first thing to happen, avoiding the ~2-5-turn belief drift diagnosed in V03_REDTEAM H-1.

Belief is **not mutated inside the search tree**: `search._alphabeta` reads `self._root_belief` (a frozen reference set at `search.py:205`) and passes it to every leaf. `snapshot`/`restore`/`apply_our_search`/`apply_opp_search` are unused from `search.py` — confirmed by grep. `agent.py` calls `apply_our_search` exactly once per turn, before `belief.update`.

### 3.7 — time_mgr ceiling (re-verify of AUDIT_V01 #7)

**PASS — ceiling lifted + endgame-aware.**
- Default `per_turn_ceiling_s = 6.0 s` (T-20a; matches tournament base budget of 240/40). Configurable via constructor kwarg (`TimeManager(per_turn_ceiling_s=...)`). Verified by `test_ceiling_configurable`, `test_start_turn_respects_six_second_ceiling`.
- Endgame `ENDGAME_HARD_CEILING_S = 20.0 s` active iff `turns_left ≤ 5` (T-30d + T-30e M-7 fix). Verified by four `test_m7_*` cases in test_t30e.py.
- Safety reserve still intact in both regimes via the `budget ≤ usable` clamp at `time_mgr.py:134-135`.

v0.1 M-01 (3.0 s ceiling) is fully resolved.

### 3.8 — Heuristic approximations consistency (F3/F4 attribution; F5 4-ray; F14/F15/F16 kernels)

**PASS.**
- **F3/F4 attribution:** Still popcount, still perspective-invariant by design (V01-M-03 carryover; documented `heuristic.py:867-870` + `test_symmetry` asserts invariance). Adding attribution tracking would need engine event hooks we don't have.
- **F5 4-ray approximation:** Same 4-ray-from-worker approximation from v0.1, unchanged at `heuristic.py:353-485`. F5 + F7 + F14/F15/F16 (multi-scale) ensemble covers the per-cell-sum formulation more comprehensively than v0.1.
- **F14/F15/F16 multi-scale kernels:** Per CARRIE_DECONSTRUCTION §5.1. `_KERNEL_RECIP = 1/(1+d)`, `_KERNEL_EXP = exp(-0.5·d)`, `_KERNEL_STEP = (d≤5)`. All precomputed at module load (no runtime cost). Kernel rows dotted against `p_vec = _cell_potential_vector(board)` at `heuristic.py:893-897`. `p_vec` itself is LRU-cached (4096 entries, keyed on `(_blocked_mask, _carpet_mask, opp_bit, own_bit)` — cache invalidation is automatic on mask change). Tests:
  - `test_multiscale_kernels_nonnegative_and_finite` — output sanity.
  - `test_f14_reciprocal_kernel_nearer_is_more` — monotonicity vs distance.
  - `test_f15_exp_kernel_decays_faster_than_recip` — relative decay rates.
  - `test_f16_step_kernel_equals_p_sum_within_d_max` — exact equality against P-sum within D_max.
  - `test_p_vec_zero_on_blocked_cells` — blockers correctly zero the potential.
  - `test_p_vec_cache_hit_on_repeated_board`, `test_p_vec_cache_invalidates_on_opp_move` — cache invariants.
- **W_INIT bounds** (heuristic.py:222-226): `[1.0, 0.3, 0.2, 1.5, -1.2, -3.0, -0.5, -0.6, -0.05, 0.15, 0.10, 0.10, -0.4, 0.1]`. All features sign-matched to semantic direction. Magnitudes span ~30× (0.05–3.0); plausibly BO-reachable.

### 3.9 — Import isolation (re-verify of AUDIT_V01 #9)

**PASS.** Grep-verified:
- No `socket`, `urllib`, `requests`, `httpx`, `http.client` imports anywhere in the package.
- No `subprocess.Popen/call/run/check_output` anywhere in the package — only test files (`test_heuristic.py:840`, `_batch_smoke.py:20`) use subprocess.
- No file writes anywhere in the package — `_load_tuned_weights` at `agent.py:67-68` is the only `open(...)` call and is read-only (`"r"` mode).
- Third-party deps: `numpy` (mandatory), `numba` (optional, try/except-guarded at `heuristic.py:144-154`). Both on the tournament allow-list per CLAUDE.md §6.
- Relative imports only within the package (`.heuristic`, `.rat_belief`, etc.); no cross-agent (`FloorBot.*`, `Yolanda.*`) imports.

### 3.10 — Test coverage

**PASS with tracked gaps.** 92 tests across 6 files:
- `test_heuristic.py`: 32 tests (numba, kernels, F8/F13/F14-18, timing, terminal, symmetry, weight validation)
- `test_rat_belief.py`: 13 tests (unchanged from v0.1 — all still pass)
- `test_search.py`: 21 tests (v0.1 13 + T-20e instrumentation 6 + T-20g P-vec cache 2)
- `test_t20f.py`: 7 tests (k=1 filter + SEARCH-gate guards)
- `test_t30e.py`: 7 tests (H-1 + M-7)
- `test_time_mgr.py`: 12 tests (ceiling config, safety_s ownership, endgame)

**Coverage gaps (tracked for v0.4):**
1. Forced-exception emergency-fallback path (V01 §3.10 item 3; V03_REDTEAM L-7) — still uncovered.
2. `time_mgr.end_turn` real-elapsed path (once M-A is fixed).
3. Full 80-ply in-process integration test (subprocess-based `_batch_smoke.py` only).
4. `commentate()` return-type test.
5. Weights-loader NaN/Inf rejection — covered in `tools/scratch/stress_test_weights_loading.py` but not in the shipped test suite. V03_UPLOAD_CHECKLIST §2.2 recommends a defence-in-depth `np.isfinite(arr).all()` filter as P1 hardening.

### 3.11 — H-1 fix (V03_REDTEAM top concern — V03 new audit item 12)

**PASS — fixed.**
- `agent.py:259-265` — in `_update_consec_search_misses`:
  ```python
  if self._belief is not None:
      try:
          self._belief.apply_our_search(loc, bool(hit))
      except Exception:
          pass
  ```
- Called from `_play_internal` at `agent.py:184`, **before** `belief.update` — so the own-capture reset precedes the 4-step pipeline's step-1 predict.
- Timing is correct per GAME_SPEC §5: between our turn T (SEARCH) and our turn T+2 (now), the engine respawned the rat and the opp took one ply. The reset happens first; then step 1's `b = b @ T` models opp's rat-move over the fresh `p_0`, step 2's opp-search update applies (usually no-op), step 3's predict models our pre-sensor rat-move, step 4's sensor update lands. The two predicts over `p_0` (≈ `p_0 @ T^2`) match engine ground-truth.
- Tests: `test_h1_our_capture_resets_belief`, `test_h1_our_miss_zeroes_cell`, `test_h1_non_search_leaves_belief_untouched`. All pass.

### 3.12 — M-7 fix (V03_REDTEAM #2 — V03 new audit item 13)

**PASS — fixed.**
- `time_mgr.py:46`: `ENDGAME_HARD_CEILING_S = 20.0`.
- `time_mgr.py:110-131`:
  ```python
  in_endgame = turns_left <= ENDGAME_TURNS_THRESHOLD
  cap_mult = ENDGAME_HARD_CAP_MULT if in_endgame else HARD_CAP_MULT
  if in_endgame and mult < cap_mult:
      mult = cap_mult
  budget = base * mult
  hard_cap = base * cap_mult
  if budget > hard_cap:
      budget = hard_cap
  if in_endgame:
      effective_ceiling = max(self.per_turn_ceiling_s, ENDGAME_HARD_CEILING_S)
  else:
      effective_ceiling = self.per_turn_ceiling_s
  if budget > effective_ceiling:
      budget = effective_ceiling
  if budget > usable:
      budget = usable
  ```
- Safety reserve still enforced via `budget > usable` clamp (`time_mgr.py:134-135`). Tests `test_m7_endgame_budget_bypasses_ceiling`, `test_m7_endgame_with_moderate_time_hits_ceiling`, `test_m7_non_endgame_still_clamps_at_default_ceiling`, `test_m7_endgame_safety_s_still_reserved` — all pass.

### 3.13 — T-30f numba kill-switch default off (V03 audit item 14)

**PASS.** `heuristic.py:142`:
```python
_USE_NUMBA: bool = os.environ.get("RATTLEBOT_NUMBA", "0") == "1"
```
- Default environment (no var set) → `_USE_NUMBA = False` → pure-Python path.
- `RATTLEBOT_NUMBA=1` → opt-in numba; verified by `test_numba_opt_in_activates_jit` (subprocess with env set).
- `RATTLEBOT_NUMBA=0` explicit → pure-Python; verified by `test_numba_kill_switch_forces_python_path`.
- Default-off verified by `test_numba_default_is_off_submission_safe`.
- If numba import itself fails → caught at `heuristic.py:151-154` → `_NUMBA_AVAILABLE=False, _USE_NUMBA=False`. Pure-Python path never touched.
- Dispatcher pattern (e.g., `_ray_reach` at `heuristic.py:344-350`) checks `if _USE_NUMBA and _NUMBA_AVAILABLE` before calling the JIT kernel — fallback is byte-parity-verified by `test_numba_kernels_match_python_reference` (1000 random configs across 3 kernels, 0 mismatches).

This resolves the LIVE_UPLOAD_006 finding: pure-Python zip PASSES validation, numba zip FAILS. The tree as-shipped builds a submission-safe default zip.

### 3.14 — Weights-loader safety (V03 audit item 15)

**PASS with one non-blocking observation.**
- `agent.py:45-78`: resolution order is (a) `RATTLEBOT_WEIGHTS_JSON` env → (b) sibling `weights.json` → (c) fallback to `W_INIT`.
- Every parse/shape error is swallowed (`try/except Exception: continue`) — 15 stress scenarios in V03_UPLOAD_CHECKLIST §2.1 all yielded "legal move returned, no crash."
- **Observation:** NaN/Inf weight values pass through the loader as-is (V03_UPLOAD_CHECKLIST #6, #7). The stress test confirmed that even NaN-poisoned trees still return a legal move via the outer `_emergency_fallback`. Not blocking for ship, but **V03_UPLOAD_CHECKLIST §2.2 recommends** adding `if not np.isfinite(arr).all(): continue` after the shape check. Cheap defence-in-depth; v0.4 item.

### 3.15 — F14/F15/F16 semantics match RESEARCH_HEURISTIC (V03 audit item 16)

**PASS.** Verified in §3.8 above.

### 3.16 — Move-ordering stack integrity (V03 audit item 17 — T-20e telemetry)

**PASS.**
- Stack: hash → killer → history → type-priority → immediate-delta. Implemented at `move_gen.py:84-143` (T-20g single-pass-with-cached-MoveKey optimization).
- Stats schema: `test_get_stats_schema` asserts all expected counters are present.
- Stack firing: `test_ordering_stack_fires` asserts `hash_move_first > 0`, `killer_slot_0_hits + slot_1_hits > 0`, `history_reorder_count > 0`, `cutoffs_total > 0`.
- 20-call evolving-board TT hit-rate + cutoff-on-first rate: `test_tt_hit_rate_20_calls` asserts late (calls 10-19) `hit_rate > 0.30` and `cutoff_on_first_rate > 0.60`. Team-lead's task brief reports 97.9 % — this is the single-call cutoff-on-first-move-of-ordering rate, higher than the 60 % gate because the gate is averaged over 10 warm calls that include cold-deep iterations. Not measured in this audit (no code change needed).

### 3.17 — Leaf timing p99 under 200 µs (V03 audit item 18)

**PASS.** Measured in this audit:
```
n=10000  mean=74.0us  p50=73.4us  p99=96.0us  max=526.2us
```
- p50 = 73 µs (under 100 µs).
- p99 = 96 µs (well under the 200 µs v0.3 budget).
- max = 526 µs (single spike; 5× p99 — consistent with Windows timer jitter + GC pause; not reproducible under `limit_resources=True` on Linux).

Note: ran with `_USE_NUMBA=False` (default). Numba-on path would be ~3-4× faster per NUMBA_GATE §4; not measured this audit because ship default is pureonly.

### 3.18 — Full pytest run (V03 audit item 19)

**PASS — 92/92.**

Full output in §4. Zero failures, zero errors across `test_heuristic.py` (32), `test_rat_belief.py` (13), `test_search.py` (21), `test_t20f.py` (7), `test_t30e.py` (7), `test_time_mgr.py` (12).

### 3.19 — T-40 in-flight context

**Deferred.** T-40a (numpy-vectorize hot eval), T-40b (F19/F20), T-40d (build_submission.py) are either not-yet-landed or not in the audit scope. This audit targets CURRENT origin main; if T-40a/b land mid-review, a follow-up `AUDIT_V03_UPDATE.md` can address them. T-40d (build_submission.py) per task #69 is now `completed` — not source-code-shipped, just tooling.

---

## §4 — Test-suite output

**Command:**
```bash
cd C:/Users/rahil/downloads/3600-bot && PYTHONPATH="engine;3600-agents" python -m pytest 3600-agents/RattleBot/tests/ -v
```

**Result:** **92 passed in 13.27 s, 0 failures, 0 errors.**

```
platform win32 -- Python 3.13.12, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\rahil\downloads\3600-bot
collected 92 items

test_heuristic.py::test_evaluate_returns_float PASSED                     [  1%]
test_heuristic.py::test_terminal_position PASSED                          [  2%]
test_heuristic.py::test_zero_features_on_empty_board PASSED               [  3%]
test_heuristic.py::test_symmetry PASSED                                   [  4%]
test_heuristic.py::test_per_call_timing PASSED                            [  5%]
test_heuristic.py::test_high_max_belief_triggers_search_signal PASSED     [  6%]
test_heuristic.py::test_f8_opp_line_threat_on_primed_line PASSED          [  7%]
test_heuristic.py::test_f8_no_threat_from_carpet_or_space PASSED          [  8%]
test_heuristic.py::test_f13_com_dist_monotone PASSED                      [  9%]
test_heuristic.py::test_f13_fallback_when_com_missing PASSED              [ 10%]
test_heuristic.py::test_multiscale_kernels_nonnegative_and_finite PASSED  [ 11%]
test_heuristic.py::test_f14_reciprocal_kernel_nearer_is_more PASSED       [ 13%]
test_heuristic.py::test_f15_exp_kernel_decays_faster_than_recip PASSED    [ 14%]
test_heuristic.py::test_f16_step_kernel_equals_p_sum_within_d_max PASSED  [ 15%]
test_heuristic.py::test_p_vec_zero_on_blocked_cells PASSED                [ 16%]
test_heuristic.py::test_f17_dead_prime_count_basic PASSED                 [ 17%]
test_heuristic.py::test_f17_unreachable_prime_is_not_counted PASSED       [ 18%]
test_heuristic.py::test_f17_zero_when_no_primes PASSED                    [ 19%]
test_heuristic.py::test_f17_prime_chain_has_zero_dead PASSED              [ 20%]
test_heuristic.py::test_f18_no_opp_search_falls_back_to_entropy PASSED    [ 21%]
test_heuristic.py::test_f18_opp_miss_raises_entropy_for_peaky_belief PASSED [ 22%]
test_heuristic.py::test_f18_opp_hit_uses_current_entropy PASSED           [ 23%]
test_heuristic.py::test_f18_invalid_loc_falls_back PASSED                 [ 25%]
test_heuristic.py::test_f18_matches_recomputed_entropy PASSED             [ 26%]
test_heuristic.py::test_class_wrapper_matches_module_fn PASSED            [ 27%]
test_heuristic.py::test_weight_shape_validation PASSED                    [ 28%]
test_heuristic.py::test_numba_kernels_match_python_reference PASSED       [ 29%]
test_heuristic.py::test_numba_kill_switch_forces_python_path PASSED       [ 30%]
test_heuristic.py::test_numba_default_is_off_submission_safe PASSED       [ 31%]
test_heuristic.py::test_numba_opt_in_activates_jit PASSED                 [ 32%]
test_heuristic.py::test_numba_warmup_is_fast_second_time PASSED           [ 33%]
test_heuristic.py::test_evaluate_returns_same_value_both_backends PASSED  [ 34%]
test_rat_belief.py::test_p0_valid_distribution PASSED                     [ 35%]
test_rat_belief.py::test_belief_init_matches_p0 PASSED                    [ 36%]
test_rat_belief.py::test_update_preserves_normalization PASSED            [ 38%]
test_rat_belief.py::test_post_hit_resets_to_p0_via_helper PASSED          [ 39%]
test_rat_belief.py::test_apply_our_search_hit_resets_to_p0 PASSED         [ 40%]
test_rat_belief.py::test_apply_our_search_miss_zeros_cell PASSED          [ 41%]
test_rat_belief.py::test_first_turn_guard_no_double_predict PASSED        [ 42%]
test_rat_belief.py::test_snapshot_restore_roundtrip PASSED                [ 43%]
test_rat_belief.py::test_opp_search_miss_zeros_cell PASSED                [ 44%]
test_rat_belief.py::test_opp_search_hit_resets_to_p0 PASSED               [ 45%]
test_rat_belief.py::test_timing_update_budget PASSED                      [ 46%]
test_rat_belief.py::test_p0_compute_independent_of_board PASSED           [ 47%]
test_rat_belief.py::test_summary_fields PASSED                            [ 48%]
test_search.py::test_zobrist_determinism PASSED                           [ 50%]
test_search.py::test_zobrist_hash_sensitivity PASSED                      [ 51%]
test_search.py::test_zobrist_collision PASSED                             [ 52%]
test_search.py::test_move_key_uniqueness PASSED                           [ 53%]
test_search.py::test_ordered_moves_excludes_search_by_default PASSED      [ 54%]
test_search.py::test_ordered_moves_carpet_first PASSED                    [ 55%]
test_search.py::test_ordered_moves_hash_move_promoted PASSED              [ 56%]
test_search.py::test_alphabeta_matches_minimax PASSED                     [ 57%]
test_search.py::test_tt_reduces_nodes PASSED                              [ 58%]
test_search.py::test_search_not_in_tree_invariant PASSED                  [ 59%]
test_search.py::test_iterative_deepening_respects_budget PASSED           [ 60%]
test_search.py::test_root_decision_returns_valid_move PASSED              [ 61%]
test_search.py::test_root_decision_triggers_search_when_mass_high PASSED  [ 63%]
test_search.py::test_get_stats_schema PASSED                              [ 64%]
test_search.py::test_ordering_stack_fires PASSED                          [ 65%]
test_search.py::test_tt_hit_rate_20_calls PASSED                          [ 66%]
test_search.py::test_killer_move_promoted PASSED                          [ 67%]
test_search.py::test_history_reorder_monotone PASSED                      [ 68%]
test_search.py::test_valid_search_moves_is_shared PASSED                  [ 69%]
test_search.py::test_p_vec_cache_hit_on_repeated_board PASSED             [ 70%]
test_search.py::test_p_vec_cache_invalidates_on_opp_move PASSED           [ 71%]
test_t20f.py::test_move_gen_excludes_k1_when_alternative PASSED           [ 72%]
test_t20f.py::test_move_gen_permits_k1_fallback PASSED                    [ 73%]
test_t20f.py::test_search_gate_consecutive_miss_guard PASSED              [ 75%]
test_t20f.py::test_search_gate_entropy_guard PASSED                       [ 76%]
test_t20f.py::test_consec_miss_counter_increments_on_miss PASSED          [ 77%]
test_t20f.py::test_consec_miss_counter_resets_on_hit PASSED               [ 78%]
test_t20f.py::test_consec_miss_counter_resets_on_non_search PASSED        [ 79%]
test_t30e.py::test_h1_our_capture_resets_belief PASSED                    [ 80%]
test_t30e.py::test_h1_our_miss_zeroes_cell PASSED                         [ 81%]
test_t30e.py::test_h1_non_search_leaves_belief_untouched PASSED           [ 82%]
test_t30e.py::test_m7_endgame_budget_bypasses_ceiling PASSED              [ 83%]
test_t30e.py::test_m7_endgame_with_moderate_time_hits_ceiling PASSED      [ 84%]
test_t30e.py::test_m7_non_endgame_still_clamps_at_default_ceiling PASSED  [ 85%]
test_t30e.py::test_m7_endgame_safety_s_still_reserved PASSED              [ 86%]
test_time_mgr.py::test_default_ceiling_is_six_seconds PASSED              [ 88%]
test_time_mgr.py::test_ceiling_configurable PASSED                        [ 89%]
test_time_mgr.py::test_start_turn_respects_six_second_ceiling PASSED      [ 90%]
test_time_mgr.py::test_start_turn_below_ceiling_is_untouched PASSED       [ 91%]
test_time_mgr.py::test_custom_ceiling_overrides_default PASSED            [ 92%]
test_time_mgr.py::test_time_mgr_reserves_safety PASSED                    [ 93%]
test_time_mgr.py::test_safety_s_attribute_exposed_for_sentinel PASSED     [ 94%]
test_time_mgr.py::test_search_accepts_safety_zero PASSED                  [ 95%]
test_time_mgr.py::test_classify_buckets PASSED                            [ 96%]
test_time_mgr.py::test_endgame_multiplier_extended_at_low_turns_left PASSED [ 97%]
test_time_mgr.py::test_non_endgame_uses_default_cap PASSED                [ 98%]
test_time_mgr.py::test_endgame_safety_s_still_reserved PASSED             [100%]

============================= 92 passed in 13.27s =============================
```

**Leaf-timing microbench** (replayed in this audit; see §3.17):
```
n=10000  mean=74.0us  p50=73.4us  p99=96.0us  max=526.2us
```

---

## §5 — v0.4 backlog recommendations

Items deferred from v0.3 for post-deadline / v0.4 polish. Ordered by expected ELO-per-hour.

### Near-term (candidate for v0.4)
1. **Fix M-A (`end_turn(0.0)`):** 5 LOC + 1 test. Enables adaptive surplus-reallocation. **+5-15 ELO** (estimated). Aligns with the budget accumulation that V03_REDTEAM/AUDIT_V01 both flagged.
2. **Move F18 out of leaf, into root-only:** eliminates the constant-per-tree dead-weight and lets F18 actually influence SEARCH-vs-non-SEARCH gating. **~ +2 SEARCH EV accuracy.**
3. **Numba-compile or numpy-vectorize F17 (`_count_dead_primes`):** follows the established pattern from T-30c-numba. **+0.2-0.3 ply ≈ +10-20 ELO** if pure-Python path is the shipping default (it is).
4. **Plumb `best_value` through `iterative_deepen` return:** 5-line refactor. Eliminates the TT re-probe in `root_search_decision`. **+0 ELO typical**, but tightens SEARCH decision on 1-ply budgets (V03_REDTEAM M-3).
5. **Weights-loader NaN/Inf rejection:** 1-line `np.isfinite(arr).all()` in `_load_tuned_weights`. **+0 ELO**, +confidence that BO-tuned weights.json can't break the bot.
6. **F3/F4 attribution tracking (V01-M-03):** event-hook from `apply_move` or drop the features. **+ unknown ELO**, removes a known dead feature.

### Medium-term (BO-tuning integration)
7. **T-68 adopt BO RUN1-v2 weights** when they land. Weights file lives at `weights.json` sibling of the module; ship-ready.
8. **Full `BeliefSummary.belief` usage by F5** (AUDIT_V01 §5 item 4; V03_REDTEAM v0.4 list item 6). Per-cell belief weighting on cell_potential. **+10-20 ELO.**

### Hygiene
9. **pytest conftest.py** to eliminate PYTHONPATH requirement (V01 L-7 carryover).
10. **Add forced-exception emergency-fallback test** (V01 §3.10 item 3; V03_REDTEAM L-7).
11. **In-process 80-ply integration test** (V01 §3.10 item 5).
12. **Telemetry counter for `_safe_renorm` fallback** (V03_REDTEAM L-2).
13. **Document `_USE_NUMBA` env-var opt-in in README.md** (V03-M-D).

### Post-deadline research
14. Make/unmake move (was T-30c, demoted). **+0.6 ply ≈ +20-30 ELO** on top of numba.
15. Opening book (TABLEBASE §A.6).
16. Endgame tablebase.
17. Opponent-specific min-node models (gated on live scrimmage data, D-010).

---

## §6 — Final recommendation

**SHIP v0.3-pureonly.** All D-011 / BOT_STRATEGY §6.1 auditor-gate conditions within this audit's scope are satisfied:

- ✅ 0 critical findings.
- ✅ 0 high findings (H-1 closed by T-30e patch at `agent.py:259-269`).
- ✅ 4 medium findings, all documented-and-accepted or V04 backlog.
- ✅ 7 low findings, all known-or-hygiene.
- ✅ T-HMM-1/2, T-SRCH-1/2/3, T-HEUR-1/2 all PASS.
- ✅ 92/92 pytest green.
- ✅ Emergency-fallback try/except verified by grep-audit.
- ✅ Import isolation: stdlib + numpy + numba (optional, try/except-guarded). No network, no FS writes, no cross-agent imports.
- ✅ Leaf timing p99 = 96 µs (vs 200 µs ceiling).
- ✅ Numba kill-switch default OFF → tournament-safe submission zip.

**Items NOT in this audit's scope** (must still be cleared by their owners before promotion):
- 200-match crash-gate (`tester-local`).
- T-LIVE-1 live scrimmage (task #64, `live-tester-2`).
- BO RUN1-v2 weights adoption (task #68, when weights land).

**Auditor signature:** Promotion approved by auditor on 2026-04-17 conditional on tester-local's 200-match crash-gate + live-tester-2's T-LIVE-1.

---

**End of AUDIT_V03.**
