# SYNTHESIS — Consolidated Wave-1 Research Briefing

**Author:** research-synthesizer
**Date:** 2026-04-16
**Status:** Decision-ready. Strategy-Architect should be able to read ONLY this + `docs/GAME_SPEC.md` to produce `BOT_STRATEGY.md`.
**Inputs synthesized:** `CLAUDE.md`, `docs/TEAM_CHARTER.md`, `docs/STATE.md`, `docs/PIPELINE.md`, `docs/DECISIONS.md`, `docs/GAME_SPEC.md`, `docs/research/RESEARCH_HMM_RAT.md` (HMM), `docs/research/RESEARCH_ADVERSARIAL.md` (SEARCH), `docs/research/RESEARCH_PRIOR_ART.md` (PRIOR), `docs/research/RESEARCH_HEURISTIC.md` (HEUR), `docs/research/CONTRARIAN_SCOPE.md` (CON).

Citation convention: `HMM §X`, `SEARCH §X`, `PRIOR §X`, `HEUR §X`, `CON §X`, `SPEC §X`.

---

## Section A — Agreed facts (cross-confirmed across docs)

Ground-truth facts stated consistently in ≥ 2 docs. These are load-bearing for planning.

**Game mechanics**

- **Total plies:** 80 (40 per player). Board 8×8. Corner blockers random from `{2×3, 3×2, 2×2}` per corner. (`SPEC §1`, `CLAUDE.md §1`)
- **Tournament time budget = 240 s total (not per-move)**, across 40 moves → 6 s/move mean. Local dev budget is 360 s, a 50 % gap — **all local benchmarking must use `limit_resources=True` or divide by 1.5**. (`SPEC §7 / §10 item 5`; `HMM §-`; `SEARCH §A.5 / errata 2`; `HEUR §H.2`; `CON §A-1 / E-1 / F-1`)
- **Init budget:** 10 s tournament / 20 s local (separate from play). (`SPEC §7`; `CON §E-5`)
- **Memory cap:** 1.5 GB RSS (not 200 MB — that's zip size). (`SPEC §7/§10 item 22`; `CON §A-9`)
- **Spawn geometry:** A is always `x ∈ {2,3}`, B mirrored at `(7-x, y)`, same `y ∈ {2..5}`. NOT uniform over inner 4×4. (`SPEC §1 / §10 item 7`; `HEUR §H.1`; `CON §A-2`)
- **Spawn-on-BLOCKED:** code-level vulnerability exists; no defensive check. With current `{2×3, 3×2, 2×2}` shape set, **cannot actually collide** — engine is accidentally safe. No defensive code needed. (`SPEC §1 / §10 item 17`; `CON §A-prime claim 3`)

**Rat / HMM**

- **Transition matrix T**: row-stochastic 64×64, passed to `__init__` as JAX float32, drawn per-game from one of four base `.pkl` files with ±10 % multiplicative noise row-renormalized. Zero-pattern preserved. **Re-compute per game; never cache T-derived tables offline.** (`SPEC §3.1`; `HMM §A.4 / Appendix`; `PRIOR §F.2`; `CON §A-6 / E-3`)
- **Initial prior `p_0 = e_{(0,0)} · T^1000 ≈ π` (stationary).** TV distance ≤ 5e-6 at k=1000 across all four shipped matrices; mixing times 170–385 steps; max entry ≤ 0.038. **Early searches are pure VoI — never point-+EV from cold start.** (`HMM §B.2–B.5`; `HEUR §E.1`; `PRIOR §F.1`; CLAUDE.md §7)
- **Post-capture belief reset is `p_0`, NOT `δ_{(0,0)}`.** Rat respawns at (0,0) and takes 1000 more silent moves with no observations emitted. (`SPEC §3.2 / §3.6 / §10 item 9`; `HMM §D.3`; `HEUR §H.3`; `CON §E-4`; STATE R-HMM-001)
- **Observation likelihood factorizes cleanly:** `L(o | s, w) = P(n | cell_type(s)) · P(d | |s - w|_1)`. Two independent draws inside `rat.sample`. (`SPEC §3.4–3.5`; `HMM §A.2`)
- **Distance likelihood clipping:** reported `d=0` absorbs offsets −1 and 0 when true `k=0` → P(0|0) ≈ 0.82. (`SPEC §3.5 / §10 item 11`; `HMM §A.2`)
- **Rat moves before sensor draw**, at top of every ply, before the acting player's `play()` is called. Noise reflects cell type *pre-* this turn's move. (`SPEC §3.3 / §9 item 19`; `HMM §D.1`)
- **`apply_move(SEARCH)` is a `pass`** — no point delta, no rat state, no belief effect. The +4/−2 and `rat.spawn()` happen in `play_game` after `apply_move` returns. Any game-tree SEARCH node must apply side-effects manually. (`SPEC §2.4 / §9 item 11 / §10 item 20`; `HMM §E.6`; `SEARCH errata 1 / §F`; `HEUR §H.3`; `CON §A-5 / A-prime claim 2`)
- **Search EV threshold = 1/3.** `EV_pts = 6p − 2`. At cold-start `p_max ≤ 0.038`, no search is point-+EV. (`HMM §C.1`; `HEUR §A.4 / E.1`; `CLAUDE.md §7`)

**Search / tree**

- **Branching factor b ≈ 6.3–6.8 excluding SEARCH** (p90 = 8, late-max = 11); **~70 including all 64 SEARCH moves.** (`SEARCH §A.2 / Appendix`)
- **Pure-Python throughput:** ~50 k node-expansions/s, ~318 k `get_valid_moves`/s, ~48 k full-step/s (uncalibrated; tournament sandbox may shift ±20 %). (`SEARCH §A.5 / Appendix`; `SEARCH errata 2`)
- **Perspective mechanics:** `reverse_perspective()` swaps workers only — not `is_player_a_turn`, not `player_search / opponent_search`, not masks. A game tree must replicate the deque-based search swap of `play_game`. (`SPEC §5 / §6 / §9 item 14`; `SEARCH §F.2`; CLAUDE.md §7)
- **Opponent can park on your primed line to deny a carpet roll** (`is_cell_carpetable` rejects opp worker). (`SPEC §2.3 / §9 item 1`; `CON §A-4`)

**Grading context**

- **Ref bots** (from assignment.pdf / CLAUDE.md, cross-cited everywhere): **George ≥ 70 %** (greedy, no lookahead, opportunistic search), **Albert ≥ 80 %** (expectiminimax + HMM + simple heuristic), **Carrie ≥ 90 %** (same + "cell potential × distance" heuristic). ELO resets at lock-in. (`CLAUDE.md §5`; `PRIOR §E`; `HEUR intro`; `CON §C / §D-2`)
- **The 80 %→90 % delta = heuristic quality.** Albert and Carrie share architecture; only the eval differs. (`HEUR intro`; `PRIOR §E`)

---

## Section B — Consensus recommendations (≥ 2 docs agree)

Design choices where independent researchers converged. Strong defaults for the Architect.

| # | Recommendation | Supporting docs |
|---|----------------|-----------------|
| B1 | **α-β + iterative deepening + transposition table (Zobrist)** as search backbone. | SEARCH §B.3 (5/5); PRIOR §D / §G.3 (recommend); HEUR implicit |
| B2 | **Handcrafted-linear heuristic (F2) over NN (F3)** given the 3-day deadline; NN is anti-pattern at this timeline. | HEUR §F.1–F.4 / §H.2; PRIOR §F anti-pattern 3 / §G.10 |
| B3 | **9-feature linear core heuristic** (F1, F3–F5, F7, F9–F12 per HEUR §C), tuned by CMA-ES or hand. | HEUR §F.2 / §G.1 |
| B4 | **Carrie-style cell potential with distance discount:** `P(c) = [best_roll + 0.3·second_best_roll]·(1 − 0.5·P_opp_first)/(1 + 0.3·dist(worker, c))`. This is the 80→90 % lever. | HEUR §B.2 / §summary; PRIOR §E / §G-4 |
| B5 | **Exact linear-space forward HMM filter with per-turn renorm**, float64, 64-vector × 64×64 matrix ops. Sub-ms/turn. Log-space unnecessary. | HMM §E.1–E.4; PRIOR §G.1 (CS188 Ghostbusters analogue) |
| B6 | **Precompute `p_0` in `__init__`**, reuse on every rat capture; 1000-step iteration costs < 10 ms. | HMM §B.5 / §E.5; CON §E-3 / §E-4 |
| B7 | **Model SEARCH as a 2-outcome chance node manually** (hit→reset belief to `p_0`, +4; miss→zero cell+renorm, −2). Apply by hand; `forecast_move` will silently give wrong leaves. | HMM §E.6; SEARCH §F.1 / errata 1; HEUR §H.3; CON §A-5 |
| B8 | **Keep SEARCH out of the in-tree move list; handle root-only, EV-gated.** Include all 64 SEARCH = branching × 10. | SEARCH §A.2 / §C.1; HMM §C (implicit via VoI); HEUR §E.4 |
| B9 | **Belief as leaf-potential (F.1c hybrid), not in-tree chance nodes** for rat position. Branching stays ≤ ~7. | SEARCH §F.1 / §F.2 / §I-2; HMM §F item 7 |
| B10 | **Pin `limit_resources=True` for all local benchmarking.** | SEARCH errata 2; HEUR §H.2; CON §F-1 / §A-1; STATE blockers |
| B11 | **Paired-match evaluation** (same T, same spawn, same seed) — 50 unpaired matches ±14 pp; need ~400 unpaired or ~50 paired for 5 pp detection. | CON §B-3; HEUR §F.2 (tuning discipline) |
| B12 | **Gomoku-style line-of-k "threat-count" framing for prime extension:** our carpet `{-1,2,4,6,10,15,21}` is super-linear and maps to connect-K heuristics; value partial prime-lines by extendibility, not count. | HEUR §A.2 / §B.1; PRIOR §C.3 / §G.2 |
| B13 | **Use init time aggressively:** `p_0`, reach tables, manhattan LUT, Zobrist constants, JAX-JIT warmup. Don't burn play clock. | HMM §E.5; PRIOR §G-5; CON §E-2 |
| B14 | **Time manager = ID with 0.2 s safety + adaptive `0.6× / 1.0× / 1.6×` multipliers, capped at 2.5× base.** | SEARCH §D.4–D.5 |
| B15 | **Move-ordering stack: hash-move → killer → history → type-priority → immediate-point-delta.** | SEARCH §C / §I-4 |
| B16 | **NO null-move pruning** (primed-line Zugzwang analogs) and **NO magic bitboards** (no sliding pieces). | SEARCH §G table |
| B17 | **Re-read `cell_type(s)` every update** — do not cache per-cell noise likelihood across turns; primes/carpets mutate it. | HMM §D.6 |
| B18 | **Track the absolute-frame search tuples manually in any tree**: the deque pattern `opponent_search = searches[-1], player_search = searches[-2]` after `reverse_perspective`. | SPEC §5; SEARCH §F.2 |
| B19 | **Asymmetric opponent-first prior** `P_opp_first(c)`: center x∈{3,4} contested; own half safe in opening. F13 (center control) de-weighted — spawns already near center. | HEUR §H.1; SPEC §1 |
| B20 | **Per-leaf-eval target ≤ 100 μs in tournament mode**; requires numpy-vectorized ray scans + cached belief reads. | HEUR §H.2 / §C.4 |

---

## Section C — Conflicts / tensions (explicit disagreements)

Where the docs disagree. Each side is laid out with evidence. **Not resolved here** — for the Architect.

### C1. Single deep architecture vs. reactive-floor-bot insurance

- **HMM / SEARCH / HEUR default:** expectiminimax + HMM + linear heuristic as the primary path to 90 %. Research-phase investment assumes this backbone.
- **CON §C-1 / §F-4:** *before* committing, ship a reactive-policy floor bot by hour 12. No search; ~20 features + hand-tuned priority list. Never times out, never crashes. Insurance against the 70 % floor. Probability estimates: P(>70 %) ≈ 0.90, P(>80 %) ≈ 0.55, P(>90 %) ≈ 0.25.
- **Tension:** pipeline phase 0 already consumed ~6 h on research before any code ships. CON argues this is scope creep; primary docs argue the heuristic quality *is* the 90 % lever, so research is load-bearing.

### C2. In-tree chance nodes vs. belief-as-leaf-potential

- **SEARCH §F.1 / HMM §F item 7:** prefer F.1c hybrid — belief outside the tree, SEARCH children as exact chance nodes at root/near-root. Keeps b ≈ 7. Tentative default.
- **PRIOR §F-5:** alternative — "particle-filter fallback" or Monte Carlo sample of belief-futures for deeper belief-aware rollouts. Lower priority.
- **CON §C-3:** flags MCTS/ISMCTS as rejected for primary but as potential auxiliary; implicitly sides with the hybrid position.
- **Tension:** the hybrid *ignores* that our/opponent's imagined-future moves change cell types and therefore future noise models. Error is claimed small within a 6-depth window but is unverified.

### C3. Search-cell objective — max-belief vs. min-entropy vs. weighted

- **HMM §C.3 option (a) Max-belief:** pure point-EV `argmax_s b_t(s)`.
- **HMM §C.3 option (b) Min expected posterior entropy:** pure info objective.
- **HMM §C.3 option (c) Weighted:** `6p − 2 + λ · VoI(s)`.
- **HEUR §H.3 revised F15:** `(6p − 2) + γ_info · E[InfoValue(c)] − γ_reset · p · H(p_0)` — adds a belief-reset penalty on hits (late-game, a hit resets your sharper belief back to diffuse `p_0`).
- **Tension:** options are empirically competitive; HMM explicitly punts to Architect. HEUR's F15 goes further and says late-game **hits can be information-negative** — more nuanced than any HMM option alone.

### C4. F2 linear vs. NN (F3) vs. pure reactive policy

- **HEUR §F summary:** build F1 (hand-tuned linear) → F2 (CMA-ES tuned) → F3 (small NN) only if both land early. F3 is upside-only.
- **CON §C-1:** pure reactive policy (no tree) might beat a shallow expectiminimax — Albert/Carrie's tree is likely depth 2–3; better eval without tree could win. P(beats Carrie) ≈ 0.20 for reactive.
- **PRIOR §F anti-pattern 3:** NN from scratch in < 1 week is a documented anti-pattern (Halite / Battlecode / CodinGame consensus).
- **Tension:** HEUR treats "tree + eval" as the given; CON argues that at shallow depth the tree adds little and a stronger eval standalone wins. HEUR's F3 time-budget analysis (`H.2` ≤ 100 μs per eval) also flags NN as marginal under tournament clock.

### C5. Time allocation — deep research vs. early-ship-and-iterate

- **PIPELINE.md:** Phase 0 (6 h) + Phase 1 (4 h) + Phase 2 (3 h) = 13 h of docs before code.
- **CON §B-1 / §F-4:** cap Phase 0 at 4 h; ship a minimum-viable bot by hour 18 regardless of research quality. Empirically game-AI wins come from Phase 5 implementation-level tricks (bitboards, TT, tuning), which are being under-budgeted.
- **Tension:** the orchestrator has already consumed the 6 h; the question is whether Phase 1/2 compresses and the reactive bot lands immediately, or whether the strategy blueprint proceeds as originally scoped.

### C6. Architecture-selection bias in the research brief itself

- **PIPELINE.md / RESEARCH_ADVERSARIAL.md brief:** "investigate expectiminimax with chance nodes, alpha-beta pruning, iterative deepening..." — anchors on expectiminimax.
- **CON §B-2:** confirmation bias — the researcher's mandate is to flesh out expectiminimax, not to compare it against alternatives.
- **SEARCH §B:** surveys 8 candidates (expectiminimax, *-minimax/Star1-2, α-β+ID+TT, MCTS-UCT, IS-MCTS, PUCT, beam, 1-ply policy) with suitability scores — this *partially* addresses the bias but still defaults to α-β+ID+TT without a full ELO-projection comparison.
- **Tension:** on record, the anchoring hasn't been fully corrected; Strategy-Architect should weigh whether the dismissals in SEARCH §B.4–B.8 hold up under the tighter tournament budget.

### C7. Opponent-modeling as primary vs. optional

- **CON §C-6:** opponent-specific exploit of George/Albert/Carrie heuristics — 1-day investment, P(beats Carrie) ≈ 0.25–0.35, "strongly recommended" and rated highest-leverage alternative.
- **HMM §D.4 / §F item 8:** opponent belief modeling is a Phase-5 enhancement; out-of-scope for the base HMM.
- **SEARCH §F.3:** likewise Phase-5.
- **HEUR §D.3:** blocking play is captured implicitly by F4 (`opp_cell_potential`) — no dedicated opponent model needed.
- **Tension:** CON rates opponent-modeling as **the** highest-EV alternative track; the other three docs treat it as nice-to-have.

### C8. Local benchmarks vs. tournament clock skew

- **SEARCH §A.5 / §H:** projects 6–8 ply pure Python, 9–11 with numba. Disclaims "without `limit_resources=True`".
- **HEUR §H.2:** per-eval budget in tournament is ≤ 100 μs, much tighter than local; pushes preference toward F2 over F3.
- **CON §A-1 / §E-1 / §F-1 / §F-2:** explicitly flags the local-360s / tournament-240s gap as a HIGH risk; additionally, the local driver runs with **no seccomp at all** (dev-vs-prod sandbox gap).
- **Tension:** these aren't contradictory, but HEUR's ≤ 100 μs target and SEARCH's optimistic depth projections live in slight tension — a 100 μs eval ceiling at 100 k nps makes the 9–11 ply "numba leaf" projection contingent on very fast leaf eval *and* a very fast search skeleton.

---

## Section D — Open architectural choices (Architect must decide)

Merged from the "open choices" sections of each research doc. Each has: provisional default, evidence, what would flip.

| # | Choice | Provisional default | Evidence for default | What would flip it |
|---|--------|--------------------|-----------------------|---------------------|
| D1 | **Backbone algorithm** | α-β + ID + TT | SEARCH §B.3 5/5; PRIOR §G.3 | MCTS/PUCT if heuristic dev stalls or we ship a NN prior cheaply. Reactive-only if CON §C-1 self-play evidence says tree adds no ELO at shallow depth. |
| D2 | **Rat chance-node model** | Belief-as-leaf-potential (F.1c hybrid) | SEARCH §F.1 / §I-2 | In-tree chance if SEARCH-heavy play turns out competitive, or belief-evolution timing matters for opponent moves. |
| D3 | **SEARCH inclusion in tree** | Root-only, EV-gated by `max_p > 1/3` + VoI bonus | SEARCH §C.1 / §I-3; HMM §C.4 | Evidence of missed mid-sequence SEARCH opportunities in match logs. |
| D4 | **Search-cell objective** | Hybrid: max-belief when `p > 1/3`, else min-entropy | HMM §C.3; HEUR §H.3 F15 | CMA-ES weights converge on pure (a) or (c); local ablation decides. |
| D5 | **Move ordering stack** | hash → killer → history → type-priority → immediate-delta | SEARCH §C / §I-4 | Profiling shows TT hit-rate too low; drop hash-priority. |
| D6 | **Time allocation** | Adaptive `0.6× / 1.0× / 1.6×` + 0.2 s safety + 2.5× cap | SEARCH §D.5 / §I-5 | Early timeouts → flat 5.5 s with stricter cutoffs. |
| D7 | **Numba/Cython/JAX for leaf** | Profile first; only compile if >40 % wall & >2× speedup | SEARCH §I-6; HEUR §H.2 | Init budget or zip-size squeeze; or NN path needs torch/jax anyway. |
| D8 | **Opponent model** | Assume min-node uses our heuristic (self-play) | SEARCH §I-7 | Wins vs Albert but loses to George → pessimistic/opponent-specific model. Or CON §C-6 opponent-specific exploit track. |
| D9 | **Depth ceiling** | Cap at d=16 | SEARCH §I-8 | Never flip. |
| D10 | **ISMCTS fallback** | No | SEARCH §I-9 | Opponent-belief-tracking pays off. |
| D11 | **Beam-search pruning (top-K)** | No; rely on α-β + ordering | SEARCH §I-10 | Profiling shows deep-node branching dominates wall-time. |
| D12 | **Heuristic architecture** | F2 (9-feature linear, CMA-ES-tuned) | HEUR §F.2 / §summary; CON §C-1 agrees linear floor | F2 finishes early → try F3 (small NN). Tuning harness flaky → fall back to F1 hand-tuned. |
| D13 | **Feature-set granularity** | 9 MUST+STRONGLY — F1,F3,F4,F5,F7,F9,F10,F11,F12 | HEUR §G.1 | Search-timing weak → add F8 (belief entropy). Opening weak → add HEUR §H.1 F13' (opening-half bias). |
| D14 | **Float precision (HMM)** | float64 | HMM §F-1 / §E.1 | Unified dtype with JAX heuristic; float32 fine with per-turn renorm. |
| D15 | **Log-space vs linear HMM** | Linear with per-turn renorm | HMM §A.3 / §E.1 | Profiling shows numeric drift. Unlikely. |
| D16 | **Reactive floor-bot insurance** | **Build in parallel, ship by hour 12** | CON §C-1 / §F-4 | **Orchestrator decision pending** (this is C1 above) |
| D17 | **Opponent-specific exploit track** | Phase 5 add-on, 1-day budget | CON §C-6 / §F-8 | Budget squeezed → drop; stays as optional. |
| D18 | **Opening book** | Defer; 648 topologies is borderline feasible | CON §C-2; HEUR no-signal | Have spare time in Phase 5; offline optimizer could add +5–10 pp. |
| D19 | **Endgame tablebase** | Phase 5 add-on for last 5–8 turns | CON §C-4 (+3–5 pp) | Never harmful; add if time. |
| D20 | **Matrix identification from T-samples** | Skip — `T^1000 ≈ π` regardless | HMM §F-5 / §B.3 | Would need cheap discriminator surviving ±10 % noise; unlikely. |
| D21 | **Paired-match evaluation** | Use it — same T/spawn/seed | CON §B-3; HEUR §F.2 | Never flip. |
| D22 | **HMM→search interface** | Summary stats (top-k cells, entropy, max-mass) vs full 64-dim | HMM §F-7 open | Leaf profiling. |

---

## Section E — Consolidated risk register

De-duplicated across CON and the other docs. Severity: Critical / High / Medium. Owner in parens.

**Critical**
- **R-TIME-01** Local-vs-tournament time budget gap (360 s vs 240 s, init 20 s vs 10 s, no-seccomp locally). Misses propagate to every benchmark. (`CON §A-1 / E-1 / E-5`, `SEARCH errata 2`, `HEUR §H.2`, `SPEC §7`) — **owner: tester-local + strategy-architect**.
- **R-SEARCH-01** `apply_move(SEARCH)` and `forecast_move(SEARCH)` are silent-footgun no-ops for points/belief. Any in-tree SEARCH must hand-apply `+4 / −2` and belief collapse. (`CON §A-5 / A-prime-2`, `SPEC §2.4 / §10-20`, `HMM §E.6`, `SEARCH errata 1`, `HEUR §H.3`) — **owner: dev-search + dev-hmm**.
- **R-HMM-01** Belief reset on both-sides' rat captures must go to `p_0`, not `δ_{(0,0)}`. Naive implementation catastrophically wrong after ~100 post-hit turns. (`HMM §D.3`, `HEUR §H.3`, `SPEC §3.2 / §3.6`, `CON §E-4`) — **owner: dev-hmm**.

**High**
- **R-SANDBOX-01** Seccomp sandbox only active under `limit_resources=True`; default local runs have **no seccomp at all**. A library (`prctl`, `seccomp`, `execve`) call that works locally will kill in tournament. (`CON §A-8 / E-1`, `SPEC §7`) — **owner: dev-integrator + tester-local**.
- **R-INIT-01** JAX/JIT first-call in `play()` can burn 1–5 s of the 240 s clock. Force JIT warmup in `__init__`. (`CON §E-2`) — **owner: dev-integrator**.
- **R-ARCH-BIAS** Research brief anchored on expectiminimax; full architecture comparison (reactive / MCTS / opponent-specific) still partial. (`CON §B-2 / §C`) — **owner: strategy-architect**.
- **R-EVAL-01** 50-match unpaired batches have ±14 pp 95 % CI — too noisy to detect 5 pp improvements. Need paired matches or n≈400. (`CON §B-3`) — **owner: tester-local**.
- **R-GRADE-FLOOR** No reactive floor-bot insurance yet; if primary bot times out / crashes by hour N, no fallback. (`CON §C-1 / §F-4`) — **owner: orchestrator / dev-integrator**.
- **R-PARTNER** Two-agent partnership — partner could overwrite the submission. No explicit lock-in protocol. (`CON §B-7 / §E-6 / §F-5`) — **owner: orchestrator (confirm with user)**.
- **R-PERSP-01** `reverse_perspective()` swaps workers only; any tree must manually track `opponent_search / player_search` via deque pattern. (`SPEC §6 / §9-14`, `SEARCH §F.2`) — **owner: dev-search**.

**Medium**
- **R-BELIEF-SYNC** `cell_type(s)` mutates during opp's turn (prime/carpet); noise-likelihood table must be re-read every update, not cached. (`HMM §D.6`) — **owner: dev-hmm**.
- **R-FORECAST-GC** `get_copy()` allocates ~112 B + Workers per call; 10^6 forecasts = GC pressure. Need make/unmake pattern in hot loop. (`CON §E-8`) — **owner: dev-search**.
- **R-HEUR-BUDGET** ≤ 100 μs per eval in tournament mode; NN path marginal without numba. (`HEUR §H.2`) — **owner: dev-heuristic + auditor**.
- **R-CARPET-DENY** Opponent parking on your primed line denies the roll. Must model in heuristic / move-ordering. (`SPEC §2.3 / §9-1`, `CON §A-4`) — **owner: dev-heuristic**.
- **R-SCRIM-BIAS** Live scrimmage ELO ≠ tournament ELO (selection bias, weak-opponent inflation). Log per-opponent, not aggregate. (`CON §B-4`) — **owner: tester-live**.
- **R-ZIP** `__pycache__` / `.DS_Store` leaking into zip can fail under seccomp. Clean-zip discipline. (`CON §E-7`) — **owner: dev-integrator**.
- **R-T-CACHE** Don't cache any T-derived table from disk — T is per-game noisy. (`CON §E-3`, `PRIOR §F-2`) — **owner: dev-hmm**.
- **R-TIE** A draw is 0.5 ELO; heuristic should have a "prefer guaranteed tie over 40/60 gamble" knob near endgame. (`CON §A-7`) — **owner: dev-heuristic**.
- **R-SPAWN-BLOCK** Spawn-on-BLOCKED is a latent vulnerability but currently inert (shape-set accident). Don't waste engineering on recovery logic; note as fragile invariant. (`SPEC §1 / §9-17`, `CON §A-prime-3`) — **owner: game-analyst (doc-level only)**.

---

## Section F — Evidence-flipping matrix

Pre-commit triggers: "if we observe X in local tests, switch from default Y to alternative Z." Makes the plan falsifiable.

| Observation (X) | Current default (Y) | Switch to (Z) | Source of rule |
|-----------------|---------------------|----------------|----------------|
| Reactive-policy floor-bot wins ≥ 50 % paired vs our depth-4 α-β+ID+TT at matched budget. | α-β + ID + TT primary | Ship reactive as primary; add minimal lookahead only for endgame. | CON §C-1 |
| Our primary bot loses > 20 % to George in paired play. | Self-play heuristic assumption | Opponent-specific model (pessimistic or explicit George/Albert/Carrie predictor). | SEARCH §I-7; CON §C-6 |
| Local paired matches show 5 pp improvement but tournament scrimmage shows regression. | Trust local tuning | Re-run all tuning under `limit_resources=True`; drop any gain that doesn't survive. | CON §A-1 / E-1 |
| `max_p > 1/3` happens < 3 times per average game. | Root-only SEARCH gate | Add VoI-based info-gathering search threshold lower than 1/3 mid-game. | HMM §C.2 / C.4; HEUR §E.2 |
| Opponent captures rat > 40 % of games (belief-reset events frequent). | Passive belief tracking | Add opponent-belief predictor; prioritize denial-searches before their EV moves. | CON §C-6; HMM §D.4 |
| Leaf-eval profile > 40 % of wall time with > 2× speedup achievable. | Pure Python/numpy leaf | Compile with numba; push depth +1–2 plies. | SEARCH §I-6 |
| TT hit-rate < 5 % after 100 matches. | hash-move first in move order | Drop hash-move tier; promote killer/history. | SEARCH §I-4 |
| Our carpet-denials by opp > 1/game average. | Implicit blocking via F4 | Add explicit opp-parking-risk term to F5/F16 heuristic. | CON §A-4; HEUR §D.1 |
| F2 CMA-ES tuning converges to weights near F1 handcrafted (< 10 % drift). | CMA-ES tuned F2 | Ship F1; bank the tuning budget elsewhere. | HEUR §G.2 |
| JAX JIT warmup measured > 2 s in init. | JIT as-needed | Force warmup in `__init__` with dummy call; or replace JAX with numpy if budget squeezed. | CON §E-2 |
| Local 50-match batch tied but 200-match paired shows ≥ 5 pp. | 50-match go/no-go | Promote minimum-batch to 200 paired for finalist gates. | CON §B-3 |
| Games with `bigloop.pkl` (slow-mix) show belief-entropy persistently > 5 bits into mid-game. | Uniform across matrices | Matrix-specific early-game SEARCH policy; burn early VoI more aggressively. | HMM §B.2 / §B.3 |
| Live scrimmage vs Carrie specifically loses ≥ 70 %. | Generic tuning | Open 1-day opponent-specific exploit track targeting Carrie's "cell potential × distance" greed. | CON §C-6 / §D-2 |
| Tree-search times out in ≥ 2 / 50 matches. | Adaptive 0.6×/1.0×/1.6× allocator | Flat 5.5 s with hard ID cutoffs + 0.5 s reserve. | SEARCH §I-5 |
| Endgame turns 35–40 show sub-par heuristic move quality. | Heuristic leaf | Endgame exact-search branch (solve last 5–8 turns). | CON §C-4 |

---

## Section G — Recommended Strategy-Architect agenda

The order of decisions is itself constrained — earlier choices bound later ones. Walk this decision tree to produce `BOT_STRATEGY.md`.

**Step 0 — Insurance decision (≤ 1 h)**

- Decide: ship reactive-policy floor bot in parallel (CON §C-1, RISK R-GRADE-FLOOR)? YES/NO. If YES, assign dev-integrator to ship by hour 12 as a reserved backup submission. This does not gate other work.

**Step 1 — Backbone (decide D1, D2)**

- Default: α-β + ID + TT with Zobrist incremental hashing; belief-as-leaf-potential (F.1c hybrid).
- Alternative to explicitly rule in/out: MCTS/PUCT; PUCT-with-handcrafted-prior (B.6 in SEARCH).
- Record rationale referencing SEARCH §B.3 suitability, branching b ≈ 7, 6 s/move budget, pure-Python nps projections.

**Step 2 — SEARCH integration (decide D3, D4)**

- SEARCH in tree? Default: root-only, EV-gated by `max_p > 1/3` with VoI bonus (SEARCH §C.1). Alternative: near-root chance nodes.
- Objective: pick default from HMM §C.3 options (a)/(b)/(c) or HEUR §H.3 F15 formulation. Record `γ_info`, `γ_reset` starting guesses.

**Step 3 — Time manager (decide D6)**

- ID + 0.2 s safety + adaptive multipliers OR flat. Must be robust to tournament 240 s budget (R-TIME-01).
- Bake in `time_left()` polling every 1024 node-expansions (SEARCH §D.4).

**Step 4 — Heuristic architecture (decide D12, D13, D14, D15)**

- F1 handcrafted → F2 CMA-ES (primary) → F3 NN (stretch). Default F2 (HEUR §F / §summary).
- Feature list: fix the 9 MUST+STRONGLY (F1,F3,F4,F5,F7,F9,F10,F11,F12) for v1; schedule F8/F13'/F15 additions.
- `P(c)` formula: HEUR §B.2 with `λ=0.3, α=0.3, β=0.5` defaults. Confirm the Carrie-style distance discount as the 80→90 % lever.

**Step 5 — HMM module (decide D14, D15, and HMM §F items 6, 7)**

- Float64 linear-space with per-turn renorm. Belief stored as numpy `(64,)`.
- Precompute `p_0 = e_0 @ T^1000` in `__init__` via iterative multiply (~3 ms).
- Define the HMM→search interface: pass belief array? summary stats? (HMM §F item 7; D22).
- Update pipeline: predict → opp-search-update → predict → obs-update → normalize (HMM §E.3).

**Step 6 — Move generation and ordering (decide D5, D11)**

- SEARCH excluded from in-tree moves. Move ordering stack B15.
- No beam pruning; rely on α-β + ordering. Make/unmake pattern in hot loop (R-FORECAST-GC).

**Step 7 — Testing protocol (decide D21 and defense against R-EVAL-01, R-SANDBOX-01)**

- Paired-match eval (same T/spawn/seed) for all A/B.
- Always run `limit_resources=True` for tournament-comparable numbers.
- Per-opponent ELO ledger (R-SCRIM-BIAS).
- 200-match finalist gate; 50-match go/no-go.

**Step 8 — Phase-5 add-ons (decide D17, D18, D19)**

- Prioritize: opponent-specific exploit (CON §C-6, highest-leverage alt) → endgame tablebase → opening book → NN F3 → opponent-belief modeling.
- Time-box each at 0.5–1 day; revert on any ELO regression.

**Step 9 — Submission discipline (R-PARTNER, R-ZIP)**

- Confirm partner lock-in protocol (rahiljav@gmail.com). Who activates final submission?
- Clean zip via `zip -r BotName.zip BotName -x '*/__pycache__/*' '*.pyc' '.DS_Store'`.
- Activation checklist at T-6 h.

**Step 10 — Record in `DECISIONS.md`**

- For each of D1–D22 that the Architect pins, a D-00X entry with: decision, rationale, dismissed alternatives, contrarian dissent (if CON's recommendation differed).

---

## Flagged missing pieces (for the Architect to note; no new research here)

These are gaps I noticed while synthesizing — they are **open items**, not actions for me.

- No quantitative ELO delta estimate for the reactive-floor-bot vs the primary path; C1 tension is unresolved without one.
- No confirmed observational data on George/Albert/Carrie move distributions (CON §D-2 weaknesses are hypothesis-grade).
- The HEUR `≤ 100 μs per eval` budget (§H.2) and SEARCH `9–11 ply with numba` (§H) projections have not been reconciled into a single "achievable depth × leaf-cost" envelope.
- No decision yet on whether our tree needs full 64-dim belief at every node or summary stats (D22 / HMM §F item 7).
- Per-seed `p_0` shape variability within a single base matrix (±10 % noise) is not quantified beyond entropy summary (HMM §B.4); could affect whether per-game init cost is 3 ms or 30 ms.

---

**End of SYNTHESIS.**
