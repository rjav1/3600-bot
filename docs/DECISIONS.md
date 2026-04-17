# Decisions Log

Append-only. Each entry: ID, date, decision, rationale, dismissed alternatives, contrarian dissent (if any).

---

## D-001 — 2026-04-16 — Adopt multi-agent orchestration model

**Decision:** Use a team of specialized sub-agents coordinated by a lightweight orchestrator session. All artifacts go into `docs/` so the team survives context resets.

**Rationale:** The project is too complex (research + HMM + search + heuristic + live testing) and the deadline too tight (~3 days) for serial single-agent work. Parallel specialization + document-based coordination lets us burn through research and build in parallel.

**Alternatives dismissed:**
- Single agent writes the whole bot: too slow, too much single-agent-hallucination risk.
- No contrarian role: past experience shows LLM tunnel vision; explicit contrarian enforces hygiene.

**Contrarian dissent:** None at this stage; contrarian role itself is the dissent mechanism.

---

## D-002 — 2026-04-16 — Architecture decision DEFERRED until research completes

**Decision:** Do NOT pre-commit to any specific bot architecture (expectiminimax / MCTS / neural / heuristic-only). The Strategy-Architect will select an architecture only AFTER researchers have delivered evidence-based findings.

**Rationale:** Pre-committing to expectiminimax + HMM would be orchestrator-bias injected into the pipeline. Real research pipelines generate evidence first, then decide. The assignment hints at Albert/Carrie using expectiminimax + HMM, but that is their design — it does not prove it is optimal for *beating* them. Researchers must establish what the state-of-the-art actually says about: (a) adversarial search under partial information, (b) HMM on 8x8 grids with this specific noise model, (c) what approaches have won prior bytefight / similar competitions, (d) whether a non-standard approach (e.g. pure MCTS, or a lightweight NN over handcrafted features) could dominate.

**How architecture will be chosen:**
1. Researchers complete `docs/research/RESEARCH_*.md` with evidence.
2. Contrarian writes `docs/research/CONTRARIAN_SCOPE.md` challenging the dominant hypothesis.
3. Strategy-Architect synthesizes into `docs/plan/BOT_STRATEGY.md` with the chosen architecture and its justification.
4. A second contrarian pass red-teams the strategy.
5. Orchestrator records the ratified choice as `D-00X` in this file.

**Contrarian dissent:** N/A — this meta-decision IS the contrarian correction of the original D-002.

---

## D-004 — 2026-04-16 — Architecture committed

**Decision:** Primary bot (`RattleBot`) uses **α-β + iterative deepening + Zobrist transposition table** as search backbone, with **belief-as-leaf-potential** (no in-tree rat chance nodes), **root-only EV-gated SEARCH**, a **9-feature F2 linear heuristic** (Carrie-style cell-potential with distance discount as the 80→90 % lever), CMA-ES-tuned weights, and **adaptive iterative-deepening time management** (0.2 s safety + 0.6×/1.0×/1.6× multipliers, 2.5× cap). Full walk of SYN §G and resolution of all 22 D1–D22 open choices in `docs/plan/BOT_STRATEGY.md` (see its §2 and Appendix A).

**Rationale:** SYNTHESIS.md §B1/§B2/§B3/§B9 establish the expectiminimax + α-β + linear-heuristic backbone as cross-confirmed consensus across all four research tracks. Branching factor b ≈ 6.3–6.8 excluding SEARCH (SEARCH §A.2) makes depth-6–8 reachable in pure Python; leaf-as-belief-potential keeps b unchanged vs. explicit chance nodes (× 64 blowup). F2 linear (CMA-ES tuned) outperforms NN-from-scratch under 3-day deadline (HEUR §F, PRIOR §F anti-pattern 3). Carrie's heuristic shape is the documented 80→90 % delta (HEUR intro). Root-only SEARCH gate with `max_p > 1/3` + VoI bonus keeps in-tree branching at ≈ 7.

**Alternatives dismissed:**
- MCTS / PUCT / ISMCTS — SEARCH §B.5–B.7 suitability lower than α-β for this branching/depth regime; PUCT needs a prior we don't have.
- NN-from-scratch heuristic — anti-pattern at < 1-week timeline (PRIOR §F).
- In-tree rat chance nodes — branching factor blowup unjustified given HMM §F item 7's analysis that within-tree rat drift is ~3 % TV over 6 plies.
- Reactive-only (no tree) primary — SYN §F row 1 makes this a flip-trigger, not the default. FloorBot covers the grade-floor without sacrificing the 90 %+ ceiling.
- Beam search / null-move pruning / magic bitboards — SYN §B16, no sliding pieces, no Zugzwang-valid positions.
- MCTS rewrite as late-stage pivot — §8 non-goal unless v0.5 is insufficient at T − 12 h.

**Contrarian dissent:** Strategy-contrarian red-team is pending per PIPELINE.md Phase 1 exit. D-004 is committed provisionally; orchestrator will re-arbitrate after contrarian review.

---

## D-005 — 2026-04-16 — Module decomposition committed

**Decision:** Package `3600-agents/RattleBot/` consisting of: `agent.py` (entry point), `rat_belief.py` (HMM), `search.py` (α-β+ID+TT), `heuristic.py` (F2 linear eval), `move_gen.py` (ordered moves), `time_mgr.py` (adaptive time controller), `zobrist.py` (hash keys + move packing), `types.py` (BeliefSummary + TTEntry + Undo + MoveKey dataclasses). Interface and per-call budgets per `docs/plan/BOT_STRATEGY.md` §3. Headline numbers: TT = 2^20 × 2-slot depth-preferred+always-replace, belief = float64 (64,), leaf budget ≤ 100 μs tournament, HMM update ≤ 2 ms, `γ_info=0.3, γ_reset=0.5, ε_tiebreak=0.25`.

**Rationale:** Separation matches SYN §G's 10-step agenda and supports parallel v0.1 wave (dev-hmm, dev-search, dev-heuristic, dev-integrator concurrent). BeliefSummary interface decouples HMM from search leaf, allowing HMM dev-loop to ship independently. Zobrist table size calibrated against 1.5 GB RSS cap (SPEC §7) with 40 MB footprint.

**Alternatives dismissed:**
- Monolithic `agent.py` — prevents parallel dev; harder to audit; harder to ablate.
- Passing full 64-dim belief to every leaf vs. summary stats — adds per-call copy cost; summary stats cover F11/F12 needs at O(1).
- log-space HMM — unnecessary at 64 states with per-turn renorm (HMM §A.3).

**Contrarian dissent:** Pending.

---

## D-006 — 2026-04-16 — FloorBot is the live-submission baseline; RattleBot is promoted on gate

**Decision:** FloorBot (Task #9) is the **active live submission on bytefight.org from T − 60 h through primary-bot promotion**. RattleBot is promoted to live only after passing a 4-condition gate: (1) wins ≥ 60 % paired local matches vs FloorBot over 100 runs under `limit_resources=True`, (2) survives ≥ 200 matches without crash or timeout, (3) passes T-LIVE-1 (5-match live scrimmage vs George with ≥ 3 wins), (4) auditor sign-off on v0.3 code. Promotion is one-directional by default; orchestrator retains veto. RattleBot's `agent.py` embeds FloorBot's `emergency_fallback(board) -> Move` function as a try/except safety-net at every play-time call.

**Rationale:** CON §C-1 / SYN §F row 1: a crash-proof reactive bot gives grade-floor insurance — P(≥ 70 %) lifts from ~0.85 to ~0.92. The cost is ~ ½ dev-day of integrator review (FloorBot itself is owned by floor-bot-dev, not the RattleBot team). The promotion gate is falsifiable and paired — eliminates "I think it's better" hand-waving.

**Opponent-specific exploit track (CON §C-6, SYN §C7):** pre-scheduled for T − 36 h as a parallel side-track (dev-opponent-model produces a drop-in `min_node_estimator` keyed on `OPPONENT_MODEL` runtime flag). Conditional promotion based on T-OPP-1 (§5). Not a blocking path for v0.1–v0.4.

**Alternatives dismissed:**
- No FloorBot (SYN §C1 primary docs' position): leaves the floor uncovered; if RattleBot slips we get a 0 % grade. Rejected — the cost of parallel FloorBot is small and the insurance value is large.
- Opponent-exploit track as v0.5 optional (HEUR §D.3 position): underweights the highest-leverage alternative. Compromise is "scheduled but not blocking" — lets us absorb scrimmage evidence without committing dev-search/dev-heuristic.

**Contrarian dissent:** Pending.

