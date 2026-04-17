# BOT_STRATEGY — Authoritative Strategic Plan for the Primary Competitive Bot

**Author:** strategy-architect
**Date:** 2026-04-16
**Status:** v1.0, pending red-team by strategy-contrarian (pipeline Phase 1 exit criterion).
**Scope:** `docs/plan/BOT_STRATEGY.md` per PIPELINE.md Phase 1 and TEAM_CHARTER.md §3.
**Inputs consulted:** `CLAUDE.md`, `docs/TEAM_CHARTER.md`, `docs/STATE.md`, `docs/PIPELINE.md`, `docs/DECISIONS.md`, `docs/GAME_SPEC.md`, `docs/research/SYNTHESIS.md` (primary), targeted reads of `docs/research/CONTRARIAN_SCOPE.md` §C-6 / §G-1.
**Citations:** `SYN §X` → SYNTHESIS.md section; `SPEC §X` → GAME_SPEC.md section; `CON §X` → CONTRARIAN_SCOPE.md.

**Target:** rank #1 on `bytefight.org/compete/cs3600_sp2026`, final ELO > Carrie's + 25-point safety margin, by 2026-04-19 23:59 (T-3.3 days from now).

---

## Section 1 — Executive summary

**Core architecture decision:** Expectiminimax-style α-β search with iterative deepening and a Zobrist transposition table, over a tree that treats the opponent as `min` and **does not** embed the rat position as a chance node — the rat is tracked by an external HMM forward filter and surfaces into leaf evaluation as belief-weighted potential. SEARCH is excluded from the in-tree move set and decided root-only by an EV/VoI gate.

**Component inventory (one line each):**

- `agent.py` — entry point, orchestrates belief update → root decision → move selection.
- `rat_belief.py` — float64 forward-filter HMM on the 64-cell grid; predict / sensor-update / opp-search-update / rat-capture-reset.
- `search.py` — α-β + iterative deepening + TT + killer/history heuristics; root-only SEARCH branch.
- `heuristic.py` — 9-feature linear leaf eval with Carrie-style cell-potential term (the 80→90% lever).
- `move_gen.py` — wrapper over `board.get_valid_moves`, adds ordering, pre-filters illegal carpets.
- `time_mgr.py` — adaptive iterative-deepening controller with 0.2 s safety + adaptive multipliers.
- `zobrist.py` — 64-bit hash keys over the 4 bitboards + two worker positions + parity + search-state.
- `types.py` — shared dataclasses (TTEntry, BeliefSummary, SearchStats).

**Honest grade-probability estimate under this plan (copy-updated from CON §D/§F-8 with small architect adjustments):**

| Threshold | Estimate | 95 % CI (subjective) |
|-----------|----------|----------------------|
| ≥ 70 % (beat George's ELO floor) | 0.92 | 0.85–0.97 |
| ≥ 80 % (beat Albert) | 0.58 | 0.40–0.75 |
| ≥ 90 % (beat Carrie) | 0.28 | 0.15–0.45 |

Deltas vs CON: +0.02 at the 70 % band because FloorBot is being built in parallel (grade-floor insurance per D-I below), +0.03 at the 90 % band because the CMA-ES tuning harness and opponent-specific exploit track are committed here rather than optional. Confidence intervals are wide because paired-match evaluation has not yet been run on any version of the bot — these estimates will be revised after the v0.2 ELO gate (see §4 milestone table).

**Risk-weighted escalation:** if by T-36 h we are not at or above Albert on paired live scrimmage, open the opponent-specific exploit track (CON §C-6) unconditionally, and if by T-24 h we are not tracking Carrie, freeze generic heuristic work and burn the remaining budget on exploit + endgame tablebase.

---

## Section 2 — Chosen architecture (walk of SYN §G)

For each of the 10 steps in SYN §G I commit a concrete decision. "Decision" is the normative choice; "Why" cites the evidence; "Flip trigger" names the falsifiable observation that would reverse it (cross-referenced with the matrix in §7).

### 2.0 — Insurance decision (SYN §G Step 0, D16, CON §C-1)

**Decision:** **YES** — ship FloorBot in parallel. FloorBot is a reactive/greedy no-tree bot built by `floor-bot-dev` per Task #9. It is the **baseline submission** that ships to bytefight.org by T-2.5 days (hour 12 of the build, i.e. 2026-04-17 ≈ midday). The primary bot (this document) runs on a parallel track. The active live submission only gets promoted from FloorBot to primary once primary beats FloorBot by ≥ 10 pp on a 100-match paired local run AND survives a 50-match `limit_resources=True` live scrimmage without crash or timeout.

**Why:** CON §C-1 grade-floor insurance argument — P(>70 %) jumps from ~0.85 to ~0.92 when a known-safe fallback exists. The opportunity cost is low because FloorBot is owned by a separate agent (not the dev-HMM / dev-search / dev-heuristic team). Downside is purely budget (~ ½ dev-day for integrator review of FloorBot's safety wrappers — addressed in §6).

**Flip trigger:** None — insurance is permanent even after primary ships, because primary could develop a late-breaking bug.

### 2.a — Search algorithm (SYN §G Step 1, D1)

**Decision:** **Expectiminimax with α-β pruning + iterative deepening + Zobrist transposition table.** No MCTS, no PUCT, no beam search.

**Why:**
- `SYN §B1, SEARCH §B.3` rate α-β+ID+TT 5/5 for this game shape (branching b ≈ 6.3–6.8 excluding SEARCH, ≈ 70 including all 64 SEARCH locations).
- 80-ply horizon is shallow; depth 6–8 pure Python is enough to matter (`SEARCH §H`, `SYN §A`).
- MCTS rejected: 50 k-nps pure-Python throughput (`SYN §A`) gives ~300 k simulations over 240 s split across 40 turns; UCT exploration on a 6-ply tree with b≈7 would under-sample late-game critical lines vs α-β+ID+TT (`SEARCH §B.5–B.8`).
- PUCT without a trained prior adds engineering for no gain; our only prior source would be the F2 heuristic itself, which α-β already exploits via move ordering.

**Note on terminology:** technically our tree is a **minimax with heuristic leaves that absorb expectation**. True expectiminimax would require a chance node at every ply where the rat moves. We don't do that (see 2.b); the expectation over rat positions is taken at the leaf via `belief @ cell_potential_vector`. Where we do have chance nodes is SEARCH outcomes (§2.d).

**Flip triggers** (one observation, one action — see §7 matrix):
- Leaf-eval profile > 40 % of wall-time AND numba yields ≥ 2× speedup → compile; push depth +1–2 plies. Unchanged algorithm.
- Reactive FloorBot wins ≥ 50 % paired vs primary at depth 4 under `limit_resources=True` → fundamental architecture re-think; promote reactive as primary (SYN §F row 1, CON §C-1).
- TT hit-rate < 5 % after 100 matches → drop hash-move tier but keep α-β+ID (`SYN §F` row 7).

### 2.b — Rat-as-chance-node vs belief-as-leaf-potential (SYN §G Step 1, D2)

**Decision:** **Belief-as-leaf-potential (the F.1c hybrid).** The rat's position is **not** a chance node inside the tree. We track a single belief vector `b: np.ndarray (64,) float64` externally, evolve it before we enter the tree, and pass summary statistics (see §2.h / D22) into every leaf for evaluation. Inside the tree, the only chance node is the SEARCH outcome branch (§2.d).

**How SEARCH moves interact with the tree:** SEARCH is **not a child in the tree's move generator** (B8, SEARCH §A.2). At the **root only**, we consider the root SEARCH option separately and compare `ValueOfRootSearch(loc*)` vs `BestNonSearchRootValue`, where:
- `loc* = argmax_s b(s)` for the max-belief objective (or weighted objective — see §2.d).
- `ValueOfRootSearch(loc*) = 6·b(loc*) − 2 + γ_info·ΔH(b | obs) − γ_reset·b(loc*)·H(p_0)` (from HEUR §H.3 F15, SYN §C3).
- `BestNonSearchRootValue = max over non-SEARCH root children of −αβ(child, depth − 1)` at the current iterative-deepening depth.
- The tree that produced `BestNonSearchRootValue` is evaluated against the current (pre-root-move) belief; we do **not** re-enter the tree with a hypothetical post-SEARCH belief. This is the "root-only, EV-gated" pattern (B8).

**Why belief-as-leaf and not in-tree chance:**
- Branching stays at ≈ 7 instead of × 64 at every rat-chance ply (`SYN §B9, SEARCH §F.1/F.2`).
- The rat-position distribution evolves as `predict(T)` regardless of who moves (`SYN §A`, `HMM §D.1`) — so its within-tree effect is symmetric and roughly cancels between max and min nodes. The claim is approximate but supported by HMM §F item 7: at depth ≤ 6 the predictive spread stays within ~3 % TV of `p_t` for the rat-in-tree-absent-action case.
- Known error case: **our own moves can create primes/carpets** which change `cell_type(s)` and therefore the *future* noise model the opponent would see (HMM §D.6). This second-order effect is **not** modeled in the leaf, because we don't simulate future sensor draws inside the tree. Heuristic compensates via F4 (opp_cell_potential) — not perfect but the best tradeoff at this depth.

**Provisional leaf-eval interface:**
- Leaf gets: `board_state`, `belief_summary: BeliefSummary` (see `types.py` in §3).
- `BeliefSummary` carries: `top8_cells: List[Tuple[Tuple[int,int], float]]`, `entropy: float`, `max_mass: float`, and a lazy-loaded full `belief: np.ndarray (64,)` for leaf features that need it.
- Leaf does NOT re-run `predict(T)` per-ply. The belief passed in is the belief *as if no further rat motion happened*, which is fine because the **leaf-value comparison is monotone in belief shift**: all leaves in the tree see the same pre-tree belief, so relative values are preserved. Absolute values are optimistic by O(entropy_drift), which the search doesn't care about.

**Flip trigger:** if in local ablation we see that opp-SEARCH threats matter (CON C6 / SYN §C7 — opponent captures rat > 40 % of games), re-introduce opponent's root SEARCH as an explicit chance node at min-nodes within depth ≤ 2 of root. This is a targeted patch, not a rewrite.

### 2.c — Heuristic family (SYN §G Step 4, D12, D13)

**Decision:** **F2, the 9-feature handcrafted linear heuristic with CMA-ES weight tuning.** No NN (F3 rejected for v1 per SYN §B2, HEUR §F.1–F.4, CON §C-1).

**Final feature list (names from HEUR §C; aliased to `heuristic.py` constants for clarity):**

1. **F1 — `score_diff`** = `player.points − opponent.points`. Weight must be large — this is the ground-truth objective.
2. **F3 — `prime_line_potential`** = Σ over each contiguous same-direction primed line of `(k × 0.7 + 0.3·(k+extendable_neighbors))·(carpet_points_table[k])` for `k` = line length. Captures "how many points can I roll away right now".
3. **F4 — `opp_prime_line_potential`** = same, but from opponent's workers. Sign is **negative** in the leaf.
4. **F5 — `cell_potential_sum`** = Σ over all SPACE cells `c` of `P(c)` (see Carrie formula below). This is the 80→90 % lever.
5. **F7 — `opp_cell_potential_sum`** = same, from opponent's perspective. Sign negative.
6. **F9 — `worker_mobility`** = count of non-SEARCH legal moves (`len(board.get_valid_moves(enemy=False, exclude_search=True))`). Proxy for "future optionality".
7. **F10 — `opp_mobility_denied`** = number of cells adjacent to `opp.position` that we have primed or carpeted. Proxy for carpet-deny pressure (SYN §A, CON §A-4).
8. **F11 — `rat_belief_max`** = `max(belief)` if belief defined — a bigger max means we have a mid-game +EV search. HEUR §B.2 calls this out as SEARCH-gating feature.
9. **F12 — `expected_search_ev_best`** = `max_s (6·b(s) − 2)` clamped at 0. Integral over the "best available search" as a latent value. Strongly correlated with F11 but includes the +EV threshold.

**F8 (belief entropy), F13 (center control), F15 (SEARCH chance-node-aware term), F16 (explicit opp-denial geometry):** scheduled v0.2+ stretch; not in v0.1 (see §4). Per SYN §B19 F13 is de-weighted because our spawn is already near center.

**Carrie-style cell-potential formula (HEUR §B.2, SYN §B4):**

```
P(c) = [best_roll_from_c + 0.3·second_best_roll_from_c]
       · (1 − 0.5·P_opp_first(c))
       / (1 + 0.3·dist(worker, c))
```

Where `best_roll_from_c` and `second_best_roll_from_c` are the top two values of `CARPET_POINTS_TABLE[k]` over the 4 cardinal rays from `c` of lengths `k ∈ 1..7`, constrained to the current primed/space pattern. `P_opp_first(c)` is 1 if opponent is closer to `c` by Manhattan distance, 0 if we are, 0.5 on tie; spawn-asymmetry correction per SYN §B19 maps center `x ∈ {3,4}` to 0.5 by default, own half to 0, opp half to 1 in opening turns (first 6 plies).

**Leaf score formula (commit):**

```
V(board, belief) =
    w[0]·F1 + w[1]·F3 − w[2]·F4 + w[3]·F5 − w[4]·F7
    + w[5]·F9 − w[6]·F10 + w[7]·F11 + w[8]·F12
```

Where `w[0..8]` are the 9 CMA-ES-tuned weights, bootstrapped from a hand-tuned initial vector (F1-proxy values: `w_init = [1.0, 0.6, 0.6, 0.25, 0.25, 0.05, 0.4, 1.2, 1.0]`). Tuning discipline is paired-match only (see §2.i, §5).

**Why linear and not NN:**
- 3-day deadline is an anti-pattern for NN-from-scratch (PRIOR §F anti-pattern 3, SYN §B2).
- ≤ 100 μs per eval in tournament mode (HEUR §H.2, SYN §B20) — a numpy vectorized 9-dot-product fits comfortably; a 3-layer MLP does not without careful compilation.
- CMA-ES converges on 9 dims in ~300 evaluations (HEUR §G.1); each evaluation = 50 paired matches = 5 CPU-min at pure-Python speeds. Achievable in our budget.

**Flip triggers:**
- CMA-ES converges to within 10 % of `w_init` → ship F1 hand-tuned, bank time (SYN §F row 9).
- F2 lands early AND wins cleanly → escalate to F3 small-NN stretch.
- Scrimmage shows endgame (turns 35–40) move quality sub-par → add F-endgame branch (SYN §F row 15).

### 2.d — SEARCH-move policy (SYN §G Step 2, D3, D4)

**Decision:** **Root-only SEARCH with hybrid objective.** SEARCH is evaluated once per turn at the root. It is chosen iff `V_SEARCH > V_BEST_NONSEARCH + ε_tiebreak`.

**Objective formula (commit, merging HMM §C.3 and HEUR §H.3 F15):**

```
V_SEARCH(loc) =
    6·b(loc) − 2                            # point EV (HMM §C.1)
    + γ_info · E[ΔH(b | obs_at_loc)]        # info value, on miss-branch only
    − γ_reset · b(loc) · H(p_0)             # belief-reset cost, on hit-branch only
```

With starting weights `γ_info = 0.3`, `γ_reset = 0.5`. `E[ΔH]` is the expected entropy reduction from the miss-branch update: `b' = renormalized(b * (cell ≠ loc))`; `H(p_0) ≈ 5.2 bits` (near-stationary, HMM §B.2).

**Search location choice:**
- Default `loc* = argmax_s b(s)` (max-belief, HMM §C.3 option a).
- **Override rule:** if `b(argmax) < 1/3` AND `turn_count < 60` (still mid-game), use `loc* = argmax_s E[ΔH(b | obs_at_s)]` (min-entropy-left, option b). This captures the VoI motivation that early in the game nothing is point-+EV but information harvesting might be (HMM §C.2, HEUR §E.2).
- Tie-break: if two cells have equal objective, prefer the one with shorter Manhattan distance to our worker (so the sensor ends up cheaper to read next turn — distance-likelihood is sharper at shorter range, SPEC §3.5).

**EV-gate threshold:** `ε_tiebreak = 0.25` (in point-units, leaf score scale). Rationale: CMA-ES-tuned weights will put F1 (score_diff) at weight ≈ 1.0, so 0.25 ≈ 1/4-point of heuristic preference for non-SEARCH, enough to avoid noise-triggered SEARCHes.

**No in-tree SEARCH at depth > 0.** Reason: including 64 SEARCH children at any internal node would explode branching to ~70 and destroy depth reachability (SYN §A, SEARCH §A.2). The root-only gate gives us the major point-EV opportunities without that cost.

**Flip triggers:**
- `max_p > 1/3` occurs < 3 times per average game → lower `ε_tiebreak` to 0.1 or widen the VoI override window (SYN §F row 4).
- Scrimmage logs show we are losing turns by searching when opp could have rolled big carpet instead → tighten `ε_tiebreak` upward OR add a "don't search if any of my primed lines ≥ 4 is rollable next turn" guard.

### 2.e — Time manager (SYN §G Step 3, D6)

**Decision:** **Adaptive iterative deepening with 0.2 s safety margin and per-turn adaptive multipliers.**

- **Base per-move budget:** `base_budget = time_left() / max(1, turns_left) − 0.05`. The `−0.05` is per-turn pessimism.
- **Adaptive multiplier:** classify the position by three signals:
  - `easy` (multiplier 0.6×): only 1 non-SEARCH valid move; OR the top move dominates by ≥ 4 points immediate delta.
  - `normal` (multiplier 1.0×): default.
  - `critical` (multiplier 1.6×): turn_count ∈ [60, 78] (endgame); OR `rat_belief_max > 0.33` (a search is point-+EV, must be careful); OR my primed-line ≥ 5 is rollable this turn (huge swing); OR opponent primed-line ≥ 5 is rollable this turn (must block/race).
- **Hard cap:** `min(2.5 × base_budget, time_left() − 0.2)`. 0.2 s is the safety margin for IPC jitter and final leaf (`extra_ret_time` is 5 s but that's IPC slack, not compute slack — SPEC §7).
- **Poll rate:** `time_left()` checked every 1024 node-expansions inside the ID loop (SEARCH §D.4). Also after each completed depth — if next depth's estimated cost (> 6× last depth's cost by branching-factor projection) exceeds remaining budget, exit early with the last-complete-depth result.
- **Hard stop in ms before engine deadline:** 200 ms. The `check_win` code deducts `player_worker.time_left -= timer` on return and a 0.5 s band is the tie-vs-loss boundary (SPEC §7 `check_win`) — 200 ms gives us safety against Python GC pauses and IPC serialization.
- **Endgame override:** last 5 turns get at least `max(base_budget, 3.0 s)` regardless of easy/critical, because endgame mistakes are unrecoverable (R-TIE plus the point table is super-linear).
- **Budget accounting:** `time_mgr` maintains a rolling estimate of "surplus so far = sum(base - actual) for t=0..turn-1" and reallocates surplus to later turns by raising their multipliers up to 2.5× cap.

**Why adaptive:**
- Flat 6 s/turn is too rigid: the average turn doesn't need 6 s but endgame chokepoints do (CON §C-4, HEUR §B).
- Too aggressive (flat 8 s on critical turns, 2 s else) risks tournament timeouts under `limit_resources=True` where nps could drop 20 % (SYN §A, SEARCH errata 2).

**Flip trigger:** tree-search times out in ≥ 2 / 50 matches → flat 5.5 s with hard cutoffs + 0.5 s reserve (SYN §F row 14).

### 2.f — Move ordering (SYN §G Step 6, D5)

**Decision:** **Ordering stack: hash-move (from TT) → killer[depth] → history[move] → type-priority → immediate-point-delta.**

Per-tier rationale:
1. **Hash-move first:** if this node's TT entry gives a best-move, try it first. Gives the best α-β cutoffs on TT hit (`SYN §B15, SEARCH §C`).
2. **Killer move (2 slots per depth):** moves that caused β-cutoffs at this depth in sibling subtrees. Classic chess trick; fits directly (`SEARCH §C`).
3. **History heuristic:** global score per `(move_type, direction, roll_length)` bucket updated on cutoffs. 2D 4×7 table = 28 counters per direction for CARPET rolls, 4 for PLAIN/PRIME.
4. **Type-priority:** CARPET (big roll first, so k=7 before k=2) → PRIME → PLAIN. Rationale: CARPETs are score-changing, PRIMEs are +1 and prep-work, PLAINs are mobility. This ordering exploits the super-linear CARPET table.
5. **Immediate-point-delta:** tiebreak by immediate score change (`move.move_type == CARPET: CARPET_POINTS_TABLE[k]; PRIME: +1; PLAIN: 0; SEARCH: filtered out at move-gen`).

**SEARCH is NOT in this order** — it's handled at root only (§2.d). Do not include 64 SEARCH children in the in-tree move list.

**Flip trigger:** TT hit-rate < 5 % → drop hash-move tier and rely on killer+history (SYN §F row 7).

### 2.g — TT hashing scheme (SYN §G Step 1, implied D-TT)

**Decision:** **Zobrist 64-bit hash over:**
- 4 × 64 random constants for `_space_mask`, `_primed_mask`, `_carpet_mask`, `_blocked_mask` cell states (one key per cell-state pair — XOR in if set).
- 2 × 64 random constants for player-worker position and opponent-worker position.
- 1 × 2 constants for `is_player_a_turn`.
- 2 × 65 random constants for `player_search.loc` and `opponent_search.loc` (65 = 64 cells + "None" sentinel).
- 2 × 2 constants for `player_search.result` and `opponent_search.result`.

Total Zobrist table size ≈ 4·64 + 2·64 + 2 + 2·65 + 4 = 392 u64 values = 3.1 KB. Precomputed in `zobrist.py` at `__init__`.

**Incremental update:** on `apply_move`, XOR out old state / XOR in new state. PLAIN: 2 worker-pos XORs. PRIME: 2 worker-pos + 2 cell-state (my cell: SPACE→PRIMED). CARPET k: 2 worker-pos + 2k cell-state (each cell PRIMED→CARPET). SEARCH: only search-state XOR + parity XOR.

**Caveat on masks:** the engine's masks are disjoint — exactly one bit set per cell across the 4 masks (SPEC §1). So "cell is PRIMED" = one Zobrist key. We do **not** XOR the full mask as an integer (would collide); we XOR per-cell-per-state-change.

**TT replacement policy:** "depth-preferred with always-replace backup" (two-slot scheme):
- Slot A: highest-depth entry ever seen for this key. Replace only if new depth ≥ old depth.
- Slot B: most recent entry regardless of depth. Always replace.
- Probe both slots; return hit from either.

**TT size:** 2^20 = 1 048 576 buckets × 2 slots × (8 B hash + 4 B depth + 2 B best_move + 4 B value + 1 B flag) ≈ 40 MB. Well under the 1.5 GB RSS cap (SPEC §7).

**TTEntry fields:**
- `hash: u64` (upper 44 bits stored, lower 20 are the index).
- `depth: u8`.
- `best_move: u16` (packed `move_type`:2 + `direction`:2 + `roll_length`:3 + `search_x`:3 + `search_y`:3).
- `value: float32`.
- `flag: u8` (EXACT / UPPER / LOWER enum).

**Flip trigger:** TT hit-rate < 5 % in profiling → reduce table size (saves init cost) OR drop the scheme and rely on killer+history only (SYN §F row 7).

### 2.h — Belief state (SYN §G Step 5, D14, D15, D22)

**Decision:** **`float64 np.ndarray` of shape `(64,)` (NOT 8×8 — flat 1-D to allow direct `b @ T` multiplication).** Precompute `p_0 = (e_{(0,0)} @ T^1000)` in `__init__`.

**Update order per turn (the canonical pipeline, HMM §E.3, SYN §B7/B17):**

For every ply, execute exactly this sequence in `rat_belief.update(board, sensor_data)`:

1. **predict(T)** — `b = b @ T`.
2. **opp-search-update** — if `board.opponent_search = (loc, result)`:
   - If `result is True`: **reset** `b = p_0.copy()`. The opponent just captured; rat has re-spawned with 1000 silent headstart. This is the **correct** post-capture prior (SYN §A, HMM §D.3, NOT `δ_{(0,0)}`).
   - Else if `loc is not None and result is False`: miss. Set `b[loc_idx] = 0.0`; renorm `b /= b.sum()`.
   - Else (`loc is None`): no-op (opp didn't search this ply).
3. **predict(T)** — second predict, because between the opp's turn-end and our sensor draw the rat moves again (SPEC §3.3, SYN §A, HMM §D.1). `b = b @ T`.
4. **sensor-update** — Bayesian update from our `sensor_data = (noise, est_dist)`:
   - For each cell `s` of the 64 cells: `L(s) = P(noise | cell_type(s)) · P(est_dist | |s − worker_pos|₁)`.
   - `b *= L`; `b /= b.sum()`.
   - **Re-read `cell_type(s)` every update** — do not cache (SYN §B17, HMM §D.6, because prime/carpet mutate during opp's move).

**Rat-capture-reset (my own SEARCH):**
- On successful SEARCH (we see `board.player_search = (loc, True)` on our next turn), reset `b = p_0.copy()` BEFORE step 1. The engine respawns the rat between our successful-search and our next turn.

**Noise likelihood table:**
- Precomputed in `__init__` as `NOISE_LIK: np.ndarray (3, 4)` where rows are Noise enum and cols are Cell enum. Exact values from SPEC §3.4.
- Distance likelihood: precompute `DIST_LIK: np.ndarray (max_dist+3,)` for each possible `actual` 0..14 → conditional P(est_dist | actual) for est_dist ∈ [max(0, actual−1), actual+2] with clamping handled per SPEC §3.5 (reported d=0 absorbs offsets −1 AND 0 when actual=1, so P(0|0) = 0.82 not 0.70 — HMM §A.2).
- Manhattan-distance LUT: precompute `MAN[64][64] = |x_i − x_j| + |y_i − y_j|` in `__init__` (4 KB).

**Float precision:** `float64`. HMM §F-1 allows float32 with per-turn renorm, but float64 removes one whole class of numerical-drift worry at negligible cost (64 cells, not 64 k). If later JAX/torch heuristic wants float32, we cast on the `BeliefSummary.belief` output.

**Interface to search:** `BeliefSummary` dataclass (§3 `types.py`) with:
- `belief: np.ndarray (64,) float64` — the full vector (cheap to pass by reference).
- `entropy: float` — `−Σ b·log(b+1e-12)` — cached, recomputed on every update.
- `max_mass: float` — `b.max()`.
- `argmax: int` — `b.argmax()`.
- `top8: List[Tuple[int, float]]` — precomputed (sorted top-8 by mass).

The search code calls leaf eval with a reference to this summary — O(1) to read max_mass/entropy, O(64) amortized for full-belief feature computation. Leaf is expected to use the summary for F11/F12 and NOT touch the full `belief` unless F5/F7 want a belief-weighted variant (v0.2 extension).

**Flip trigger:** profiling shows numeric drift (`|1 − b.sum()|` > 1e-9) or leaf eval becomes a bottleneck — move to log-space or float32 (SYN §F row — none yet; HMM §A.3).

### 2.i — Blocker-corner / spawn awareness (SYN §G Step 5 side-note, SPEC §10 item 7, CON §A-prime claim 3)

**Decision:** **Trust the accidental-safety invariant but add a `_safe_spawn_sanity()` guard in `agent.__init__`** that asserts `not board.is_cell_blocked(board.player_worker.position)` and **falls back to FloorBot behavior** if the assertion fails. This is a belt-and-suspenders move.

**Why:** Per SYN §A and CON §A-prime, the current shape-set `{(2,3), (3,2), (2,2)}` cannot actually produce a spawn-on-BLOCKED collision. But an engine update (adding a (3,3) shape, for example) would silently break us. The sanity check is O(1) and survives any shape-set change.

**Asymmetric spawn prior (SYN §B19):** in the leaf, `P_opp_first(c)` treats:
- Own-half columns (A: x∈{0,1,2,3}; B: x∈{4,5,6,7}) → `P_opp_first = 0`.
- Opponent's half → `P_opp_first = 1`.
- Middle columns (x∈{3,4}) → `P_opp_first = 0.5`.
This replaces the naive "closer-worker" heuristic for the first 6 plies; after turn 6, switch to pure Manhattan distance (by then workers have moved enough that spawn asymmetry washes out).

### 2.j — Opponent modeling (SYN §G Step 8, D8, D17, CON §C-6)

**Decision:** **Phase-5 optional track BUT elevated-priority and pre-scheduled.** Default for v0.1–v0.4: min-node uses our own F2 heuristic (self-play assumption, SYN §B3). Explicit George/Albert/Carrie models are v0.5 only, but **the dev-opponent-model task is spawned and budgeted starting at T-36 h regardless of whether v0.5 is reached**, so that if scrimmage data hits the exploit track trigger (SYN §F row 2 or 13) we have partial work already in progress.

**Arbitration between SYN §C7 positions:**
- HMM §D.4, SEARCH §F.3, HEUR §D.3 say Phase-5, nice-to-have — they are correct about **primary architecture** (the F2 linear heuristic already captures a lot of "don't let opp roll" via F4/F7/F10).
- CON §C-6 says highest-leverage alternative, P(beats Carrie) ≈ 0.25–0.35 — this is correct about **grade-ceiling** (a generic bot *might* beat Carrie; an opponent-specific bot *should*).
- The resolution: since generic v0.5 (pure generic against Carrie's heuristic) hits the 90 % threshold with P ≈ 0.28 (my estimate above), and opponent-specific adds ~5–10 pp on top, we can't afford to defer it entirely. But we also can't sabotage v0.1–v0.4 by diverting dev-search/dev-heuristic.
- **Compromise:** spawn `dev-opponent-model` as a new role (see §10) with a well-defined interface — it produces a drop-in replacement for the `min_node_estimator()` function in `search.py`, selected by a runtime flag `OPPONENT_MODEL ∈ {"self-play", "carrie_greedy", "george_greedy"}`. The primary search code doesn't care which is active.

**Flip triggers:**
- Lose > 70 % live vs Carrie → open Carrie-specific exploit as critical path (SYN §F row 13).
- Win vs Albert in scrimmage but lose > 20 % vs George → open George-specific pessimistic model (SYN §F row 2).
- Budget squeezed → drop opponent-model track entirely; ship generic v0.5.

---

## Section 3 — Module decomposition

Each module is specified with filepath (relative to `3600-agents/<our-bot-folder>/`), public interface, data structures, per-call time budget, dependencies, v0.1 scope, v0.2+ scope. **Bot folder name commits to `RattleBot` per STATE.md open loops.**

Target package layout (`3600-agents/RattleBot/`):

```
RattleBot/
├── __init__.py           # from .agent import PlayerAgent  (multi-file import fix, CLAUDE.md §4)
├── agent.py              # PlayerAgent entry point
├── rat_belief.py         # HMM tracker
├── search.py             # α-β + ID + TT
├── heuristic.py          # F2 linear eval
├── move_gen.py            # ordered move generation
├── time_mgr.py           # adaptive time controller
├── zobrist.py            # hash key tables + packing
└── types.py              # shared dataclasses
```

### 3.1 `agent.py` — the entry point

- **Classes:** `PlayerAgent`.
- **Signatures (exact per assignment contract, CLAUDE.md §4):**
  - `__init__(self, board: Board, transition_matrix: np.ndarray | jnp.ndarray = None, time_left: Callable = None)`.
  - `play(self, board: Board, sensor_data: Tuple[Noise, int], time_left: Callable) -> Move`.
  - `commentate(self) -> str`.
- **Init-time work (≤ 8 s of 10 s tournament init budget):**
  - Convert `transition_matrix` to `np.asarray(T, dtype=np.float64)` (SPEC §10 item 10 — JAX array incoming).
  - Compute `p_0 = iterative_multiply(e_{(0,0)}, T, 1000)` via 10 squarings (`T^2, T^4, …, T^1024`) then `e_0 @ T^1000 = e_0 @ (T^512 · T^256 · …)`. ~3 ms per HMM §B.5.
  - Precompute Zobrist tables (~ 3 KB of RNG draws).
  - Precompute distance-likelihood matrix and Manhattan LUT.
  - Precompute noise-likelihood table per cell-type.
  - Initialize `belief = p_0.copy()`.
  - Allocate TT (2^20 buckets, ~40 MB).
  - **No JAX JIT unless heuristic uses it.** If we do, force-warm by running a dummy `V_leaf(dummy_board, dummy_summary)` once to kill first-call latency (R-INIT-01).
- **Per-turn `play()` budget: ≤ `time_mgr.budget(turn)` (see §3.6).**
  - Phase 1 — `rat_belief.update(board, sensor_data)` — target ≤ 2 ms.
  - Phase 2 — `root_decide()`:
    - Call `search.alphabeta_id(board, belief_summary, budget)` — returns `(best_move, best_value)`.
    - Independently evaluate `V_SEARCH(argmax_b)` per §2.d.
    - Return whichever has higher value, clipped by `ε_tiebreak`.
  - Phase 3 — safety check: if `best_move is None` (search failed somehow), fall back to FloorBot logic: pick a random valid PLAIN move that doesn't walk onto a PRIMED cell. Defensive; never expected to fire.
- **Dependencies:** all other modules.
- **v0.1 scope:** full flow, self-play min-node, F2 with `w_init` weights (no CMA-ES yet).
- **v0.2 scope:** CMA-ES-tuned weights plug in from a `weights.json` file bundled in the zip.
- **v0.3+ scope:** runtime `OPPONENT_MODEL` flag switches min-node estimator; endgame-tablebase override in last 5 turns.

### 3.2 `rat_belief.py` — HMM tracker

- **Classes / functions:**
  - `class RatBelief:`
    - `__init__(self, T: np.ndarray, board: Board)`: store T, precompute `p_0`, noise LUT, distance LUT, Manhattan LUT, init `self.belief = p_0.copy()`.
    - `update(self, board: Board, sensor_data: Tuple[Noise, int]) -> BeliefSummary`.
    - `handle_post_capture_reset(self, captured_by_us: bool) -> None`: reset `self.belief = p_0.copy()`.
    - `summary(self) -> BeliefSummary`: cheap getter.
  - Module-level helpers: `_compute_p0(T, steps=1000) -> np.ndarray`, `_noise_likelihood_table() -> np.ndarray`, `_distance_likelihood_row(actual: int) -> np.ndarray`.
- **Data structures:**
  - `self.belief: np.ndarray (64,) float64`.
  - `self.p_0: np.ndarray (64,) float64` — immutable reference snapshot.
  - `self.T: np.ndarray (64, 64) float64`.
  - `self.noise_lik: np.ndarray (3, 4) float64` — rows Noise, cols Cell.
  - `self.dist_lik: Dict[int, np.ndarray (64,)]` — actual_dist → per-cell conditional likelihood. Actually precomputed as `DIST_LIK: np.ndarray (15, 15)` covering actual 0..14 and reported 0..14 (SPEC §3.5).
- **Time budget per `update`:** ≤ 2 ms (target 0.5 ms).
  - Two matrix-vector products: `2 × (64 × 64) ≈ 8 k FLOPs × 2 = 16 k` — sub-ms numpy.
  - One element-wise multiply `b *= L` over 64 cells.
  - Two renorms.
- **Dependencies:** numpy. Optionally `engine.game.enums` for Noise/Cell enums.
- **v0.1 scope:** full forward-filter, all 4 update cases (predict, opp-search-hit, opp-search-miss, sensor, self-capture-reset).
- **v0.2 scope:** vectorized `update_batch` for use inside speculative post-move belief updates if we ever want in-tree belief refinement.
- **Correctness hooks:**
  - `_safe_renorm(b)` asserts `b.sum() > 1e-12`; on failure, log and reset to `p_0` (defensive — should never fire given numerics).
  - Post-update `assert abs(self.belief.sum() − 1.0) < 1e-9`.
  - Tests (see §5): 100-turn traced game, reset on simulated capture returns belief to `p_0` within ε.

### 3.3 `search.py` — α-β + ID + TT

- **Classes / functions:**
  - `class SearchEngine:`
    - `__init__(self, tt_size: int = 1 << 20, heuristic: Callable, zobrist: ZobristTable)`.
    - `alphabeta_id(self, board: Board, belief_summary: BeliefSummary, time_manager: TimeManager) -> Tuple[Move, float]` — top-level ID loop.
    - `_alphabeta(self, board, depth, alpha, beta, belief_summary, is_maximizing, ply_from_root) -> float` — recursion.
    - `_order_moves(self, moves: List[Move], board: Board, depth: int, tt_entry: TTEntry | None) -> List[Move]`.
    - `_probe_tt(self, hash_key: int) -> TTEntry | None`.
    - `_store_tt(self, hash_key: int, depth: int, value: float, flag: int, best_move: Move) -> None`.
  - Module-level: `MATE_SCORE = 1e9`, `DRAW_SCORE = 0.0`.
- **Data structures:**
  - `self.tt: np.ndarray` — a structured array of 2 × tt_size entries (depth-preferred + always-replace).
  - `self.killer: np.ndarray (MAX_DEPTH=20, 2)` — packed u16 moves.
  - `self.history: Dict[MoveKey, int]` — move → cutoff count.
- **Per-call budget:** driven by `TimeManager.budget`; typical 2–6 s on a normal turn, 0.5–2 s on easy, up to `2.5 × base_budget` on critical.
- **Recursion structure (pseudocode, per SYN §G Step 6):**
  - `_alphabeta(board, depth, α, β, belief_summary, is_max, ply)`:
    - If `time_manager.should_stop()`: raise `StopIteration` (unwound at ID-top with a try/except).
    - TT probe: if hit and entry.depth ≥ depth, maybe return (with flag check).
    - If `depth == 0 or board.is_game_over()`: return `heuristic.V_leaf(board, belief_summary)`.
    - Generate moves via `move_gen.get_ordered_moves(board, is_max, tt_hit.best_move)`.
    - For each move (make/unmake pattern — see below):
      - `child_board = board.forecast_move(move, check_ok=False)` — but this allocates; see make/unmake below.
      - `child_board.reverse_perspective()`; **manually update `opponent_search / player_search` via deque-equivalent** (SYN §B18, SPEC §5).
      - `v = −_alphabeta(child_board, depth−1, −β, −α, belief_summary, not is_max, ply+1)` (negamax form).
      - α-β bookkeeping; if β-cutoff, record killer + history.
    - TT store.
- **Make/unmake optimization (R-FORECAST-GC):**
  - v0.1 uses `forecast_move` for correctness; GC pressure accepted (~ 10^4 copies/turn at depth 4).
  - v0.2 adds `search._make_move(board, move) -> Undo` and `search._unmake_move(board, undo)` that mutate in place and restore via stored diffs. ~ 3× throughput gain per SEARCH §I-6.
- **Dependencies:** `heuristic`, `move_gen`, `zobrist`, `types`.
- **v0.1 scope:** depth-fixed ID (deepens until time runs out), no make/unmake, simple move ordering (type-priority + immediate-delta only — no TT move yet, no killer yet).
- **v0.2 scope:** full TT + killer + history ordering stack.
- **v0.3+ scope:** make/unmake hot-loop; possible numba compilation of `_alphabeta` if profiling shows > 40 % wall-time (SYN §F row 6).

### 3.4 `heuristic.py` — evaluation function

- **Classes / functions:**
  - `class Heuristic:`
    - `__init__(self, weights: np.ndarray (9,) float64)`.
    - `V_leaf(self, board: Board, belief_summary: BeliefSummary) -> float`.
    - `set_weights(self, new_w: np.ndarray) -> None` — used by CMA-ES.
  - Private: `_f1_score_diff, _f3_prime_line, _f4_opp_prime_line, _f5_cell_potential_sum, _f7_opp_cell_potential_sum, _f9_mobility, _f10_opp_denial, _f11_belief_max, _f12_search_ev_best`.
  - Private helper: `_cell_potential(board, cell, worker_is_us, turn_count) -> float` — the Carrie formula.
- **Data structures:** weights vector; temporary feature vector per call.
- **Per-call budget: ≤ 100 μs** (SYN §B20). This is tight; implementation notes:
  - Vectorize F5/F7 across all 64 cells in one pass using precomputed direction rays; no per-cell Python loops.
  - F3/F4 prime-line scan uses bitmask tricks: find maximal runs of set bits along each row/column.
  - F9/F10 use the precomputed `get_valid_moves` + a cached "adjacent-to-opp" bitmask.
  - F11/F12 are O(1) on `BeliefSummary.max_mass`.
  - **Do not recompute `p_0` or belief here** — read `belief_summary`.
- **Dependencies:** numpy, `board` (via board.py interface), `types.BeliefSummary`.
- **v0.1 scope:** F1, F3, F4, F5, F7, F11, F12 only (the heavy hitters). F9, F10 added in v0.1.1.
- **v0.2 scope:** full 9-feature vector, CMA-ES-tuned weights loaded from `weights.json`.
- **v0.3+ scope:** F8 entropy, F13' opening-asymmetric center-control, F15 SEARCH-aware term.
- **Self-test:** unit tests compute F5 on hand-constructed boards and assert agreement with a pure-Python reference implementation to 1e-6.

### 3.5 `move_gen.py` — ordered move generation

- **Classes / functions:**
  - `get_ordered_moves(board: Board, is_max: bool, hash_move: Move | None, killer: Tuple[Move, Move] | None, history: Dict[MoveKey, int]) -> List[Move]`.
  - `get_root_moves_with_search(board: Board, belief_summary: BeliefSummary) -> Tuple[List[Move], Move | None]` — returns (non_search_moves, root_search_candidate_or_None).
  - `_filter_deny_opp_mobility(moves, board) -> List[Move]` — v0.2, prunes moves that give opponent a free carpet-deny.
- **Wrappers over `Board.get_valid_moves`:**
  - v0.1: call `board.get_valid_moves(enemy=False, exclude_search=True)` (SPEC §2, CLAUDE.md §7) then sort.
  - v0.2: pre-check with bitmask tricks to avoid allocating `List[Move]` for illegal moves; reconstruct only the survivors.
- **Data structures:** ordered list of Move objects.
- **Per-call budget: ≤ 200 μs at internal nodes** (excluded from the 100 μs leaf budget).
- **Dependencies:** `engine.game.board.Board`, `engine.game.move.Move`.
- **v0.1 scope:** type-priority + immediate-delta sort; use engine's `get_valid_moves`.
- **v0.2 scope:** add killer + history; pre-filter obviously-bad CARPET(k=1) unless it's the only move.
- **v0.3+ scope:** custom move generator bypassing `get_valid_moves` for hot path.

### 3.6 `time_mgr.py` — adaptive time controller

- **Classes / functions:**
  - `class TimeManager:`
    - `__init__(self, total_budget_s: float = 240.0 − 0.2)` — hard cap 0.2 s below engine timeout.
    - `start_turn(self, board: Board, time_left_fn: Callable[[], float]) -> float` — returns `turn_budget_s`.
    - `classify(self, board: Board, belief_summary: BeliefSummary) -> str` — "easy"|"normal"|"critical".
    - `should_stop(self) -> bool` — returns True if current elapsed ≥ turn_budget.
    - `remaining(self) -> float`.
    - `end_turn(self, actual_elapsed_s: float) -> None` — track surplus/deficit.
- **Data structures:** `self.cumulative_used: float`, `self.turn_budgets_planned: List[float]`, `self.classification_log: List[str]` (for post-match diagnostics).
- **Per-call budget:** negligible (O(1) per call; target < 10 μs per `should_stop`).
- **Dependencies:** `time.perf_counter`, `engine.game.board.Board`, `types.BeliefSummary`.
- **v0.1 scope:** simple base_budget = time_left / turns_left − 0.05; no classification (multiplier = 1.0).
- **v0.2 scope:** full easy/normal/critical classification + surplus rebalancing.
- **v0.3+ scope:** learned-classifier from local match data.

### 3.7 `zobrist.py` — hash keys

- **Classes / functions:**
  - `class ZobristTable:`
    - `__init__(self, seed: int = 0xBEEF1234)` — deterministic given seed; precompute all random u64 tables per §2.g spec.
    - `hash_from_scratch(self, board: Board) -> int`.
    - `xor_plain(self, old_hash, from_cell, to_cell, is_player_a) -> int`.
    - `xor_prime(self, old_hash, from_cell, to_cell, is_player_a) -> int`.
    - `xor_carpet(self, old_hash, direction, k, from_cell, is_player_a) -> int`.
    - `xor_search_update(self, old_hash, new_loc, new_result, acting_is_a) -> int`.
    - `xor_parity(self, old_hash) -> int`.
  - Move packing: `pack_move(m: Move) -> int (u16)`, `unpack_move(packed: int) -> Move`.
- **Data structures:** static u64 tables totaling ~ 3.1 KB.
- **Per-call budget:** each XOR op < 1 μs (numpy/int arithmetic).
- **Dependencies:** `engine.game.enums`, `engine.game.move`.
- **v0.1 scope:** tables + `hash_from_scratch` + PLAIN/PRIME/CARPET incremental XOR. Search-state XOR deferred.
- **v0.2 scope:** full SEARCH-state XOR + move packing for TT entries.

### 3.8 `types.py` — shared dataclasses

- `BeliefSummary`: `belief: np.ndarray (64,)`, `entropy: float`, `max_mass: float`, `argmax: int`, `top8: List[Tuple[int, float]]`. Immutable once computed per turn.
- `TTEntry`: `hash: int`, `depth: int`, `best_move_packed: int`, `value: float`, `flag: int` (EXACT=0, LOWER=1, UPPER=2).
- `Undo`: for future make/unmake — stores the diff to reverse an `apply_move` (mask bits changed, worker pos, points delta). v0.2+.
- `MoveKey`: `Tuple[int, int, int]` = `(move_type, direction, roll_length_or_search_idx)` — used as history-heuristic dict key.

Module is dependency-light (stdlib `dataclasses` + numpy).

---

## Section 4 — Phased build plan

**Time remaining at plan ratification:** assume ratification + contrarian review + arbitration completes by 2026-04-16 end-of-day → **T − 72 h to deadline**.

**Milestones and wave allocation:**

| Milestone | Target ELO goal | Build hours | Modules touched | Tests | Expected ELO delta | ETA |
|-----------|-----------------|-------------|-----------------|-------|---------------------|-----|
| **v0.1 — Playable skeleton** | Beats Yolanda ≥ 90 % on 50 paired matches | 10 h | agent.py, rat_belief.py (full), search.py (fixed-depth, no TT), heuristic.py (5 features: F1+F3+F4+F11+F12), move_gen.py (engine passthrough), time_mgr.py (trivial 5 s flat), zobrist.py (scratch hash only), types.py | §5 tests T-HMM-1, T-SRCH-1, T-HEUR-1, T-INT-1 | baseline; ≥ 1400 vs Yolanda self-play. | T − 62 h |
| **v0.2 — Beats Yolanda ≥ 95 %, beats George paired** | + 80–120 ELO over v0.1 | 14 h | search.py (TT + killer + history + ID), heuristic.py (add F5, F7, F9, F10), move_gen.py (ordered + deny-filter), time_mgr.py (adaptive multipliers), zobrist.py (incremental XOR). Begin CMA-ES tuning harness. | §5 tests T-SRCH-2/3, T-HEUR-2, T-TIME-1 | baseline vs Yolanda ≥ 95 %; vs George ≥ 55 % paired. | T − 48 h |
| **v0.3 — Beats George ≥ 70 % paired, FloorBot-beater** | + 50–100 ELO over v0.2 | 10 h | CMA-ES-tuned weights installed; search make/unmake; heuristic F8 (entropy) added; time-mgr surplus rebalancing. Live upload as candidate submission. | §5 tests T-HEUR-3, T-TIME-2, T-LIVE-1 | Shifts primary to bytefight.org as candidate (FloorBot stays as fallback). Vs George ≥ 70 % paired; vs Albert ≥ 40 % live scrimmage. | T − 30 h |
| **v0.4 — Beats Albert majority live** | + 40–80 ELO over v0.3 | 8 h | Heuristic F13' (opening-asymmetric), F15 (SEARCH-aware); possible numba leaf compilation; endgame-tablebase stub (last 5 turns exact). | §5 tests T-HEUR-4, T-SRCH-4, T-LIVE-2 | Vs Albert > 50 % live paired scrimmage. | T − 18 h |
| **v0.5 — Beats Carrie, #1 on leaderboard** | + 20–60 ELO over v0.4 | 10 h | Opponent-specific exploit track (CON §C-6) — Carrie-greedy and George-greedy min-node models; select via runtime flag. Possible opening book (6 turns max). | §5 tests T-LIVE-3, T-OPP-1 | Vs Carrie > 50 % live; final submission activation at T − 6 h. | T − 6 h |

**Parallelization of build waves:**

- v0.1 spawn concurrently: dev-hmm (rat_belief), dev-search (search+types+zobrist scratch), dev-heuristic (heuristic v0.1 features), dev-integrator (agent.py + time_mgr trivial). Expected collision: zobrist/move_gen — dev-integrator owns those. Integration point: end of v0.1 hour 10.
- v0.2 spawn: dev-search (TT + ordering), dev-heuristic (features + CMA-ES harness), tester-local (paired-match runner + ELO ledger). Auditor reviews concurrently.
- v0.3 spawn: tester-live (Chrome MCP upload + live scrimmage). Dev-integrator owns make/unmake. Tester-local runs 200-match paired gates.
- v0.4 spawn: dev-heuristic (F13', F15). If profiling shows > 40 % wall in leaf, dev-auditor spins up numba compile track.
- v0.5 spawn: dev-opponent-model (new role). Dev-integrator handles final-zip discipline (CON §E-7, SPEC §7).

**Exit criterion for each milestone** = passing BOTH the test gate in §5 AND the ELO gate in the table above on paired-match `limit_resources=True` local runs. A failure at any gate blocks promotion to the next milestone but does NOT block the other modules' internal development (we keep FloorBot as the live submission).

---

## Section 5 — Falsifiable success metrics

Each subsystem has a metric + threshold that defines "working". Failure to meet threshold is a falsification → the subsystem is re-scoped, not patched.

### T-HMM-1 — Belief tracker basic correctness (v0.1 gate)

- **Metric:** On a 100-turn traced game (scripted rat trajectory + sensor emissions reconstructed from `engine/game/rat.py`), after each turn `|belief.sum() − 1.0| < 1e-9` AND `argmax_rank(true_rat_cell)` is in the top-8 of `belief` on ≥ 60 % of turns past turn 10.
- **Owner:** dev-hmm.
- **Why this threshold:** 60 % top-8 is HMM-literature-consistent for our noise model; anything below is wasted mass.

### T-HMM-2 — Post-capture reset correctness (v0.1 gate)

- **Metric:** Simulate a successful own-SEARCH at turn `k`; the belief on turn `k+1` (after the reset pipeline) must equal `p_0` to within `TV < 1e-6`. Likewise for simulated opp-SEARCH success.
- **Owner:** dev-hmm.
- **Why:** SYN §R-HMM-01 classifies wrong reset as a **critical** risk (belief catastrophically drifts after a few post-capture turns).

### T-SRCH-1 — Search never illegal (v0.1 gate)

- **Metric:** 500 self-play matches vs Yolanda; number of games ended by INVALID_TURN or CODE_CRASH = 0.
- **Owner:** dev-search + dev-integrator.
- **Why:** SPEC §8 — either causes an immediate loss, so one such event kills the grade signal.

### T-SRCH-2 — Iterative-deepening monotonicity (v0.2 gate)

- **Metric:** On 100 fixed positions, depth `d+1` move value ≥ depth `d` move value minus `0.05` (leaf-noise tolerance). Violations indicate search bug.
- **Owner:** dev-search.

### T-SRCH-3 — TT hit-rate (v0.2 gate)

- **Metric:** Across 50 matches, average TT hit-rate ≥ 15 %. Below 5 % triggers SYN §F row 7 flip (drop hash-move tier).
- **Owner:** dev-search, audit by auditor.

### T-SRCH-4 — Depth reachability under tournament clock (v0.4 gate)

- **Metric:** With `limit_resources=True`, average ID depth achieved per turn ≥ 5.0. Falling below 4.0 triggers numba compilation track or algorithm re-evaluation.
- **Owner:** dev-search + tester-local.

### T-HEUR-1 — Feature computation correctness (v0.1 gate)

- **Metric:** Unit tests on hand-constructed boards; computed F1..F5 match reference pure-Python implementation to 1e-6. Run on 100 boards.
- **Owner:** dev-heuristic.

### T-HEUR-2 — Leaf budget (v0.2 gate)

- **Metric:** Average `V_leaf` call time ≤ 100 μs under `limit_resources=True` across a 10 000-position microbench. Stretch: ≤ 50 μs.
- **Owner:** dev-heuristic.

### T-HEUR-3 — CMA-ES convergence (v0.3 gate)

- **Metric:** CMA-ES tuning run of ~ 300 generations produces a weight vector whose paired ELO vs the `w_init` baseline is ≥ +30 ELO on 50 paired matches. If the tuned weights are within 10 % of `w_init` (SYN §F row 9), ship `w_init` and bank the budget.
- **Owner:** dev-heuristic + tester-local.

### T-HEUR-4 — Carrie exploit effectiveness (v0.4 gate, stretch)

- **Metric:** On 100 paired local matches **vs a locally-simulated Carrie-style bot** (implementation of Carrie's heuristic as documented in CLAUDE.md §5), F2 wins ≥ 55 %. Below 50 % triggers §F row 13 flip.
- **Owner:** dev-heuristic + dev-opponent-model.
- **Caveat:** we don't have Carrie's actual code. This is a proxy target. Live scrimmage data replaces it in v0.5.

### T-TIME-1 — No timeouts in v0.2 gauntlet (v0.2 gate)

- **Metric:** 200 matches vs George under `limit_resources=True`; 0 games lost to TIMEOUT.
- **Owner:** dev-integrator + tester-local.

### T-TIME-2 — Average turn budget utilization (v0.3 gate)

- **Metric:** Average per-turn wall-time used / available ∈ [0.6, 0.9]. Below 0.6 = wasting budget; above 0.9 = timeout risk.
- **Owner:** tester-local.

### T-INT-1 — Full end-to-end smoke (v0.1 gate)

- **Metric:** 20 runs of `python3 engine/run_local_agents.py RattleBot Yolanda` — zero crashes, zero timeouts, all runs produce valid game JSON with RattleBot as the winner in ≥ 18 / 20.
- **Owner:** dev-integrator + tester-local.

### T-LIVE-1 — First live scrimmage successful (v0.3 gate)

- **Metric:** v0.3 uploaded to bytefight.org via Chrome MCP; 5 live scrimmage matches vs George; no INVALID_TURN or TIMEOUT; win ≥ 3/5.
- **Owner:** tester-live.

### T-LIVE-2 — Albert-level (v0.4 gate)

- **Metric:** 20 live paired matches vs Albert; win-rate ≥ 50 %; ELO delta ≥ +10 over Albert.
- **Owner:** tester-live.

### T-LIVE-3 — Carrie-level (v0.5 gate = final)

- **Metric:** 20 live paired matches vs Carrie; win-rate ≥ 50 %; final ELO ≥ Carrie + 25.
- **Owner:** tester-live + orchestrator (arbitration).

### T-OPP-1 — Opponent-exploit track is +EV (v0.5 optional)

- **Metric:** Opponent-specific `OPPONENT_MODEL="carrie_greedy"` wins ≥ 5 pp more against simulated-Carrie than generic self-play min-node. If < 0 pp, revert to generic.
- **Owner:** dev-opponent-model.

---

## Section 6 — Floor-bot relationship

**FloorBot (Task #9) is being built by `floor-bot-dev` in parallel.** Primary bot (this doc) is a separate codebase. Interaction rules:

### 6.1 Activation policy on bytefight.org

- **T − 60 h (≈ v0.2 complete):** FloorBot is the **active live submission** on bytefight.org. Primary bot (RattleBot) is held as a local candidate only.
- **T − 30 h (≈ v0.3 complete):** If RattleBot v0.3 wins ≥ 60 % paired local vs FloorBot over 100 matches under `limit_resources=True`, AND zero crashes/timeouts over 200 matches, AND has scrimmaged successfully on bytefight.org (T-LIVE-1), promote RattleBot to live submission. Otherwise FloorBot stays live, RattleBot development continues.
- **T − 6 h final lockdown:** whichever bot has the higher verified live ELO against the reference set is the final submission. Tie-breaker: the more mature bot (fewer known bugs in the audit ledger).
- **Promotion is one-directional by default** — once RattleBot is live we don't demote to FloorBot unless a catastrophic regression is detected (e.g., a TIMEOUT in > 1 of 20 scrimmage matches). Demotion must be explicitly approved by the orchestrator per TEAM_CHARTER.md §4.

### 6.2 Safety inheritance from FloorBot

- **YES, with a specific interface.** RattleBot's `agent.py` **must import and embed FloorBot's `emergency_fallback(board) -> Move` function** (wrapped such that if FloorBot package is missing, a local copy of the function is used). This is the safety net for any `play()` call that fails: wrap the entire body in try/except; on exception return `emergency_fallback(board)`.
- The emergency_fallback contract: given a board, return a **valid, non-crashing move** within 10 ms. Implementation: pick the first legal `PLAIN` move in fixed direction order (UP, DOWN, LEFT, RIGHT per SPEC §10 item 13); if no PLAIN is legal, try PRIME in same order; if none, try CARPET(k=1) from each direction. If every move is illegal (impossible per game rules unless opponent blocks us in a dead-end), submit CARPET(UP, 1) and accept the INVALID_TURN — it's a lost game either way.
- **Defense in depth:** each subsystem (rat_belief, search, heuristic) also has a try/except at its public API that returns a safe default on failure (e.g., `rat_belief.update` returns the pre-update `BeliefSummary` on internal failure). This is belt-and-suspenders — the top-level `emergency_fallback` catches anything they miss.

### 6.3 Is FloorBot the default submission?

**YES until RattleBot v0.3 is verified.** This is the grade-floor insurance from CON §C-1 / SYN §F row 1. If RattleBot development catastrophically slips, FloorBot is still on the leaderboard earning a ≥ 70 % grade. The orchestrator has explicit veto power to revert to FloorBot at any time.

---

## Section 7 — Evidence-flipping matrix (verbatim from SYN §F)

Reproduced here so devs don't context-swap. These are the **pre-committed** triggers. Any agent observing one of these conditions MUST escalate to the strategy-architect (me) or orchestrator for arbitration before making the switch — but the default action is the switch.

| # | Observation (X) | Current default (Y) | Switch to (Z) | Source |
|---|------------------|---------------------|---------------|--------|
| 1 | Reactive-policy floor-bot wins ≥ 50 % paired vs our depth-4 α-β+ID+TT at matched budget. | α-β + ID + TT primary | Ship reactive as primary; add minimal lookahead only for endgame. | CON §C-1 |
| 2 | Our primary bot loses > 20 % to George in paired play. | Self-play heuristic assumption | Opponent-specific model (pessimistic or explicit George/Albert/Carrie predictor). | SEARCH §I-7; CON §C-6 |
| 3 | Local paired matches show 5 pp improvement but tournament scrimmage shows regression. | Trust local tuning | Re-run all tuning under `limit_resources=True`; drop any gain that doesn't survive. | CON §A-1 / E-1 |
| 4 | `max_p > 1/3` happens < 3 times per average game. | Root-only SEARCH gate | Add VoI-based info-gathering search threshold lower than 1/3 mid-game. | HMM §C.2 / C.4; HEUR §E.2 |
| 5 | Opponent captures rat > 40 % of games (belief-reset events frequent). | Passive belief tracking | Add opponent-belief predictor; prioritize denial-searches before their EV moves. | CON §C-6; HMM §D.4 |
| 6 | Leaf-eval profile > 40 % of wall time with > 2× speedup achievable. | Pure Python/numpy leaf | Compile with numba; push depth +1–2 plies. | SEARCH §I-6 |
| 7 | TT hit-rate < 5 % after 100 matches. | hash-move first in move order | Drop hash-move tier; promote killer/history. | SEARCH §I-4 |
| 8 | Our carpet-denials by opp > 1/game average. | Implicit blocking via F4 | Add explicit opp-parking-risk term to F5/F16 heuristic. | CON §A-4; HEUR §D.1 |
| 9 | F2 CMA-ES tuning converges to weights near F1 handcrafted (< 10 % drift). | CMA-ES tuned F2 | Ship F1; bank the tuning budget elsewhere. | HEUR §G.2 |
| 10 | JAX JIT warmup measured > 2 s in init. | JIT as-needed | Force warmup in `__init__` with dummy call; or replace JAX with numpy if budget squeezed. | CON §E-2 |
| 11 | Local 50-match batch tied but 200-match paired shows ≥ 5 pp. | 50-match go/no-go | Promote minimum-batch to 200 paired for finalist gates. | CON §B-3 |
| 12 | Games with `bigloop.pkl` (slow-mix) show belief-entropy persistently > 5 bits into mid-game. | Uniform across matrices | Matrix-specific early-game SEARCH policy; burn early VoI more aggressively. | HMM §B.2 / §B.3 |
| 13 | Live scrimmage vs Carrie specifically loses ≥ 70 %. | Generic tuning | Open 1-day opponent-specific exploit track targeting Carrie's "cell potential × distance" greed. | CON §C-6 / §D-2 |
| 14 | Tree-search times out in ≥ 2 / 50 matches. | Adaptive 0.6×/1.0×/1.6× allocator | Flat 5.5 s with hard ID cutoffs + 0.5 s reserve. | SEARCH §I-5 |
| 15 | Endgame turns 35–40 show sub-par heuristic move quality. | Heuristic leaf | Endgame exact-search branch (solve last 5–8 turns). | CON §C-4 |

---

## Section 8 — Explicit non-goals

Per CON guardrails, these are out of scope and MUST NOT be pursued without explicit orchestrator approval:

- **NO neural network trained from scratch.** F3 NN is a stretch (v0.4+ only) and even then must be ≤ 4-layer MLP fitting in 100 μs leaf budget. No RL, no self-play data pipeline (PRIOR §F anti-pattern 3).
- **NO network calls of any kind from the agent.** All lookups precomputed at init (SPEC §7 seccomp).
- **NO filesystem writes outside cwd.** No logging, no match traces. Debug via `commentate()` return strings only (SPEC §7).
- **NO MCTS rewrite unless v0.5 is insufficient by T − 12 h** — and even then, only with orchestrator approval and a contrarian re-review.
- **NO additional heuristic-features-for-features'-sake.** Features outside the 9 named must demonstrate ≥ +15 ELO in isolated ablation before entering the codebase.
- **NO particle filter** — 64 states; exact beats PF always (HMM §F-5, CON §G-1). The only exception is a PF over opponent-belief distributions in §2.j Phase-5 — still off by default.
- **NO offline hard-coding of T-derived tables** — T is per-game noisy (SPEC §3.1, CON §E-3). Recompute `p_0` in `__init__` every game.
- **NO reliance on local-benchmark timings without `limit_resources=True`** — (CON §A-1, §F-1). Any dev that runs a local bench without this flag is producing misleading data.
- **NO `__pycache__` / `.DS_Store` in the submission zip** — clean-zip discipline per CON §E-7, SPEC §7.
- **NO change to the architecture decision in §2 without a paired-match evidence trigger from §7.** This includes "I have a better idea" mid-stream. Evidence-first.
- **NO opening book for v0.1–v0.4.** Only considered for v0.5 if spare time remains (D18). 648 topologies at 6 plies each = non-trivial.
- **NO endgame tablebase wider than 5 turns** for v0.5. (D19) 5×7 plies at b≈7 ≈ 80 k positions — tractable. 8 turns isn't.
- **NO ISMCTS or PUCT. No beam search. No null-move pruning. No magic bitboards.** (SYN §B16, D10, D11).
- **NO partner-overwrite risk.** R-PARTNER: orchestrator MUST confirm with user (rahiljav@gmail.com) the partner-lock-in protocol before first live upload.

---

## Section 9 — Risk register + mitigations (de-duplicated, with owners)

Merged from SYN §E plus architect-identified new risks (marked **NEW**). Severity: Critical / High / Medium.

### Critical

| ID | Risk | Mitigation | Owner |
|----|------|-----------|-------|
| R-TIME-01 | Local-vs-tournament time budget gap (360 vs 240 s). | All local benchmarks use `limit_resources=True`. Tester-local's batch runner enforces the flag. Primary bot's `time_mgr` uses 240 − 0.2 s cap regardless of local env. | tester-local, dev-integrator |
| R-SEARCH-01 | `apply_move(SEARCH)` silent-no-op for points/belief; `forecast_move(SEARCH)` misleads. | Search code **never** calls `forecast_move(SEARCH)` — SEARCH is root-only and its effect is modeled manually in `V_SEARCH()`. Tests verify this via T-SRCH-1. | dev-search, dev-hmm |
| R-HMM-01 | Belief reset to wrong prior after rat capture. | Pipeline in §2.h step 2 (result=True → `b = p_0.copy()`). T-HMM-2 verifies. Code-review by auditor specifically checks this path. | dev-hmm |
| **NEW R-PARTNER-01** | Two-agent partnership submission overwrite. | Orchestrator MUST coordinate with user before each live upload. Partner is informed of our submission queue. Final-6-h lockdown requires explicit user confirmation. | orchestrator |
| **NEW R-SUBMISSION-01** | Final submission not activated before 2026-04-19 23:59. | T − 6 h checklist item; orchestrator automates a calendar reminder. Fallback: FloorBot stays active throughout — a slipped activation still grades at ≥ 70 %. | orchestrator, tester-live |

### High

| ID | Risk | Mitigation | Owner |
|----|------|-----------|-------|
| R-SANDBOX-01 | Seccomp not active in local default; imports that work locally may fail under `limit_resources=True`. | CI gate: at least one test per module runs under `limit_resources=True`. Final integration test is 50-match live scrimmage. | dev-integrator, tester-local |
| R-INIT-01 | JAX/JIT first-call burns 1–5 s of play clock. | `__init__` forces JIT warmup with a dummy `V_leaf()` call. If heuristic is pure numpy (default), no JAX is loaded at all. | dev-integrator |
| R-ARCH-BIAS | Research anchored on expectiminimax; alternatives partially evaluated. | Strategy-architect (this doc) explicitly considered and documented non-selected alternatives (§2.a). Strategy-contrarian will red-team the choice (Phase 1 pipeline). Evidence-flipping matrix row 1 triggers a re-consideration if reactive wins. | strategy-architect |
| R-EVAL-01 | 50-match unpaired has ±14 pp CI. | All evaluation uses paired matches (same T/spawn/seed per pair). Finalist gates are 200 paired matches. | tester-local |
| R-GRADE-FLOOR | No reactive fallback if primary fails. | FloorBot (Task #9) is active by T − 60 h. RattleBot embeds FloorBot's `emergency_fallback` as a try/except catch-all. | orchestrator, floor-bot-dev, dev-integrator |
| R-PERSP-01 | `reverse_perspective` swaps workers only; game tree must replicate deque-search swap. | Spec'd in §3.3 (`search.py`). Unit test T-SRCH-extra verifies searches consistent across 4 plies of simulated play. | dev-search |
| **NEW R-HEUR-INIT-01** | F2 CMA-ES weights not converged by v0.2 deadline. | v0.1 ships with `w_init` hand-tuned; v0.2 tries CMA-ES but falls back to `w_init` + manual tweak if gate misses. SYN §F row 9 codifies this. | dev-heuristic |
| **NEW R-DEV-COUPLING-01** | Dev-HMM and dev-search both modify belief-summary interface, cause drift. | `types.py` is owned by dev-integrator and changes require PR review. Interface is frozen at v0.1 end. | dev-integrator |

### Medium

| ID | Risk | Mitigation | Owner |
|----|------|-----------|-------|
| R-BELIEF-SYNC | `cell_type(s)` mutation not caught in likelihood table. | §2.h step 4 re-reads per update. Test T-HMM-1 covers multi-turn primed/carpet scenarios. | dev-hmm |
| R-FORECAST-GC | ~10^6 `forecast_move` copies / turn → GC pressure. | v0.1 accepts the cost; v0.2 migrates hot path to make/unmake. | dev-search |
| R-HEUR-BUDGET | Leaf > 100 μs under tournament clock. | Vectorized numpy per §3.4; profile gate T-HEUR-2. Numba compile if needed. | dev-heuristic, auditor |
| R-CARPET-DENY | Opp parks on our primed line. | F10 in heuristic; move_gen v0.2 can emit deny-weighted ordering. | dev-heuristic |
| R-SCRIM-BIAS | Live scrimmage ELO ≠ tournament ELO. | Per-opponent ELO ledger in `docs/tests/ELO_LEDGER.md`; avoid aggregate. | tester-live |
| R-ZIP | `__pycache__` etc. leak into zip. | Final-submission zip command spec'd in §2/§8. CI check scans zip contents. | dev-integrator |
| R-T-CACHE | Caching T-derived table off-disk breaks per-game noise. | All T-derived structures are computed in `__init__` only. Test asserts no module-level T-derived constant. | dev-hmm |
| R-TIE | Draw is 0.5 ELO; heuristic should prefer guaranteed tie over 40/60 gamble near endgame. | v0.4 adds "endgame tiebreak" heuristic tweak — when we're ahead on points with 5 turns left, penalize variance. | dev-heuristic |
| R-SPAWN-BLOCK | Spawn-on-BLOCKED latent bug. | `_safe_spawn_sanity` in §2.i + fallback. Doc-only note in GAME_SPEC. | dev-integrator |
| **NEW R-CMA-HARNESS-01** | CMA-ES harness mis-measures fitness (wrong baseline, non-paired). | Harness spec'd in §4 v0.2 milestone; uses paired-match infrastructure from tester-local. Auditor reviews the harness config. | dev-heuristic, auditor |
| **NEW R-TT-COLLISION-01** | Zobrist collision rate on 2^20 buckets may be nontrivial over 50 k-nps × 240 s. | Upper-44-bit hash stored per-entry to detect collisions; mismatched-hash probes are misses. Measured in T-SRCH-3. | dev-search |
| **NEW R-BELIEF-BUDGET** | `b @ T` with float64 numpy: if heuristic uses JAX the dtype mismatch causes silent transfers. | Force `np.asarray(T, dtype=np.float64)` in `__init__`. Heuristic stays numpy. | dev-hmm, dev-heuristic |

---

## Section 10 — Work breakdown for the next wave

The orchestrator should spawn the following tasks. Each is one-line title + short brief. IDs are suggestive; orchestrator assigns real IDs.

- **T-11 — strategy-contrarian: red-team BOT_STRATEGY.md.** Red-team this document. Find holes in §2 arbitrations, §4 milestone scheduling, §5 thresholds, §9 risk coverage. Output `docs/plan/CONTRARIAN_STRATEGY.md`. Blocks all dev work.
- **T-12 — dev-integrator: scaffold RattleBot package.** Create `3600-agents/RattleBot/{__init__.py, agent.py, types.py}` stubs per §3. Wire imports per CLAUDE.md §4. Ensure local smoke test `python3 engine/run_local_agents.py RattleBot Yolanda` runs without crash (even if RattleBot just returns a random PLAIN). Blocks T-13/T-14/T-15.
- **T-13 — dev-hmm: implement `rat_belief.py` v0.1.** Per §3.2. Pass T-HMM-1 and T-HMM-2 tests. Uses `float64`. Commit only after auditor sign-off.
- **T-14 — dev-search: implement `search.py` v0.1 + `zobrist.py` scratch hash + `move_gen.py` engine-passthrough.** Per §3.3, §3.5, §3.7. Fixed-depth α-β + ID, no TT yet. Passes T-SRCH-1.
- **T-15 — dev-heuristic: implement `heuristic.py` v0.1 (5 features).** Per §3.4. Feature set F1+F3+F4+F11+F12 with `w_init`. Passes T-HEUR-1.
- **T-16 — dev-integrator: complete `agent.py` and `time_mgr.py` v0.1.** Wire HMM → search → heuristic. Safety try/except with FloorBot fallback. Passes T-INT-1 gate.
- **T-17 — tester-local: build paired-match batch runner.** Takes 2 agent names + N + seed; outputs per-match JSON + ELO + CI. Enforces `limit_resources=True`. This is the ELO-measurement backbone of all subsequent gates. Blocks T-18 onward.
- **T-18 — auditor: v0.1 code review + benchmark.** Reviews T-12–T-16 output against this doc's §3 specs. Writes `docs/audit/AUDIT_V01.md`.
- **T-19 — dev-search: add TT + killer + history (v0.2 search).** Per §2.f, §2.g. Passes T-SRCH-2, T-SRCH-3.
- **T-20 — dev-heuristic: add F5, F7, F9, F10 + CMA-ES harness.** Passes T-HEUR-2, T-HEUR-3.
- **T-21 — tester-local: run v0.2 gate gauntlet.** 200 paired matches vs Yolanda, 200 paired vs George. Reports in `docs/tests/RESULTS_V02.md`.
- **T-22 — floor-bot-dev → dev-integrator: hand off FloorBot `emergency_fallback` interface.** Exposes the pure function for RattleBot to embed per §6.2.
- **T-23 — tester-live: v0.3 live upload + scrimmage.** Chrome MCP flow; 5 live matches vs George. Writes `docs/tests/ELO_LEDGER.md` first entry. Passes T-LIVE-1.
- **T-24 — dev-opponent-model: begin Carrie-greedy min-node estimator.** Pre-work for v0.5. Self-contained; doesn't block v0.3/v0.4 ship.
- **T-25 — dev-heuristic + dev-search: v0.4 improvements.** F13', F15, optional numba leaf, endgame-tablebase stub.
- **T-26 — tester-live: v0.5 live gate + opponent-exploit A/B.** Compares generic-v0.5 vs carrie-greedy-v0.5 under `OPPONENT_MODEL` flag. Passes T-LIVE-3 / T-OPP-1.
- **T-27 — orchestrator: final submission lockdown at T − 6 h.** Confirms with user. Activates the winning bot on bytefight.org. Screenshots leaderboard.

**Parallelization notes:** T-12 is a hard blocker. T-13, T-14, T-15 can run concurrently. T-16 blocks on all three. T-18 runs concurrently with T-19 onwards. T-22 can happen any time after FloorBot ships but must complete before T-19 ends (dev-integrator needs the fallback interface for the promotion criterion). T-24 is a side-track with its own budget.

---

## Appendix A — Cross-ref to SYN §D open architectural choices

For traceability. Each of D1–D22 from SYN §D is resolved or deferred here:

| SYN D# | Title | This doc's decision | Section |
|--------|-------|----------------------|---------|
| D1 | Backbone algorithm | α-β+ID+TT | §2.a |
| D2 | Rat chance-node model | Belief-as-leaf-potential | §2.b |
| D3 | SEARCH inclusion in tree | Root-only EV-gated | §2.d |
| D4 | Search-cell objective | Hybrid max-belief / min-entropy (HEUR F15 formula) | §2.d |
| D5 | Move ordering stack | hash → killer → history → type → delta | §2.f |
| D6 | Time allocation | Adaptive multipliers + 0.2 s safety | §2.e |
| D7 | Numba/Cython/JAX for leaf | Numpy first; profile; numba only if leaf > 40 % wall AND 2× speedup achievable | §2.c, §9 R-HEUR-BUDGET |
| D8 | Opponent model (tree side) | Self-play default; Carrie-greedy via runtime flag v0.5 | §2.j |
| D9 | Depth ceiling | d=16 | §3.3 MAX_DEPTH=20 (safety) |
| D10 | ISMCTS fallback | No | §8 |
| D11 | Beam-search pruning | No | §8 |
| D12 | Heuristic architecture | F2 9-feature linear + CMA-ES | §2.c |
| D13 | Feature-set granularity | 9 features listed in §2.c; F8/F13'/F15 scheduled v0.2+ | §2.c |
| D14 | Float precision (HMM) | float64 | §2.h |
| D15 | Log-space vs linear HMM | Linear with renorm | §2.h |
| D16 | Reactive floor-bot insurance | YES, live from T − 60 h | §2.0, §6 |
| D17 | Opponent-specific exploit track | Pre-scheduled T − 36 h; conditional promotion | §2.j |
| D18 | Opening book | Defer; v0.5 spare-time only | §8 |
| D19 | Endgame tablebase | v0.5 last-5-turns stub | §4, §8 |
| D20 | Matrix identification from T-samples | Skip | §8 |
| D21 | Paired-match evaluation | Use it | §5, §9 |
| D22 | HMM→search interface | Summary stats + lazy full-belief ref | §2.h, §3.8 |

---

## Appendix B — Commitments list (a dev-facing checklist)

The following are load-bearing numeric commitments. If any of these changes, this document needs an amendment:

- Agent folder name: `RattleBot`.
- Zobrist table size: 2^20 × 2-slot TT.
- TT entry: 19 B packed (8 hash + 1 depth + 2 move + 4 val + 1 flag + 3 pad).
- Belief dtype: `float64`, shape `(64,)`.
- `γ_info = 0.3`, `γ_reset = 0.5`, `ε_tiebreak = 0.25`.
- Time safety: 0.2 s before engine cutoff. Per-turn pessimism: 0.05 s.
- Adaptive multipliers: 0.6× / 1.0× / 1.6×, cap 2.5×.
- Node-expansion `time_left()` poll rate: every 1024 expansions.
- Heuristic leaf budget: ≤ 100 μs tournament mode.
- Feature count v0.1: 5 (F1, F3, F4, F11, F12). v0.2+: full 9.
- `w_init = [1.0, 0.6, 0.6, 0.25, 0.25, 0.05, 0.4, 1.2, 1.0]`.
- FloorBot promotion gate: RattleBot wins ≥ 60 % paired local vs FloorBot over 100 matches + 0 crashes/timeouts over 200 matches + live T-LIVE-1 pass.
- Paired-match finalist gate: 200 matches.
- Opp-exploit track spawn time: T − 36 h (unconditional).

---

**End of BOT_STRATEGY v1.0.**
