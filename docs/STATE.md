# STATE — Rolling Snapshot

**Last updated:** 2026-04-16 (research-synthesizer finished SYNTHESIS.md)
**Current phase:** Phase 0 — Foundations (wave 1 synthesized; ready for Phase 1 Strategy-Architect)
**Deadline:** 2026-04-19 23:59

## Active agents

| Name                 | Role                 | Current task            | Status    |
|----------------------|----------------------|-------------------------|-----------|
| game-analyst         | game-analyst         | Write GAME_SPEC.md      | completed |
| researcher-hmm       | researcher-hmm       | RESEARCH_HMM_RAT.md     | completed |
| researcher-search    | researcher-search    | RESEARCH_ADVERSARIAL.md | completed |
| researcher-prior     | researcher-prior     | RESEARCH_PRIOR_ART.md   | completed |
| researcher-heuristic | researcher-heuristic | RESEARCH_HEURISTIC.md   | completed |
| contrarian-scope     | contrarian-scope     | CONTRARIAN_SCOPE.md     | completed |
| research-synthesizer | research-synthesizer | SYNTHESIS.md            | completed |

## Recent decisions

- **D-001** (2026-04-16): Adopt multi-agent orchestration model per `TEAM_CHARTER.md`. Contrarian and researcher roles mandatory. Documents in `docs/` are single source of truth.
- **D-002** (2026-04-16): Architecture decision DEFERRED. No architecture pre-committed; it will be chosen by Strategy-Architect after research evidence is in. (Corrects earlier prejudgment.)
- **D-003** (2026-04-16): `docs/GAME_SPEC.md` landed. Ground-truth spec is authoritative over `CLAUDE.md`; see its §10 for the CLAUDE.md discrepancy list.
- **R-HMM-001** (2026-04-16): HMM research delivered in `docs/research/RESEARCH_HMM_RAT.md` — forward-filter math, `p_0 = e_0 @ T^1000 ≈ π` (stationary, TV < 5e-6 at k=1000 for all four shipped matrices; mixing times 170-385 steps; max entry ≤ 0.038 so early searches are pure VoI), opponent-search update recipe (miss → zero+renorm, hit → reset to `p_0` NOT `δ_{(0,0)}`), runtime <1 ms/turn. Open forks to Strategy-Architect listed in doc §F.
- **R-HEUR-001** (2026-04-16): Heuristic research delivered in `docs/research/RESEARCH_HEURISTIC.md`. Key results: (a) prime-then-roll PPT rises monotonically 1.33 (k=2) → 3.50 (k=7); realistic 40-turn ceiling 80–110 pts. (b) Carrie's cell potential `P(c)` formulated as `[best_roll + 0.3·second_best_roll]·(1 − 0.5·P_opp_first)/(1 + 0.3·dist(worker,c))` — this IS the 80%→90% leverage. (c) 9-feature linear heuristic (F1, F3–F5, F7, F9–F12) with CMA-ES-tuned weights is the recommended architecture; small-NN is upside-only given deadline. Open forks to Strategy-Architect in §G.
- **R-HEUR-002** (2026-04-16): `RESEARCH_HEURISTIC.md` bumped to v1.1 with new Section H reconciling GAME_SPEC §10 facts. Key amendments: (a) asymmetric spawn prior — A is always left-half (x∈{2,3}), B right-half; `P_opp_first(c)` must treat center cells (x=3,4) as contested, own-half cells as safe; F13 (center control) de-weighted. (b) Per-eval budget tightened to **≤ 100 μs** in tournament mode (240 s / 40 moves) — tilts preference further toward F2 linear over F3 NN; tuning harness must run with `limit_resources=True`. (c) SEARCH chance-node explicit: leaf eval must add `6p − 2` to F1 manually AND model belief-collapse side-effect (on hit, belief resets to `p_0 = e_0 @ T^1000` NOT `δ_{(0,0)}`); new F15 formula includes `−γ_reset · p · H(p_0)` term penalizing the belief-reset cost of a successful search.
- **R-PRIOR-001** (2026-04-16): Prior-art research delivered in `docs/research/RESEARCH_PRIOR_ART.md`. (a) Carpet/rat game is new to Sp2026; no prior-winner code is public (only gatech.edu blurb on chicken-game winner "StockChicken", minimax+AB+Bayes). (b) Berkeley CS188 Project 4 "Ghostbusters" is a near-identical HMM setup — use its forward-algorithm recipe. (c) Gomoku threat-space-search heuristics directly apply to our super-linear carpet-roll bonus. (d) NN-from-scratch is an anti-pattern at <1-week timeline (Halite/Battlecode/CodinGame consensus). (e) Bytefight public page contains nothing beyond CLAUDE.md; no public leaderboard without login.
- **R-SEARCH-001** (2026-04-16): Adversarial-search research delivered in `docs/research/RESEARCH_ADVERSARIAL.md`. Empirical branching factor **b ≈ 6.3–6.8 excluding SEARCH** (p90=8, late-max=11); **~70 with all 64 SEARCH moves**. Pure-Python throughput: 50 k node-expansions/sec, 318 k move-gen/sec, 48 k full-step/sec. Projected feasible α-β+ID+TT depth: **6–8 ply pure Python, 9–11 ply with numba leaf eval**. Eight candidates surveyed with pseudocode + 1–5 suitability (expectiminimax, *-minimax/Star1-2, α-β+ID+TT+Zobrist, MCTS-UCT, IS-MCTS, PUCT, beam, 1-ply policy) — no winner picked per the contrarian brief. Tentative defaults (all flippable): (1) rat belief as leaf-potential NOT in-tree chance nodes — keeps b at ~7 and matches R-HMM-001; (2) SEARCH excluded from tree, root-only EV-gated at `P(rat)>1/3`; (3) ID controller + 0.2 s safety + 0.6×/1.0×/1.6× adaptive multipliers; (4) move ordering stack = hash-move → killer → history → type-priority → immediate-point-delta; (5) NO null-move pruning (primed-line Zugzwang analogs), NO magic bitboards. 10 open decisions for Strategy-Architect in doc §I. Note: benchmarks above were run without `limit_resources=True`; tournament sandbox may shift nps ±20%, per C-SCOPE E-1.
- **SYN-001** (2026-04-16): Wave-1 synthesis delivered in `docs/research/SYNTHESIS.md`. (a) §A–B consolidate 20 cross-confirmed agreed facts and consensus recommendations (α-β+ID+TT backbone, F2 9-feature linear heuristic with Carrie-style `P(c)` distance-discount, `p_0 = e_0 @ T^1000` prior and reset, SEARCH as manual chance node, `limit_resources=True` pinned, paired-match eval). (b) §C surfaces 8 unresolved tensions — reactive-floor-bot vs deep-arch insurance, in-tree vs leaf belief, max-belief vs min-entropy vs weighted search objective, F2 vs NN vs reactive, research-depth vs early-ship, architecture-selection bias, opponent-modeling priority, local-vs-tournament clock skew. (c) §D lists 22 open architectural choices with provisional defaults and flip-triggers; §E is a de-duplicated risk register (3 critical, 8 high, 9 medium) with owners; §F is a 15-row evidence-flipping matrix pre-committing falsifiable switch rules; §G is the Strategy-Architect 10-step decision agenda. Flagged missing pieces: no quantitative reactive-vs-primary ELO delta, unreconciled `≤ 100 μs per eval` vs `9–11 ply numba` envelope, HMM→search interface undecided.
- **C-SCOPE-001** (2026-04-16): Red-team critique delivered in `docs/research/CONTRARIAN_SCOPE.md`. No pipeline-halting issue. Top recommendations (Phase-1-blockers): (1) enforce `limit_resources=True` in all benchmarking — dev-vs-tournament time/sandbox gap is underweighted; (2) rewrite `RESEARCH_ADVERSARIAL.md` brief to compare architectures (expectiminimax / MCTS / reactive policy / opponent-model), current scope is anchored on expectiminimax; (3) ship a reactive-policy floor bot by ~hour 12 as grade-floor (70%) insurance, before any deep architecture commit; (4) switch to paired-match eval (same T/spawn/seed) — 50 unpaired matches has ±14 pp 95% CI, inadequate for detecting 5 pp improvements; (5) add 1-day "opponent-specific exploit" track (model George/Albert/Carrie explicitly) — highest-leverage alt at ~0.25-0.35 P(beats Carrie); (6) honest grade-probability estimates: P(>70%)≈0.90, P(>80%)≈0.55, P(>90%)≈0.25.

## Blockers

None pipeline-halting. Top-priority items the orchestrator should address before Phase 1 per `docs/research/CONTRARIAN_SCOPE.md` §F: the time-budget note in CLAUDE.md (A-1), sandbox-test gap (E-1), architecture-comparison rewrite (B-2), reactive floor-bot insurance (C-1), partner activation protocol (B-7).

## Open loops

- Agent folder for our bot has not been created yet. Recommended name TBD (proposed: `RattleBot`).
- No test infrastructure yet; Tester-Local will build a batch runner in Phase 3.
- bytefight.org credentials / session — Tester-Live needs to confirm the user is logged in on Chrome before uploads.

## Top-3 surprising discoveries from GAME_SPEC work

1. **Local tournament time budget differs (240 s vs 360 s).** `engine/gameplay.py:232-238` gives the player 360 s total when `limit_resources=False` (i.e. `run_local_agents.py`) and only 240 s on bytefight.org. Local self-play benchmarks are therefore running under 50% more CPU than the actual tournament — any time-per-move tuning derived from local runs will be optimistic and must be rescaled. Also `init_timeout` is 20 s locally vs 10 s on the tournament machine.
2. **`apply_move(SEARCH)` does NOT change points; `play_game` does, after the call.** `engine/game/board.py:256-258` has the SEARCH branch as a bare `pass`. The +4/-2 delta and rat respawn are performed in `engine/gameplay.py:434-445`, outside of `apply_move`. Consequence: `forecast_move(SEARCH)` on a copied board will not reflect rat-catch points — any expectiminimax with SEARCH chance nodes must apply the point delta (and the belief-collapse side effect) manually.
3. **Spawns can collide with the random corner blockers.** `board_utils.generate_spawns` picks `y ∈ {2,3,4,5}` without checking the blocked mask. A 3-deep top-left corner block covers y=0..2; a 3-deep bottom corner covers y=5..7. So spawns at y=2 or y=5 can land on a BLOCKED cell. Also: spawns are *not* uniform over the inner 4×4 — A is always in `x ∈ {2,3}`, B always mirrored at `7-x`, and both are on the same `y`. CLAUDE.md's "inner 4×4" framing is misleading.

## Pointers (required reading for new agents)

- `CLAUDE.md` — project-level brief (read first).
- `docs/TEAM_CHARTER.md` — operating model.
- `docs/PIPELINE.md` — process pipeline (research-first workflow; NOT a strategic plan).
- `docs/STATE.md` — this file (always).
- Role-specific doc (e.g., for researcher: `docs/research/RESEARCH_QUESTIONS.md` once written).
- `engine/game/*.py` — ground-truth source.
- `assignment.pdf` — official spec.
