# STATE — Rolling Snapshot

**Last updated:** 2026-04-16 (Phase 0 kickoff)
**Current phase:** Phase 0 — Foundations
**Deadline:** 2026-04-19 23:59

## Active agents

| Name               | Role                | Current task          | Status  |
|--------------------|---------------------|-----------------------|---------|
| (to be spawned)    | game-analyst        | Write GAME_SPEC.md    | pending |
| (to be spawned)    | researcher-hmm      | RESEARCH_HMM_RAT.md   | pending |
| (to be spawned)    | researcher-search   | RESEARCH_ADVERSARIAL.md | pending |
| (to be spawned)    | researcher-prior    | RESEARCH_PRIOR_ART.md | pending |
| (to be spawned)    | contrarian-scope    | CONTRARIAN_SCOPE.md   | pending |

## Recent decisions

- **D-001** (2026-04-16): Adopt multi-agent orchestration model per `TEAM_CHARTER.md`. Contrarian and researcher roles mandatory. Documents in `docs/` are single source of truth.
- **D-002** (2026-04-16): Architecture decision DEFERRED. No architecture pre-committed; it will be chosen by Strategy-Architect after research evidence is in. (Corrects earlier prejudgment.)

## Blockers

None yet.

## Open loops

- Agent folder for our bot has not been created yet. Recommended name TBD (proposed: `RattleBot`).
- No test infrastructure yet; Tester-Local will build a batch runner in Phase 3.
- bytefight.org credentials / session — Tester-Live needs to confirm the user is logged in on Chrome before uploads.

## Pointers (required reading for new agents)

- `CLAUDE.md` — project-level brief (read first).
- `docs/TEAM_CHARTER.md` — operating model.
- `docs/PIPELINE.md` — process pipeline (research-first workflow; NOT a strategic plan).
- `docs/STATE.md` — this file (always).
- Role-specific doc (e.g., for researcher: `docs/research/RESEARCH_QUESTIONS.md` once written).
- `engine/game/*.py` — ground-truth source.
- `assignment.pdf` — official spec.
