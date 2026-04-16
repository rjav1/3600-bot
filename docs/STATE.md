# STATE — Rolling Snapshot

**Last updated:** 2026-04-16 (Phase 0 kickoff)
**Current phase:** Phase 0 — Foundations
**Deadline:** 2026-04-19 23:59

## Active agents

| Name               | Role                | Current task          | Status    |
|--------------------|---------------------|-----------------------|-----------|
| game-analyst       | game-analyst        | Write GAME_SPEC.md    | completed |
| (to be spawned)    | researcher-hmm      | RESEARCH_HMM_RAT.md   | pending   |
| (to be spawned)    | researcher-search   | RESEARCH_ADVERSARIAL.md | pending |
| (to be spawned)    | researcher-prior    | RESEARCH_PRIOR_ART.md | pending   |
| (to be spawned)    | contrarian-scope    | CONTRARIAN_SCOPE.md   | pending   |

## Recent decisions

- **D-001** (2026-04-16): Adopt multi-agent orchestration model per `TEAM_CHARTER.md`. Contrarian and researcher roles mandatory. Documents in `docs/` are single source of truth.
- **D-002** (2026-04-16): Architecture decision DEFERRED. No architecture pre-committed; it will be chosen by Strategy-Architect after research evidence is in. (Corrects earlier prejudgment.)
- **D-003** (2026-04-16): `docs/GAME_SPEC.md` landed. Ground-truth spec is authoritative over `CLAUDE.md`; see its §10 for the CLAUDE.md discrepancy list.

## Blockers

None yet.

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
