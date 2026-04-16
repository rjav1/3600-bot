# Team Charter — CS3600 Carpet-Bot Project

**Goal:** Submit the #1 ranked agent (ELO) on bytefight.org/compete/cs3600_sp2026 by **2026-04-19 23:59**. Score must be ≥ 90% (i.e., rank above Carrie, the strongest reference bot).

**Today:** 2026-04-16. ~3 days left.

---

## 1. Operating model

This is a multi-agent orchestration with a human-facing orchestrator (Claude-Code session) and a team of sub-agents. Philosophy:
- **Everyone is a PhD researcher.** No jumping to conclusions. Every decision is backed by evidence, not vibes. Hypothesis → experiment → evidence → decision.
- **Everything is a document.** Research outputs, plans, audits, test results, decisions — all written to `docs/` so future agents (post-context-compaction) can pick up seamlessly.
- **Orchestrator does NOT deep-dive.** Orchestrator's context is sacred. It delegates to subagents, reads only *summaries* of their outputs (referenced by path), and coordinates.
- **Contrarians enforce rigor.** Every major design decision has an assigned contrarian whose job is to find holes, biases, and blind spots. Balance = primary proposal + contrarian critique + synthesizer reconciliation.
- **Context compaction hygiene.** When an agent nears 200k tokens, it hands off via a detailed state-dump document to a fresh successor. Named state files make this recoverable.
- **Ralph-loop style iteration.** Research → plan → build → test → audit → iterate. Each loop leaves the bot measurably stronger or the decision log more informed.

## 2. Roles

| Role              | Count | Responsibility                                                             |
|-------------------|-------|----------------------------------------------------------------------------|
| Orchestrator      | 1     | Human session; plans phases, delegates, arbitrates, never deep-dives.      |
| Game-Analyst      | 1     | Deep reading of engine source + assignment.pdf; writes ground-truth spec. |
| Researcher        | 2–3   | Read papers / prior art / references; write RESEARCH_*.md outputs.        |
| Strategy-Architect| 1     | Synthesizes research into a BOT_STRATEGY.md blueprint.                     |
| Contrarian        | 1     | Red-teams every plan/code/heuristic. Finds holes. Balanced, not reflexive.|
| Dev-HMM           | 1     | Implements Hidden-Markov rat belief tracker.                                |
| Dev-Search        | 1     | Implements expectiminimax / alpha-beta / iterative-deepening.              |
| Dev-Heuristic     | 1     | Implements evaluation function.                                             |
| Dev-Integrator    | 1     | Glues components, manages agent.py entry point.                            |
| Auditor           | 1     | Code review, performance profiling, invariant checking.                    |
| Tester-Local      | 1     | Runs large-batch local scrimmages, writes RESULTS_*.md.                    |
| Tester-Live       | 1     | Uses Chrome extension to upload/scrimmage on bytefight.org.               |

Agents can be added/retired as needs evolve. New agents must read `docs/STATE.md` and their role-specific docs before acting.

## 3. Shared documents (source of truth)

All under `docs/`:
- `STATE.md` — rolling snapshot: current phase, active agents, active blockers, last 3 decisions.
- `BACKLOG.md` — prioritized task queue (distinct from TaskList tool; this is the design-level backlog).
- `DECISIONS.md` — append-only decision log with rationale and contrarian dissent.
- `GAME_SPEC.md` — authoritative game-mechanics spec (from Game-Analyst).
- `research/RESEARCH_*.md` — research outputs, one topic per file.
- `plan/BOT_STRATEGY.md` — the master strategy blueprint.
- `plan/ARCHITECTURE.md` — code architecture (modules, interfaces).
- `audit/AUDIT_*.md` — audit findings.
- `tests/RESULTS_*.md` — match results, ELO tracking, ablations.

## 4. Protocols

### Starting a new task
1. Read `docs/STATE.md` (always).
2. Read the doc for your role/task.
3. Before acting, write a 1-paragraph plan comment on the task.
4. Produce output as a markdown document in the appropriate folder.
5. Update `docs/STATE.md` with what you just did.
6. Mark task completed.

### Before a major decision
1. Proposer writes proposal in `docs/decisions/PROPOSAL_<N>.md`.
2. Contrarian writes critique.
3. Orchestrator arbitrates in `docs/DECISIONS.md` (one paragraph: choice + reasoning + dismissed alternatives).

### Context-compaction handoff
If nearing context limit:
1. Write `docs/state/HANDOFF_<agent-name>_<timestamp>.md` containing: goal, work done, open loops, next action.
2. Orchestrator spawns successor with the handoff doc as required reading.

## 5. Testing infrastructure

- **Local:** `python3 engine/run_local_agents.py <ours> <opp>`; stochastic, so always run **≥ 50 matches** per candidate-vs-baseline comparison. Automate a batch runner.
- **Live:** bytefight.org via Chrome browser MCP tools. Upload zip, scrimmage vs George/Albert/Carrie, record ELO deltas.
- **ELO tracking:** maintain `docs/tests/ELO_LEDGER.md`.

## 6. Definition of Done

- Agent beats Yolanda ≥ 95% on 50-match local runs.
- Agent beats George ≥ 75% on local runs.
- Agent wins vs Albert majority on live scrimmages (ELO positive).
- Agent wins vs Carrie majority on live scrimmages (ELO positive).
- Agent uploaded & activated on bytefight.org.
- Leaderboard ranking confirmed #1 (or tied #1) with final ELO ≥ Carrie's + margin.
