# BOT_STRATEGY v0.2 Addendum — Concrete ELO-Gain Plan for RattleBot v0.2

**Author:** v02-planner
**Date:** 2026-04-17 (T − 54 h to submission lock)
**Status:** Proposed. Supersedes nothing; extends `docs/plan/BOT_STRATEGY.md` v1.1 §4 (v0.2 row) and §10 (T-19..T-21) with specifics.
**Scope:** v0.2 ONLY. v0.3/v0.4/v0.5 get a one-paragraph preview in §7 for schedule sanity.
**Inputs consulted:** `docs/plan/BOT_STRATEGY.md` v1.1 (primary), `docs/audit/AUDIT_V01.md` §2/§5, `docs/plan/RATTLEBOT_V01_NOTES.md` S-1..S-6, `docs/research/RESEARCH_HEURISTIC.md` v1.2 §C/§D/§F, `docs/research/RESEARCH_ADVERSARIAL.md` §C/§G, `docs/research/CONTRARIAN_SCOPE.md` §C-6/§D-2, `docs/DECISIONS.md` D-008/D-009/D-010/D-011, `docs/STATE.md` (v0.1 landed state), `3600-agents/RattleBot/{agent.py, search.py, time_mgr.py, heuristic.py}` (as shipped), `tools/paired_runner.py`, `requirements.txt`.

---

## §1 — Scope & non-goals

### 1.1 What v0.2 IS
A focused **tuning + small-feature + small-search** wave layered on the v0.1 audit-clean skeleton. Concretely:
- **Heuristic weight tuning** via Bayesian optimization (D-009) against paired self-play vs FloorBot, producing a `weights.json` artifact the agent loads at init.
- **Heuristic feature expansion 7 → 9**, promoting two features that research marks as high-value: F8 (opponent-line-threat, mapped onto `opp_longest_primable` from `RESEARCH_HEURISTIC.md` §C.2 F9/F10) and F13 (center-of-mass belief distance from worker, mapped onto `RESEARCH_HEURISTIC.md` §E.2 VoI term).
- **Time-ceiling lift** (M-01): remove the v0.1-only `_PER_TURN_CEILING_S = 3.0` cap once the heuristic is calibrated — reclaim the other ~50 % of the tournament budget.
- **Safety-margin cleanup** (M-02): single-source `safety_s` in `time_mgr` and stop double-booking it in `agent → search` handoff.
- **Move-ordering audit**: confirm hash-move / killer / history are all actually firing in `_alphabeta` per D-004 stack; fix if not.
- **Opponent-modeling scaffolding** (NOT implementation): a drop-in `min_node_estimator` interface behind a runtime `OPPONENT_MODEL` flag, deferred for implementation until the D-010/T-24 scrimmage-data precondition is met.

### 1.2 What v0.2 IS NOT
- **No new search architecture.** No MCTS, no PUCT, no in-tree chance nodes, no null-move pruning. (BOT_STRATEGY §8 non-goals — binding.)
- **No NN heuristic.** F3 from `RESEARCH_HEURISTIC.md` §F.3 remains a v0.5 stretch at earliest. (PRIOR §F anti-pattern 3.)
- **No JAX / torch / flax** loaded at runtime. v0.1 shipped as pure numpy + Python; keep it that way. (R-INIT-01.)
- **No make/unmake optimization.** v0.3 scope per BOT_STRATEGY §3.3. If v0.2 ELO gate passes with `forecast_move` throughput, we don't touch it.
- **No numba / cython leaf compilation.** v0.3+ contingent on flip-trigger §7 row 6 (`leaf > 40 % wall AND ≥ 2× speedup achievable`). Current heuristic p99 is 8.5 µs (AUDIT §3.8), nowhere near the trigger.
- **No opening book, no endgame tablebase.** v0.5 scope. (BOT_STRATEGY §8, D18/D19.)
- **No live uploads.** v0.2 is a local-tuning release; live promotion is a v0.3 task (T-23, gated on D-010's AUDIT_V03.md). Tester-live stays on FloorBot triage (task #24).

---

## §2 — Prioritized v0.2 tasks (ordered by expected ELO Δ per hour)

Ordering is Δ-ELO / hour, highest first. Every row has an expected ELO delta, hours estimate, testability, and a flip-trigger that reverts the change.

| ID     | Task                                                              | Owner            | Expected ELO Δ | Hours | Testability                                                                                              | Flip-trigger                                                                                               |
|--------|-------------------------------------------------------------------|------------------|----------------|-------|----------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| T-20a  | Lift `_PER_TURN_CEILING_S` 3 s → 6 s + configurable                | dev-integrator   | +30 to +50     | 1–2   | 20-match paired vs v0.1 under `limit_resources=True`; assert avg depth rises, 0 TIMEOUTs.                | If TIMEOUTs appear in ≥ 1/50 matches → revert to 3 s OR flat 5.5 s per BOT §7 row 14.                      |
| T-20b  | Consolidate M-02 `safety_s` — single source in `time_mgr`          | dev-integrator   | +0 to +5       | 0.5   | Pytest: a new test checks `search.iterative_deepen(..., safety_s=0.0)` when agent.py already reserved.   | None — pure cleanup. If tests regress, revert the 4-line diff.                                             |
| T-20e  | Move-ordering v0.2 audit: confirm TT hash-move / killer / history  | dev-search       | +10 to +30     | 1–2   | Per-search stats dump: TT hit-rate ≥ 15 % at depth 5–6 on 50-match sweep (T-SRCH-3 gate, BOT §5).        | If TT hit-rate stays < 5 % after fix → drop hash-move tier per BOT §7 row 7.                               |
| T-20c  | Feature expansion 7 → 9 (add F8, F13)                              | dev-heuristic    | +20 to +40     | 3–4   | Unit tests on hand-crafted boards (T-HEUR-1 extended); p99 leaf time remains ≤ 100 µs.                   | If BO in T-20d cannot find weights that beat 7-feature `w_init` by ≥ +20 ELO → drop the 2 new features.    |
| T-20d  | Bayesian-opt weight tuning pipeline (`tools/bo_tune.py`)           | dev-heuristic    | +40 to +80     | 6–10  | BO output beats `w_init` by ≥ +30 ELO on 50-match paired vs FloorBot **AND** ≥ +20 ELO vs Yolanda.      | If BO fails to beat `w_init` by +30 ELO → ship `w_init` per BOT §7 row 9; bank the compute budget.         |
| T-20f  | Opponent-modeling drop-in interface spec (no impl)                 | dev-integrator   | +0 (v0.2)      | 1     | Interface-compile-only; `OPPONENT_MODEL="self-play"` default path is byte-identical to v0.1 search.      | None — interface without bind. Implementation blocked on T-24 precondition (D-010, ≥ 10 scrimmages).       |

**Totals:** 12.5–20.5 hours of dev time + 6–10 hours parallel BO wall-clock. Fits the BOT_STRATEGY §4 "14 h dev + 6–10 h parallel BO" v0.2 budget.

**Aggregate expected ELO Δ at v0.2 exit (vs v0.1): +100 to +200**, center estimate **+140**. Source: (T-20a 40) + (T-20c 30) + (T-20d 60) + (T-20e 20) − (overlap penalty 10 since T-20d retunes weights for the new features → their wins partly overlap). This is consistent with BOT_STRATEGY §4's "v0.2: +80 to +120 ELO over v0.1" row; our estimate is slightly more aggressive because the time-ceiling lift (M-01) was explicitly documented as "+30-50 ELO on the table" in AUDIT_V01 §3.7.

### 2.1 T-20a — Lift M-01 per-turn time ceiling (3 s → 6 s, configurable)

**Current state (AUDIT_V01 §3.7, RATTLEBOT_V01_NOTES S-2):** `time_mgr.py:39` has `_PER_TURN_CEILING_S = 3.0` which overrides both the adaptive multipliers and the 2.5× surplus cap. On a late-game `critical` turn (turns_left=2, time_left=60 s), the ceiling lets the turn use only 3.0 s out of 47.6 s of adaptively-computed budget — **5 % utilization**. Tournament budget is `240 / 40 = 6 s/turn` base; the ceiling halves even a normal turn.

**Why it was there (S-2):** v0.1 heuristic was uncalibrated; deeper search on a biased leaf converges faster to the wrong move. With BO-tuned weights (T-20d) and 34/34 passing audit (AUDIT_V01), the premise is gone.

**Change (concrete):**
1. In `time_mgr.py`: replace module-level `_PER_TURN_CEILING_S = 3.0` with a `TimeManager.__init__` arg `per_turn_ceiling_s: float = 6.0`. Store on `self`.
2. The ceiling clause at `time_mgr.py:79-80` reads from `self.per_turn_ceiling_s`.
3. Expose via `agent.py` so a future tournament variant can set 5.5 or 6.0 without a code edit.
4. Document in `commentate()` output line `f"v0.2 ceiling={self._time_mgr.per_turn_ceiling_s:.1f}s"` so tournament logs record the cap in effect.
5. Adaptive multipliers and 2.5× surplus cap (D-004) remain unchanged — the ceiling sits on top of them.

**Expected ELO Δ:** +30 to +50 (AUDIT §3.7 end-of-section estimate). Mechanism: average ID depth rises from current ~4 (measured at 2 s budget, v0.1 T-14 notes: "~30k nps, 54k nodes / 28k leaves at 2 s") to 5–6 at 6 s. Branching factor b ≈ 6.5 gives ~6–8× more node work per depth step. Depth 5 → 6 flips enough late-game lines to move ~1 point per match on expectation; over 40-turn games that's enough for a 5–8 pp win-rate shift = 40–60 ELO.

**Testability:**
- New pytest `tests/test_time_mgr.py::test_ceiling_configurable` constructs a `TimeManager(per_turn_ceiling_s=6.0)` and asserts a hand-crafted `start_turn` returns a budget of 6.0 s (not 3.0) under generous `time_left`.
- Smoke: `python tools/paired_runner.py --agents RattleBot Yolanda --n 20 --seed 0 --quiet --no-limit-resources` — expect 0 TIMEOUTs, wins ≥ 18/20.
- Paired: `python tools/paired_runner.py --agents RattleBot_v02 RattleBot --n 50 --seed 0` — expect ≥ 55 % win-rate (directional signal; statistical confirm comes via T-21).

**Flip-trigger:**
- If TIMEOUTs fire in ≥ 1/50 matches under `limit_resources=True` (Linux run): revert to 3 s or adopt the flat-5.5 s schedule from BOT_STRATEGY §7 row 14.
- If depth-6 search produces worse moves than depth-4 (monotonicity violation) on ≥ 5 test positions: T-SRCH-2 gate has failed — defer the lift until T-20e fixes move ordering.

---

### 2.2 T-20b — Consolidate M-02 `safety_s` ownership

**Current state (AUDIT_V01 §2 M-02, §3.5):** `time_mgr.start_turn` subtracts `SAFETY_S = 0.5` to compute `usable`. Then `agent.py:128, 136` passes that `usable` to `search.iterative_deepen(...)` as `time_left_s`, which **subtracts `safety_s=0.5` a second time** (`search.py:132`). Net: 1.0 s is reserved; this is strictly conservative but obscures the invariant that one layer owns the reserve.

**Change (concrete):** Pick one of two equivalent fixes. **Recommended: option (b).**
- **(a)** In `agent.py`, pass `safety_s=0.0` when calling `iterative_deepen` and `root_search_decision`. `time_mgr` remains the single owner of the 0.5 s reserve.
- **(b)** In `time_mgr.start_turn`, return the pre-safety budget; let `search` own the 0.5 s reserve (matches the function's default `safety_s=0.5`). Update the docstring of `start_turn` to say "returns the raw budget; search applies its own safety".

Option (b) matches BOT_STRATEGY Appendix B's "Time safety: 0.5 s before engine cutoff" and keeps the reserve adjacent to the code that actually polls the clock.

**Expected ELO Δ:** **+0 to +5**. This is a correctness-and-clarity fix, not a strength boost. The 0.5 s of extra reserve translates to ~5 % less budget per move — maybe 1 fewer depth step on a single critical turn across 40. Minor.

**Testability:**
- New pytest `tests/test_agent_search_integration.py::test_no_double_safety`: mocks `time_mgr.start_turn` to return 1.0 s, mocks `_time.perf_counter` to freeze time, asserts `search.iterative_deepen` sees `budget == 1.0 s - 0.5 s = 0.5 s` (or `1.0 s`, depending on which option we choose).
- No regressions in paired vs v0.1: result should be neutral-to-slightly-positive.

**Flip-trigger:** None. If the test regresses, revert the 4-line diff.

---

### 2.3 T-20e — Move-ordering v0.2 audit

**Current state (AUDIT_V01 §3 TT hit-rate report, T-14 STATE entry):** At 2 s budget from depth 3, v0.1 measured **45.8 % TT hit-rate, 8498 hits / 3619 cutoffs, 54 732 nodes / 28 488 leaves**. That's above the T-SRCH-3 gate of 15 %. So TT is working. But the "audit" task still has value: we want confirmation that at v0.2's **deeper** budget (6 s, d=5–6), the ordering stack keeps firing — specifically that the hash-move and killer slots are being **populated** and **consulted** in the right order.

**Change (concrete):**
1. Add instrumentation inside `search.py::_alphabeta`: counters for `hash_move_hits`, `killer_slot_0_hits`, `killer_slot_1_hits`, `history_reorder_count`, `cutoff_on_first_move`, `cutoff_on_nth_move[0..7]`.
2. New `search.get_stats() -> dict` reads those counters.
3. `tools/paired_runner.py --quiet` gains a `--log-search-stats` flag that, per match, dumps `search.get_stats()` to the summary JSON.
4. New `docs/tests/SEARCH_STATS_V02.md` records 50-match paired run's aggregate stats. Gate: `cutoff_on_first_move / total_cutoffs ≥ 0.6`, `hash_move_hits > 0` on every TT-hit position, `history_reorder_count > 0` on mid-game positions.
5. **Bug-triage path:** if the instrumentation exposes that killer or history slots are NOT actually being populated (the D-004 stack names them but v0.1's implementation could have a plumbing bug), fix the plumbing inside `move_gen.ordered_moves`.

**Expected ELO Δ:** +10 to +30. Research §G.1 claims "hash-move first often 2–4× node reduction alone; trivial to add"; killer + history together add another 1.5–2×. If v0.1's instrumentation reveals a bug (a real possibility — the v0.1 T-SRCH-3 gate passed at 45.8 % hit-rate, but that's at d=3 where hash-move matters less), fixing it buys depth +0.5 to +1 at the same wall-clock.

**Testability:**
- `tests/test_search.py::test_ordered_moves_hash_move_promoted` already exists (AUDIT §3.1 test roster). Add:
  - `test_killer_move_promoted`: after a cutoff on move X at depth d, next sibling's ordering has X first.
  - `test_history_reorder_monotone`: repeated cutoffs on same move-type increase its history priority.
- Gate: `docs/tests/SEARCH_STATS_V02.md` shows `cutoff_on_first_move / total_cutoffs ≥ 0.6` at depth 5. Below 0.5 = ordering is broken.

**Flip-trigger:** TT hit-rate < 5 % after the audit + fixes → drop hash-move tier, promote killer/history only (BOT §7 row 7).

---

### 2.4 T-20c — Feature expansion 7 → 9 (F8 + F13)

**Current 7-feature vector (heuristic.py W_INIT):** `[F1, F3, F4, F5, F7, F11, F12]` with `W_INIT = [1.0, 0.3, 0.2, 1.5, -1.2, -3.0, -0.5]`.

**v0.2 target 9-feature vector:** `[F1, F3, F4, F5, F7, F11, F12, F8, F13]`.

#### F8 — opponent-line-threat (`opp_longest_primable`)
- **Definition (RESEARCH_HEURISTIC §C.2 F10):** `max` over cardinal directions `d` of `reach(opp_worker_pos, d)` — the longest contiguous line the opponent could prime-and-roll starting from their worker position, constrained by blocked/carpeted cells. Bitmask scan; O(4) per evaluation.
- **Why this one:** AUDIT §3.8 called out that `F3/F4` (our prime/carpet counts) in v0.1 are **perspective-invariant whole-board popcounts** and don't actually track opponent threat. F8 gives the heuristic a real signal for "opponent can roll a k≥5 line next turn" — the biggest single point-swing available to the opponent (carpet k=5 = 10 pts, k=6 = 15, k=7 = 21).
- **Expected magnitude:** when F8 flags an imminent opp-roll ≥ 5, the leaf should discount position by ~ `w8 · 10` pts; this should move the tree to prefer blocking/denial moves (parking on the opp's line) that F10 (`opp_mobility_denied`) would reward. Effect on win-rate: ~ 5–10 pp.
- **`w_init` bound (pre-BO):** sign **negative**, initial magnitude `-0.6` (proportional to F7 which is already `-1.2` and F7 captures a broader "where are good cells" signal; F8 is sharper but rarer, so ≈ 0.5× F7 magnitude).
- **BO search-space bound (for T-20d):** `w8 ∈ [-3.0, 0.0]`. Negative-only because an opponent threat should never help us.

#### F13 — center-of-mass belief distance (`belief_com_dist_from_worker`)
- **Definition:** `dist(worker_pos, E_b[rat_pos])` where `E_b[rat_pos] = (Σ_c b(c)·x_c, Σ_c b(c)·y_c)` is the Manhattan-distance from our worker to the belief's center-of-mass. O(64) per evaluation if computed from scratch; O(1) if precomputed in `BeliefSummary` (recommended — add a `com_x: float, com_y: float` field in `types.py`).
- **Why this one (NOT the RESEARCH_HEURISTIC F13 center-control formulation):** the TASK brief called this F13 and research §C.2 F13 is `center_control = -manhattan(worker, (3.5, 3.5))` — but research §H.4 already deprecates F13-center-control as "de-weighted because our spawn is already near center" (SYN §B19). What actually moves the needle is **how close is our worker to where the rat probably is** — i.e. distance to the belief's center-of-mass. This aligns with RESEARCH_HEURISTIC §B.3's "cell potential × distance from bot" (the Carrie-style lever already in F5 as a multiplier) but from the opposite angle: the heuristic should reward positions where our worker is near the belief COM because the next sensor reading will be sharper (distance-likelihood peaks at short range, SPEC §3.5) AND if belief concentrates, our search-move will be cheap.
- **Why this is better than a pure F15 "expected_search_value" term:** F15 is already implicit in F11 + F12 (belief max × entropy, both live in `BeliefSummary`). F13 adds a **geometric** signal the linear combination currently lacks — the interaction between worker position and belief distribution.
- **Expected magnitude:** the nearer our worker is to the rat COM, the more future information per sensor read. ~ 3–6 pp win-rate.
- **`w_init` bound (pre-BO):** sign **negative** (larger distance → worse), initial magnitude `-0.05` (Manhattan distance values in [0, 14], so max absolute contribution is ~ 0.7 pts).
- **BO search-space bound (for T-20d):** `w13 ∈ [-0.20, 0.0]`.

#### Update to `heuristic.py`
- `N_FEATURES = 9`.
- `features(board, belief_summary) -> np.ndarray(9,)` computes both new features.
- `W_INIT = [1.0, 0.3, 0.2, 1.5, -1.2, -3.0, -0.5, -0.6, -0.05]` (preserving the v0.1 first-7 slots so BO can be bootstrapped with `w_init`).
- `BeliefSummary` (in `types.py`) adds `com_x: float, com_y: float` — computed once per turn by `RatBelief.update()`, O(128) work, ~2 µs. This keeps the leaf O(1) for F13.
- Tests in `tests/test_heuristic.py`:
  - `test_f8_opp_line_threat_on_primed_line` — hand-craft a board with opp worker at (2,2) and primed cells at (3,2)(4,2)(5,2)(6,2); assert F8 = 4 (or 5 if including opp's own cell).
  - `test_f13_com_dist_monotone` — construct 3 belief distributions concentrated at (0,0), (3,3), (7,7) with worker at (3,3); assert F13 = distance to the mass: 0, small, large.
  - Update `test_per_call_timing`: 9-feature p99 must remain ≤ 100 µs (current 7-feature p99 is 8.5 µs, plenty of headroom).

**Expected ELO Δ:** +20 to +40 (net, after BO in T-20d retunes all 9 weights). Without BO retune, the raw addition with `w_init` is probably +5 to +15.

**Testability:** unit tests above + the T-20d paired gate.

**Flip-trigger:** If BO's best 9-feature config cannot beat BO's best 7-feature config by +15 ELO on 50 paired, drop F8 and/or F13. Specifically: run T-20d twice — once with N_FEATURES=7, once with N_FEATURES=9 — and promote whichever wins.

---

### 2.5 T-20d — Bayesian-opt weight tuning pipeline

**Why BO (D-009 recap):** CMA-ES at HEUR §F.2's numbers needs 42–83 h sequential; we have ~10 h. BO on 9-dim smooth objective typically converges in 20–30 trials (D-009 evidence line). Paired-match win-rate is a smooth function of weights locally; BO's Gaussian-process surrogate handles noise well.

**Tool:** **scikit-optimize** (`skopt`) — NOT in `requirements.txt` (currently 8 lines: jax, scikit-learn, flax, numpy==2.1.3, numba==0.61.0, psutil, cython, torch, pynvml). **Add `scikit-optimize==0.10.2` to `requirements.txt`.** Note: scikit-optimize is abandonware upstream but the 0.10.x line works with scikit-learn 1.4+ and numpy 2.x; it's still the simplest BO library that runs on CPU. Alternative if installation breaks: `bayesian-optimization==1.5.1` (simpler API, same GP backend).

**Search-space bounds (9 dims):**

| Idx | Feature                  | Bound lower | Bound upper | `w_init` | Sign rationale                                          |
|-----|--------------------------|-------------|-------------|----------|---------------------------------------------------------|
| 0   | F1 `score_diff`          | +0.5        | +2.0        | +1.0     | Must stay positive and dominant — ground-truth axis.    |
| 1   | F3 `primed_popcount`     | 0.0         | +1.0        | +0.3     | Approximation-invariant in self-play (AUDIT §3.8).      |
| 2   | F4 `carpet_popcount`     | 0.0         | +0.8        | +0.2     | Banked points — positive but small.                     |
| 3   | F5 `our_cell_potential`  | 0.0         | +3.0        | +1.5     | Carrie's 80→90 % lever — BO can push this hard.         |
| 4   | F7 `opp_cell_potential`  | −3.0        | 0.0         | −1.2     | Opp-equivalent of F5 — always negative.                 |
| 5   | F11 `belief_max_mass`    | −5.0        | 0.0         | −3.0     | Negative drives root SEARCH gate (agent.py:p>1/3).      |
| 6   | F12 `belief_entropy`     | −2.0        | 0.0         | −0.5     | Low entropy = good (concentrated belief).               |
| 7   | F8 `opp_line_threat`     | −3.0        | 0.0         | −0.6     | Opp threat — always negative.                           |
| 8   | F13 `belief_com_dist`    | −0.20       | 0.0         | −0.05    | Distance penalty — always negative.                     |

**Rationale for bound signs:** every `w_init` sign is preserved and the bounds stretch only in the direction BO is allowed to amplify. BO is NOT allowed to flip a sign — doing so would encode "up is down" (e.g. positive F11 weight would mean "we want the belief UNCONCENTRATED", the opposite of the SEARCH gate's premise). This is a soft prior; if BO converges to a boundary we review whether that dim's bound was too tight.

**Objective:**
- `f(w) = paired_win_rate(RattleBot_with_w, FloorBot)` evaluated by a call into `paired_runner._run_pair` for `N=20` pairs (40 matches). Per-trial wall-time ≈ 40 × 30 s = 20 min on 1 core, or ~5 min parallelized at 4 cores.
- BO maximizes `f(w) - λ · regularization` where `regularization = 0.01 * ||w - w_init||_2 / ||w_init||_2`. Light regularization to prefer small moves from the hand-tuned prior; BO can override if signal is strong.

**Stopping criteria (either triggers stop):**
- **25 trials** completed, OR
- **2 h wall-clock** elapsed (whichever comes first), OR
- **Early stop**: no improvement in best-observed `f(w)` over 8 consecutive trials.

**Parallelism:** BO's core loop is inherently sequential (each trial depends on the posterior from previous trials). Real speed comes from parallelizing the **per-candidate evaluation**: each 40-match evaluation itself is 40 independent matches → use `paired_runner`'s existing `multiprocessing` pool (`n_workers = cpu_count() − 1`) inside the objective function.

If the user has ≥ 8 cores, also enable **scikit-optimize's `n_points` batched-ask/tell** (evaluate 2–4 candidates per GP update). This is approximate async BO and reduces wall-clock by ~1.5× at the cost of slightly worse surrogate quality.

**Infra: new file `tools/bo_tune.py`**
- CLI: `python tools/bo_tune.py --opponent FloorBot --n-per-trial 20 --max-trials 25 --max-hours 2 --out 3600-agents/RattleBot/weights.json --seed 0`.
- Entry: imports `paired_runner._run_pair` directly (programmatic, already exposed per `tools/paired_runner.py:181`).
- For each BO candidate `w`: monkey-patch `heuristic.W_INIT` (or set it via an env var `RATTLEBOT_WEIGHTS_JSON`, which `agent.py:__init__` loads if present), then call `_run_pair` N=20 times with pair_seed=`trial_idx * 1000 + i`. Collect wins, compute Wilson CI and win-rate, return to BO.
- Output: `weights.json` with the best-observed `w`, plus a `tuning_log.json` recording every trial's `(w, win_rate, ci)` for auditability.
- `agent.py` modification: at `__init__`, check `os.path.join(os.path.dirname(__file__), "weights.json")` and if present, `np.loadtxt` or `json.load` the vector into `heuristic.W_INIT` (or pass via constructor). Fallback to the hard-coded `W_INIT` if file missing — this keeps the submission zip functional without the tuned weights if tuning slips.

**Success gate (T-HEUR-3 per BOT §5):**
- BO's best weights beat `w_init` by ≥ **+30 ELO** on a 50-match paired evaluation vs FloorBot (Wilson 95 % CI lower bound ≥ +10 ELO).
- **AND** BO's best weights do not **regress** against Yolanda (cross-validation): ≥ 90 % vs Yolanda (v0.1 is at 100 % per STATE; accept 90 % as the safety floor).
- If the gate fails, **ship `w_init`** (BOT §7 row 9). Do not force a tuned vector that isn't clearly better.

**Expected ELO Δ:** +40 to +80 over `w_init` at the center of the estimate (BOT_STRATEGY §4 "v0.2: +80 to +120" minus the portion allocated to T-20a/e).

**Testability:**
- Unit test: `tools/test_bo_tune.py::test_objective_is_deterministic_under_fixed_seed` — same `w`, same seeds → same win-rate.
- Integration: `tests/test_agent.py::test_weights_json_override` — drop a `weights.json` in the package dir, assert `PlayerAgent().heuristic.weights == loaded`.
- Gate per above.

**Flip-trigger:**
- BO cannot beat `w_init` → ship `w_init`, bank the 6–10 h (BOT §7 row 9).
- BO's best on paired-FloorBot regresses vs Yolanda → the harness is over-fitting to FloorBot; add Yolanda to the objective as a 50/50 mix.

---

### 2.6 T-20f — Opponent-modeling drop-in interface (spec only)

**Why this is in v0.2:** setting up the interface now keeps T-24's critical-path clean and is ~ 1 h of spec work. Actual implementation of a George-greedy or Carrie-greedy model stays blocked on D-010's precondition (≥ 10 live scrimmages in `docs/tests/ELO_LEDGER.md`).

**Interface spec (new module `3600-agents/RattleBot/opp_model.py`):**
```python
from typing import Callable, Optional
from game.board import Board
from game.move import Move

# Type alias: opponent model = function mapping (board from opp's perspective,
# belief_summary) -> opponent's predicted best move. Returns None to signal
# "use the generic min-node estimator" (current v0.1 behavior).
OpponentModel = Callable[[Board, "BeliefSummary"], Optional[Move]]

def get_model(name: str) -> Optional[OpponentModel]:
    """Registry lookup. Returns None for 'self-play' (default, byte-identical
    to v0.1). Returns a callable for named models ('george_greedy',
    'carrie_greedy', 'albert_simple'). Unknown names -> raise ValueError.
    Implementations are stubbed until T-24."""
    ...
```

**Integration point in `search.py`:**
- `Search.__init__` takes an optional `opponent_model: Optional[OpponentModel] = None`.
- In `_alphabeta` at min nodes: if `opponent_model is not None`, try calling it; if it returns a Move, evaluate that move AS THE ONLY min-node child (pure-play opponent model, not a mixed distribution). If it returns None, fall through to the generic min-node.
- This keeps the "generic" path byte-identical to v0.1.

**Runtime flag:** `agent.py::__init__` reads `os.environ.get("OPPONENT_MODEL", "self-play")`; `opp_model.get_model(name)` is called and passed to `Search`. Default env unset → `"self-play"` → None → v0.1 behavior.

**v0.2 scope:** ship the interface, the `get_model("self-play") -> None` default, and the env-flag plumbing. All other names raise `NotImplementedError`. One test: `tests/test_opp_model.py::test_self_play_byte_identical` — constructs two `PlayerAgent`s with/without the env flag set to `"self-play"`, runs 20 turns, asserts identical moves.

**Expected ELO Δ in v0.2: +0.** (Interface-only; no behavioral change with default flag.)

**v0.3/v0.5 handoff:** when T-24 unblocks, dev-opponent-model implements `george_greedy` first (cheapest per RESEARCH_HEURISTIC §D.2 — George is "greedy carpet + prime + opportunistic SEARCH" per CLAUDE.md §5, easy to ape). Expected ELO Δ when paired vs actual George: +30 to +60 (CONTRARIAN_SCOPE §C-6 "0.25–0.35 P(beats Carrie)" implies large exploitation gains on easier opponents).

**Testability:** interface compiles; default path passes the byte-identical test.

**Flip-trigger:** if T-24 is SUSPENDED at T − 30 h per D-010 precondition, the interface remains shipped but inert. No cost.

---

## §3 — Sequencing & dependencies

DAG (→ = blocks):

```
       T-20a (lift ceiling) ──┐
       T-20b (safety_s)   ────┤
       T-20e (move-order) ────┼──► T-21 (v0.2 gate gauntlet, 200-match paired)
       T-20c (F8+F13)     ──► T-20d (BO) ──┘
       T-20f (opp spec)   ────┘
                                   │
                                   ▼
                          (v0.2 ships; dev-opponent-model T-24 unlocks
                           only when ≥10 live scrimmages exist per D-010)
```

Parallel-friendly:
- **Wave 1 (parallel):** T-20a, T-20b, T-20c, T-20e, T-20f — all independent code changes, no shared files except the documented test-file additions.
- **Wave 2 (serial, blocks on Wave 1):** T-20d — the BO harness must use the 9-feature heuristic (T-20c) and the lifted time ceiling (T-20a, because deeper search means different optimal weights). Starting BO on the 7-feature heuristic would waste the tuning budget.
- **Wave 3 (serial, blocks on Wave 2):** T-21 — the v0.2 gate gauntlet (BOT §10 T-21) runs 200 paired matches vs Yolanda and 200 vs FloorBot, writes `docs/tests/RESULTS_V02.md`.

**Critical path:** T-20c → T-20d → T-21. Estimated **8–12 h** (3–4 h for T-20c, 6–10 h for T-20d including BO wall-clock, 1 h for T-21 gate setup which is mostly paired_runner reuse).

**Parallel work the user can dispatch now:**
- One agent on T-20a + T-20b + T-20f (total 2.5–3.5 h).
- One agent on T-20e (1–2 h).
- One agent on T-20c (3–4 h).
All three finish in ~ 4 h wall-clock; T-20d launches against the merged state.

---

## §4 — Success metrics (v0.2 exit gate)

Gate passes iff **all** of the following are satisfied on `tools/paired_runner.py --limit-resources=True` (Windows fallback documented — the gate runs on Linux for authoritative measurement, per STATE T-17 note):

| Metric                                                                                                            | Gate                                               | Measured by                                                                 |
|-------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|-----------------------------------------------------------------------------|
| **v0.2 vs v0.1 paired win-rate**                                                                                  | ≥ **62 %** over 100 paired matches, p < 0.05        | `tools/paired_runner.py --agents RattleBot_v02 RattleBot --n 50`            |
| **v0.2 vs FloorBot paired win-rate** (the new floor)                                                              | ≥ **75 %** over 100 paired matches                  | `--agents RattleBot_v02 FloorBot --n 50`                                    |
| **v0.2 vs Yolanda paired win-rate** (regression guard)                                                            | ≥ **95 %** over 50 paired matches                   | `--agents RattleBot_v02 Yolanda --n 25`                                     |
| **Crash gate**                                                                                                    | 0 TIMEOUT, 0 INVALID_TURN, 0 CODE_CRASH over 200 matches | Aggregate from all paired runs above                                    |
| **TT hit-rate at depth 5–6**                                                                                      | ≥ 15 % average across 50 matches                    | `search.get_stats()` dumped by `paired_runner --log-search-stats`          |
| **Avg ID depth achieved**                                                                                         | ≥ **5.0** under `limit_resources=True`              | `search.get_stats()`; parallels T-SRCH-4 gate from BOT §5                   |
| **Leaf eval p99 timing**                                                                                          | ≤ 100 µs with 9 features                            | `tests/test_heuristic.py::test_per_call_timing` (existing)                  |
| **All pytests pass**                                                                                              | 34 + new tests = 40+ PASS                           | `PYTHONPATH="engine;3600-agents" python -m pytest 3600-agents/RattleBot/tests/ -v` |

**Why ≥ 62 % and not ≥ 65 %:** the D-010 gate (65 %/100 OR 58 %/200) is the **live-promotion** gate against FloorBot. The v0.2→v0.1 internal gate is about validating that the v0.2 changes are actually helping; a 62 % threshold gives us a Wilson 95 % lower bound of ~53 %, strongly-positive signal. 65 % would be over-tight for an internal gate.

**If any metric fails:** the v0.2 release is held and the specific task causing the regression is debugged. The v0.1 build remains the FloorBot-promotion candidate (`agent.py` unchanged).

---

## §5 — Tools needed

| Tool / Infra                    | Status                            | Action for v0.2                                                                                           |
|---------------------------------|-----------------------------------|-----------------------------------------------------------------------------------------------------------|
| `tools/paired_runner.py`        | Shipped T-17. Programmatic entry = `_run_pair` (line 181). | No changes needed for BO; BO imports `_run_pair` directly. Add `--log-search-stats` flag (T-20e).           |
| `tools/bo_tune.py`              | **New file for v0.2.**            | Write per T-20d spec above. ~200 LOC.                                                                    |
| `scikit-optimize`               | **NOT in `requirements.txt`.**    | Add line `scikit-optimize==0.10.2` to `requirements.txt`. Pin the version because upstream is unmaintained. |
| `3600-agents/RattleBot/weights.json` | **New artifact from T-20d.**    | Generated by BO harness. Committed to repo so submission zip includes it.                                 |
| `3600-agents/RattleBot/opp_model.py` | **New file for v0.2.**         | Interface only per T-20f. ~60 LOC, mostly type aliases and a stub registry.                              |
| `docs/tests/RESULTS_V02.md`     | **New doc from T-21.**            | Records the §4 gate evaluation. Auditor reads this during AUDIT_V02 (pre-v0.3 promotion audit).           |
| `docs/tests/SEARCH_STATS_V02.md` | **New doc from T-20e.**           | Records the post-fix TT / killer / history stats.                                                        |
| pytest `conftest.py` in `3600-agents/RattleBot/tests/` | Not yet present (AUDIT nit #8). | Add `sys.path.insert(0, ...)` so `python -m pytest` works without `PYTHONPATH` set. Low-value nit.      |

**Compute requirement for T-20d (BO wall-clock budget):**
- 25 trials × 40 matches/trial = 1000 matches.
- At 30 s/match on 1 core under `limit_resources=True`: 8.3 h sequential.
- At 4 cores parallel (user's local machine, typical dev laptop): ~ 2.5 h wall-clock.
- At 8 cores (stretch): ~ 1.5 h.
- Fits the BOT_STRATEGY §4 "6–10 h parallel BO" budget comfortably.

---

## §6 — Risk register for v0.2

Focused on new risks introduced by v0.2 changes. Existing risks from BOT_STRATEGY §9 remain in force.

| ID                       | Risk                                                                                        | Mitigation                                                                                                                 | Owner            |
|--------------------------|---------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|------------------|
| **R-V02-BO-OVERFIT**     | BO-tuned weights over-fit to FloorBot's evaluator and don't generalize to George/Albert.   | Cross-validate BO output against Yolanda (≥ 95 % gate, §4) and — if live-scrimmage infra exists by T-21 — against George. If gate fails, ship `w_init`. | dev-heuristic    |
| **R-V02-CEILING-LIFT**   | Lifting `_PER_TURN_CEILING_S` triggers a slow-path bug that shows up only at depth 5–6.     | Smoke test (T-20a) runs 20 matches at 6 s ceiling before the gate gauntlet. Any TIMEOUT reverts the ceiling to 3 s.       | dev-integrator   |
| **R-V02-F8-F13-BUGS**    | F8 and F13 compute wrong values on edge-case boards (corner, dead-end worker).             | Unit tests in `test_heuristic.py` for each feature, including corner-worker and empty-belief cases (p_0 is the fallback). | dev-heuristic    |
| **R-V02-SKOPT-DEPS**     | `scikit-optimize` 0.10.x has pinned upper bounds on `scipy` / `scikit-learn` that conflict with numpy 2.1.3. | Test install in a clean venv before writing `bo_tune.py`. If it breaks, swap to `bayesian-optimization==1.5.1`.          | dev-heuristic    |
| **R-V02-WEIGHTS-JSON**   | `weights.json` is not committed to the submission zip, so tournament loads `w_init` instead of tuned weights. | Add `weights.json` to the package at `3600-agents/RattleBot/weights.json`, add a `tests/test_weights_json_loaded.py` test asserting the loaded weights match the committed file. | dev-integrator   |
| **R-V02-MOVE-ORDER-REGRESSION** | T-20e "fix" introduces a bug that breaks ordering for hash-move or killer on rare boards. | Run the v0.1 pytest suite (34 tests) against v0.2 before the gate gauntlet. `test_ordered_moves_hash_move_promoted` is existing coverage. | dev-search       |
| **R-V02-OPP-MODEL-CREEP** | T-20f's interface tempts someone to start implementing a George-greedy before the T-24 precondition is met. | Explicit marker in `opp_model.py` docstring: `RuntimeError("T-24 suspended until ≥10 scrimmages per D-010")` if `get_model()` is called for anything other than `"self-play"`. | orchestrator     |

---

## §7 — v0.3 / v0.4 / v0.5 preview

Not detailed — this is a v0.2 addendum. One paragraph each for schedule sanity.

### v0.3
**Goal:** cross the D-010 promotion gate (≥ 65 %/100 vs FloorBot + crash gate + T-LIVE-1 + AUDIT_V03.md). Primary work: make/unmake optimization in `search.py` (BOT §3.3 v0.3 scope), first live upload via Chrome MCP (T-23), live scrimmage vs George (5) and Albert (3), auditor writes `AUDIT_V03.md`. If the FloorBot triage bug (task #24) is unfixed, v0.3 uploads may also hit LIVE-002-style `invalid` verdicts — mitigation is pre-upload triage. Expected ELO Δ: +50 to +100 over v0.2 (mostly from make/unmake buying +1 depth). ETA: T − 30 h.

### v0.4
**Goal:** beat Albert majority live. New heuristic features from BOT §3.4 v0.3+ scope (F15 SEARCH-aware term with `γ_info / γ_reset` per D-011), F13-prime opening-asymmetric center-control for first-6-ply handling (SYN §B19). Possible numba leaf compilation ONLY if flip-trigger §7 row 6 fires (leaf > 40 % wall-time). Endgame-tablebase stub for last 5 turns (exact search, fastest + 3–5 pp critical-path per CONTRARIAN_SCOPE §C-4). Expected ELO Δ: +40 to +80. ETA: T − 18 h.

### v0.5
**Goal:** beat Carrie, final submission. Opponent-exploit track (T-24 implementations — `george_greedy`, `carrie_greedy`) IF the ≥ 10-scrimmage precondition has been met by T − 24 h (D-010). Opening book for the first 4 plies (DEFERRED v0.5 per BOT §8 D18). Final submission activation at T − 6 h with orchestrator-confirmed partner-lock-in (R-PARTNER-01). Expected ELO Δ: +20 to +60. ETA: T − 6 h.

---

## §8 — End of addendum

**v0.2 summary:** 5 concrete tasks with expected combined ELO Δ of +100 to +200 (center +140), fitting the BOT_STRATEGY §4 v0.2 budget of 14 h dev + 6–10 h parallel BO. Every task has a measurable gate in §4 and a flip-trigger that reverts the change if the gate fails.

**Handoff:** after this doc lands, the team-lead should:
1. Spawn dev-integrator (T-20a + T-20b + T-20f, parallel) and dev-search (T-20e, parallel) and dev-heuristic (T-20c, parallel).
2. After all four complete, spawn dev-heuristic + tester-local (T-20d BO harness + gate).
3. After T-20d lands, spawn tester-local for T-21 gate gauntlet.
4. Auditor writes `AUDIT_V02.md` (pre-v0.3 review) based on RESULTS_V02.md.

**File paths produced/modified by v0.2:**
- `3600-agents/RattleBot/time_mgr.py` (T-20a, T-20b)
- `3600-agents/RattleBot/agent.py` (T-20a, T-20b, T-20f)
- `3600-agents/RattleBot/heuristic.py` (T-20c)
- `3600-agents/RattleBot/types.py` (T-20c — add `com_x/com_y`)
- `3600-agents/RattleBot/rat_belief.py` (T-20c — compute `com_x/com_y` in update)
- `3600-agents/RattleBot/search.py` (T-20e — stats counters; T-20f — opp_model hookup)
- `3600-agents/RattleBot/move_gen.py` (T-20e — ordering bug-fix if instrumentation reveals one)
- `3600-agents/RattleBot/opp_model.py` (T-20f — NEW)
- `3600-agents/RattleBot/weights.json` (T-20d — NEW, generated)
- `3600-agents/RattleBot/tests/*` (new tests for each task)
- `3600-agents/RattleBot/tests/conftest.py` (NEW, optional cleanup)
- `tools/bo_tune.py` (T-20d — NEW)
- `tools/paired_runner.py` (T-20e — `--log-search-stats` flag)
- `requirements.txt` (T-20d — add `scikit-optimize`)
- `docs/tests/RESULTS_V02.md` (T-21 — NEW)
- `docs/tests/SEARCH_STATS_V02.md` (T-20e — NEW)

**End of BOT_STRATEGY_V02_ADDENDUM.**
