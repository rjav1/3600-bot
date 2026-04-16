# Research Pipeline — Process, not Strategy

**IMPORTANT:** This document describes the *workflow pipeline* — the process by which we will produce the real strategic plan. It does **NOT** prescribe the actual bot design; that comes later.

The actual technical/strategic plan (`docs/plan/BOT_STRATEGY.md` and `docs/plan/ARCHITECTURE.md`) is **produced by the Strategy-Architect ONLY AFTER** researchers have finished their investigations. Any assumptions below (e.g., "expectiminimax + HMM") are provisional working hypotheses the researchers must confirm, refine, or reject with evidence.

Research happens first. Strategic conclusions emerge from research, not from the orchestrator's guesses.

---

## Route: research → synthesis → plan → build → test → iterate

## Phase 0 — Foundations (hours 0–6)

**Parallel work streams:**

1. **Game-Analyst writes `docs/GAME_SPEC.md`**
   - Read every file in `engine/game/` + `engine/gameplay.py` + `engine/board_utils.py`.
   - Document: exact move semantics, exact rat noise model, perspective-flip conventions, edge cases discovered (e.g., what happens when a search hits a blocked square, carpet-roll semantics at edges).
   - Confirm or correct everything in `CLAUDE.md`.

2. **Researcher-A writes `docs/research/RESEARCH_HMM_RAT.md`**
   - Investigate HMM filtering on 8x8 grids with noisy observations.
   - Formalize: prior = δ_(0,0) @ T^1000; posterior update with the given noise + distance model.
   - Compute: what's the stationary distribution of the given Ts? How quickly does belief collapse? When is a search +EV?
   - Output: math + concrete numpy/jax recipe.

3. **Researcher-B writes `docs/research/RESEARCH_ADVERSARIAL.md`**
   - Investigate: expectiminimax with chance nodes, alpha-beta pruning in partial-info games, iterative deepening, move ordering for our move space, transposition tables for 8x8 bitboards.
   - Look at: chess-bot literature applicable to 8x8 bitboards, Sebastian Lague's series, standard heuristics for territory-painting games.
   - Output: algorithm spec + pseudocode.

4. **Researcher-C writes `docs/research/RESEARCH_PRIOR_ART.md`**
   - Search for: bytefight.org winners in prior years, similar games (paint-the-floor, rat-search HMM), relevant competition writeups.
   - Look at the class git history / example bots / public discussion channels for the course (if findable).
   - Document any leaks about how reference bots George/Albert/Carrie behave.

5. **Contrarian-0 writes `docs/research/CONTRARIAN_SCOPE.md`**
   - Challenge: is expectiminimax actually the right approach? Could a heuristic + pattern-match bot beat a naive expectiminimax due to time constraints? What non-obvious strategies could dominate?
   - Any concerns about the official grading being gameable (e.g., ELO rubber-banding, exploiting reference-bot weaknesses)?

**Exit criterion:** All five docs exist and have been cross-read. `docs/STATE.md` summarizes top 3 takeaways.

---

## Phase 1 — Strategy blueprint (hours 6–10)

**Strategy-Architect writes `docs/plan/BOT_STRATEGY.md`:**
- Synthesizes Phase-0 research into a coherent strategy.
- Decomposes into: move generation, rat tracker, search algorithm, evaluation heuristic, time manager, search-move decision policy, opponent modeling.
- Specifies interfaces between components.
- Lists expected point-per-turn targets and ELO projections.

**Contrarian-1 writes `docs/plan/CONTRARIAN_STRATEGY.md`:**
- Red-teams the blueprint.
- Identifies assumptions that may fail under adversarial play.
- Proposes 2+ alternative strategies the author didn't consider.

**Orchestrator arbitrates, records decision in `docs/DECISIONS.md`.**

---

## Phase 2 — Architecture & module specs (hours 10–13)

**Strategy-Architect + Dev-Integrator co-write `docs/plan/ARCHITECTURE.md`:**
- Module boundaries: `rat_belief.py`, `search.py`, `heuristic.py`, `move_gen.py`, `time_mgr.py`, `agent.py`.
- Exact function signatures.
- Data structures (e.g., belief grid layout, transposition table key).
- Performance budget per module per move.

**Contrarian reviews.**

---

## Phase 3 — Implementation wave 1 (hours 13–28)

**Parallel, with continuous auditor review:**
- Dev-HMM implements `rat_belief.py` + tests.
- Dev-Search implements `search.py` + tests.
- Dev-Heuristic implements `heuristic.py` + tests.
- Dev-Integrator implements `agent.py` stub + plugs in above.
- Auditor reviews each PR; writes `docs/audit/AUDIT_MODULE_*.md`.

**Exit criterion:** Bot runs end-to-end without crashing in ≥ 50 self-play matches vs Yolanda. Wins ≥ 90% of them.

---

## Phase 4 — Live scrimmage & first upload (hours 28–32)

- Tester-Live uploads v0.1 to bytefight.org via Chrome MCP.
- Scrimmages vs George, Albert, Carrie. Records ELO delta in `docs/tests/ELO_LEDGER.md`.
- Auditor reviews match logs to identify losing patterns.

**Exit criterion:** Beats George. Identifies top 3 weaknesses vs Albert/Carrie.

---

## Phase 5 — Iterate loop (hours 32 → deadline)

**Tight Ralph-loop:**
1. Pick the top weakness from latest audit.
2. Spawn a focused work-stream (researcher/dev/auditor triad).
3. Ship, test locally (≥ 50 matches), test live.
4. Update ELO ledger.
5. If improved, set as new baseline. If regressed, revert and log.

Continue until leaderboard position #1 confirmed and ELO > Carrie's + safety margin, OR deadline hits.

**Candidate iteration topics (already identified):**
- Opponent modeling (tracks their search belief about the rat).
- Endgame tablebase (last 8 turns often have tight exact EV calculations).
- Neural-net heuristic trained on self-play logs (if PACE resources viable in time).
- Opening book (first 4 moves from corners — tiny, can be hand-tuned).
- Anti-carrying-capacity heuristic (avoid over-priming in areas opponent will roll first).

---

## Phase 6 — Pre-deadline hardening (last 6 hours)

- Auditor does a full safety pass: no invalid moves possible, no timeouts, no crashes.
- Run 500-match local gauntlet vs every opponent strength we have.
- Live scrimmage final confirmation on bytefight.org.
- **Confirm activation of the final submission on bytefight.org before 23:59 April 19.**

---

## Budgets & constraints

- **Time/move (runtime):** 240 s / 40 moves = 6 s/move avg. Adaptive allocation: fewer on early obvious moves, more on midgame pivots, careful in endgame.
- **Init time:** 10–20 s. Use aggressively to precompute T^1000 prior, stationary distribution, corner-blocker reachability, etc.
- **Zip size:** ≤ 200 MB. NN weights if used must fit.
- **No network, no FS outside cwd.** Sandbox is strict.

---

## Risk log (live)

- Risk: expectiminimax too slow on full-move-space — Mitigation: prune to top-K by heuristic, use bitboard tricks, profile early.
- Risk: HMM floats overflow/underflow — Mitigation: log-space or normalized belief updates.
- Risk: Chrome MCP flakiness — Mitigation: manual upload fallback; script the upload if possible.
- Risk: Test games are stochastic — Mitigation: always 50+ matches per comparison.
- Risk: Deadline miss because activation forgotten — Mitigation: Checklist item at T-6hrs.
