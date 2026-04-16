# CONTRARIAN_SCOPE — Red-team of the pipeline, CLAUDE.md, and the orchestrator's anchored assumptions

**Author:** contrarian-scope
**Date:** 2026-04-16
**Scope:** This document is a structured, evidence-based critique *before* any strategic plan is committed. It is not a strategy. Its job is to surface real risks and force the rest of the team to choose with eyes open.

Overall: the pipeline is **structurally sound but scope-anchored**. The single most dangerous move the orchestrator has already made is treating "expectiminimax + HMM + hand-heuristic" as the provisional baseline. With 3 days to deadline, **budget ≠ research**; every hour spent confirming the staff-bot architecture is an hour not spent building what beats it. Section F lists concrete changes I recommend **right now** (before Phase 1).

No **pipeline-halting** critical issue found. Several **HIGH-priority** items worth escalating — flagged inline and in §F.

---

## Section A-prime — Verification of GAME_SPEC / STATE §33 top-3 discoveries (added 2026-04-16 post-GAME_SPEC)

Team-lead asked me to sanity-check the three "surprising" claims in `docs/STATE.md` §33. Verdicts:

### Claim 1 — Local 360 s vs tournament 240 s time budget. **CONFIRMED, HIGH-PRIORITY.**
Source: `engine/gameplay.py:232-238`. `play_time = 240` then overridden to `360` when `limit_resources=False`. `init_timeout` likewise 10 s → 20 s. This matches my §A-1 finding. **Strategy-Architect must not miss this.** All local benchmarking that doesn't set `limit_resources=True` is running at 1.5× the tournament CPU budget; any "6 s/move average" tuning derived from the default driver is optimistic. Mitigation in §F-1.

### Claim 2 — `apply_move(SEARCH)` is a no-op; scoring happens in `play_game`. **CONFIRMED, HIGH-PRIORITY.**
Source: `engine/game/board.py:256-258` (SEARCH case is `pass` before `end_turn`); scoring logic in `engine/gameplay.py:434-443`. This matches my §A-5 finding. **Consequence for Dev-Search (high-impact):** any expectiminimax that uses `forecast_move` to simulate a SEARCH will get (a) no point delta (+4/-2), (b) no rat respawn, (c) no belief reset. The search-node expected-value calculation must be written by hand; do NOT trust `forecast_move` for this move type. This is the single highest-risk engine quirk I've seen.

### Claim 3 — Spawns can land on BLOCKED cells. **PARTIALLY CORRECT — literally true at the code level, but the consequence does not materialize given the actual corner shapes.**

`engine/board_utils.py:186-190`: `generate_spawns` samples `x ∈ {2,3}`, `y ∈ {2,3,4,5}` with no query of `board._blocked_mask`. So the code **does not** defend against a blocked spawn. That part of the claim is correct.

**But:** with the hard-coded corner shape set `[(2,3), (3,2), (2,2)]` (`engine/gameplay.py:255`), I ran the overlap check manually for each of 3 shapes × 4 corners against the spawn set:
- TL 3×2 covers x∈{0,1,2} y∈{0,1} — hits x=2 OR y<2, never both in the spawn set.
- TL 2×3 covers x∈{0,1} y∈{0,1,2} — hits y=2 but x<2, not spawn.
- BL 2×3 covers x∈{0,1} y∈{5,6,7} — hits y=5 but x<2, not spawn.
- BL 3×2 covers x∈{0,1,2} y∈{6,7} — hits x=2 but y>5, not spawn.
- Right-side corners are symmetric for B's spawn (x∈{4,5}).

**No corner block in the current shape set can reach A's (x∈{2,3}, y∈{2..5}) or B's mirror.** The engine is accidentally safe.

**Net:** GAME_SPEC/STATE's wording ("spawns can land on BLOCKED cells") is **overstated in its consequence but correct about the missing defensive check**. The underlying vulnerability means:
- If course staff ever adds a 3×3 or 4×2 corner shape, spawns **will** collide silently.
- For our bot in this tournament, **no defensive code is needed against blocked-spawn.**

**Recommendation to Strategy-Architect:** note in GAME_SPEC as "the engine does not defend against blocked-spawn; safe only by coincidence of the current shape set." Do NOT spend implementation time on spawn-recovery logic. I recommend game-analyst tighten the STATE §33 wording; I'll propose the edit if team-lead wants it.

---

## Section A — Factual errors / misleading claims in `CLAUDE.md`

Line-by-line. Each claim is verified against the engine source. I flag errors (wrong), misleading (technically ok but invites a bug), and underspecified (missing info that matters).

### A-1. (HIGH) CLAUDE.md §1 time budget is wrong for local dev runs
> "**4 minutes total** across all 40 of your moves" — CLAUDE.md:26

`engine/gameplay.py:232-238` sets `play_time = 240` only when `limit_resources=True`. The default driver (`python3 engine/run_local_agents.py`) runs with **`limit_resources=False`**, which sets `play_time = 360` and `init_timeout = 20`. CLAUDE.md never mentions the 50% gap. **Consequence:** bots tuned on local 6-min-budget will time out in tournament. `docs/GAME_SPEC.md` must record both numbers and the team must develop against the tournament number (240 s) with a safety margin, not the dev number.

### A-2. (HIGH) Spawn geometry is narrower than CLAUDE.md suggests
> "Players spawn **horizontally mirrored** in the inner 4×4 (x ∈ {2,3,4,5}, y ∈ {2,3,4,5})." — CLAUDE.md:31

`engine/board_utils.py:186-190`:
```python
x = random.randint(BOARD_SIZE // 2 - 2, BOARD_SIZE // 2 - 1)  # 2 or 3
y = random.randint(BOARD_SIZE // 2 - 2, BOARD_SIZE // 2 + 1)  # 2..5
return (x, y), (BOARD_SIZE - 1 - x, y)
```
So A's x ∈ **{2, 3}** (only two values), B's x is mirrored ∈ {4, 5}; **both on the same y**. A is always on the left, B always on the right. That is a **strong structural invariant** the orchestrator's pipeline has not exploited. An opening book (see §C) is radically more feasible than CLAUDE.md implies — the distinct starting situations are just `2 x-values × 4 y-values × 3^4 corner-shape configurations = 648` spawn topologies, many of which are symmetric. That's on the border of tractable.

### A-3. (MEDIUM) Noise-table headers mislabeled in the assignment PDF vs. the code
`assignment.pdf` p.3 labels the noise columns "Squeak / Scratch / Squeal" but the prose above says "The rat can make the following noises: squeak, scratch." — Squeal is omitted from the prose but is a valid Noise enum value (`engine/game/enums.py:33`, `engine/game/rat.py:10-15`). **Trust the code**, not the prose. CLAUDE.md captures all three correctly.

### A-4. (MEDIUM) Carpet-roll semantics: CLAUDE.md is technically correct but easy to misread
> "Destination square must not be blocked or primed." — CLAUDE.md:15 (prime-step row)
> "roll over k contiguous primed squares in a straight line, converting them all to CARPET" — CLAUDE.md:16

Correct per `is_valid_move` / `is_cell_carpetable` (`engine/game/board.py:108-120, 552-575`), but the **critical** detail CLAUDE.md hides: `is_cell_carpetable` returns False if the enemy worker is on the primed cell (board.py:564-567). **So the opponent can park on your prime-line and deny you the roll.** This is an exploitable mechanic and belongs in GAME_SPEC. The Dev-Heuristic must account for it.

### A-5. (MEDIUM) "SEARCH does not move" but also `apply_move` does nothing for SEARCH
`apply_move` with `MoveType.SEARCH` calls `end_turn(timer)` but **does not score the +4/-2** — the scoring is done in `gameplay.py:434-443` *outside* `apply_move`. CLAUDE.md never mentions this and the search-EV calculation in any self-play simulator we build must duplicate that logic, not call `apply_move`. **This is a silent footgun for Dev-Search's simulation.**

### A-6. (LOW) Rat headstart claim slightly misleading
> "the rat has taken 1000 silent steps from (0,0) before the game starts. The initial belief should be `e_{(0,0)} @ T^1000`, **not** uniform." — CLAUDE.md:211

True, but there's a subtler point: the rat's **T is generated with ±10% multiplicative noise then row-renormalized per game** (`engine/gameplay.py:22-29`). Since the noise is applied to all entries (including the ~59 zeros per row) and then clipped at 0, the nonzero structure is strictly preserved (zeros stay zero because `0 * (1+noise) = 0` and `maximum(., 0)` doesn't introduce new nonzeros). So the belief math is clean: the prior is `e_{(0,0)} @ T^1000` with the **actual game T**, not one of the 4 base matrices. CLAUDE.md:210 says the right thing. Good.

### A-7. (MEDIUM) "Both out of turns → higher points wins (ties allowed)" — missing tiebreaker
`board.check_win` (board.py:299-305) declares TIE on equal points with WinReason=POINTS. ELO systems typically treat ties as 0.5 for each side. **A draw is ≥ 50% of a win for ELO purposes; if the team heuristic ever reaches "good enough to tie Carrie", the ELO impact is nonzero.** The heuristic eval should have an explicit "prefer a guaranteed tie over a 40/60 win-loss gamble" knob. CLAUDE.md doesn't suggest this.

### A-8. (LOW) Seccomp sandbox — CLAUDE.md gives a partial picture
CLAUDE.md:199: "**No network**, no FS writes outside cwd, no reading outside cwd." The code (`engine/player_process.py:44-134`) is stricter and weirder:
- `exit` syscall is KILLed (line 121). That's fine for normal Python exits (which use `exit_group`) but could bite if the agent spawns a child that expects to call raw `exit`.
- `unlink`, `rename`, `mkdir`, `creat` are commented out → **file creation, deletion, and rename are allowed** inside cwd. We can do more than CLAUDE.md implies — e.g. persist a lookup table during init and read it during play, although init-time writes are probably simpler.
- `ioctl` is commented out → allowed. `prctl` and `seccomp` are KILLed (line 107, 110).
- `execve`/`execveat` is KILLed — **no subprocess spawn**. This rules out shelling out to a precompiled C++ binary.
- `clock_settime`/`adjtimex` killed but `clock_gettime` not touched — wall-clock reads work.

The sandbox differences between local dev (`limit_resources=False`, **no seccomp at all** — see player_process.py:210-218) and tournament (`limit_resources=True`) are a substantial test-vs-prod gap. **HIGH-priority risk:** we may write code that only fails under seccomp.

### A-9. (LOW) Memory limit is ~1.5 GB, not 200 MB
CLAUDE.md:198 focuses on the 200 MB zip limit. The runtime memory limit is `limit_mb = 1536` (player_process.py:166), i.e. **1.5 GB RSS** per agent, 4 GB VRAM if GPU. Much more headroom than the zip size suggests. We can load larger precomputed tables.

### A-10. (LOW) `forecast_move` semantics footnote
CLAUDE.md:86 says `forecast_move` "does **not** reverse perspective." Correct. But `forecast_move` also defaults to `check_ok=True` and returns `None` on invalid moves (board.py:199-216). In a tight search loop, check_ok=False is 30-50% faster but risks crashing. This trade-off is worth surfacing in GAME_SPEC.

### A-11. (MEDIUM) Libraries in assignment.pdf vs. `requirements.txt`
`assignment.pdf` p.4 lists: numpy, PyTorch, JAX, FLAX, Plyvel, Scikit-learn. `requirements.txt` (per CLAUDE.md:108) adds numba, psutil, cython, torch, pynvml. **Plyvel** (leveldb) is in the PDF but not typically discussed — could be used for large precomputed KV stores. **Numba** and **Cython** offer 10-100× speedups on hot loops. CLAUDE.md barely mentions them. **The team's time-budget maths should account for numba-JITed inner loops.**

### A-12. (LOW) `ALLOWED_TIME = 240` constant exists but isn't authoritative
`engine/game/enums.py:15` defines `ALLOWED_TIME = 240`. But this constant is unused in the game loop (which uses `play_time` passed to `Board.__init__`). If a team member trusts the constant but gameplay.py has `play_time=360` locally, confusion ensues. Not a bug, just a doc trap.

---

## Section B — Unstated assumptions in `PIPELINE.md`

### B-1. (HIGH) "Research-first" is not free with 3 days on the clock
`PIPELINE.md` Phase 0 allots 6 hours to research. Phase 1 (blueprint) another 4 hours. Phase 2 (architecture) another 3. **That's 13 hours before any code ships.** With ~72 hours total and iteration loops in Phases 4-5 needing at least 12-16 hours to be meaningful, the schedule already consumes 25+ hours on documents.

**Risk:** Research-quality docs are a lagging indicator of project velocity. If researchers over-deliver at 8 hours each instead of ~4, we lose the iteration loop. Empirically: many of the hardest wins in game-AI come from *implementation-level* tricks (bitboard move-gen, transposition tables, evaluation tuning) discovered during Phase 5. The pipeline underweights phases 4-6 relative to their ELO impact.

**Honest mitigation:** Timebox Phase 0 hard to 4 hours, not 6. Set a "minimum viable bot" milestone (expectiminimax depth-2 + uniform-belief tracker + greedy heuristic) to ship by hour 18, regardless of research quality. Iteration loops beat perfect research on a 3-day horizon.

### B-2. (HIGH) Pipeline anchors on expectiminimax+HMM by describing it as "provisional"
`PIPELINE.md` line 5: "Any assumptions below (e.g., 'expectiminimax + HMM') are provisional working hypotheses the researchers must confirm, refine, or reject with evidence." That is the language of someone who will *rationalize the chosen hypothesis.* The `RESEARCH_ADVERSARIAL.md` task (line 29) is literally "Investigate: expectiminimax with chance nodes, alpha-beta pruning..." — **the researcher's mandate is to flesh out expectiminimax, not to compare it against alternatives.** This is confirmation bias baked into the pipeline.

**Evidence:** CLAUDE.md:191 already commits: *"Realistic path to 90%+: solid expectiminimax, good heuristic on prime/carpet potential, tight HMM tracker."* `D-002` says "deferred" but the research questions are shaped like expectiminimax is the answer.

**Mitigation:** Rewrite `RESEARCH_ADVERSARIAL.md` brief to explicitly compare ≥3 architectures (expectiminimax, MCTS, pure-policy) with back-of-envelope ELO projections before any module gets designed.

### B-3. (MEDIUM) "50-match batches are statistically sound"
`TEAM_CHARTER.md` line 73 / `PIPELINE.md` line 141 mandate ≥50 matches per comparison. Standard error for a win-rate of p on n matches is √(p(1-p)/n). For p=0.55, n=50 → σ ≈ 0.070, 95% CI ±0.14. That means two bots that truly differ by 5 percentage points in winrate will look statistically tied in 50 matches. **To detect a 5pp improvement at 95% confidence you need ~400 matches.**

Given the board stochasticity (random T, random spawns, random blocked corners, random rat), 50 matches will give noisy go/no-go signals. We will make wrong keep/revert decisions.

**Mitigation:** (a) Use paired-match design (same T, same spawns, same seeds — both bots see identical boards; only the agent differs). Paired variance is much lower. (b) Run 200-match batches on finalist candidates. (c) Use sequential testing (SPRT) to stop early when signal is clear.

### B-4. (MEDIUM) "bytefight.org scrimmages give real-ELO signal"
`PIPELINE.md` Phase 4: upload and scrimmage. The ELO system on bytefight before the final reset might:
- Have a population heavily biased toward random starters (inflated ELO for our bot).
- Pair us against opponents we choose (selection bias in our favor).
- Not include a reference bot we beat once but would lose to on a bad T.

**Claim worth stress-testing:** scrimmage ELO ≠ tournament ELO. Tournament pairings are (presumably) uniform random after 1500 reset. Our scrimmage ELO may be an overestimate if we've cherry-picked opponents.

**Mitigation:** Every live scrimmage should log opponent identity, T-hash if obtainable, and match result. Maintain a separate ELO against each reference bot (George/Albert/Carrie specifically) — not an aggregate ELO.

### B-5. (MEDIUM) "Beating Albert/Carrie is achievable in 3 days"
Albert (80%) uses expectiminimax + HMM + simple heuristic. Carrie (90%) uses expectiminimax + HMM + "cell potential × distance" heuristic. If our team writes the **same architecture + a marginally better heuristic**, we converge to Carrie's strength, not above it. The pipeline's implicit strategy is "same architecture, tune the heuristic harder" — that is *differential improvement* over a known-good baseline, which is hard to do reliably in 3 days.

**Honest probability estimate (mine, open to challenge):**
- P(beat George, 70%+ grade floor) ≈ 0.90
- P(beat Albert, 80%+ grade floor) ≈ 0.55
- P(beat Carrie, 90%+ grade floor) ≈ 0.25
- P(top #1 leaderboard) ≈ 0.05

If the team's real goal is "maximize expected grade", the 70%→80% transition yields the biggest expected-grade gain per engineering hour. **Spend the last 24 hours on robustness (no crashes, no timeouts, beats George 80%+) rather than chasing Carrie.**

### B-6. (LOW) "Albert/Carrie are deterministic" — unverified
CLAUDE.md and the assignment describe Albert/Carrie but we have no evidence they're deterministic. If they are, we can extract exploitable patterns; if they randomize (e.g. Carrie tiebreaks randomly), we can't. **Test this assumption early** by running 5 scrimmages with identical T/spawn (if bytefight allows) and checking move sequences.

### B-7. (MEDIUM) No explicit model of the two-agent partnership risk
`TEAM_CHARTER.md` never mentions the *human* partner. The pipeline assumes a single hand-in-the-wheel orchestrator. In reality rahil has a partner (per assignment p.5, working in a team). **Risk:** partner uploads a divergent version 10 minutes before deadline and overwrites the team's bytefight submission. **Single point-in-time failure.**

**Mitigation:** Establish explicit lock-in protocol. Our orchestrator should confirm via the user which teammate has the authoritative login and when final submission will be activated. Ideally rahil makes the final activation and it is timestamped.

---

## Section C — Alternative architectures dismissed too quickly

For each, I give: (concept), (argument for), (cost to build), (P(beats Carrie)), (honest verdict).

### C-1. Pure reactive policy (hand-tuned decision tree / feature-rules bot)

**Concept:** No game tree. For each state, compute ~20 features (own carpet-roll EV in each direction, best prime extension length, belief mass in cell under worker's attack radius, own/opp points gap, turns left) and apply a hand-tuned priority list: "if best_carpet_value ≥ 4, take it; else if belief_mass_at_best_search > 0.4, search; else extend prime in highest-EV direction; else plain-step toward unprime-dense area." Move compute in <10 ms. 98% of time budget unused.

**Argument for:** Albert/Carrie's expectiminimax is shallow (likely depth 2-3; the branching factor per ply is ~12-20 moves plus 64 search moves = ~80, times 64 rat positions as chance nodes — *they* can't go deep either). If their evaluator dominates shallow search, a *better evaluator* without search may beat a *worse evaluator* with search.

Additional win condition: a reactive bot that **never times out** and never errors has an absolute ELO floor against buggy expectiminimax bots that occasionally eat too much clock.

**Cost:** 1 day to design the feature set + tune. Can be iterated quickly.

**P(beats Carrie):** 0.20 — unlikely to beat a well-tuned eval-function bot, but not impossible. **Sleeper threat:** probably beats Albert (0.55 P) just by being more consistent. A reactive bot as a *backup submission* is cheap insurance.

**Verdict:** Build this **as v0** in the first 8 hours. Ship it to bytefight by hour 12 as our grade-floor submission. Replace only if the search-based bot beats it in 200-match paired play.

### C-2. Opening book

**Concept:** Per §A-2, the initial state space is small — ~648 distinct spawn topologies (2 x-values × 4 y-values × 3^4 corner configs), many symmetric. First 4-6 moves can be **offline-optimized** by running expectiminimax at depth 8-10 on each spawn class, cached as a lookup table. At runtime, look up the precomputed first N moves, then switch to online search.

**Argument for:** Opening theory dominates chess at all levels. The rat's prior at game start is the same for every game of a given T-class (δ_0 @ T^1000 + a few turns) — so "what do I do on turn 1" is substantially a solved problem given T.

**Cost:** 1 day to write the offline optimizer. Depends on having a working engine first.

**P(beats Carrie):** As a standalone architecture, ~0.10. As a **complement** to online search, +5 to +10 pp of win-rate — which could be the margin we need. **Higher confidence as an add-on** than as a replacement.

**Verdict:** Plan to integrate in Phase 5 if time permits. The research-phase T-analysis by researcher-hmm can compute the T-stationary-ish prior for free.

### C-3. MCTS / UCT with a smart rollout policy

**Concept:** Replace expectiminimax with UCT. Belief over rat position emerges implicitly: rollouts sample rat trajectories; tree statistics reflect the chance nodes.

**Argument for:** MCTS handles large branching factors and stochasticity gracefully without requiring a heuristic function. Assignment PDF p.9 explicitly sanctions MCTS. On 8×8×40 turns, rollouts are cheap.

**Cost:** 1.5-2 days for correct implementation (it's easy to write buggy UCT). Tuning exploration constant and rollout policy takes iteration.

**Risk:** vanilla UCT with random rollouts may lose to a well-tuned heuristic bot on a short horizon. It needs AlphaZero-style policy/value guidance to be strong, and we don't have self-play training time.

**P(beats Carrie):** 0.15 — high variance, needs implementation excellence. Poor fit for a 3-day deadline unless the dev-search already has strong MCTS muscle memory.

**Verdict:** **Reject for primary architecture.** The team's dev-capacity is better spent on expectiminimax. But: MCTS-with-handcrafted-rollout could be a useful *auxiliary* for endgame tree search where belief is tight.

### C-4. Endgame tablebase (last N turns solved)

**Concept:** Last 5-8 turns of the game have small remaining move-tree (worker is likely trapped in a corner of useful territory; few new primes possible; search becomes extremely high-EV as belief concentrates). Solve exactly with deep search + full expectiminimax.

**Argument for:** The heuristic's biggest weakness is endgame — a value function trained on mid-game is systematically wrong in endgame because the "potential" of a cell drops to zero when there aren't enough turns to realize it. Exact search fixes this.

**Cost:** 0.5 day to add a "turns_left ≤ N → run deeper exact search" branch.

**P(beats Carrie marginal contribution):** +3 to +5 pp winrate if it catches a handful of close endgames per match.

**Verdict:** **Build this** late in Phase 5. Cheap, high ROI, bounded risk.

### C-5. Two-agent ensemble / vote

**Concept:** Run two search bots (e.g. different depth budgets, or different heuristics) and arbitrate between moves (prefer the move both agree on; fall back to the stronger's choice).

**Argument for:** Diversity bonus against deterministic opponents who've been engineered against a known architecture.

**Cost:** Deceptively high. Two bots cost 2× time budget (we only have 240 s total per game). Coordination logic is fiddly.

**P(beats Carrie):** 0.10 — the time budget eats most of the gain.

**Verdict:** **Reject.** Not worth it on 4-minute budget.

### C-6. Adversarial-mirror / opponent-specific exploitation

**Concept:** Build an explicit model of Albert/Carrie's likely moves (same expectiminimax + HMM + known heuristic shape). Tree-search against **that specific** opponent model, not a generic minimax opponent. If Carrie's heuristic favors "cell potential × distance", predict she'll walk toward high-potential cells, and prime/carpet to trap her there.

**Argument for:** Knowing the opponent's evaluation function gives large exploitation edge. Tournament games against George/Albert/Carrie are ≥ 3/5 of the grading signal.

**Cost:** 1 day to reverse-engineer their heuristics (partly guessable from CLAUDE.md descriptions, confirmable by observing scrimmage move patterns). 0.5 day to integrate.

**P(beats Carrie):** 0.25-0.35 — this is the **highest-leverage alternative** I've identified. It directly attacks the grading bots rather than trying to be generally strong.

**Verdict:** **Strongly recommend** investing 1 day in opponent modeling in parallel with the generic bot. This is an unstated high-EV option.

### Summary table

| Architecture               | Build cost | P(beats Carrie) | Role |
|----------------------------|------------|-----------------|------|
| Reactive policy            | 1 day      | 0.20            | v0 grade-floor submission |
| Opening book               | 1 day      | 0.10 (standalone) / +5-10pp | Add-on to search |
| MCTS UCT                   | 1.5-2 days | 0.15            | Reject for primary |
| Endgame tablebase          | 0.5 day    | +3-5pp          | Build in Phase 5 |
| Ensemble vote              | 1 day      | 0.10            | Reject |
| **Opponent-specific exploit** | **1 day**  | **0.25-0.35**   | **Strongly recommend** |
| Expectiminimax + HMM (baseline) | 2 days  | 0.30            | Primary |

**Net recommendation on architecture choice:** Don't pick one. Build a small reactive-policy floor bot (C-1) by hour 12 as insurance. Run expectiminimax+HMM as primary in parallel. Add opponent-modeling (C-6) in Phase 5. Skip MCTS and ensemble.

---

## Section D — Grading-system gaming (ethical within rules)

### D-1. ELO optimization tactics
- **Submit late, not early.** Every scrimmage before the ELO-reset is wasted effort from a grading perspective. Test exhaustively, but activate the final submission as close to the deadline as safely possible to maximize info about the final field. CLAUDE.md already flags the activation checklist; make it a hard rule.
- **Don't scrimmage against weak bots publicly once confident.** If the final ELO is computed *including* pre-reset scrimmages (this needs verifying — `assignment.pdf` p.6 says "ELO will be reset to 1500 when the final submissions are locked in", which suggests pre-reset history is discarded, but confirm with the course staff / ed discussion), then no gaming opportunity. But do confirm.
- **Choice of scrimmage opponents.** Early-phase, scrimmage only against reference bots (George/Albert/Carrie). Learn their patterns. Avoid scrimmages against other student bots — they leak our strategy and give no information about grading thresholds.

### D-2. Exploitable weaknesses of reference bots (speculative, to be confirmed)

- **George** is "no lookahead; greedily extends primes + rolls carpet" (CLAUDE.md:184). **Exploit:** parking on George's prime line denies him rolls (§A-4). Greedy bots don't re-plan after denial — they'll stay stuck on sub-optimal local moves. Force George into a corner, prime-line him in, take the game by carpeting around him.
- **Albert** uses "very simple heuristic" (CLAUDE.md:185) in expectiminimax. **Exploit:** simple heuristic = likely doesn't value piece-mobility or territory. Can probably beat Albert by making moves that look bad to Albert but are good to us (fork him between two prime-lines).
- **Carrie** uses "cell potential × distance from bot" (CLAUDE.md:186). **Exploit:** this heuristic is greedy about nearby potential — it undervalues *contest* of high-potential cells the opponent is about to roll. If we prime high-potential regions that Carrie will roll for us, she'll help us by carpeting our primes in convenient spots. Lure-and-harvest play.

**Verdict:** All three weaknesses are hypothesis-grade, not confirmed. A 2-hour observation session of live scrimmage play (replay logs) against each would confirm/refute and inform the heuristic.

### D-3. Dominant-strategy corner cases
None found in 30 minutes of looking. The game is not trivially solvable. Carpet-roll EV table (n=5,6,7 → 10, 15, 21 pts) means *one* long roll beats several short rolls; if we can build a 7-prime line that the opponent can't park on, we win instantly. **Long-line setup strategy** deserves heuristic weight.

### D-4. Risk-averse submissions near deadline
Assignment p.6: "Whatever you have uploaded/activated at 11:59pm on April 19th 2026 will be used." The activation step is distinct from upload. Dominant-strategy advice: **never activate an untested version.** Keep two bots active at all times — a known-good one and a candidate. Promote the candidate only after ≥200 paired matches.

---

## Section E — Risks underweighted by the orchestrator

### E-1. (HIGH) Seccomp sandbox divergence (dev vs tournament)
Re-stating from §A-8 because it's critical: the **default local run has NO seccomp** (player_process.py:210-218). Tournament environment has the full seccomp sandbox. If we use a library call that hits a KILLed syscall (e.g. any test code that unintentionally touches `prctl`, `seccomp`, or `execve`), we pass dev and fail tournament.

**Mitigation:** Write a dev script that runs matches with `limit_resources=True`. Add this to the Phase 4 checklist. Specifically test: jax/jnp import paths (they touch `prctl`), numpy with threading, pickle loads at init time.

### E-2. (HIGH) `time_left` granularity and noise
`time_left` is computed via `time.perf_counter()` (player_process.py:207-208) inside the subprocess. Accuracy is typically microseconds on Linux. But:
- **Process pausing/resuming** (SIGSTOP/SIGCONT, player_process.py:532-627) inside the gameplay loop pauses the subprocess between turns. Wall-clock while paused doesn't count. *But* the gameplay driver uses `time_left - (get_cur_time() - start)` in the **subprocess**, so within a turn, it's accurate.
- **GC pauses or JIT compilation** in the subprocess can consume 100s of ms. JAX's first compilation is notoriously slow. **Init-time matters:** any JIT compile that's deferred to first `play()` call will eat ~1-5 seconds of our 240-s budget. Force JIT in `__init__`.

**Mitigation:** (1) Measure `time_left()` frequently in the search loop (every node if possible, since node eval is fast). (2) Reserve a 500-ms buffer per turn. (3) In `__init__`, pre-trigger any JAX JIT compilation with a dummy call.

### E-3. (MEDIUM) ±10% T noise breaks pre-trained models
If we train an NN or precompute a belief table against a fixed T (e.g. `bigloop.pkl` loaded from disk), the actual game T will differ by up to 10% per entry, renormalized. Stationary distribution shifts noticeably under 10% per-entry noise. A cached T^1000 against `bigloop` is off from the real T^1000 after 1000 steps.

**Mitigation:** Recompute T^1000 in `__init__` from the actual passed-in transition_matrix. Don't cache anything T-dependent from disk. CLAUDE.md:123-124 warns about this but the pipeline hasn't assigned anyone to enforce it.

### E-4. (MEDIUM) Rat respawn resets belief
`engine/gameplay.py:436-439`: when the rat is caught (search succeeds), `rat.spawn()` runs, which re-initializes to (0,0) and runs 1000 silent moves again. Our belief grid must reset to `δ_0 @ T^1000` on our own successful searches AND on our opponent's successful searches (we see opponent_search result — `engine/gameplay.py:457-460`).

**Mitigation:** This is a straightforward bug risk. Dev-HMM must handle it and it should be an explicit test case.

### E-5. (MEDIUM) Init timeout is 10 s in tournament, 20 s in local dev
`engine/gameplay.py:233-238`. Another dev-vs-prod gap. Computing T^1000 with jax/numpy is fast (<1 s) but if we precompute belief propagation tables, stationary distributions, mixing-time bounds, etc., we may blow the 10 s tournament init budget while succeeding locally.

**Mitigation:** Always time `__init__` with `limit_resources=True`. Budget init at ≤7 s target, 10 s hard limit.

### E-6. (LOW) Two-partner version control
Re-stated from §B-7. The partner can overwrite our submission. Establish upload/activation ownership.

### E-7. (LOW) Zip contents — `__pycache__`, `.DS_Store`, etc.
If we zip the agent folder on macOS and include `.DS_Store`, bytefight's import may succeed but a stray file import could fail under seccomp (e.g. if `__pycache__` has a stale binary). Zip cleanly via `zip -r BotName.zip BotName -x '*/__pycache__/*' '*.pyc' '.DS_Store'`.

### E-8. (LOW) Pickling state in `forecast_move`'s `get_copy`
`board.get_copy()` copies bitboards and workers but **not** the history (by default). If our search uses `forecast_move` in a tight loop, each call allocates a new Board object (~112 bytes of state + Worker copies). 10^6 forecasts = 100+ MB GC pressure. Use bit-level undo if search is hot.

**Mitigation:** Dev-Search should implement a make/unmake pattern rather than pure `forecast_move` to avoid GC death.

---

## Section F — Rank-ordered recommendations (do these NOW)

1. **[HIGH] Correct CLAUDE.md on time budget (dev=360, tournament=240).** Add a note: "All local benchmarking MUST use `limit_resources=True` before comparison." This is item A-1. Without this fix, every RESULTS_*.md is misleading.

2. **[HIGH] Fix the sandbox test gap.** Add a task: "Run a full match with `limit_resources=True` and `user_name/group_name` set, once the reactive bot stub exists." Make this a hard Phase-3 exit criterion. (Item E-1.)

3. **[HIGH] Rewrite `RESEARCH_ADVERSARIAL.md` brief to compare architectures, not just expectiminimax.** The current task anchors on one solution. Add explicit asks: "compare expectiminimax vs MCTS vs reactive policy, with time-budget and ELO estimates." (Item B-2.)

4. **[HIGH] Ship a reactive-policy floor bot by hour 12**, before any architecture decision. This is our "at least 70% grade" insurance. It does NOT need to be good — it needs to never crash, never time out, and beat Yolanda. Upload to bytefight as a reserved backup activation.

5. **[HIGH] Confirm partner-submission protocol with the user.** Who activates? When? Is rahil the designated submitter? (Item B-7 / E-6.)

6. **[MEDIUM] Switch to paired-match evaluation (same T, same seed, both bots play same board).** 50 paired matches beats 200 unpaired. Noise reduction: ~3×. (Item B-3.)

7. **[MEDIUM] Update `docs/GAME_SPEC.md` task** to explicitly include:
   - spawn geometry (from §A-2)
   - opponent-can-block-carpet rule (§A-4)
   - search scoring happens outside `apply_move` (§A-5)
   - rat-respawn-on-catch belief reset (§E-4)
   - all memory/time/init differences between dev and tournament (§A-1, §E-5).

8. **[MEDIUM] Add an "opponent modeling" track in Phase 5.** Spend 1 day of dev time explicitly exploiting George/Albert/Carrie weaknesses (§C-6). This is higher-ROI than a 3rd heuristic tweak.

9. **[MEDIUM] Set an explicit grade-target hierarchy in DECISIONS.md:**
   - Primary: beat Albert (80%+). P ≈ 0.55.
   - Stretch: beat Carrie (90%+). P ≈ 0.25.
   - Floor: beat George (70%+). P ≈ 0.90.
   Align time allocation to where marginal effort yields marginal grade. Don't spend 20 hours chasing Carrie when the reactive bot isn't yet beating George reliably.

10. **[LOW] Pre-trigger JAX JIT in `__init__`.** Add as architectural constraint. (Item E-2.)

11. **[LOW] Make `is_cell_carpetable` behavior with enemy on cell a tested invariant** in any self-play simulator. (Item A-4.)

12. **[LOW] Document the 1.5 GB RSS budget** in CLAUDE.md. We have more room than the 200 MB zip limit suggests — can cache bigger tables. (Item A-9.)

---

## Honest meta-assessment

The pipeline is **generally sound**: document-driven, role-specialized, contrarian-enforced, state-handoff-ready. The biggest things working in its favor: clear entry criteria, defined artifacts, and explicit compaction hygiene. A weaker team would have committed to expectiminimax in hour 1 without a D-002; this team at least noticed.

The biggest thing working *against* it: research-phase scope creep in a 3-day sprint. **If Phase 0 runs more than 5 hours, stop it and force-ship the reactive floor bot.** The research docs are a means to an end, not the end.

My confidence in the final strategy emerging well from this pipeline: **moderate** (~60%). My confidence that we'll at least clear the 70% floor: **high** (~90%). My confidence that we'll beat Carrie: **low-moderate** (~25%, honest). The pipeline is better than the probable outcome, which is a fine place to be — it means we have optionality if things go well.

No pipeline-halting issue. Proceed to Phase 1 with items F-1 through F-5 addressed first.
