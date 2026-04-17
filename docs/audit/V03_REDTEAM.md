# V03_REDTEAM — RattleBot v0.3 Red-Team Pre-Ship Audit

**Auditor:** v03-contrarian (fresh eyes, no prior involvement with scope or strategy contrarian work)
**Date:** 2026-04-16 (T ≈ 3 days to final submission lock)
**Scope:** `3600-agents/RattleBot/{agent,heuristic,search,rat_belief,move_gen,time_mgr,zobrist,types,__init__}.py` at HEAD, against `docs/GAME_SPEC.md` + `docs/plan/BOT_STRATEGY.md` v1.1 + V03_ADDENDUM + V03_ADDENDUM_UPDATE_T20G + AUDIT_V01 + V01_LOSS_ANALYSIS + FLOORBOT_TRIAGE.
**Method:** Static read + cross-checked invariants against the engine source. No code changes made.

---

## §1 — Executive summary + verdict

**Verdict: YELLOW — CONDITIONAL GO.** One **HIGH** severity finding that silently degrades HMM belief after our own successful captures must be resolved (or knowingly accepted as a known-loss) before shipping. No **CRITICAL** findings — the try/except emergency fallback at `agent.py:164-167` contains any catastrophic pathway. Several **MEDIUM** findings are load-bearing for maximum-strength play but survivable if left.

**Severity tally:** 0 Critical, 1 High, 6 Medium, 7 Low.

**Top-3 concerns (must-read for team-lead):**
1. **HIGH: `RatBelief.update` never consumes `board.player_search`.** After our own successful SEARCH the engine respawns the rat to `p_0`, but our belief is not reset. It stays "stuck" on the pre-capture distribution and slowly re-aligns via sensor updates. This directly contradicts the rat_belief docstring ("Reads board.opponent_search AND board.player_search directly") and contradicts AUDIT_V01 §3.6 (which claimed the reset was wired). Concrete symptom: 2-5 turns of mis-aligned belief after every rat-catch — and since v0.3's SEARCH gate requires `max_mass > 1/3`, a stuck-belief burst right after a catch can re-trigger SEARCH on an already-respawned rat with wrong peak. Detailed evidence in §2.H-1 below.
2. **MEDIUM: `agent.py:223` accumulates `end_turn(0.0)`.** The `cumulative_used` / surplus accounting path never sees real wall time. The adaptive multiplier "surplus reallocation" described in the strategy doc is effectively dead code. Not a correctness risk; it means depth won't be redistributed across turns as designed, so peak time may pile up in a single endgame turn and trip TIMEOUT-adjacency.
3. **MEDIUM: TT cross-position collisions through turn_count exclusion.** The Zobrist key intentionally omits `turn_count` (T-20e) to lift hit-rate. Combined with the root TT entry always being stored as `EXACT`, a recent shallow result for the "same masks + positions + side" pattern at turn 20 can bleed into a depth-probe at turn 36, returning a stale exact value. The 2-slot TT mitigates this but does not eliminate it. In endgame this matters more than mid-game.

Three medium items endorsed as "seen, acceptable risk": the F3/F4 attribution approximation (known, AUDIT_V01 M-03), the double-safety-margin (AUDIT_V01 M-02, cosmetic), and the `__init__.py` pytest-path fragility (local-test only; tournament engine injects `game.*`).

---

## §2 — Findings by severity

Each finding has: file:line citation + symptom + suggested fix + ship/hold recommendation.

### CRITICAL

*None.*

### HIGH

#### H-1 — `RatBelief.update` ignores `board.player_search` (our own capture resets)

- **File:** `3600-agents/RattleBot/rat_belief.py:136-171`, docstring claim at `rat_belief.py:143`.
- **Symptom:** The canonical 4-step HMM pipeline only reads `board.opponent_search` in step 2. The post-capture-reset for OUR OWN SEARCH is not applied inside `update()`. The separate helper `handle_post_capture_reset()` exists (`rat_belief.py:228-230`) but **is never called from `agent.py`** (grep-verified — no call site in the package outside tests).
- **Engine protocol (GAME_SPEC §5):** On our turn after our last-turn SEARCH, `board.player_search = (loc, True)` if we caught it. The engine already respawned the rat with 1000 silent headstart — ground truth is exactly `p_0`.
- **Runtime effect:**
  - Step 1 (`b = b @ T`) advances our stale belief through opp's rat-move.
  - Step 2 consults `opponent_search` (likely `(None, False)` unless opp also searched) — no reset.
  - Step 3 (`b = b @ T`) advances again. Now `b` is `old_b @ T^2` plus maybe a zeroed cell if opp missed.
  - Step 4 (sensor update) Bayesian-updates against the TRUE new-rat noise.
  - Result: `b` slowly drifts toward the new rat location over 2-5 turns, but during that window our `max_mass`, `entropy`, and `argmax` (feeding F11/F12/F18, the SEARCH gate, and `root_search_decision`) are all wrong.
- **Why it hides in testing:** Under self-play (both sides caught the rat), the mirror-effect is symmetric — both sides have the same bug, so PAIRED metrics look fine. The test `test_apply_our_search_hit_resets_to_p0` (`tests/test_rat_belief.py:138-146`) calls the helper DIRECTLY, not via `update()`. It tests the helper, not the integration.
- **Worst-case scenario:**
  - We catch the rat at turn T. Belief has `max_mass = 0.85` at cell X (correct — that's why we searched).
  - Engine respawns to (0,0)+headstart; true rat is now distributed as `p_0`.
  - Turn T+2: our belief is still peaked near X (after 2 `predict(T)` + sensor update). Sensor is weak, so `max_mass` may still be > 1/3 near X.
  - SEARCH gate fires again on cell X, which is now cold. −2 pts.
  - Consecutive-miss guard (`SEARCH_GATE_MAX_CONSEC_MISSES=2`) stops the spiral at 2 misses, so **bounded damage ≈ −4 points per our-own capture**.
  - Expected frequency: if we capture 1–2 rats per game, this costs 4–8 pts per game in the worst case; better but still real.
- **Against stronger opponents** (Carrie) where wrong-SEARCHes have higher opportunity cost (we should have been priming / rolling instead), this could flip a close game.
- **Fix (≤ 10 LOC):** In `rat_belief.update()`, after the `skip_opp_phase` block and before step 3's predict, also apply our own last-turn search:
  ```python
  if not self._first_call:  # our prior ply can only be step-2-relevant after first call
      own_search = getattr(board, "player_search", (None, False))
      self._apply_search_result(own_search)
  ```
  Placement matters: per GAME_SPEC §5 the `player_search` tuple reflects the search we took 2 plies ago, AFTER which the engine respawned the rat; the respawn happened between our T+0 ply (the search) and our T+2 ply (now). The opp took one ply in between (generating step 1's predict and step 2's opp-search update). So the correct placement is AFTER step 2 and BEFORE step 3: the rat-move in step 3 then advances from the just-reset `p_0`. One extra 1 ms of work per turn; zero risk.
- **Ship recommendation:** **PATCH BEFORE SHIP.** 10 LOC + 2 test cases. If absolutely no bandwidth, accept as a known loss (~4 pts per captured-rat event), but flag the audit explicitly in AUDIT_V03.md.

### MEDIUM

#### M-1 — `agent.py:223` passes `0.0` elapsed-time to `time_mgr.end_turn`

- **File:** `3600-agents/RattleBot/agent.py:223`, consumer at `time_mgr.py:145-146`.
- **Symptom:** `self._time_mgr.end_turn(0.0)` unconditionally. The `cumulative_used` accumulator that was supposed to drive adaptive surplus-reallocation (BOT_STRATEGY §2.e) is permanently zero.
- **Effect:** The classifier + multiplier stack still works. What's dead: the strategy's "surplus from fast early turns reallocated to critical endgame turns via a surplus-aware multiplier cap." Currently every turn just gets `base × multiplier` bounded by the constant `per_turn_ceiling_s=6.0` (or 3.5× in endgame).
- **Side-effect:** `time_left()` returns real wall clock, not `cumulative_used`, so the `usable = time_left - safety_s` path is still correct. This is a monitoring/optimization gap, not a correctness bug.
- **Fix:** `agent.py:223` currently reads `self._time_mgr.end_turn(0.0)`. Should read:
  ```python
  elapsed = _time.perf_counter() - self._time_mgr._turn_start
  self._time_mgr.end_turn(elapsed)
  ```
  Or cleaner: have `time_mgr.end_turn()` compute elapsed internally from `_turn_start`. Either way, < 5 LOC.
- **Ship recommendation:** **DEFER TO v0.4.** Not on the path from GREEN to RED; addresses a dead-code optimization, not a live failure surface.

#### M-2 — TT Zobrist omits `turn_count` AND `opponent_search`/`player_search` state

- **File:** `3600-agents/RattleBot/zobrist.py:63-88`.
- **Symptom:** The hash includes cell masks + worker positions + side-to-move but NOT:
  1. `turn_count` (documented intentional omission per T-20e).
  2. `opponent_search`, `player_search` tuples.
- **For #2:** Since SEARCH is explicitly excluded from the in-tree move list (`_alphabeta` assertion at `search.py:352-354`), the search-tuple state cannot mutate along any tree path. So within a single tree-walk, omitting search-state is safe.
- **But cross-turn TT reuse** is where it bites: at turn T we store an EXACT value for some (masks, positions, side) triple. At turn T+2, the same triple can recur with a DIFFERENT `opponent_search` (opp did a SEARCH in between). The leaf eval at turn T+2 might compute a different F18 (`_opp_belief_entropy` depends on `board.opponent_search`). The TT returns the turn-T value anyway.
- **Magnitude:** F18's `W_INIT[13] = 0.1`, entropy swing ≤ `log(64) ≈ 4.16` nats → at most 0.4 leaf-value drift. Per-leaf, tiny. But aggregated across a deep search, it biases the result by O(0.4) — comparable to `eps_tiebreak = 0.25`, so it **can flip a SEARCH-vs-non-SEARCH decision** at the root.
- **For #1 (turn_count):** Similar argument — F13 (belief_com_distance) and F5 (cell_potential) depend on `turn_count` via `turns_left` which affects the F17 reachability filter (`_count_dead_primes`). Re-using a TT entry from turn 20 for a lookup at turn 36 can mis-value F17 by 1-2 counts (weight −0.4 each).
- **Fix options (low-risk pick-one):**
  - (a) XOR `turn_count // 2` back into the key (reverts T-20e's optimization; kills hit-rate). Rejected.
  - (b) Only exclude `turn_count` at internal nodes; for root-level probe, include `turn_count`. Mid-complexity.
  - (c) Accept the bound leakage as the price of the 15-pp TT hit-rate lift. Document in AUDIT_V03.md.
- **Ship recommendation:** **DEFER to v0.4 / ACCEPT.** The flip-scenario requires a rare exact-mask-recurrence across turns with different F17/F18. Self-play over 50+ matches would have detected this if it were a first-order bug. Document explicitly.

#### M-3 — `root_search_decision` re-probes TT for `best_value` — may be a BOUND, not EXACT

- **File:** `3600-agents/RattleBot/search.py:430-435`, also AUDIT_V01 low-table entry #4.
- **Symptom:**
  ```python
  best_move = self.iterative_deepen(...)
  root_key = self.zobrist.hash(board)
  entry = self._probe_tt(root_key)
  best_value = entry.value if entry is not None else 0.0
  ```
  If `iterative_deepen`'s last completed iteration stored a `LOWER` or `UPPER` bound at root (e.g., because a later iteration was interrupted by `_TimeUp` mid-traversal AND the TT was written by the interrupted iteration's incomplete alpha-beta path), `entry.value` is a bound.
- **Check:** `_root_search` (line 272-273) always stores `TT_FLAG_EXACT` at root after processing all moves. So on normal completion the stored value is EXACT. However, the interior `_alphabeta` (line 392-397) stores UPPER/LOWER/EXACT based on alpha-beta window — and these entries can land at the root's hash during later iterations if an interior node happens to have the same hash (cross-depth collision via omitted turn_count). Low probability but nonzero.
- **Also:** the best_value retrieved is from the deepest completed iteration's `_root_search`, which did use the full (−MATE, +MATE) window, so even EXACT values are valid. **This is sound in normal operation.**
- **Edge case:** If `_TimeUp` fires inside the very first iteration (depth=1) — possible if the budget is tiny — `last_depth_reached` stays 0 but `best_move = legal[0]` from the initial fallback. The TT probe may find nothing at root. Code returns `best_value = 0.0`, which compares equal to F1=0 initial heuristic. SEARCH's `ev > best_value + 0.25` gate will then fire a SEARCH whenever `ev > 0.25` — an over-eager SEARCH mode on super-tight time budgets.
- **Fix (≤ 5 LOC):** Plumb `best_value` out of `iterative_deepen` directly (it already computed it internally). AUDIT_V01 already flagged this as "One-line refactor."
- **Ship recommendation:** **DEFER to v0.4.** Operationally stable; only mis-behaves on 1-ply budgets.

#### M-4 — `_opp_belief_entropy` returns the same value at every leaf in a tree

- **File:** `3600-agents/RattleBot/heuristic.py:770-836`.
- **Symptom:** F18 (`_opp_belief_entropy`) reads `board.opponent_search` and the (IMMUTABLE) `belief_summary.belief`. Inside the tree:
  - `board.opponent_search` does not mutate (SEARCH excluded from moves; `apply_move` does not touch these fields for non-SEARCH moves).
  - `belief_summary.belief` is the pre-tree snapshot (belief-as-leaf-potential, frozen per the design).
  - Therefore F18 is **identical at every leaf in a single `iterative_deepen` call**.
- **Consequence:** F18 acts as a per-turn constant bias on the root value, not a discriminative signal. The leaf-level weighted feature adds `W_INIT[13] * H_opp` to every child's V, which is just a constant offset — useless for discriminating between moves. Practically F18 contributes zero to in-tree move selection.
- **Note:** F18 does affect the SEARCH-vs-non-SEARCH comparison at the root, because the `best_value` from the tree has F18 baked in, but the SEARCH EV from `_best_search_ev` does not include F18. So F18 imposes a one-sided tax on non-SEARCH moves when opp-belief entropy is high (which is correlated with "opp isn't about to catch the rat," i.e. we have time to prime).
- **Design bug vs implementation bug:** Per the docstring ("v0.4+ flag: richer multi-ply history tracker"), this is a **design placeholder** known to be weak. Not a correctness failure — just a lower-value feature than the weight `0.1` suggests.
- **Fix:** Either (a) move F18 out of the leaf and into a root-only gate (so it's compared apples-to-apples against SEARCH EV), or (b) tune `W_INIT[13] = 0` for now and ship it as a "known-no-op." BO will converge to ≈0 anyway given the constant-per-tree property.
- **Ship recommendation:** **SHIP AS-IS.** Feature is a no-op for in-tree ordering; BO can zero it out.

#### M-5 — F17 `_count_dead_primes` is O(64) per leaf under a hot loop

- **File:** `3600-agents/RattleBot/heuristic.py:727-767`.
- **Symptom:** F17 iterates all 64 cells, for each primed cell does 4 adjacency checks. Pure Python. Not numba-compiled. With depth 14-15 at 6 s and ~50 k nps, this is called ~300 k times per turn.
- **Measurement needed:** Current docstring claims p99 ≤ 200 µs at 14 features. If F17 adds 5-10 µs per leaf, a 5% perf regression on the leaf eval knocks ≈ 0.3 ply off the reachable depth (per SEARCH_PROFILE's "each 2× speedup = +1 ply").
- **Observation:** F17 depends on `turn_count` (via `turns_left`), which feeds the reachability filter. Cached through `_cell_potential_vector_cached` is NOT used here — F17 has its own cost. It also can't be trivially cached on the 4-mask key because `turns_left` changes every ply and F17 isn't in the cached path.
- **Design note:** F17 was a v0.3.1 addition (T-30b). No specific profile delta was measured. SEARCH_PROFILE.md predates F17.
- **Fix (optional):** (a) numba-compile alongside the other 3 kernels (pattern already established; consistent signature). (b) Fold F17 evaluation to the 8 primed cells only rather than 64-cell iteration (typical mid-game ≤ 8 primes; saves 56 iterations per leaf).
- **Ship recommendation:** **SHIP AS-IS but measure.** Add a p99 leaf-timing gate to AUDIT_V03.md's test list. If p99 > 250 µs post-v0.3.1, numba-compile F17 for v0.4.

#### M-6 — Numba init-time cost eats into `init_timeout=10 s` under ephemeral filesystem

- **File:** `3600-agents/RattleBot/heuristic.py:941-961` (`warm_numba_kernels`), `agent.py:134` triggers it.
- **Symptom:** `warm_numba_kernels()` forces AOT compile of 3 kernels. First call is cold: ~1-2 s per kernel per STATE.md's measurement = 953 ms cold total. With disk-cache hit (`__pycache__/*.nbi`), subsequent calls < 10 ms.
- **Risk A:** Tournament sandbox may have an ephemeral filesystem (fresh extract per match, or per-team process). If so, the disk cache never warms — cold-start every match. 1.5-2 s of the 10 s init_timeout. Still under budget, but tight.
- **Risk B:** Numba version skew. Tournament Python is 3.12 (SPEC §6). Our `requirements.txt` has numba pinned against our local version. If the tournament has a different numba minor (e.g., 0.59.0 vs our 0.60.0), the `__pycache__/*.nbi` cache is marked invalid and a recompile happens → same cold-start as Risk A.
- **Risk C:** If `import numba` raises (e.g., numba removed from the tournament requirements.txt, or JIT LLVM fails), the try/except at `heuristic.py:133-143` catches `ImportError` only. A non-ImportError failure during numba import (e.g., `RuntimeError: LLVM not found`) would propagate out and crash `heuristic.Heuristic.__init__`, which crashes `PlayerAgent.__init__`, which sets `self._init_ok = False` via the outer try/except at `agent.py:137-140`. Emergency-fallback is then the only play — but it still returns valid moves. Graceful degrade works.
- **Risk D:** Numpy 2.x ABI skew. Our code uses `np.uint64` bitmask ops (`heuristic.py:322, 338, 497`). Numpy 1.x and 2.x differ on integer type-promotion rules for `np.uint64 & python_int`. The numba kernels explicitly `np.uint64(1) << np.uint64(idx)` so they're internally consistent, but the Python-side dispatcher `heuristic.py:338` does `np.uint64(mask_blockers)` which assumes mask_blockers is a python int. Under numpy 2.x this should still work (np.uint64 constructor accepts Python ints).
- **Ship recommendation:** **SHIP WITH RUNTIME FALLBACK TESTED.** Specifically: before final submission, run the local test suite with `RATTLEBOT_NUMBA=0` env var to confirm the pure-Python path works correctly. If tournament init_timeout breaches are observed after upload, set `RATTLEBOT_NUMBA=0` and re-upload (depth drops 15-16 → 13-14 but bot ships cleanly). STATE.md already confirms 67/67 tests pass with both numba flags.

### LOW

#### L-1 — `agent.py` identity-T fallback belief freezes stationary

- **File:** `3600-agents/RattleBot/agent.py:124-127`. If `transition_matrix is None`, T is `np.eye(64)`.
- **Symptom:** Belief won't evolve — `b @ T = b`. Tournament always provides T, so this path is unreachable in production. Test-only.
- **Fix:** Document in docstring; no code change needed.
- **Ship recommendation:** SHIP AS-IS.

#### L-2 — `_safe_renorm` fall-back to `p_0` on zero-sum can mask bugs

- **File:** `3600-agents/RattleBot/rat_belief.py:216-223`.
- **Symptom:** When belief sum drops below `1e-18` (e.g., sensor update zeroed all cells), falls back to `p_0`. This hides a model-specification error (sensor likelihood inconsistent with belief). A silent reset means the HMM can quietly "recover" from an upstream bug without signaling.
- **Ship recommendation:** SHIP AS-IS; add telemetry counter in v0.4.

#### L-3 — `commentate()` exposes `per_turn_ceiling_s` — harmless but leaks version metadata

- **File:** `3600-agents/RattleBot/agent.py:142-151`.
- **Ship recommendation:** SHIP AS-IS. No info leak risk vs opponents.

#### L-4 — `zobrist.py:83` `opp_pos` XOR has no bounds check for opp=None

- **File:** `3600-agents/RattleBot/zobrist.py:83-84`.
- **Symptom:** Bounds check is `if 0 <= ox < 8 and 0 <= oy < 8`. If opp.position is a tuple outside bounds (corrupted state), the XOR is skipped — resulting in a hash collision with "no-opp" states. In practice the engine guarantees positions are in-bounds; this is defensive-only.
- **Ship recommendation:** SHIP AS-IS.

#### L-5 — `Zobrist.incremental_update` is unused (make/unmake deferred)

- **File:** `3600-agents/RattleBot/zobrist.py:90-92`.
- **Ship recommendation:** SHIP AS-IS. Documented future use.

#### L-6 — `_floor_choose` returns `prime_moves[0]` / `plain_moves[0]` without ordering

- **File:** `3600-agents/RattleBot/agent.py:300-306`.
- **Symptom:** Emergency-fallback picks the first PRIME / PLAIN move unordered. Could pick a strictly-dominated move (e.g., prime into a corner). Survivable — it's a crash-proof fallback, strength is not its job.
- **Ship recommendation:** SHIP AS-IS.

#### L-7 — No test covers `play()` catching a forced exception (AUDIT_V01 §3.10 item 3 unresolved)

- **File:** Coverage gap — `tests/test_t20f.py` covers the SEARCH-gate fix but not the forced-exception emergency-fallback path.
- **Ship recommendation:** SHIP AS-IS; trivially addable in v0.4.

---

### Red-team dimensions — what I specifically probed

#### Section A — Adversarial exploits of the heuristic

- **SEARCH-gate's 3-condition check** — the entropy ceil `0.75 * ln(64) ≈ 3.12 nats` is the tightest of the three. An opponent cannot directly manipulate our entropy (they don't touch the rat). They CAN manipulate the cell-type landscape via priming/carpeting near the rat's likely cells, which affects the noise model and therefore indirectly the sensor update that builds entropy. But the effect is weak and symmetric. **No exploit found.**
- **F17 priming-lockout** — could opp park their worker between us and our primes to flip many into "dead" (unreachable via Manhattan ≤ turns_left)? Checked: F17's reachability test is `|px-wx| + |py-wy| ≤ turns_left`, Manhattan only — it ignores blockers entirely. So an opp parking in the middle of our path does NOT flip our primes to "dead" via F17. F17 is robust against this.
- **F18 opp-belief-proxy** — could a deliberately-weird search pattern from opponent mislead us? Yes, but F18 is constant-per-tree (M-4 above), so it doesn't discriminate. Zero in-tree exploit surface.
- **Multi-scale kernels F14/F15/F16 mutual consistency** — they share the `_cell_potential_vector` P(c) but apply different decay shapes. They can pull in contradictory directions when `_KERNEL_STEP` cuts off at d=5 but `_KERNEL_EXP` has ~10% weight at d=5. BO is supposed to reallocate mass; until BO RUN2 lands, `W_INIT` values are small (0.1-0.15) and differences wash out.

#### Section B — Numba + tournament-sandbox interaction

Covered in M-6 above. Key risks: cold-start (under budget), ABI skew (runtime fallback via try/except), Numpy interop (local pass). Ship-ready with `_USE_NUMBA=True` default and `RATTLEBOT_NUMBA=0` emergency override.

#### Section C — Rat-belief edge cases

- **Near-degenerate T** (rat stuck in a blocked pocket): `_compute_p0` iterates `T^1000`. If T has an absorbing state, `p_0` concentrates there. Subsequent `predict(T)` loops forever on that state. `_safe_renorm` catches zero-sum. **No bug** — HMM is designed to handle degenerate transitions.
- **Opp catches rat 3+ times:** Each capture triggers `_apply_search_result(opp_search)` with `result=True` → `belief = p_0.copy()`. Multiple captures in a row just re-reset. **No bug.**
- **Noise enum out-of-range:** `_NOISE_LIK[int(noise), cell_types]` indexes directly. If `noise` is 3+ (not a real Noise enum value), numpy raises IndexError → outer try/except in `play()` → emergency_fallback. **Graceful.**
- **est_distance = 0 (rat under us):** `_MANHATTAN[worker_idx]` has true_dist = 0 at own cell. `_DIST_LIK[0, 0] = 0.70 + 0.12 = 0.82` (clamp). Cell under us gets the 0.82 weight. Sensor update is mathematically correct.
- **H-1 (above):** Our own SEARCH captures never reset belief. The ONLY legit rat-belief bug found.

#### Section D — Search correctness

- **`forecast_move` deep-copy under T-20g opts:** The `valid_search_moves` tuple cache is shared across copies. A child board sees the same tuple reference. Since our code never mutates that tuple, this is safe. `board.get_valid_moves(exclude_search=True)` does not touch the search-cache tuple.
- **Zobrist turn_count omission (T-20e):** Covered by M-2. Trade-off accepted; document.
- **Move ordering stack invariant** (`assert all(m.move_type != MoveType.SEARCH)`, `search.py:352-354`): always-on, tested (AUDIT_V01 §3.1). **Sound.**
- **TT 2-slot depth-preferred:** Slot 0 is depth-preferred, slot 1 always-replace. Both slots probed on hit via `_probe_tt`. Collision between different positions is handled by `zobrist_key == key` full-key check at probe time (`search.py:161-164`). **Correctness-sound.**
- **`_probe_tt` counter behavior:** `tt_hits` counts all matches (including stale same-hash-different-state, though the full-key check eliminates this). The `tt_cutoffs` counter increments only if alpha-beta window closes — correct.

#### Section E — Time management under pressure

- **Endgame multiplier chain:** at turns_left=5, critical classification (`turns_left ≤ 4` is the classify rule, so turns_left=5 is NOT critical by classify's own rule — it's the endgame-cap lift that catches turns_left ≤ 5). Wait: re-read `time_mgr.py:129`: `if turns_left <= 4: return "critical"`. But `ENDGAME_TURNS_THRESHOLD = 5` lifts the cap at turns_left ≤ 5. So at turns_left=5, classify returns "normal" (mult=1.0), endgame branch lifts cap to 3.5× base but `mult < cap_mult` so mult is bumped up to 3.5. Budget = `base * 3.5`. If `time_left = 50 s, turns_left = 5`, `base = (50-0.5)/5 = 9.9`, `budget = 9.9 * 3.5 = 34.65 s`, then `per_turn_ceiling_s = 6.0` caps it — so **endgame budget is hard-capped at 6 s per turn** unless `per_turn_ceiling_s` was raised. **The endgame 3.5× multiplier is DEAD CODE** because the 6 s ceiling ALWAYS wins at mult ≥ 0.6 × base where base > 1.7 s (typical).
- **To confirm:** `base` at turns_left=5 with 40 s remaining is `(40−0.5)/5 = 7.9 s`. `budget = base × 3.5 = 27.65 s`. Then `if budget > per_turn_ceiling_s: budget = 6.0`. So endgame turns get 6 s, same as any other turn.
- **Severity of endgame-multiplier dead-code:** T-30d expected +10-20 ELO from this. If `per_turn_ceiling_s` is not raised in endgame, the feature ships with 0 ELO gain. **This is a MEDIUM finding I initially missed; adding as M-7 below.**
- **Adaptive multiplier "critical" detection:** `classify` triggers "critical" on `max_mass >= 0.35`. Opponent cannot directly manipulate our max_mass — it's a property of OUR belief + sensor data. They CAN reduce our sensor quality by manipulating the cell type near the rat's likely location, but that's second-order. **No exploit.**

#### M-7 (added from Section E analysis) — Endgame multiplier (T-30d) masked by per_turn_ceiling_s

- **File:** `3600-agents/RattleBot/time_mgr.py:104-113`.
- **Symptom:** `in_endgame` branch lifts mult/cap to 3.5×, but the subsequent `if budget > self.per_turn_ceiling_s: budget = self.per_turn_ceiling_s` (line 112-113) hard-caps at 6 s. At typical endgame `base = 5-10 s`, `base × 3.5 = 17.5-35 s`, all capped to 6 s — same as non-endgame.
- **Fix:** Make `per_turn_ceiling_s` adaptive: `ceiling = max(per_turn_ceiling_s, base * ENDGAME_HARD_CAP_MULT) if in_endgame else per_turn_ceiling_s`. Or simply bypass the ceiling in endgame: `if not in_endgame and budget > per_turn_ceiling_s: budget = per_turn_ceiling_s`. ≤ 5 LOC.
- **Ship recommendation:** **PATCH BEFORE SHIP if budget permits.** +10-20 ELO was budgeted for T-30d; as coded, it yields ~0.

#### Section F — Score computation

- Terminal scale `(points_diff) × 10_000`: if `points_diff = 0` at turn 80, terminal returns 0. A mid-game leaf with flat features also returns ~0. These are numerically indistinguishable. **Cosmetic.** The engine's `is_game_over()` gate short-circuits so this only matters if a non-terminal leaf just happens to evaluate to 0 exactly — negligible.
- Negative score diff on terminal: propagates correctly through sign.

#### Section G — Combinatorial pin

- **Can opp pin us into a corner?** Engine prevents opp from occupying our cell. So the minimal pin is 3 adjacent blocked cells + opp on the 4th. We can still SEARCH (in-bounds = valid). We can also CARPET if we have primed cells in some ray. If we have no primes AND all 4 neighbors are blocked/opp/primed: `get_valid_moves(exclude_search=True)` returns `[]`. `iterative_deepen` at line 214-218 handles this: falls back to `exclude_search=False`, picks `legal[0]` — first SEARCH in the ordered list. Valid.
- **Emergency fallback** also handles this correctly — ultimate terminal is `Move.search((0,0))`, which is always valid.
- **No failure mode found.**

#### Section H — Cheap-to-fix items

Summary of cheap fixes worth doing before ship:
- **H-1 (RatBelief our-capture reset)**: 10 LOC, HIGH severity.
- **M-7 (endgame ceiling)**: 5 LOC, MEDIUM severity, material ELO gain.
- Total effort: < 1 hour for both patches + 1 test each.

---

## §3 — Items endorsed (code I reviewed and believe is sound)

1. **`_floor_choose` / `_emergency_fallback` chain** (`agent.py:263-306`). Four-tier fallback ends at `Move.search((0,0))` which is unconditionally valid per GAME_SPEC §2.4. Matches FLOORBOT_TRIAGE.md's gold-standard pattern. Sound.
2. **SEARCH-gate three-condition check** (`agent.py:195-199`). Correctly addresses V01_LOSS_ANALYSIS root cause #2. Consecutive-miss counter + entropy ceiling + mass floor all necessary.
3. **`_update_consec_search_misses`** (`agent.py:226-252`) — robust to the engine's (None, False) sentinel, defensive against `board.player_search` being unexpectedly malformed. Good.
4. **Zobrist construction, hash sensitivity, collision rate** (AUDIT_V01 §3.4) — 3 passing tests at 10 000 collisions measured 0.00%. Sound.
5. **HMM first-turn guard** (AUDIT_V01 §3.2) — sequence trace matches engine protocol exactly.
6. **Numba kill-switch + pure-Python fallback** (`heuristic.py:130-143`). Both paths tested in CI per STATE.md (67/67 tests both flags).
7. **k=1 CARPET filter in `move_gen.ordered_moves`** (`move_gen.py:122-123`). Correctly addresses V01_LOSS_ANALYSIS root cause #1 — k=1 only emitted when no non-k=1 exists. Sound.
8. **SEARCH-not-in-tree assertion** (`search.py:352-354`). Load-bearing invariant, always-on, tested. Endorsed.
9. **`_apply_search_result` correctness** (`rat_belief.py:173-185`) — miss zeros-and-renorms; hit resets to `p_0`. The helper itself is correct. Only the integration in `update()` is incomplete (H-1).
10. **Terminal short-circuit in `evaluate`** (`heuristic.py:918-921`) — TERMINAL_SCALE = 1e4 dominates. Sound.
11. **HARD_CAP_MULT = 2.5 in TimeManager** — correctly implements strategy doc.
12. **`iterative_deepen` safety margin** (`search.py:208-209`) — 0.5 s reserve matches GAME_SPEC §7 tie-vs-loss band. Sound.
13. **TT 2-slot depth-preferred + always-replace** — matches BOT_STRATEGY §2.g exactly. Sound.
14. **`is_game_over()` checks in search** (`search.py:320`) — correctly short-circuits terminal nodes.
15. **`W_INIT` sign conventions** — all feature signs match semantic direction (F1 positive for our-advantage, F11 negative to drive SEARCH gate, etc.).

---

## §4 — Recommended v0.4 backlog

Items too costly (or too risky) to fix pre-deadline. Ordered by expected ELO-per-hour:

1. **M-1 Fix `end_turn(0.0)` surplus accumulator.** 5 LOC + 1 test. **+5-15 ELO** (enables adaptive reallocation). Trivial.
2. **M-4 Redesign F18 to be root-only.** Move `_opp_belief_entropy` out of leaf into `root_search_decision`. **+0 in-tree, ~ +2 SEARCH EV accuracy.** Low ROI.
3. **M-5 Numba-compile `_count_dead_primes`.** Follow the established pattern. **+0.3 ply ≈ +10-20 ELO.** Medium effort.
4. **M-3 Plumb best_value through `iterative_deepen` return.** 5-line refactor. **+0 unless time budgets very tight.**
5. **make/unmake move (was T-30c, demoted).** 6 h, +0.6 ply ≈ +20-30 ELO on top of numba. Consider post-deadline.
6. **Full `BeliefSummary.belief` usage by F5** (AUDIT_V01 §5 item 4). Per-cell belief weighting on cell_potential. **+10-20 ELO.** Medium effort.
7. **Multi-ply opp-search history tracker** (enables richer F18). **Unknown ROI.** Medium.
8. **In-process integration test** covering 80-ply self-play. **Catches regressions in CI.** Low ROI pre-deadline.

Post-deadline polish candidates:
- Opening book (deferred by TABLEBASE §A.6 research)
- Endgame tablebase (deferred to time_mgr tweak)
- Opponent-specific min-node models (gated on live scrimmage data, D-010)

---

## §5 — What was NOT checked and why

1. **Full BO tuning pipeline correctness (bo_tune.py).** Out of scope — v0.3 ships with W_INIT if BO doesn't land. Audit-coverage is owned by dev-heuristic.
2. **Live tournament sandbox simulation** (WSL Linux, seccomp, limit_resources=True). Out of scope — owned by tester-local / T-30a (#50, in progress). Red-team here is static only.
3. **Paired match result variance under the sandbox.** No local match runs performed — no change to runtime behavior, audit-only.
4. **`_batch_smoke.py` / `conftest.py` harness paths.** Covered in AUDIT_V01 §3.11 harness note; unchanged since.
5. **Engine-side bugs** (e.g., the `generate_spawns` spawn-on-blocked possibility from SPEC §1). These are engine-provided constraints we must live with; mitigation is our `_safe_spawn_sanity` (already present in strategy, and spawn-cell SEARCH is always valid regardless).
6. **`commentate()` return types.** Not load-bearing.
7. **Memory profiling of the TT** at 2^20 × 2 slots × ~40 bytes/entry. ~40 MB steady-state per strategy budget. Well under the 1536 MB RSS cap per SPEC §7. Not re-measured.
8. **Alternative opponent strategies** (e.g., an opponent that deliberately plays within a narrow band to manipulate our F14/F15/F16 weighting). Out of scope; opponent-modeling is v0.5 per D-010 precondition.

---

## §6 — Final recommendation to team-lead

**GO with two patches:** (a) H-1 our-own-capture belief reset (10 LOC), and (b) M-7 endgame-ceiling bypass (5 LOC). Both are <30 minutes of work with low risk and targeted tests. After patches land, re-run the full `3600-agents/RattleBot/tests/` suite (must stay at 67-74+ green) and then the v0.3 gate gauntlet per V03_ADDENDUM §8.

**If patches cannot be made:** ship as-is with AUDIT_V03.md explicitly noting H-1 and M-7 as **known-loss items** (expected −4 pts per our-own capture, expected ~0 from T-30d when it was budgeted for +10-20). Net grade impact is modest but real — still likely above the Albert tier (80%) but could flip close Carrie-tier games.

**Hard hold:** none — no CRITICAL findings.

**End of V03_REDTEAM.**
