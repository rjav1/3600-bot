# AUDIT_V04_CHECKLIST — Pre-audit worksheet for RattleBot v0.4

**Author:** auditor (T-71 prep for T-30g auditor gate)
**Date:** 2026-04-17 (~T−30h)
**Status:** DRAFT — pre-execution checklist. AUDIT_V04.md will be produced by executing every check below against origin/main once all v0.4 code has landed.
**Upstream plan:** `docs/plan/BOT_STRATEGY_V04_ADDENDUM.md`.
**Prior audits:** `docs/audit/AUDIT_V01.md`, `docs/audit/AUDIT_V03.md`, `docs/audit/V03_REDTEAM.md`.

**Purpose of this doc:** enumerate every check AUDIT_V04 must perform, with the file:line anchor points already located where possible. When the v0.4 code freeze fires, this checklist becomes the literal AUDIT_V04.md body (checks re-executed; PASS/FAIL verdicts filled in).

---

## §0 — What's landed vs pending (as of draft time)

**Landed on origin/main (verified by grep):**
- T-30e (H-1 + M-7) — CLOSED by AUDIT_V03.
- T-30f (numba default OFF) — CLOSED by AUDIT_V03.
- T-40b (F19 `rat_catch_threat_radius`, F20 `opp_roll_imminence`) — `N_FEATURES=16`, `heuristic.py:1, 179, 239-253`. Team-lead noted ships at 883dadc with 84/84 passing.
- T-40c (context-adaptive time budget) — `time_mgr.py:62-84, 109-157, 159-` (`adjust_for_context`, `prev_eval_variance` kwarg on `start_turn`). Tests are the next gate.
- T-40d (`build_submission.py`) — tooling only, not a correctness surface.

**Pending/in-flight (AUDIT_V04 must verify once landed):**
- T-40a (numpy-vectorize `_cell_potential_vector`) — not yet in `heuristic.py`.
- T-40-BO-ADOPT (adopt BO RUN1-v4 `weights_v03.json`) — task #68 pending.
- T-40-EXPLOIT-1 / F22 prime-steal bonus — task #71 pending.
- T-40-EXPLOIT-2 / F10-ext adjacent-to-primed-endpoint — task #72 pending.
- T-40-EXPLOIT-3 / F24 opp-wasted-primes — task #73 pending.
- T-40-INFRA (engine jax-drop) — task #74 in flight.
- T-40-MCTS hybrid — conditional on MCTS N=20 gate.

**Plan:** This checklist covers every landed + every planned item. When AUDIT_V04 executes, each pending item will be either verified (if landed) or explicitly marked **N/A — not shipped in v0.4 scope** with owner-confirmation.

---

## §1 — Carry-forward checks (all 11 from T-18 + all 8 new from T-70)

Every AUDIT_V03 dimension must still hold on v0.4 code. Re-run at execution time.

### 1.1 — SEARCH-not-in-tree invariant (AUDIT_V01 #1 / T-70 #1)
- **Anchor:** `search.py:352-354` assertion + `test_search_not_in_tree_invariant`.
- **Check:** assertion still always-on; test still passes. Verify no new call-site to `ordered_moves` passes `exclude_search=False` inside `_alphabeta`.
- **Pass criteria:** test green + grep confirms `ordered_moves(..., exclude_search=True)` at every `_alphabeta` call.

### 1.2 — HMM first-turn guard (AUDIT_V01 #2 / T-70 #2)
- **Anchor:** `rat_belief.py:150-166` + `test_first_turn_guard_no_double_predict`.
- **Check:** guard unchanged; F19's `_NEAR2_MASK` reachability does not affect the turn-0 belief computation.
- **Pass criteria:** test green; `ref = p_0 @ T` equivalence for player-A turn-0.

### 1.3 — Emergency fallback (AUDIT_V01 #3 / T-70 #3)
- **Anchor:** `agent.py:164-167` (wrapper) + `agent.py:280-323` (fallback cascade).
- **Check:** wrapper still catches bare `Exception`; cascade still 4-tier ending at `Move.search((0,0))`.
- **Pass criteria:** grep + visual read; no new uncaught raise in `_play_internal`.

### 1.4 — Zobrist completeness (AUDIT_V01 #4 / T-70 #4)
- **Anchor:** `zobrist.py:63-88`.
- **Check:** 4 cell-type masks + 2 worker positions + side-to-move present; turn_count deliberately omitted per T-20e (documented).
- **Pass criteria:** `test_zobrist_determinism`, `test_zobrist_hash_sensitivity`, `test_zobrist_collision` all pass.

### 1.5 — ID safety margin (AUDIT_V01 #5 / T-70 #5)
- **Anchor:** `time_mgr.py:127` `usable = max(0.0, time_left - self.safety_s)`; `agent.py` passes `safety_s=0.0` into `iterative_deepen`.
- **Check:** 0.5 s reserve subtracted exactly once. T-40c's context multiplier still respects the `budget ≤ usable` clamp at `time_mgr.py:165-166`.
- **Pass criteria:** `test_time_mgr_reserves_safety` + `test_search_accepts_safety_zero` + `test_m7_endgame_safety_s_still_reserved` all pass.

### 1.6 — Belief snapshot/restore around SEARCH (AUDIT_V01 #6 / T-70 #6)
- **Anchor:** `agent.py:184` (`_update_consec_search_misses` → `apply_our_search` before `belief.update`); `search._alphabeta` never mutates `self._root_belief`.
- **Check:** no new in-tree belief mutation. F19 reads from `BeliefSummary.belief` only (immutable at leaf).
- **Pass criteria:** grep `snapshot|restore|apply_our_search|apply_opp_search` shows only the 1 call in `_update_consec_search_misses` (+ test files).

### 1.7 — time_mgr ceiling (AUDIT_V01 #7 / T-70 #7)
- **Anchor:** `time_mgr.py:60` (`DEFAULT_PER_TURN_CEILING_S = 6.0`), `time_mgr.py:46` (`ENDGAME_HARD_CEILING_S = 20.0`).
- **Check:** T-40c multiplier must compose correctly with the ceiling AND endgame branch (see §4.2 below).

### 1.8 — Heuristic approximations (AUDIT_V01 #8 / T-70 #8)
- **Anchor:** F3/F4 popcount `heuristic.py:867-870`, F5 4-ray in `_cell_potential_for_worker`.
- **Check:** approximations still documented; new features F19/F20 don't depend on these.

### 1.9 — Import isolation (AUDIT_V01 #9 / T-70 #9)
- **Anchor:** grep of `socket|urllib|requests|http|subprocess|os\.(system|spawn|exec)|\.write\(|open\([^)]*[\"']w`.
- **Check:** (a) no new third-party imports beyond numpy + optional numba; (b) no file writes; (c) no network; (d) no subprocess in the agent package (tests only).
- **Pass criteria:** grep clean OR all hits are in tests/ directory.

### 1.10 — Test coverage (AUDIT_V01 #10 / T-70 #10)
- **Check:** every new feature / module must have a test. Specific v0.4 additions tracked in §3-§5 below.
- **Gaps tracked for v0.5+:** forced-exception emergency-fallback path; in-process 80-ply game; `time_mgr.end_turn` real-elapsed path (linked to M-A fix below).

### 1.11 — Full pytest run (AUDIT_V01 #11 / T-70 #11)
- **Command:** `PYTHONPATH="engine;3600-agents" python -m pytest 3600-agents/RattleBot/tests/ -v`.
- **Pass criteria:** 0 failures, 0 errors. All green. Baseline is 92/92 (AUDIT_V03); T-40b should bring it to 84+ per team-lead; full v0.4 target to be confirmed at execution time.

### 1.12 — H-1 own-capture belief reset (T-70 #12)
- **Anchor:** `agent.py:259-269` (`apply_our_search(loc, bool(hit))` in `_update_consec_search_misses`, run BEFORE `belief.update`).
- **Pass criteria:** `test_h1_our_capture_resets_belief`, `test_h1_our_miss_zeroes_cell`, `test_h1_non_search_leaves_belief_untouched` all pass.

### 1.13 — M-7 endgame ceiling bypass (T-70 #13)
- **Anchor:** `time_mgr.py:46` (`ENDGAME_HARD_CEILING_S=20.0`); `time_mgr.py:149-162` endgame branch.
- **Pass criteria:** `test_m7_*` (4 tests) all pass. Verify T-40c multiplier does not re-introduce the bypass-ceiling clash.

### 1.14 — _USE_NUMBA default OFF (T-70 #14)
- **Anchor:** `heuristic.py:142` `_USE_NUMBA: bool = os.environ.get("RATTLEBOT_NUMBA", "0") == "1"`.
- **Check:** default `False` unless env opts in. `test_numba_default_is_off_submission_safe` passes.

### 1.15 — Weights-loader safety (T-70 #15)
- **Anchor:** `agent.py:45-78` `_load_tuned_weights`.
- **Check:** filename handled correctly. **v0.4 filename change: task #68 says `weights_v03.json` is BO output but loader reads `weights.json`** — see §6 below.
- **Pass criteria:** all 15 V03_UPLOAD_CHECKLIST stress scenarios still safe; NEW check for `weights_v03.json` rename.

### 1.16 — F14/F15/F16 kernel semantics (T-70 #16)
- **Anchor:** `heuristic.py:263-272` kernel statics; `heuristic.py:893-897` per-leaf dot products.
- **Check:** kernels still match CARRIE_DECONSTRUCTION §5. F19/F20 don't perturb them.

### 1.17 — Move-ordering stack integrity (T-70 #17)
- **Anchor:** `move_gen.py:84-143`, `search.py:278-311` (`_record_ordering_stats`).
- **Pass criteria:** `test_ordering_stack_fires`, `test_tt_hit_rate_20_calls` all pass; late cutoff-on-first rate > 60 %.

### 1.18 — Leaf timing p99 (T-70 #18)
- **Baseline:** AUDIT_V03 measured p99 = 96 µs at 14 features pure-Python. v0.4 adds F19/F20 (→ 16) + possibly F22/F10-ext/F24 (→ 18–19).
- **Budget:** 200 µs p99 at 14 features per `evaluate` docstring (`heuristic.py:932`). At 18+ features the budget SHOULD be revised to 250 µs or so — **check with dev-heuristic** on whether the docstring bound was updated.
- **Pass criteria at execution time:** measure leaf p99 with `test_per_call_timing`; hard-fail if p99 > 250 µs post-v0.4-features; soft-warn at 150 µs.

### 1.19 — Full pytest v0.4 (T-70 #19 equivalent)
- **Baseline: 92/92 (AUDIT_V03).**
- **Expected v0.4 additions:**
  - T-40a tests: `test_heuristic_vectorize.py` (parity test, 10 000 random boards). Required once T-40a lands.
  - T-40b tests: F19 + F20 semantic tests (landed at 883dadc per team-lead).
  - T-40c tests: entropy-high / entropy-low / variance-high / variance-low / composition-with-endgame tests.
  - F22/F10-ext/F24 tests: each feature must have at least a symmetry + hand-built semantic test.
- **Pass criteria:** 0 failures, 0 errors; total test count ≥ 100.

---

## §2 — T-40a numpy-vectorize hot eval path (V04_ADDENDUM §2-i)

**Status at draft time:** NOT YET LANDED. Will verify once shipped.

### 2.1 — Parity test (R-V04-VECTORIZE-01)
- **Check:** `test_heuristic_vectorize.py` exists and runs the vectorized kernel vs pure-Python kernel on ≥ 10 000 random `(blocked, carpet, opp_bit, own_bit, worker_xy)` configurations; assert **bitwise equality** OR `np.allclose(atol=1e-12)` (float tolerance acceptable only if documented).
- **Anchor:** property test file per V04_ADDENDUM §12 files list.
- **Pass criteria:** 10 000/10 000 matches, 0 divergences, documented tolerance if not bitwise.

### 2.2 — Depth benchmark
- **Pre-vectorize baseline (AUDIT_V03):** depth ~13 at 2 s pure-Python on the reference position.
- **Post-vectorize target (V04_ADDENDUM §2):** **+1.5× speedup on reference position**, i.e. depth ~13.5–14 at 2 s.
- **Flip-trigger (V04_ADDENDUM §2-i):** if speedup < 1.5×, ABANDON vectorization, revert to pure-Python.
- **Check:** run `tools/scratch/profile_search.py` (or successor) pre and post, report depth + nps delta.
- **Pass criteria:** speedup ≥ 1.5× OR vectorization was reverted (confirmed by grep).

### 2.3 — No new import / sandbox surface
- **Check:** vectorization uses only `numpy` (already allowed). No new third-party deps, no `@njit` re-introduced.
- **Pass criteria:** `heuristic.py` import block unchanged in terms of top-level deps.

### 2.4 — LRU cache interaction
- **Anchor:** `heuristic.py:603-623` `_cell_potential_vector_cached`.
- **Check:** if vectorization replaces `_cell_potential_vector_py`, the LRU cache keys + invalidation logic must still work. Cache tests `test_p_vec_cache_hit_on_repeated_board` + `test_p_vec_cache_invalidates_on_opp_move` must still pass.

### 2.5 — F19/F20 don't bypass the cache
- **Check:** F19 uses `_NEAR2_MASK[worker_idx]` (independent of `_cell_potential_vector`); F20 uses its own ray scan from opp_position. Neither should invalidate the P-vec cache more often than pre-v0.4.

---

## §3 — T-40b F19/F20 features (LANDED at 883dadc)

**Status:** shipped; team-lead notes 84/84 pass. AUDIT_V04 re-verifies.

### 3.1 — F19 `rat_catch_threat_radius`
- **Anchor:** `heuristic.py:313-314` (`_F19_RADIUS=2`, `_NEAR2_MASK` precomputed); evaluation `_NEAR2_MASK[worker_idx] @ belief`.
- **Semantics check:** `heuristic.py:78` docstring says `Σ_c belief[c] · I(d(worker, c) ≤ 2)`.
- **Anchor test:** `tests/test_heuristic_f19_f20.py` or similar (TBD at execution).
- **Pass criteria:** (a) monotonicity: F19 higher when belief-mass is closer to worker; (b) bounded: `0 ≤ F19 ≤ 1` (it's a sub-sum of a normalized distribution); (c) zero on a belief-at-(0,0) + worker-at-(7,7) scenario; (d) ≈ 1 on a peaky belief at worker's cell.

### 3.2 — F20 `opp_roll_imminence`
- **Anchor:** `heuristic.py:759+` (`_opp_roll_imminence`).
- **Semantics check:** `heuristic.py:83-89` — "longest PRIMED-or-SPACE cardinal run starting from opp worker" (superset of F8, which is PRIMED-only).
- **Pass criteria:** (a) F20 ≥ F8 always (superset); (b) zero when opp worker surrounded by BLOCKED/CARPET on all 4 sides; (c) matches hand-built board where opp has 3 primed + 2 space neighbors in a row → F20 = 5.

### 3.3 — W_INIT update sanity
- **Anchor:** `heuristic.py:255-260` W_INIT is now length 16.
- **Check:** `W_INIT[14] = 0.3` (F19 positive per V04_ADDENDUM §3: `W_INIT[14]` should be **negative** since higher threat is worse — CONFLICT CHECK with V04_ADDENDUM §3 F19 which says "sign negative, initial −0.15"). **Resolve ambiguity at execution:** if shipped sign is positive, verify docstring explanation OR raise as an audit finding.
- **Check:** `W_INIT[15]` is negative (F20 opp threat).
- **Pass criteria:** signs match semantics; magnitudes within plausible BO range.

### 3.4 — Regression guard
- **Baseline:** AUDIT_V03 = 92/92 pass.
- **T-40b landed target:** team-lead reports 84/84 (lower because some suites merged). **Resolve at execution:** does the 84 include all suites? Re-run full `pytest 3600-agents/RattleBot/tests/` and confirm total.
- **Check:** `test_symmetry` still passes with F19/F20 added; verify new features' perspective behavior is correct.

---

## §4 — T-40c context-adaptive time budget (LANDED)

**Status:** shipped in time_mgr.py.

### 4.1 — Method shape
- **Anchor:** `time_mgr.py:109-157` `adjust_for_context(belief_summary, prev_eval_variance)` returns clamped multiplier in `[0.5, 1.5]`.
- **Anchor:** `time_mgr.py:159+` `start_turn(..., prev_eval_variance=None)` accepts the kwarg.
- **Check:** method signature matches team-lead's brief. Clamp bounds `_CONTEXT_MULT_MIN=0.5, _CONTEXT_MULT_MAX=1.5` at `time_mgr.py:82-83`.

### 4.2 — Composition with endgame ceiling (M-7 interaction)
- **Risk:** T-40c's multiplier is applied **before** the endgame-ceiling check (if it is applied in `start_turn`). The context multiplier could push `budget` above `effective_ceiling`, triggering the `budget > effective_ceiling: budget = effective_ceiling` clamp. That's fine unless the clamp occurs BEFORE the context multiplier — in which case the multiplier would be silently wasted.
- **Check:** trace `start_turn` post-T-40c: order must be (a) compute base, (b) apply class multiplier (easy/normal/critical), (c) apply endgame multiplier lift, (d) apply T-40c context multiplier, (e) cap at endgame/regular ceiling, (f) clamp to usable.
- **Pass criteria:** read `start_turn` body + confirm T-40c application is in the correct step; tests cover composition.

### 4.3 — Safety reserve preserved
- **Critical check:** at no point in `start_turn` does `budget > usable` (where `usable = time_left - safety_s`). The 0.5 s reserve must ALWAYS hold.
- **Anchor:** `time_mgr.py:165-166` `if budget > usable: budget = usable`.
- **Pass criteria:** dedicated test `test_t40c_safety_s_preserved_with_high_entropy` (TBD — verify it exists or request it as a blocker).

### 4.4 — High-entropy / low-entropy test coverage
- **Required tests:**
  - `test_t40c_high_entropy_lifts_budget`: belief with entropy ≈ `ln 64` → multiplier ≈ 1.3.
  - `test_t40c_low_entropy_shrinks_budget`: belief with entropy ≈ 0 (delta) → multiplier = 1.0 (no ent lift).
  - `test_t40c_high_variance_lifts_budget`: `prev_eval_variance > 0.5` → multiplier += 0.2.
  - `test_t40c_low_variance_shrinks_budget`: `prev_eval_variance < 0.25` → multiplier -= 0.2.
  - `test_t40c_multiplier_clamped_at_bounds`: pathological inputs can't push outside [0.5, 1.5].
  - `test_t40c_composes_with_endgame_ceiling`: turns_left=3 + high entropy must still clamp at `ENDGAME_HARD_CEILING_S`.
- **Pass criteria:** all 6 exist, all pass.

### 4.5 — Regression: non-adaptive callers unchanged
- **Check:** calling `start_turn(board, time_left_fn)` without `prev_eval_variance` should behave identically to pre-T-40c (since `prev_eval_variance=None` → `var_term=0` per `adjust_for_context`).
- **Pass criteria:** all existing `test_time_mgr.py` + `test_t30e.py` tests still pass.

---

## §5 — T-40-EXPLOIT-1/2/3 features (PENDING)

**Status:** tasks #71, #72, #73 pending. Verify at execution or mark N/A.

### 5.1 — F22 prime-steal bonus (task #71)
- **Hypothesis:** a feature rewarding moves that convert opp's primed-line endpoints into our carpets (stealing opp's prep work into our advantage).
- **Anchor at execution:** find the feature in `heuristic.py`; check `N_FEATURES` increment.
- **Pass criteria:** (a) semantic test on a hand-built board with opp's 3-prime line + our adjacent worker rolls it; (b) `test_symmetry` passes; (c) sign is **positive** (good for us); (d) bounded.

### 5.2 — F10 extend adjacent-to-primed-endpoint (task #72)
- **Hypothesis:** feature rewards priming adjacent to one of our own primed endpoints (extending a line for bigger roll).
- **Pass criteria:** monotonicity in line-length extension; zero when no existing prime to extend.

### 5.3 — F24 opp-wasted-primes (task #73)
- **Hypothesis:** counts opp's primes that are "dead" (unreachable by opp before game end; isolated). Mirror of F17 (our dead primes).
- **Pass criteria:** parity test with F17 under perspective reversal (symmetric mirror).

### 5.4 — Combined W_INIT + BO compat
- **Check:** if features land, `N_FEATURES` bumps (16 → 18, 19, or 20). BO `BOUNDS` must be extended. Weight-loader must accept the new length.
- **Pass criteria:** `_load_tuned_weights` correctly rejects old 14-length weights; accepts new N-length.

---

## §6 — T-40-BO-ADOPT weights adoption (task #68 PENDING)

### 6.1 — Filename resolution
- **Anchor:** `agent.py:45-78` `_load_tuned_weights`. Current order: (a) `RATTLEBOT_WEIGHTS_JSON` env var; (b) sibling `weights.json`.
- **Ambiguity flagged by V03_UPLOAD_CHECKLIST §1.4 item 1:** BO output is named `weights_v03.json` but loader reads `weights.json`. AUDIT_V04 must verify either (a) loader updated to search both names, OR (b) ship script renames/copies file before zip, OR (c) BO pipeline renames.
- **Pass criteria:** shipped zip contains `RattleBot/weights.json` (whatever BO run produces is copied to that exact name inside the zip) OR the loader is updated.
- **Verify at execution:** `tools/build_submission.py` (task #69 landed) should handle this.

### 6.2 — Adoption gate (V04_ADDENDUM §5)
- **Check:** `w_runX` won ≥ +30 ELO vs `w_init` on FloorBot AND ≥ +20 ELO on FakeCarrie_v2 50-pair gauntlet. Per task #68 brief: RUN1-v4 results in BO tuner's reports.
- **Ownership:** dev-heuristic owns the decision; auditor verifies the evidence.
- **Pass criteria:** (a) the gate evidence is in `docs/tests/BO_RESULTS_*.md` or equivalent; (b) the weights file loaded at `Heuristic(weights=_load_tuned_weights())` time is the chosen one; (c) fallback to `W_INIT` works if file missing.

### 6.3 — NaN/Inf + malformed-json fallback
- **Check:** V03_UPLOAD_CHECKLIST §2 stress-test results must still pass with the new weights filename. Ideally a defence-in-depth `np.isfinite(arr).all()` check is added to `_load_tuned_weights` (V03_UPLOAD_CHECKLIST P1 recommendation).
- **Pass criteria:** either (a) `np.isfinite` check added and tested, OR (b) emergency_fallback demonstrably catches NaN-poisoned weights.

### 6.4 — Shape compatibility
- **Check:** `_load_tuned_weights` still rejects wrong-shape. With `N_FEATURES=16` (or higher after exploits), weight files from RUN1-v2 (14-dim) must be rejected → fallback to `W_INIT`. Weights from RUN1-v4 (16-dim) must be accepted.
- **Pass criteria:** stress test with wrong-shape JSON falls through to `W_INIT` (no crash).

### 6.5 — Weights file gets into submission zip
- **Check:** `tools/build_submission.py` output contains `RattleBot/weights.json` with correct 16-dim content. Verify with `python -c "import zipfile, json; z=zipfile.ZipFile('...'); print(json.loads(z.read('RattleBot/weights.json')))"` or equivalent.

---

## §7 — T-40-INFRA engine jax-drop (task #74)

**Scope:** `engine/` changes that drop jax dependency to unblock BO/paired-runner spawn-pool deadlock.

### 7.1 — Statistical equivalence
- **Check:** `T` output (64×64 transition matrix) post-jax-drop must match the pre-drop behavior statistically. Team-lead's brief calls for "statistically matches old behavior."
- **Method:** sample 50 random `T` matrices under both code paths using the same RNG seed; assert `np.allclose(T_old, T_new, atol=1e-5)` or equivalent.
- **Pass criteria:** either (a) T_old == T_new per seed, OR (b) documented distributional equivalence with test.

### 7.2 — No engine-side behavior drift
- **Check:** run `tools/sandbox_sim.py` on 3 pre-drop and 3 post-drop matches with the same seed; assert identical rat trajectory, sensor data, and game outcomes.
- **Pass criteria:** match-by-match identical OR documented tolerance within randomness slack.

### 7.3 — Tournament-safety
- **Check:** `engine/` MUST NOT be shipped in the submission zip. Auditor verifies `tools/build_submission.py` zip does not contain `engine/*`.
- **Pass criteria:** zip contents are exactly `RattleBot/*.py` + `weights.json`, nothing else.

---

## §8 — Tournament-safety ship checklist (LIVE_UPLOAD_006 lessons)

Every v0.4 submission zip must pass these:

### 8.1 — Numba default OFF
- **Anchor:** `heuristic.py:142` `_USE_NUMBA = os.environ.get("RATTLEBOT_NUMBA", "0") == "1"`.
- **Check:** no change from AUDIT_V03. Default must remain OFF. `test_numba_default_is_off_submission_safe` passes.

### 8.2 — Numpy-only, no jax/scikit-learn/cython/pytorch
- **Grep:** `from (jax|flax|sklearn|cython|torch|pynvml)` in `3600-agents/RattleBot/*.py`.
- **Pass criteria:** zero hits.

### 8.3 — No network / FS write / subprocess
- **Grep:** `socket|urllib|requests|httpx|http\.client|subprocess|os\.(system|spawn|exec)|\.write\(|open\([^)]*[\"']w` in agent package.
- **Pass criteria:** zero hits OR all hits in tests/ subdir.

### 8.4 — Zip layout
- **Check:** `python tools/build_submission.py` (task #69 landed) produces a zip with:
  - `RattleBot/__init__.py`
  - `RattleBot/agent.py`
  - `RattleBot/heuristic.py`
  - `RattleBot/move_gen.py`
  - `RattleBot/rat_belief.py`
  - `RattleBot/search.py`
  - `RattleBot/time_mgr.py`
  - `RattleBot/types.py`
  - `RattleBot/zobrist.py`
  - `RattleBot/weights.json` (if BO-tuned weights adopted)
- **Check:** no `__pycache__/*`, no `tests/*`, no `.pyc`, no `*.nbi` (numba cache). Size < 200 MB.
- **Pass criteria:** `unzip -l <zip>` confirms exactly the above.

### 8.5 — Extract + import + PlayerAgent(None) in fresh subprocess
- **Check:** extract zip to tempdir, fresh `python -c "import sys; sys.path.insert(0, 'tempdir'); from RattleBot.agent import PlayerAgent; PlayerAgent(None)"` returns without error.
- **Pass criteria:** subprocess rc=0, no exception.

### 8.6 — Cold init within init_timeout budget
- **Check:** `__init__` takes < 5 s cold (half the 10 s tournament budget). With `_USE_NUMBA=False` default, `warm_numba_kernels()` is a no-op. Primary init cost: `_compute_p0(T, steps=1000)` at ~3 ms + Zobrist table at < 1 ms + weights load at < 10 ms.
- **Pass criteria:** cold init < 5 s on dev box; < 10 s even at 4× CPU slowdown.

### 8.7 — First-play latency
- **Check:** first `play()` call doesn't absorb any deferred compile. First-turn belief-update + search budget must fit within the first-turn 6 s (or whatever `start_turn` allocates).
- **Pass criteria:** sandbox sim first-ply returns a move within budget.

---

## §9 — Meta checks (cross-cutting)

### 9.1 — `commentate()` still returns a string
- **Anchor:** `agent.py:142-151`. No PII / no info leak via the commentary string.
- **Check:** still returns `str`; no new fields that could leak private state.

### 9.2 — No DEAD-LIVE secret flags
- **Check:** no new `os.environ.get(...)` reads that could cause hidden mode switches (e.g., an "OPPONENT_MODEL" flag forgotten in live code). Grep `os.environ.get` and audit every hit.
- **Expected v0.4 hits:** `RATTLEBOT_NUMBA` (heuristic.py), `RATTLEBOT_WEIGHTS_JSON` (agent.py). Nothing else.

### 9.3 — No `print()` in agent package
- **Grep:** `^\s*print\(` in agent files (exclude tests).
- **Rationale:** `print()` to stdout in tournament may be interpreted as output; harmless but non-hygienic.
- **Pass criteria:** zero hits OR all hits in tests/ / inside `commentate()`.

### 9.4 — Deterministic Zobrist seed
- **Anchor:** `zobrist.py:53` `Zobrist(seed=0xBADDCAFE)` default. Bot's `__init__` uses default.
- **Check:** two `PlayerAgent(same_T, ...)` instances produce identical Zobrist hashes for identical boards.
- **Pass criteria:** `test_zobrist_determinism` passes.

### 9.5 — Deterministic RNG in fallback
- **Anchor:** `agent.py:110` `self._rng = random.Random(0xBA11A111)`. Emergency-fallback random picks are deterministic given same inputs.
- **Pass criteria:** no new `random.Random()` (no seed) calls anywhere in agent package.

---

## §10 — v0.4 gate wrap-up

AUDIT_V04.md's exec summary table will list each §1–§9 item with ✅/❌/N-A. Verdict mapping:
- **PASS:** 0 critical, 0 high, ≤ 5 medium, test count ≥ baseline (92).
- **AMBER:** 0 critical, ≤ 2 high, or medium > 5 with all documented.
- **FAIL:** any critical, or > 2 high, or any v0.4-gate-required test red.

### 10.1 — Severity rubric (unchanged from AUDIT_V03)
- **Critical:** ship-blocking. Would cause INVALID_TURN, TIMEOUT, or CODE_CRASH in tournament. Or: violates tournament-safety (network, FS write, seccomp-tripping import).
- **High:** must-fix before promotion. Would cost material ELO (> 15 pp) in predictable game states.
- **Medium:** should-fix but survivable. Documented approximation, or dead-code-that-doesn't-crash, or coverage gap.
- **Low:** nit / hygiene / doc.

### 10.2 — V03 carryovers expected to remain open in v0.4
From AUDIT_V03 v0.4 backlog (§5):
1. **M-A (`end_turn(0.0)`)** — V04_ADDENDUM §8 row 6 (T-40e) assigned to dev-integrator, +2–8 ELO, 0.5 h. **If not fixed by v0.4 ship, carry forward.**
2. **M-B (F18 root-only relocation)** — medium, BO expected to zero W_INIT[13]. Carry forward.
3. **M-C (F17 vectorize)** — medium, gated on T-40a (does T-40a cover F17 too?). **Verify at execution:** does T-40a's numpy vectorization extend to F17?

### 10.3 — New v0.4 risk register entries
From V04_ADDENDUM §10:
- **R-V04-VECTORIZE-01** (§2.1 above — parity test).
- **R-V04-BO-OVERFIT-02** (§6.2 above — gate condition).
- **R-V04-MCTS-SANDBOX** (if MCTS hybrid ships — currently NOT in scope).
- **R-V04-TIME-COMPRESS** (orchestrator owns).
- **R-V04-FEATURE-OVERFIT** (BO RUN3 cross-validation on FakeCarrie_v2 — tester-local owns).

### 10.4 — Final-ship go/no-go checklist
At AUDIT_V04 execution time:

| Gate | Owner | Status at exec |
|---|---|---|
| All §1 carry-forwards ✅ | auditor | TBD |
| All §2 T-40a vectorize ✅ or N-A | auditor | TBD |
| All §3 T-40b F19/F20 ✅ | auditor | TBD |
| All §4 T-40c adaptive time ✅ | auditor | TBD |
| All §5 exploit features ✅ or N-A | auditor | TBD |
| §6 BO weights adoption ✅ or N-A | auditor | TBD |
| §7 jax-drop stats equivalence ✅ or N-A | auditor | TBD |
| §8 tournament-safety ✅ (7 items) | auditor | TBD |
| §9 meta checks ✅ (5 items) | auditor | TBD |
| 200-match crash gate (tester-local) | tester-local | external |
| T-LIVE-2 live scrimmage pass (V04_ADDENDUM §9 gate 6) | live-tester-2 | external |
| paired local gates 1-4 (V04_ADDENDUM §9 gates 1-4) | tester-local | external |

Auditor sign-off line at end of AUDIT_V04.md (per BOT_STRATEGY §6.1 contract): **"Promotion approved by auditor on <DATE>, conditional on <external gates>."**

---

## §11 — Known gotchas / watch items

Specific things that could silently break v0.4:

1. **N_FEATURES drift without weights-file rebuild.** When features expand 16 → 18/19/20, BO weights from RUN1-v4 (16-dim) become shape-incompat. Must either (a) run RUN3 on new dim, OR (b) hand-extend W_INIT and disable weight-load. Loader fallback catches but we ship `W_INIT` which may regress ELO.
2. **T-40c context multiplier composition with M-7 endgame lift.** If T-40c multiplies the post-endgame-cap budget, it can push above `ENDGAME_HARD_CEILING_S=20.0` — then clamp kills the extra. Verify order of operations.
3. **Vectorize cache key invariance.** If T-40a changes the `_cell_potential_vector` implementation, the LRU cache key must remain `(blocked, carpet, opp_bit, own_bit)` — otherwise stale cache hits.
4. **Weights filename.** `weights.json` vs `weights_v03.json`. Build script must produce the filename the loader reads.
5. **F22/F10-ext/F24 perspective invariance.** New features MUST flip appropriately under `reverse_perspective()` OR document why not (F3/F4 precedent).
6. **F20 vs F8 correlation.** F20 is a superset of F8; BO may zero out F8 if F20's weight absorbs it. Verify W_INIT signs for both; allow BO to resolve.
7. **Numba kernel definitions still present but unused** when `_USE_NUMBA=False`. Harmless but the `@njit` decorated functions in `heuristic.py:319+` still exist. If numba fails to import at module-load, the `if _NUMBA_AVAILABLE and _USE_NUMBA:` guard prevents function definition. Verify this path still catches cleanly.

---

## §12 — Anchor files (execution-time read list)

When AUDIT_V04 fires, read these in order (time-budget ~30 min read + 30 min test + 30 min write):

**Source code:**
1. `3600-agents/RattleBot/__init__.py` (4 LOC; should be unchanged)
2. `3600-agents/RattleBot/agent.py` (look for M-A fix at line 223; T-40-BO-ADOPT weights filename; exploit features wiring if any)
3. `3600-agents/RattleBot/heuristic.py` (T-40a vectorize; F19/F20; F22/F10-ext/F24 if landed; N_FEATURES)
4. `3600-agents/RattleBot/move_gen.py` (likely unchanged; verify)
5. `3600-agents/RattleBot/rat_belief.py` (likely unchanged; verify)
6. `3600-agents/RattleBot/search.py` (likely unchanged from AUDIT_V03)
7. `3600-agents/RattleBot/time_mgr.py` (T-40c confirmed; verify composition)
8. `3600-agents/RattleBot/types.py` (likely unchanged)
9. `3600-agents/RattleBot/zobrist.py` (likely unchanged)

**Tests:**
10. `tests/test_heuristic.py` (F19/F20 + vectorize parity + existing)
11. `tests/test_rat_belief.py` (likely unchanged)
12. `tests/test_search.py` (likely unchanged)
13. `tests/test_t20f.py` (likely unchanged)
14. `tests/test_t30e.py` (likely unchanged)
15. `tests/test_time_mgr.py` (T-40c additions)
16. `tests/test_heuristic_vectorize.py` if exists
17. `tests/test_heuristic_f19_f20.py` if exists
18. `tests/test_t40c.py` if exists

**Plans + tests:**
19. `docs/plan/BOT_STRATEGY_V04_ADDENDUM.md`
20. `docs/tests/RESULTS_V04.md` if exists (v0.4 gauntlet results)
21. `docs/tests/BO_RESULTS_*.md` for adoption evidence
22. `tools/build_submission.py` (task #69) — verify zip layout
23. Any new LIVE_UPLOAD_00{7,8,9}.md results

---

## §13 — Execution command reference

```bash
# Full pytest
cd C:/Users/rahil/downloads/3600-bot && PYTHONPATH="engine;3600-agents" python -m pytest 3600-agents/RattleBot/tests/ -v

# Leaf timing replay
cd C:/Users/rahil/downloads/3600-bot && PYTHONPATH="engine;3600-agents" python -m pytest "3600-agents/RattleBot/tests/test_heuristic.py::test_per_call_timing" -v -s

# Import isolation scan
# (use Grep tool with pattern: socket|urllib|requests|httpx|http\.client|subprocess|os\.(system|spawn|exec)|\.write\(|open\([^)]*[\"']w)

# Env var audit
# (use Grep tool with pattern: os\.environ\.get)

# Build + verify submission zip
python tools/build_submission.py  # produces zip
python -c "import zipfile; z=zipfile.ZipFile('<zip>'); print('\\n'.join(z.namelist()))"
```

---

## §14 — AUDIT_V04.md output structure

Same as AUDIT_V01 / AUDIT_V03:

1. **§1 — Executive summary** — PASS / AMBER / FAIL verdict; severity counts; test-suite total; v0.4 gate matrix.
2. **§2 — Findings table** — sorted by severity; file:line + issue + fix-suggestion.
3. **§3 — Per-item walk** — every §1-§9 item of this checklist, with PASS/FAIL + evidence.
4. **§4 — Test-suite output** — full pytest run, leaf timing, any other measurements.
5. **§5 — v0.5 / post-deadline backlog** — nice-to-haves deferred past tournament lock.
6. **§6 — Final recommendation** — GO / NO-GO + auditor sign-off line.

Target length: 500-800 LOC for the full AUDIT_V04.md.

---

**End of AUDIT_V04_CHECKLIST.**
