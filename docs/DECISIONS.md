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
