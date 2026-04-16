# RESEARCH_PRIOR_ART.md

**Author:** researcher-prior
**Date:** 2026-04-16
**Status:** initial investigation; some sections sparse (see honest-assessment below)

Investigation into prior art directly relevant to the CS3600 Sp2026 Carpet/Rat tournament. Every non-trivial claim is cited inline with a URL. Where a search produced no useful result, I say so plainly rather than pad.

---

## Section A — bytefight.org tournament history

**Platform summary.** ByteFight is a student-led AI competition platform that hosts course-specific challenges. More than 220 students participated in over 60,000 matches in the last CS3600 chicken-game run, and ranking uses an ELO-based system updated continuously as bots improve ([gatech.edu news](https://www.cc.gatech.edu/news/students-test-ai-strategies-chicken-game-competition-0)).

**Games hosted historically (public info):**
- **CS3600 prior semester — "Chicken Game"** — players try to lay the most eggs while avoiding hidden trapdoors. Exact semester not confirmed by the news article, but it predates Sp2026 ([gatech.edu news](https://www.cc.gatech.edu/news/students-test-ai-strategies-chicken-game-competition-0)).
- **CS6601 (graduate AI)** has also run challenges on the platform, per the same source ([gatech.edu news](https://www.cc.gatech.edu/news/students-test-ai-strategies-chicken-game-competition-0)).
- Student-org/interest-form posts confirm ByteFight runs multi-course competitions out of GT ([linkedin.com](https://www.linkedin.com/posts/tylerkwok_bytefight-interest-form-activity-7289698799730475008-eRyR), [instagram.com/bytefightgt](https://www.instagram.com/bytefightgt/)).

**Carpet/Rat game specifically.** I pulled the public ruleset from `https://bytefight.org/compete/cs3600_sp2026` (via Chrome MCP; WebFetch returned 403). The rules match what is in `CLAUDE.md` and `assignment.pdf` — **no additional public info on that page** beyond what we already have: 8x8 board, 40 turns each, 4 min total, point table -1/2/4/6/10/15/21, noise model, 1000-step headstart, TA bots George / Albert / Carrie tied to 70/80/90% tiers. **The public page contains no strategy tips, no example bots, and no leaderboard snapshot accessible without login.**

**Public leaderboard / past winners.** No publicly indexed leaderboard page surfaced for *either* the chicken game or the carpet game. The only named winner in the public record is **Jason Mo**, whose chicken-game bot "StockChicken" used **minimax with alpha-beta pruning plus Bayesian statistics** to estimate hidden trapdoor locations and focused on maximizing egg placement while blocking opponents ([gatech.edu news](https://www.cc.gatech.edu/news/students-test-ai-strategies-chicken-game-competition-0)). No code repository for StockChicken was locatable via search.

**Winner-writeup corpus: near-empty.** Searches for `"bytefight" winner strategy writeup`, `"StockChicken" github`, and `"bytefight" carpet` returned no personal blog posts, devposts, or GH repos from past competitors. One `bytefight` GH user exists but is unrelated (a different project by Jonas Leisgang). **There is no accessible archive of prior-semester bots.**

**Cached / archived cs3600 material.** Searches for CS3600 Piazza / Ed Discussion / prior course websites did not surface anything describing a carpet/rat variant of the game. Every GH repo I found for "CS3600 Georgia Tech" was from older semesters (2017-2022) focused on Pac-Man / MDP / Q-learning projects, not a tournament bot ([JerAguilon](https://github.com/JerAguilon/CS-3600-Georgia-Tech-Artificial-Intelligence), [sjain0913](https://github.com/sjain0913/IntrotoAI-CS3600-Projects), [Fried-man-Education](https://github.com/Fried-man-Education/CS_3600)). **The carpet/rat game appears to be new to Sp2026.**

---

## Section B — GT CS3600 prior-year projects

CS3600 is GT's Intro to AI course. Its projects have historically tracked the Berkeley CS188 Pac-Man curriculum (search/MDP/RL/inference) — *not* custom tournament bots. I reviewed public repos from multiple years:

- **[JerAguilon/CS-3600-Georgia-Tech-Artificial-Intelligence](https://github.com/JerAguilon/CS-3600-Georgia-Tech-Artificial-Intelligence)** — Pac-Man projects, Q-learning, no tournament bot.
- **[sjain0913/IntrotoAI-CS3600-Projects](https://github.com/sjain0913/IntrotoAI-CS3600-Projects)** (Sp2020) — same Pac-Man lineage.
- **[Fried-man-Education/CS_3600](https://github.com/Fried-man-Education/CS_3600)** (Fa2022) — same pattern.
- **[budiryan/CS3600](https://github.com/budiryan/CS3600)**, **[heenap98/CS-3600](https://github.com/heenap98/CS-3600)** — no tournament bot.

**Closest analogue that IS relevant: Berkeley CS188 "Ghostbusters" project** (aka "Busters"). This is essentially the same probabilistic-inference scaffolding we need for the rat tracker:
- Pacman gets **noisy distance readings** to invisible ghosts and must maintain a belief distribution over ghost positions ([CS188 Fall 2025 Project 4](https://inst.eecs.berkeley.edu/~cs188/fa25/projects/proj4/)).
- Students implement **exact inference (forward algorithm)** and **particle filtering** on the grid.
- The time-elapse update is `bel'(x') = Σ_x T(x'|x) bel(x)` and the observation update is `bel(x) ∝ P(obs|x) · bel(x)` — **directly applicable** to our rat belief ([CS188 Fall 2025 Project 4](https://inst.eecs.berkeley.edu/~cs188/fa25/projects/proj4/)).
- `busters.getObservationProbability(noisyDistance, trueDistance)` in that project plays the role of our distance-error table.

**Takeaway:** Our distance + floor-type + transition-matrix HMM is a direct extension of Berkeley Busters. Implementation reference code is widely available. **High value.**

---

## Section C — Related game genres

### C.1 Territory-painting games

- **Halite I/II/III** (Two Sigma's grid strategy contests). Top bots used heuristic **expansion mode** scoring each neutral cell by production/strength ratio, BFS for nearest viable target, and lookahead of ~2 steps. Winning bots explicitly relied on layered heuristics + A/B self-play testing rather than emergent / NN agents ([djma/halite-bot](https://github.com/djma/halite-bot), [Helw150/halite-3](https://github.com/Helw150/halite-3), [aidenbenner/halite3](https://github.com/aidenbenner/halite3)). **Takeaway: in a short timeline (days), heuristic + self-play A/B tuning beats NN training from scratch.**

- **Splatoon** (Turf War). Not academic AI research, but the published strategy-guide heuristics are suggestive: (1) cover-opponent-paint > cover-empty, (2) map-center control > perimeter, (3) deny opponent mobility ([venturebeat.com](https://venturebeat.com/2015/06/05/5-keys-to-winning-in-splatoon-like-dont-start-by-painting-your-base/)). Translates to: prefer carpets in zones that also block opponent rolls, prefer center-board primes over corner primes. **Takeaway: tactical heuristic intuitions, not research-grade, but useful priors.**

- **Game of the Amazons.** Territory-isolation game solved by minimax + mobility heuristic + territory-distance heuristic ([rmcqueen/game-of-the-amazons-ai](https://github.com/rmcqueen/game-of-the-amazons-ai)). The "distance to territory" flavor may inform Carrie's formula (see Section E).

### C.2 Hunter / prey with noisy sensors

- **CS188 Ghostbusters** (see Section B). Closest working analogue on earth. Already described.
- **Minesweeper AI.** Not quite the same (deterministic observations, not noisy), but the probabilistic-inference literature is well developed: Bayesian networks, tensor-based CPT inference, and the fact that Minesweeper inference is co-NP-complete ([minesweepergame.com PDF](https://minesweepergame.com/math/applying-bayesian-networks-in-the-game-of-minesweeper-2009.pdf), [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0950705122002842)). **Takeaway: our rat problem is easier than Minesweeper inference because our T and observation models are tractable closed-form (linear-size state space, sparse T).** Don't over-engineer.
- **Bomb-defusal / mobile-target search** literature is sparse in public search; nothing more useful surfaced.

### C.3 Line-of-k scoring (carpet-roll bonus analogue)

The carpet-roll point table `-1, 2, 4, 6, 10, 15, 21` super-linearly rewards length ≥ 5. That's a "connect-K" incentive structure.

- **Gomoku / Go-Moku.** The canonical heuristic counts partial-line threats (open-three, closed-three, open-four, closed-four, five) and sums weighted values per direction ([baeldung.com Gomoku TSS](https://www.baeldung.com/cs/gomoku-threat-space-search), [blog.theofekfoundation.org](https://blog.theofekfoundation.org/artificial-intelligence/2015/12/11/minimax-for-gomoku-connect-five/)). **Directly applicable:** our heuristic should evaluate *partial prime lines* (lengths 2–7) and credit the *potential* future roll, not just the current primes. Also: **Threat Space Search** (Allis 1994) reduces the search space to only moves that extend threats — a potential pruning technique for our move generator.
- **Arxiv survey on Gomoku: UCT-ADP + progressive bias** ([arxiv.org/pdf/1912.05407](https://arxiv.org/pdf/1912.05407)) — more advanced MCTS variants. Likely overkill for our deadline.

**Takeaway: The prime-line-extension incentive maps to well-studied Gomoku heuristics. Adopt threat-counting.**

---

## Section D — Competition-programming playbook

### Battlecode postmortems
- **Battlecode 2023 — "Don't @ Me"** (Zhang / Liao / Misri). Key lesson: **generalize code rather than map-specific tuning**. Their pathfinding used a single-pass radial edge-relaxation heuristic rather than full Bellman-Ford, and focusing on modularity + adaptability beat case-specific hacks ([PDF](https://battlecode.org/assets/files/postmortem-2023-dont-at-me.pdf)).
- **Battlecode 2020 postmortem** (stonet2000) and **Battlecode 2021** all emphasize **bytecode-budget discipline**: unrolled loops, individual variables instead of arrays, reversed-for-loop for cheapest iteration ([stonet2000.github.io/battlecode/2020](https://stonet2000.github.io/battlecode/2020/), [blog.stoneztao.com/posts/bc21](https://blog.stoneztao.com/posts/bc21/)). *Our constraint is time, not bytecode, but the equivalent discipline for us is: vectorize HMM updates with NumPy; represent board state as bitmasks (already done in `board.py`); avoid Python attribute lookup hot paths.*
- **Battlecode 2025 "Om Nom"** postmortem confirms the same pattern ([PDF](https://battlecode.org/assets/files/postmortem-2025-om-nom.pdf)).

### CodinGame heuristic practice
- Top CodinGame bot programmers prefer **well-tuned heuristics over emergent/NN** in time-limited contests ([codingame.com/blog/finding-the-right-heuristics-to-win](https://www.codingame.com/blog/finding-the-right-heuristics-to-win/)).
- Heuristic + A/B self-play is the dominant winning pattern at the 10-day-contest level — which is roughly our 3-day window.

### Halite (Section C.1 above) — lessons:
- Expansion-mode heuristics with 2-ply lookahead dominate.
- Score each candidate cell by an explicit "value/cost" ratio.
- Iterate fast: add a feature → A/B-test against prior bot → keep or revert.

### Expectiminimax + alpha-beta (the direct algorithm recommendation from `CLAUDE.md`)
- Wikipedia formalism is stable: chance nodes take a **weighted average** of children's expectiminimax values ([en.wikipedia.org/wiki/Expectiminimax](https://en.wikipedia.org/wiki/Expectiminimax)).
- **Alpha-beta pruning on chance nodes is tricky** but tractable if the evaluation function is bounded above and below ([CS440 lec19](https://courses.grainger.illinois.edu/ece448/sp2021/slides/lec19.pdf), [baeldung.com/cs/expectimax-search](https://www.baeldung.com/cs/expectimax-search)). *Confirmed non-trivial — researcher-search and dev-search must budget time for this or choose plain expectimax + minimax without full AB on chance nodes.*
- **Iterative deepening** is standard practice for time-budgeted game trees and also improves move ordering through stored PV ([Chessprogramming wiki — Iterative Deepening](https://www.chessprogramming.org/Iterative_Deepening)). *Given our global 240 s / 40 moves budget, iterative deepening with per-move time cap is the right skeleton.*

---

## Section E — Insider intel on George / Albert / Carrie

`assignment.pdf` / `CLAUDE.md` leaks are the authoritative public info. What they say:
- **George: ≥ 70% tier.** No lookahead. Greedily extends primes, rolls carpets when possible, does an opportunistic rat search when EV looks high.
- **Albert: ≥ 80% tier.** Expectiminimax + HMM rat tracker + "very simple heuristic."
- **Carrie: ≥ 90% tier.** Same framework as Albert but with a smarter heuristic: **"cell potential × distance from bot."**

### What does "cell potential × distance from bot" imply?

This is speculation, but it's informed speculation:

1. **"Cell potential"** almost certainly means a scalar-per-cell value summarizing the future reward available from that cell. Likely components:
   - If cell is SPACE → potential value of priming it (1 pt now, plus its contribution to expected future rolls).
   - If cell is PRIMED → potential value of rolling through it (contributes to line-bonus calculation).
   - If cell is CARPET or BLOCKED → 0 (or penalty because opponent can step on carpet).
   - Probably weighted by the **rat-belief mass** on that cell (because SEARCH EV depends on belief).
   This is structurally a **potential-field heuristic** — a classic A* / game-AI pattern ([Amit's Game-Programming Heuristics](http://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html)).

2. **"× distance from bot"** is counterintuitive if interpreted literally (you'd expect *inverse* distance: close cells are more reachable). Two plausible readings:
   - **(Our bot's) cell-potential / (bot's distance to cell)** — i.e., value discounted by reachability. This is the standard "reward per step" heuristic pattern and is what Halite top bots used ([Halite winner writeups](https://projects.johnqian.com/halite)). This is my most likely interpretation; the Piazza/assignment text possibly says *divided by* and `CLAUDE.md` paraphrased.
   - **Cell-potential × (opponent's distance - our distance)** — a **relative-control** score. This is the territory-control heuristic pattern common in Amazons / Tron / influence maps. Also plausible, especially since the game has two workers.

3. **Heuristic form.** Most likely `eval(board) = Σ_cells (cell_potential[c] · f(our_dist[c], opp_dist[c])) + belief_search_bonus + score_delta`, where `f` encodes how much "we control" cell `c`. *This is worth formalizing as a hypothesis in `BOT_STRATEGY.md` and testing empirically against a simpler heuristic.*

**Piazza / Ed-Discussion search.** I searched for cached CS3600 Piazza content referencing the carpet game and found nothing indexed publicly. Not surprising — Piazza content is auth-walled. **No credential misuse attempted.** If the team wants to check Piazza for clarifications on Carrie's heuristic, the user should do so manually.

**Takeaway on reference bots.**
- To beat George: any valid expectiminimax with even a basic heuristic should suffice (George has *no* lookahead). Estimated difficulty: low.
- To beat Albert: solid expectiminimax, real HMM (not just greedy belief mode), and a non-trivial heuristic. Difficulty: medium.
- To beat Carrie: need a heuristic that *outperforms* "cell potential × distance". This is the research frontier. Candidates include: (i) richer cell-potential with line-of-k threat counting (Gomoku-style), (ii) opponent modeling (track *their* belief and deny their good carpet rolls), (iii) lookahead-augmented belief rollout for informed search moves.

---

## Section F — Anti-patterns (what NOT to do)

Documented class-of-game anti-patterns, cited where possible:

1. **Uniform initial rat prior.** The rat takes 1000 silent steps from (0,0) before the game. Using uniform(1/64) as prior throws away substantial information — the correct prior is `e_{(0,0)} @ T^1000` which concentrates near the stationary distribution. Cited directly in `CLAUDE.md` §7.

2. **Assuming the rat model is static across games.** `T` is re-randomized per game with ±10% noise on `engine/transition_matrices/*.pkl`. Memorizing any specific `T` is wasted effort (per `CLAUDE.md`).

3. **Over-engineering with NN from scratch.** Halite, CodinGame, Battlecode history all show that **in a <1-week timeline, heuristics + A/B iteration beats training a policy net from zero** ([codingame.com/blog/finding-the-right-heuristics-to-win](https://www.codingame.com/blog/finding-the-right-heuristics-to-win/), Halite winners). With ~3 days left, NN is an anti-pattern.

4. **Naive alpha-beta on chance nodes.** Standard AB pruning is unsound over chance nodes unless bounds are adjusted. Either use a bounded-AB variant ([en.wikipedia.org/wiki/Expectiminimax](https://en.wikipedia.org/wiki/Expectiminimax)) or skip AB at chance nodes. Don't silently break correctness.

5. **Deep game tree with many chance-node children.** Our rat belief spans 64 cells × 3 noise values × 4 distance offsets = up to 768 chance outcomes per ply. Full expansion of chance nodes is infeasible. Options: **collapse chance nodes by taking expected evaluation under current belief** (i.e., don't branch on future sensor obs), or **Monte Carlo sample a small number of belief-futures.**

6. **Priming lines you cannot actually roll.** Priming is +1 per square BUT prevents you from plain-stepping onto your own primed squares. Primes-that-never-get-rolled are pure loss of tempo. `CLAUDE.md` §7 already flags this.

7. **Ignoring `exclude_search=True` default in `get_valid_moves`.** Known gotcha, but warrants restating — it silently excludes searches from move generation.

8. **Invalid move = instant loss.** Any custom move generator must be fuzz-tested against `board.is_valid_move`. Standard rule in this class of contest.

9. **Not using init time.** `__init__` has its own 10–20 s budget that is separate from the 240 s play budget. Use it to precompute `T^1000`, stationary distribution, blocked-corner reachability LUT, etc. Not doing so burns scarce midgame time.

10. **Over-eager searches.** Search-move EV is +EV only when P(rat-there) > 1/3. Searching at lower probability is usually negative expectation (unless the information value is high late-game). George reportedly does "opportunistic" searches — we shouldn't imitate *naive* George; we should gate search on a hard belief-mass threshold that decays over turn-count to accept information-value late.

---

## Section G — Actionable takeaways (ranked)

### HIGH value (implement these; they are direct wins)

1. **Adopt the CS188 Ghostbusters HMM recipe verbatim** for the rat tracker. Exact forward-algorithm inference is tractable on 64 cells, and the project provides a canonical pseudo-code: time-elapse `bel'(x') = Σ_x T(x'|x) bel(x)` then observation `bel(x) ∝ P(noise|cell_type(x)) · P(dist_obs | |worker−x|₁) · bel(x)` ([CS188 Fall 2025 Project 4](https://inst.eecs.berkeley.edu/~cs188/fa25/projects/proj4/)). *Why directly applicable: the noise model and distance-offset distribution are almost identical in structure to busters; only the exact likelihood numbers differ.*

2. **Gomoku-style line-extension heuristic for prime/carpet evaluation.** Our carpet-roll bonus table is super-linear in length — same incentive as connect-K. Use threat-counting: for each direction from each prime, count the *open* contiguous-prime-line length and credit the potential roll value ([baeldung.com Gomoku TSS](https://www.baeldung.com/cs/gomoku-threat-space-search)). *Why: strictly better than "count primes" because it captures the 5/6/7-length jackpot.*

3. **Iterative-deepening expectimax (minimax + chance at sensor nodes) with bounded alpha-beta.** Standard time-budgeted game-tree skeleton ([chessprogramming.org Iterative Deepening](https://www.chessprogramming.org/Iterative_Deepening), [en.wikipedia.org/wiki/Expectiminimax](https://en.wikipedia.org/wiki/Expectiminimax)). *Why: gives us a graceful time-vs-depth tradeoff and is what Albert/Carrie already use, so we *must* match or exceed.*

4. **Potential-field heuristic with cell_value × reachability_discount.** Codify the likely form of Carrie's heuristic (Section E) as a baseline to beat. Then iterate. *Why: directly closes the gap to Carrie; any improvement over this exact form tips the tier.*

5. **Use `__init__` aggressively for precomputation.** T^1000 prior, stationary distribution, distance-from-any-cell tables for each potential worker position, line-of-k LUTs per (row, column, diagonal? — no, this game has only cardinal rolls). *Why: free compute off the 240 s clock.*

### MEDIUM value (likely worth doing if time permits)

6. **Halite-style A/B self-play harness.** Every heuristic change tested ≥50 matches vs the prior version ([Halite winner writeups](https://github.com/djma/halite-bot)). *Why: cheap; turns vibes-engineering into evidence-driven engineering.*

7. **Particle-filter fallback for the HMM.** If exact 64-cell inference bottlenecks late in a game, particle filtering is the standard approximation ([CS188 Project 4](https://inst.eecs.berkeley.edu/~cs188/fa25/projects/proj4/)). *Why: insurance. Likely unnecessary at 64 cells but trivial to add.*

8. **Opponent modeling of their rat belief.** Track a *second* belief grid approximating what the opponent believes, so we can (a) anticipate their search moves and (b) avoid making carpets where they'll gain most. *Why: in section C.1 Splatoon-style, denying opponent value scales with 2× (opponent's gain prevented is equivalent to own gain).*

9. **Threat-space move-ordering pruning** (Gomoku TSS variant). Prioritize moves that extend existing prime-lines at the root of the search tree to improve alpha-beta cutoffs ([baeldung.com Gomoku TSS](https://www.baeldung.com/cs/gomoku-threat-space-search)). *Why: substantial branching-factor reduction late-game.*

### LOW value (mentioned for completeness; do not pursue)

10. **Neural-net heuristic trained on self-play.** Halite winners and CodinGame blog ([codingame.com](https://www.codingame.com/blog/finding-the-right-heuristics-to-win/)) agree: at ≤1 week timeline, heuristic-iteration wins. *Why low: risk of eating the deadline with infra plumbing, PACE GPU flakiness, and zip-size limits (200 MB).*

11. **MCTS / AlphaZero-style from scratch.** Same reason. MCTS variants of Gomoku exist ([arxiv.org/pdf/1912.05407](https://arxiv.org/pdf/1912.05407)) but are overkill for 80-ply games.

12. **Minesweeper-style Bayesian-network inference.** Our inference problem is easier than Minesweeper (tractable forward algorithm); Bayesian-network machinery is overkill ([minesweepergame.com PDF](https://minesweepergame.com/math/applying-bayesian-networks-in-the-game-of-minesweeper-2009.pdf)).

13. **Memorizing specific `bigloop.pkl`, `hloops.pkl` structure for the rat T.** `T` is noise-perturbed per game and renormalized; hard-coded rat behavior would be incorrect (per `CLAUDE.md` §7).

---

## Honest assessment: what prior art is sparse or absent

- **No public writeup from any past ByteFight competitor** — chicken or otherwise — beyond the gatech.edu news blurb about Jason Mo. The winner-writeup corpus that exists for Battlecode, Halite, CodinGame does *not* exist for ByteFight as of today.
- **No public code for StockChicken** (the only named ByteFight winner).
- **No public Piazza / Ed Discussion archive** for CS3600 carpet-rat discussion (auth-walled).
- **No prior-semester variant of the carpet/rat game** is findable — this game appears to be new to Sp2026.
- **No direct academic paper on "rat-hunting with noisy-distance + noisy-floor-type observations on a partially-blocked grid."** We are extrapolating from the Berkeley Busters analogue.

Consequence: we are **not going to win by copying a prior winner's bot**. We will win by executing the Battlecode-postmortem-style discipline (modular code, A/B-tested heuristics, graceful time management) on top of well-understood primitives (CS188 HMM, Gomoku heuristics, expectiminimax).

---

## Citations (consolidated)

- [Georgia Tech CoC news — Students Test AI Strategies in Chicken Game Competition](https://www.cc.gatech.edu/news/students-test-ai-strategies-chicken-game-competition-0)
- [ByteFight — CS3600 Spring 2026 Tournament Rules (public page)](https://bytefight.org/compete/cs3600_sp2026)
- [Berkeley CS188 Project 4 — Ghostbusters / HMM inference (Fall 2025)](https://inst.eecs.berkeley.edu/~cs188/fa25/projects/proj4/)
- [Wikipedia — Expectiminimax](https://en.wikipedia.org/wiki/Expectiminimax)
- [Wikipedia — Alpha-beta pruning](https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning)
- [Chess Programming Wiki — Iterative Deepening](https://www.chessprogramming.org/Iterative_Deepening)
- [Baeldung — Win Gomoku with Threat Space Search](https://www.baeldung.com/cs/gomoku-threat-space-search)
- [Theofek Foundation — Minimax for Gomoku](https://blog.theofekfoundation.org/artificial-intelligence/2015/12/11/minimax-for-gomoku-connect-five/)
- [CodinGame Blog — Finding The Right Heuristics To Win](https://www.codingame.com/blog/finding-the-right-heuristics-to-win/)
- [djma/halite-bot (Halite I winner-ish)](https://github.com/djma/halite-bot)
- [Helw150/halite-3 (Halite III gold-ranked)](https://github.com/Helw150/halite-3)
- [aidenbenner/halite3](https://github.com/aidenbenner/halite3)
- [Battlecode 2023 postmortem — Don't @ Me](https://battlecode.org/assets/files/postmortem-2023-dont-at-me.pdf)
- [Battlecode 2025 postmortem — Om Nom](https://battlecode.org/assets/files/postmortem-2025-om-nom.pdf)
- [stonet2000 Battlecode 2020 postmortem](https://stonet2000.github.io/battlecode/2020/)
- [Battlecode 2021 postmortem (Stone)](https://blog.stoneztao.com/posts/bc21/)
- [Applying Bayesian networks in the game of Minesweeper (PDF)](https://minesweepergame.com/math/applying-bayesian-networks-in-the-game-of-minesweeper-2009.pdf)
- [ScienceDirect — A solver of single-agent stochastic puzzle: Minesweeper](https://www.sciencedirect.com/science/article/pii/S0950705122002842)
- [VentureBeat — 5 keys to winning in Splatoon](https://venturebeat.com/2015/06/05/5-keys-to-winning-in-splatoon-like-dont-start-by-painting-your-base/)
- [UCT-ADP Progressive Bias for Gomoku (arxiv)](https://arxiv.org/pdf/1912.05407)
- [Amit's Game-Programming Heuristics](http://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html)
- [CS440 lecture 19 — Alpha-Beta and Expectiminimax (PDF)](https://courses.grainger.illinois.edu/ece448/sp2021/slides/lec19.pdf)
- [Baeldung — Expectimax Search Algorithm](https://www.baeldung.com/cs/expectimax-search)
- [rmcqueen/game-of-the-amazons-ai](https://github.com/rmcqueen/game-of-the-amazons-ai)
