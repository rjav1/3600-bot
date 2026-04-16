# RESEARCH_HEURISTIC.md — Heuristic-Evaluation Theory for Carpet/Rat

**Author:** researcher-heuristic
**Date:** 2026-04-16
**Status:** v1.2 — updated 2026-04-16 with GAME_SPEC.md §10 amendments (§H) and explicit task-brief checklist mapping (§I).

**Why this document matters:** per `assignment.pdf` §9, Albert and Carrie share the same expectiminimax + HMM backbone. The *only* difference that moves a bot from the 80% tier to the 90% tier is heuristic quality. Carrie is literally described as using "an estimate of the potential of each cell and its distance from the bot". This document is the leverage point for the whole project.

Scope: the heuristic is a function `h(board, belief_grid) -> float` evaluated at leaves of expectiminimax. It must be cheap (called thousands of times per move) *and* informative. Everything below treats that trade-off explicitly.

No code; pseudocode and formulas only. Source simulations were run in bare Python (see Section A).

---

## Section A — The scoring landscape

### A.1 Raw point sources (from `engine/game/enums.py::CARPET_POINTS_TABLE` and `board.apply_move`)

| Source | Points | Turn cost |
|---|---|---|
| Prime step | +1 | 1 turn, converts current cell SPACE → PRIMED, moves worker to neighbor |
| Carpet roll of length k | CARPET_POINTS_TABLE[k] = {1:-1, 2:2, 3:4, 4:6, 5:10, 6:15, 7:21} | 1 turn |
| Search correct (P > 0) | +4 | 1 turn |
| Search wrong | −2 | 1 turn |
| Plain step | 0 | 1 turn (positioning only) |

### A.2 Prime-then-roll sequence value (k primes + 1 roll)

A "clean" sequence is: prime k times along a straight line, then roll length k back over them (worker ends one cell past the roll line's start). Total cost = k+1 turns. Total points = k + CARPET[k].

| k | prime pts | roll pts | total pts | turns | pts/turn | Δpts vs k−1 |
|---|---|---|---|---|---|---|
| 1 | 1 | −1 | 0 | 2 | 0.000 | — |
| 2 | 2 | 2 | 4 | 3 | **1.333** | +4 |
| 3 | 3 | 4 | 7 | 4 | **1.750** | +3 |
| 4 | 4 | 6 | 10 | 5 | **2.000** | +3 |
| 5 | 5 | 10 | 15 | 6 | **2.500** | +5 |
| 6 | 6 | 15 | 21 | 7 | **3.000** | +6 |
| 7 | 7 | 21 | 28 | 8 | **3.500** | +7 |

**Key observations:**

1. **PPT is strictly increasing in k.** Longer rolls are pure Pareto-better *per turn*, not just per roll. A 7-roll is 2.7× more efficient per turn than a 2-roll.
2. **Marginal value of the (k+1)-th prime is superlinear from k=3 onward.** Going 4→5 adds 5 pts, 5→6 adds 6, 6→7 adds 7. So once you've already primed 4, each additional prime is cheap (1 turn) and adds 5–7 pts. This is the "keep extending" heuristic flag.
3. **k=1 is a trap.** Rolling a single prime is −1 raw (i.e. you primed for +1 and then rolled for −1 = net 0 over 2 turns). It's *never* profitable absent positional reasons.
4. **k=2 is the minimum viable roll** (+4 pts over 3 turns, 1.33 PPT).

### A.3 Theoretical ceilings over a 40-turn budget

Assuming no interference, a bot that does nothing but prime-then-roll with fixed k:

| Strategy | Cycles in 40 turns | Total pts | PPT |
|---|---|---|---|
| Loop k=2 | 13 cycles × 4 + 1 leftover | 52 | 1.30 |
| Loop k=3 | 10 cycles × 7 | **70** | 1.75 |
| Loop k=4 | 8 cycles × 10 | **80** | 2.00 |
| Loop k=5 | 6 cycles × 15 + 4 leftover | **90** | 2.25 |
| Loop k=6 | 5 cycles × 21 + 5 leftover | **105** | 2.62 |
| Loop k=7 | 5 cycles × 28 | **140** | 3.50 |

The k=7 ceiling requires five separate 7-long empty lines on the board; the 8×8 board has corner blockers so this is basically impossible to sustain. The k=6 strategy (5 cycles × 21 = 105 pts) is the *aspirational* ceiling. **Realistic target is 80–110 points**, dominated by k=3–6 sequences. Anything over ~80 should win the game absent interference.

### A.4 Rat-search value

- Break-even: P(rat in chosen cell) > 1/3 (since 0.333·4 − 0.667·2 = 0).
- EV at P = 0.5: +1.0 point per turn.
- EV at P = 1.0: +4.0 points per turn (rare).
- **But search has secondary value**: even a wrong search is a *hard negative* observation that collapses probability mass elsewhere. This can be worth more than the −2 direct loss when belief is diffuse (entropy reduction argument — see §E).

### A.5 Implication for the heuristic: "long-horizon potential" dominates

Because a single k=6 roll is worth 21 points (≈ half a typical game score) and requires 6 contiguous primeable cells, the heuristic *must* value *the ability to build long lines* more than instantaneous point count. A bot that greedily rolls k=2s will max out around 50–60 points. A bot that waits, builds k=5–6 lines, and rolls cleanly will beat it on score. **This is what Carrie's "cell potential × distance from bot" phrase is gesturing at.**

---

## Section B — Cell-potential modeling

A "cell potential" `P(c)` for cell `c` estimates the **expected future points the bot can capture by eventually owning the priming initiative at or near `c`**. It is a surrogate for deep minimax lookahead; the heuristic uses it to value board positions that haven't been rolled yet.

### B.1 Candidate definitions

Let `reach(c, d)` = the number of contiguous non-blocked, non-carpet, non-opponent-worker cells in direction `d ∈ {U,D,L,R}` starting from `c` (inclusive of `c` itself up to the first blocker).

**Candidate B.1 — Best-roll potential (greedy cell-only):**
```
P_1(c) = max over directions d of roll_value(min(reach(c,d), 7))
where roll_value(k) = CARPET_POINTS_TABLE[k] if k >= 2 else 0
```
Simple; captures the biggest single roll achievable if we were standing on `c` with a fully-primed line already in front of us. Under-counts because it ignores the prime cost that already paid for that line; in leaf evaluation we want to include already-earned prime points separately (see §C).

**Candidate B.2 — Direction-weighted sum (multi-roll potential):**
```
P_2(c) = sum over directions d of w_d · roll_value(min(reach(c,d), 7))
```
with e.g. `w_d = 0.25` uniform. This captures that a cell with long reach in two directions (an "intersection") is more flexible than one with only one direction. Risks double-counting: two rolls from `c` cost more prime turns than one.

**Candidate B.3 — Flexibility-weighted sum:**
```
P_3(c) = max_d roll_value(reach(c,d))   +   λ · (second_best_d roll_value(reach(c,d)))
```
with `λ ≈ 0.3`. First term is the "primary shot". Second term is a "flexibility bonus" for cells with two good options (robust against opponent blocking). Recommended default for the Phase-3 implementation.

**Candidate B.4 — Distance-discounted (Carrie-style):**
```
P_4(c) = P_base(c) / (1 + α · manhattan_dist(worker, c))
```
with `α ∈ [0.2, 0.5]`. Values *reachable* potential more than far-away potential, because a far-away opportunity costs turns to reach. This matches the assignment's phrase "cell potential × distance from bot". Two interpretations:
- **Interpretation 1 (per-cell max):** `H = max_c P_base(c) / (1 + α · dist)` — single best future opportunity.
- **Interpretation 2 (weighted sum):** `H = Σ_c P_base(c) / (1 + α · dist)` — total territory accessible.

Interpretation 2 is richer but slower. Interpretation 1 is fast and probably what Carrie does.

**Candidate B.5 — Opponent-adjusted potential:**
```
P_5(c) = P_4(c) · (1 − β · P_opp_reaches_first(c))
```
where `P_opp_reaches_first(c) ≈ 1` if opponent is strictly closer to `c` by Manhattan, `0.5` if tied, `0` if we're strictly closer. Penalizes lines the opponent can eat first (either by rolling a prime line we started, or by plain-stepping into the empty space and priming first).

### B.2 Recommended default

`P_3` composed with `P_4`'s distance discount and `P_5`'s opponent adjustment:

```
P(c) = [max_d roll_value(min(reach(c,d), 7))
        + λ · second_best_d roll_value(min(reach(c,d), 7))]
       · (1 − β · P_opp_first(c))
       / (1 + α · dist(worker, c))
```

with starting guesses `λ = 0.3`, `α = 0.3`, `β = 0.5`. Board-level summary:

- **`H_cell = max_c P(c)`** (our best future shot)
- **`H_cell_opp = max_c P(c | worker = opponent)`** (their best future shot)
- Use `H_cell − H_cell_opp` as a differential feature.

### B.3 Interpreting "cell potential × distance from bot"

The phrase is ambiguous. Three plausible readings:

1. **Product (elementwise):** `H = Σ_c potential(c) · f(dist(bot, c))` with `f` *decreasing* — Carrie values a rich cell near the bot, discounts rich cells far away. Matches reading 2 above.
2. **Product (scalar):** `H = max_c potential(c) · f(dist)` — single best reachable opportunity.
3. **Literal multiplication:** `H = Σ_c potential(c) · dist(bot, c)` with `f(d) = d` — this would value far cells *more* than near ones, which is nonsensical for a time-pressured bot. Almost certainly **not** what Carrie does.

**Our working assumption: reading 1.** It generalizes the "territory control" concept from Go/Risk to this game.

### B.4 Cost of computing P(c)

Naively, `P(c)` for all 64 cells requires 4 ray scans from each cell = 4·64 = 256 ray traces. Each ray is up to 7 cells. Total ≈ 1800 ops per heuristic call. At ~6 s/move budget and expectiminimax reaching ~10k leaves, that's 18M ops, manageable if written in numpy/bitboard style. **Precompute the 4 direction rays as 64×4 arrays of (reach_length, roll_value)** per board-state and reuse. Better: incremental update when only one cell changes.

---

## Section C — Feature list for a linear / small-NN evaluator

The heuristic is called at every leaf of expectiminimax. It must be fast. A linear blend of well-chosen features is our baseline.

### C.1 Primary features (MUST HAVE — these are the ~7 features the linear heuristic needs)

| # | Name | Formula | Rationale |
|---|---|---|---|
| F1 | **score_diff** | `ours.points − theirs.points` | The ground truth. At terminal nodes this *is* the answer. Away from terminal, it's a lower bound on future. |
| F2 | **turns_left** | `ours.turns_left` | Multiplier on how much future potential matters. At `turns_left=0`, only F1 matters. |
| F3 | **our_cell_potential** | `max_c P(c)` from §B.2 (our worker) | Biggest future roll we can realistically score. |
| F4 | **opp_cell_potential** | `max_c P(c)` (from opp perspective) | Mirror of F3; predicts what they'll score. |
| F5 | **our_prime_owned** | count of bits in `primed_mask ∩ our_primes_history` | Already-primed cells we can still roll (primes = +1 already banked; roll will convert them to pts per table). In practice this is hard to track without history because `primed_mask` doesn't record *who* primed. Use proxy: count of primed cells within our immediate rollable neighborhood. |
| F6 | **carpeted_count** | count of bits in `carpet_mask` | Frozen-in territory, mostly informational (already scored). Weak feature but useful for timeout / tempo. |
| F7 | **rat_belief_max** | `max_c belief[c]` | Peak belief concentration. If > 1/3, a search is +EV *right now*. |

### C.2 Secondary features (NICE TO HAVE, add to push from Albert to Carrie tier)

| # | Name | Formula | Rationale |
|---|---|---|---|
| F8 | **rat_belief_entropy** | `−Σ belief[c] · log(belief[c])` | Low entropy = search is high-EV. Used for information-value search decisions. |
| F9 | **our_longest_primable** | max over dirs `d` of `reach(worker_pos, d)` | Directly estimates the next roll length we can achieve. |
| F10 | **opp_longest_primable** | same for opponent | Mirror of F9. |
| F11 | **our_worker_mobility** | count of valid non-search moves | Mobility is survival; if we can't move we lose (invalid-move loss). Dramatic penalty when mobility ≤ 2. |
| F12 | **opp_worker_mobility** | same for opponent | Dual of F11. Negative correlation with win prob if theirs is low (we want them stuck). |
| F13 | **center_control** | `-manhattan(worker, (3.5, 3.5))` | Workers near the center can prime in any direction; corners are trapped. |
| F14 | **blocker_proximity_penalty** | `max(0, 2 − min_dist_to_blocker)` | Being next to a blocker cuts your reach — slight negative. |
| F15 | **expected_search_value** | `max(0, 4·p_max − 2·(1−p_max))` where `p_max` = F7 | EV of the best single search; used to decide whether to take search action. |
| F16 | **carpet_owned_by_us_reachable** | primed/carpet cells we could still roll | Opponent primes are *free rolls* for us if we reach them first. |

### C.3 Features to avoid (or use with care)

- **Raw `primed_mask` bit count** — misleading: primes are +1 each *and* liability (can't walk on them). Same count can be good or bad depending on whether *we* can roll them.
- **Static distance to opponent worker** — this is not chess; no check/checkmate. Distance to opponent matters only for resource-contention (F5/F16).
- **Historical move counts** — fine for logging but too brittle for heuristics.

### C.4 Feature-extraction cost estimates

| Feature | Cost (ops) | Comments |
|---|---|---|
| F1, F2 | O(1) | Direct field reads |
| F3, F4 | O(64·4) ≈ 256 | Ray scans (precompute once per leaf) |
| F5, F16 | O(64) | Bitmask pop + ray |
| F6 | O(1) | popcount of carpet_mask |
| F7, F8, F15 | O(64) | Belief iteration |
| F9, F10 | O(4) | Only from worker position |
| F11, F12 | O(1) | `get_valid_moves` count |
| F13, F14 | O(1) | Scalar arithmetic |

Total per heuristic call: **~500 ops**. At 10k leaves/move, that's 5M ops — well within budget.

---

## Section D — Adversarial heuristic considerations

### D.1 Shared primes — both players can roll any primed line

This is the single biggest asymmetry in the game: **primes are not owned**. If our bot primes cells `(3,3), (3,4), (3,5)` and the opponent walks over to `(3,6)`, they can carpet-roll our 3 primes for +4 points. Our prime cost (+3 turns) becomes **their** gain.

**Heuristic implication:** when scoring a position with N of our primes laid out, discount by `P(opp_rolls_first)`. A rough model:

```
P_we_roll_line_L_first = 1 if our_dist_to_roll_start < opp_dist_to_roll_start else 0
```

where `roll_start` is either endpoint of the primed run. Replace F5 with:

```
F5' = sum over our primed lines L of (line_value(L) · P_we_roll_first(L))
    − sum over same lines of (line_value(L) · (1 − P_we_roll_first(L)))
```

The (1 − P) term is double-discounted because we paid the prime cost *and* gave them the roll.

### D.2 Opponent primes reachable by us

Conversely, opponent-laid primes within our Manhattan reach are *free future points*. Add to F16. Rule of thumb: if opponent primes are on row/col `L` with length `k`, and we're closer to `L`'s endpoint:

```
bonus = roll_value(k) · P(we_reach_first(L))
```

This means a strong heuristic actually **welcomes** opponent priming in our direction — a counterintuitive but important signal.

### D.3 Blocking play

A purely defensive move: prime cells in a way that breaks opponent's long lines. If the opponent is building a k=5 line, dropping a prime between their head and end reduces them to two k=2 lines = 4 pts instead of 15. This is captured by F4 (opp_cell_potential) going down after our prime — so the heuristic naturally rewards blocking without an explicit feature, provided F4 looks at their perspective.

### D.4 Tempo

If it's our turn and we can trigger a +6 roll now vs their expected +4 next turn, we prefer ours-first (tempo matters). Expectiminimax already captures this via depth. The heuristic doesn't need an explicit tempo feature provided F1 and F3/F4 are evaluated from the "to-move" side.

---

## Section E — Rat-search heuristic

Rat search is a different beast: no worker motion, direct ±2/±4 outcome, information value on the belief grid.

### E.1 Immediate-EV calculation

Let `p = belief[(x,y)]`:
- EV(search @ (x,y)) = `4·p − 2·(1 − p) = 6p − 2`.
- Break-even: `p ≥ 1/3`.
- At `p = 1`: EV = +4 (rare).

### E.2 Value of information beyond immediate EV

Search also updates the HMM belief grid with a hard observation (correct → collapse to delta on that cell, wrong → zero that cell and renormalize). This is useful for *future* searches. The information-value of a wrong search is the entropy reduction:

```
InfoValue(search @ c) = H(belief) − E[H(belief | search outcome)]
                     ≈ (1−p) · log(1/(1−p))  for small p
```

For **our heuristic**, combining:

```
heuristic_search_value(c) = (6p − 2) + γ · InfoValue(c)
```

with `γ ≈ 0.5` as a starting weight. This pushes the bot to take slightly-negative-EV searches early in the game to sharpen belief for later high-EV searches.

### E.3 When to wait

If all beliefs are below 1/3 AND the rat is likely to continue mixing (i.e., `T^k · belief` stays diffuse for several steps), the best immediate action is to **prime+roll** while passively letting sensor readings sharpen the belief. The heuristic encodes this by making F15 (expected_search_value) competitive with F3 (cell_potential) only when p_max is high.

Rule of thumb for the integrator: take a search move only if `heuristic_search_value > α_search · H_cell` with `α_search ≈ 0.3`. Otherwise stick with movement.

### E.4 Search-move competes with prime for turn budget

40 turns is tight. A search spent on p=0.4 EV = +0.4 is less efficient than a prime (which on average earns part of a +4 to +21 future roll). Reserve searches for *decisive* moments: p > 0.5, or endgame (fewer turns left for priming, so information-value dominates).

---

## Section F — Three candidate heuristic architectures

Each is a tradeoff between implementation speed and expected ELO gain. Assume the expectiminimax + HMM backbone is given.

### F.1 Architecture F1 — Handcrafted linear blend (baseline)

```
h(board) = w1·F1 + w3·F3 − w4·F4 + w5·F5 + w7·F7 + w9·F9 − w10·F10 + w11·F11 − w12·F12
```

**Feature set:** F1, F3, F4, F5, F7, F9, F10, F11, F12 (nine features from §C).
**Weights (starting guess):**
- w1 = 1.0 (score diff is unit)
- w3 = 0.8 (cell potential, per-point)
- w4 = 0.8 (mirror)
- w5 = 0.5 (discounted primes)
- w7 = 2.0 (peak belief × search bonus)
- w9 = 0.3 (longest primable)
- w10 = 0.3 (mirror)
- w11 = 0.5 (mobility)
- w12 = 0.5 (mirror)

**Training procedure:** hand-tune by running 50-match tournaments vs George/Albert and nudging weights. No gradient; pure local search. Expected tuning time: 2–4 hours wall-clock once match-runner exists.

**Expected performance:** beats Yolanda easily, beats George comfortably, competitive with Albert (possibly wins majority). Probably **falls short of Carrie** because of linear bias (no interaction terms).

**Implementation time:** 2–3 hours for features + 1h glue.

**Risk:** low. This is the safe floor.

### F.2 Architecture F2 — Linear heuristic with learned weights (recommended)

Same feature set as F1, but weights optimized by **CMA-ES or Bayesian optimization** over self-play matches.

**Objective:** maximize win-rate against a fixed opponent (our own F1 implementation, or George). Budget 500–1000 matches per generation, ~5–10 generations.

**Why CMA-ES over gradient descent:** win-rate is a noisy, non-differentiable function of weights. CMA-ES handles this gracefully with ~20 samples per generation × 5 generations = 100 weight-vector evaluations × 50 matches each = 5000 matches. At ~5 s/match this is ~7 hours wall-clock; feasible but tight.

**Alternative — regression to minimax-eval:** play a handful of deep (depth-6) searches, extract leaf evaluations from the minimax bubbling, and fit features to those targets via linear regression. Much cheaper; weight quality depends on how consistent the deep-search evaluations are.

**Expected performance:** **this is the realistic path to beating Carrie.** Self-play-tuned linear heuristics have repeatedly shown they can match hand-tuned ones with zero expert bias. Expect +50–100 ELO over F1.

**Implementation time:** 4–6h for the tuning harness + 6–10h of self-play compute.

**Risk:** medium. Tuning harness can have bugs; stochastic board means high variance. Mitigation: run a paranoid sanity ablation after tuning (set all new weights to 0, verify bot still plays sensibly).

### F.3 Architecture F3 — Small NN over features

Inputs: 10–15 features from §C. Hidden: 32 units, tanh. Output: 1 scalar.

**Training:** either
- (a) **Policy-gradient** on self-play outcomes. Long training time, high variance.
- (b) **Regression** on bootstrapped minimax evaluations (similar to AlphaZero's value network, minus the policy head).

**Why it could win:** captures interactions that linear can't — e.g., "cell potential is only valuable if worker has mobility" (F3 × F11). Carrie likely *doesn't* do this, so it's a potential leapfrog.

**Why it's risky given 3-day deadline:**
- Training pipeline is nontrivial (self-play generation + target computation + torch fitting + weight export).
- Potential for overfitting / distribution shift.
- 32-unit NN evaluated 10k times/move = 320k multiply-adds; fast in numpy but might push us over the per-move budget if other parts are slow.

**Expected performance:** **highest ceiling** (could approach Carrie+100 ELO), also **highest variance** (could underperform F1 if undertrained).

**Implementation time:** 12–20h including training. **Not recommended** as the primary plan given deadline; consider as Phase 5 iteration if F2 lands early.

### F.4 Side-by-side comparison

| Architecture | Features | Training | Expected ELO vs Albert | Implementation hours | Risk |
|---|---|---|---|---|---|
| F1 linear handcrafted | 9 | none | +0 to +50 | 3–5 | Low |
| F2 linear CMA-ES | 9–12 | self-play | +50 to +150 | 10–15 | Medium |
| F3 small NN | 10–15 | regression on deep-search | +100 to +200 *or* negative | 15–25 | High |

**Recommendation: Build F1 first, ablate, then graduate to F2.** F3 only if both land early and have spare compute.

---

## Section G — Open choices for Strategy-Architect

These are decisions the heuristic design explicitly defers to the strategy blueprint.

### G.1 Must-have vs nice-to-have feature set

**Must have (no debate):** F1 (score_diff), F3 (our_cell_potential), F4 (opp_cell_potential), F7 (rat_belief_max).

**Strongly recommended:** F5 (prime ownership with opp-first discount), F9/F10 (longest primable), F11/F12 (mobility), F15 (search EV).

**Debatable (tune or drop):** F6 (carpet count — low signal), F13 (center control — implicit in F3), F14 (blocker proximity — implicit in F3), F8 (belief entropy — only adds value for search-vs-prime trade-off).

Recommendation: start with 9 features (the "must + strongly recommended" list). Add F8 if search-timing is weak in playtesting.

### G.2 Handcrafted vs learned weights (the ~72h question)

- **If you trust the match-runner is solid by hour 24:** go F2. Reserve hours 40–55 for CMA-ES, hour 55+ for validation.
- **If match-runner is flaky or late:** stay on F1. 50 ELO below Carrie is better than 200 ELO below because CMA-ES diverged.
- **Hybrid:** seed CMA-ES with F1's handcrafted weights as the mean; tight sigma. Means even if CMA-ES runs out of compute, the fallback is the hand-tuned baseline.

### G.3 How to regularize / ablate

- **Ablation protocol:** for each feature, run 50 matches with its weight zeroed. If win-rate drops < 2%, drop the feature.
- **Regularization for F2:** L2 penalty on weights during CMA-ES (keeps weights bounded; prevents one feature from swamping others when the "real" signal is elsewhere).
- **Regularization for F3:** dropout on hidden layer; early-stopping on validation match-batch.
- **Cross-validation:** hold out a set of opponents (e.g., train vs George, validate vs Albert-emulator) to detect overfitting to specific opponent style.

### G.4 Heuristic evaluation side (whose turn? perspective?)

Convention: heuristic is always computed from "the side to move" perspective, returning **positive = good for side to move**. At the leaf of expectiminimax, the driver code knows whose side to negate. This is the cleanest pattern and matches chess-engine conventions. The researcher recommends this; Strategy-Architect to confirm in ARCHITECTURE.md.

### G.5 Belief-grid interaction with heuristic

The heuristic needs belief access for F7, F8, F15. Options:
- **Option a:** pass belief as a separate argument to the heuristic; expectiminimax tracks it in parallel with the board.
- **Option b:** store belief inside the forecast-board copies (more copies, slower).

Option (a) is cheaper and decouples concerns. Confirmed recommendation.

---

## Summary — The single takeaway

**Carrie's advantage over Albert = better `P(c)` with a distance term.** We reproduce that in §B.2 with the formula:

```
P(c) = [best_roll(c) + 0.3 · second_best_roll(c)] · (1 − 0.5 · P_opp_first(c)) / (1 + 0.3 · dist(worker, c))
```

Used as features F3 and F4 in a 9-feature linear heuristic (Architecture F2) with CMA-ES-tuned weights, this is the straight path to the 90% tier. Everything else — NNs, opening books, endgame tablebases — is upside, not the main bet.

---

## Section H — Amendments after GAME_SPEC.md §10 (added 2026-04-16)

Three ground-truth facts from `docs/GAME_SPEC.md` force concrete revisions to the earlier sections. Each is applied inline below with its specific consequence.

### H.1 Spawns are NOT uniform in the inner 4×4, and can land on BLOCKED cells

**Fact (GAME_SPEC §1 + §10 item 7 + item 17):** `generate_spawns` picks `x ∈ {2,3}` for Player A, then mirrors to `(7-x, y)` for Player B. Both spawns share the same `y ∈ {2,3,4,5}`. So A is *always* on the left half, B *always* on the right half; and `generate_spawns` does **not** check against `_blocked_mask` — a 3-deep corner blocker at (0..2, 0..2) can legally contain A's spawn at (2,2).

**Consequence for heuristic (§C, F13–F14):**

- **F13 (center control)** — drop or reweight. Workers are already constrained to x ∈ {2,3} or {4,5}; `manhattan(worker, (3.5, 3.5))` varies over a tight 1–3 range at spawn. The feature adds almost no signal in the opening and is better replaced by **F13' (opening-half bias)**: for Player A, reward leftward reach (west-side `reach`) in the opening 5–10 turns; for Player B, mirror. Rationale: you start on your half and the opponent's half is unreachable without crossing contested center cells.
- **F14 (blocker_proximity_penalty)** — keep, but **compute dynamically against `_blocked_mask`**, not against "corner" assumptions. The feature must never hard-code corner positions because a 3×2 block and a 2×3 block have different footprints and the blocker layout is per-game random (CLAUDE.md §1.3).
- **New F14a (spawn-on-blocker check):** on the very first `play()` call, if `board.get_cell(player_worker.position) == BLOCKED`, the agent must still act; it cannot prime (PRIME requires current cell = SPACE). The heuristic should not panic — just verify move generation handles this. Add an assertion in integration tests, not in the heuristic itself. Strategy-Architect should flag this to Dev-Heuristic as a Day-1 sanity test.
- **Cell-potential `P(c)` (§B):** the **opponent-first discount** `P_opp_first(c)` must use actual opponent worker coordinates, not a symmetric prior. Since A is always left-half and B always right-half, *center cells (x=3 and x=4)* are the contested zone — `P_opp_first` should approach 0.5 for these cells in the opening. Cells on your own half (x ≤ 3 for A, x ≥ 4 for B) default to `P_opp_first ≈ 0` early. Bake this into the initial-move heuristic rather than treating all cells symmetrically.
- **Distance discount α (§B.2):** may need **asymmetric tuning** per player color. Player A (moves first) has a 1-ply initiative advantage on contested center cells; a slightly smaller α for A means we value reaching across the center more aggressively than B does. Low priority — let CMA-ES find this if it exists.

### H.2 Tournament time budget is 240 s (not 360 s); per-move ≤ 6 s — heuristic eval cost is a hard constraint

**Fact (GAME_SPEC §7 + §10 item 5, 14):** tournament mode (`limit_resources=True`) gives each player **240 s total** across all 40 moves. Local self-play uses 360 s (50% more). Mean per-move budget on bytefight.org ≈ 6 s, but includes HMM update + expectiminimax + leaf evals.

**Consequence for heuristic cost budget (§C.4, §F):**

- **Revise per-heuristic-eval target.** Earlier §C.4 estimated ~500 ops and 5M ops/move at 10k leaves — that's fine in C but actually ~50–500 ms in pure Python. With a 6 s total move budget and HMM update taking ~1 ms + search overhead + move-gen, the heuristic should aim for **≤ 100 μs per eval** in the *tournament-mode* regime. This is achievable only with:
  - numpy-vectorized ray scans (not Python loops),
  - precomputed reach tables updated incrementally when the primed/carpet masks change,
  - belief features (F7, F8, F15) read from a cached belief array, not recomputed per leaf.
- **Downgrade the NN architecture (F3).** A 10→32→1 NN at ~340 multiply-adds per eval with numpy is ~30 μs — technically within budget, but with numpy overhead could reach 200–500 μs. **F3 is only feasible if the model is exported to a numba/cython-compiled path** (both are in `requirements.txt`). Flag this as a deployment risk to Strategy-Architect.
- **Local-vs-tournament benchmark skew.** Any heuristic tuning that passes locally must leave **≥ 33% runtime slack** to survive the tournament's tighter budget. Rule of thumb for the tuning harness: if a match finishes with `time_left > 80 s` locally (out of 360), it will finish with `time_left > 30 s` on bytefight.org (out of 240). Anything tighter is suspect.
- **Implication for Architecture choice (§F).** Tilts the recommendation further toward **F1/F2 linear** and away from F3 NN. F2's CMA-ES tuning already assumes 50 matches per weight-vector; those matches must themselves be time-safe. Consider running CMA-ES with `limit_resources=True` even in local evaluation so tuning targets the real budget.
- **Adaptive per-move time allocation.** Heuristic quality matters most mid-game (turns 15–30) when the board is complex; use time-left-aware evaluation depth in expectiminimax. Heuristic itself stays the same; the *search* around it adapts. Flag to Dev-Search.

### H.3 `apply_move(SEARCH)` is a no-op on points — heuristic must model +4p − 2(1−p) and the rat-capture side-effects

**Fact (GAME_SPEC §2.4 + §10 item 20):** the SEARCH branch in `apply_move` is `pass`. Points (+4 correct, −2 wrong) and rat respawn (new `δ_{(0,0)} · T^1000`) happen only in `play_game`, outside `apply_move`/`forecast_move`. Therefore `forecast_move(Move.search(...))` returns a board where `player_worker.points` is **unchanged** and the belief grid is **unchanged**.

**Consequence for heuristic (§E, F7/F8/F15):**

- **F15 (expected_search_value) must be computed in the heuristic itself, not read from board state.** The leaf evaluator, when examining a SEARCH child node, must:
  1. Compute `p = belief[search_loc]` from the *pre-search* belief grid.
  2. Compute the **expected score delta**: `E[Δ] = 4·p − 2·(1−p) = 6·p − 2`.
  3. Add `E[Δ]` to the forecast-board's `points_diff` feature F1 manually.
  4. Compute the **expected belief update**:
     - With probability `p`: rat was there → captured → rat respawns → belief_new = `p_0 = e_0 @ T^1000` (the shipped prior). **NOT `δ_{(0,0)}`** — see `RESEARCH_HMM_RAT.md` for why.
     - With probability `1-p`: rat not there → zero that cell, renormalize the rest.
  5. Evaluate the heuristic on the expectation over these two outcomes, weighted by `p` and `1-p`.
- **Integration with expectiminimax as a chance node.** SEARCH is effectively a 2-outcome chance node (hit vs miss). The engine handles this in `play_game` but the in-tree search does not. **Dev-Search must wrap SEARCH children in chance-node logic.** This is an architecture-level fact, not just heuristic.
- **Search-heuristic tie-in with belief entropy (F8).** The value-of-information argument in §E.2 is now concrete: the expected *post-search* entropy is
  ```
  E[H(belief_new)] = p · H(p_0)  +  (1−p) · H(belief \ {search_loc}, renormalized)
  ```
  On a miss, entropy drops by `−log(1−p) − p/(1−p) · log(p)` if small-p. On a hit, entropy jumps *up* to `H(p_0)` (the shipped prior is more diffuse than a late-game belief — so a hit can be an information *loss*).
  Consequence: late-game, searching on a high-p cell gives +4 points but resets your belief grid. **The heuristic should prefer searching WHEN points are decisive** (e.g., trailing + few turns left) and AVOID searching when point-differential is comfortable but belief mass is concentrated (use that belief for the *next* search instead).
- **Revised F15 formula:**
  ```
  F15(c) = (6·p − 2) + γ_info · E[InfoValue(c)] − γ_reset · P(hit) · H(p_0)
  ```
  The `γ_reset · p · H(p_0)` term penalizes the belief-collapse cost of a successful search. Starting guesses: `γ_info = 0.5`, `γ_reset = 0.3`. CMA-ES should find the right balance.
- **Opponent-search tracking (defensive).** The opponent might capture the rat; when they do, *our* belief grid must also be reset to `p_0`. This is not strictly a heuristic concern, but any features F7/F8/F15 that consume belief need to be fed a grid that was reset on `opponent_search == (loc, True)` from the prior ply. Flag to Dev-HMM (it is already flagged in `RESEARCH_HMM_RAT.md`).

### H.4 Summary of diffs from v1

- **Added:** F13' (opening-half bias), F14a (spawn-on-blocker sanity), revised F15 formula with belief-reset penalty, chance-node treatment of SEARCH in leaf eval.
- **Tightened:** per-eval time budget (≤ 100 μs tournament), pushing preference to F2 linear over F3 NN.
- **Clarified:** `P_opp_first(c)` must use asymmetric left/right-half spawn prior, not symmetric.
- **Corrected:** prior for belief reset after capture is `p_0 = e_0 @ T^1000`, not `δ_{(0,0)}` (the 1000 silent steps happen before any observation is possible).

---

## Section I — Checklist mapping against task brief (added 2026-04-16)

The original task brief (auto-restated as Task #5) enumerated items (a)–(g). This section maps each to concrete coverage in this document and adds tightening where earlier sections were thin.

### I.(a) What makes a cell "valuable"

Covered in §B.1 (P_1–P_5) and §C. Explicit summary:

| Factor | Feature / formula | Where |
|---|---|---|
| Proximity to long primeable line | `max_d reach(c, d)`, composed into `P(c)` | §B.1 P_1 |
| Adjacent existing primes (free continuation) | `P_3` second-best direction; F5/F16 | §B.1, §C.1–C.2 |
| Distance from opponent | `P_opp_first(c)` multiplicative penalty | §B.1 P_5 + §D.1 |
| Distance from blocked corner | F14 `blocker_proximity_penalty`; implicit in reach saturation | §C.2 F14 |
| Distance from own worker | `1 / (1 + α · dist)` distance decay | §B.1 P_4, §B.2 |

### I.(b) Partial prime line vs completing a shorter roll now

**Keep-building vs roll-now decision rule.** Let `k_now` = current primed-run length in front of worker, `k_max` = max feasible extension (bounded by reach / turns_left / opponent proximity). The choice between "roll at `k_now`" and "prime one more then roll at `k_now+1`":

```
roll_now_value = CARPET_POINTS_TABLE[k_now]                    (1 turn, immediate)
extend_value   = 1 + CARPET_POINTS_TABLE[k_now+1]
                 − P_opp_rolls_first(line) · CARPET_POINTS_TABLE[k_now]
                                                                (2 turns: +1 prime, +roll, minus opp-theft risk)
```

Take the extend branch iff `extend_value / 2 > roll_now_value`, i.e. **if the per-turn amortized value of extending beats rolling immediately, AND opponent-theft probability is low enough**. From the PPT table in §A.2:

| k_now | roll_now | extend (no opp risk) | extend better? |
|---|---|---|---|
| 1 | −1 | (1 + 2)/2 = 1.5 | **yes, obviously** |
| 2 | 2 | (1 + 4)/2 = 2.5 | yes |
| 3 | 4 | (1 + 6)/2 = 3.5 | close — yes |
| 4 | 6 | (1 + 10)/2 = 5.5 | no, roll |
| 5 | 10 | (1 + 15)/2 = 8.0 | no, roll |
| 6 | 15 | (1 + 21)/2 = 11.0 | no, roll |

**Interpretation (no opp risk, no other constraints):** extend while `k_now ≤ 3`; roll at `k_now ≥ 4`. Even 30% theft probability at `k_now=3` still prefers extend. This rule lives *implicitly* inside the heuristic via F3 (cell_potential picks the longer roll) plus F1 (score_diff rewards immediate points) — the linear blend weights decide. Ablation target: verify the chosen weights reproduce this curve.

**Optional explicit feature F17 (continuation_bonus):**
```
F17 = max(0, CARPET[k_current + 1] − CARPET[k_current] − 1)
      · I(worker can reach extension cell next turn)
```
Starting weight ~0.5. Classed as "nice-to-have" per §G.1.

### I.(c) EV of priming at location X vs Y given N-move lookahead

The **heuristic does not compute multi-ply EV directly** — that is expectiminimax's job. The heuristic is the *leaf approximation* that lets the search pick without recursing to infinite depth.

At the heuristic level, a one-ply approximation of prime-location EV is:
```
EV_prime(c, d) ≈ +1 + γ · [P(new_worker_pos) − P(old_worker_pos)]
```
with `γ ≈ 0.8` converting future-potential units to realized-point units. The direction `d*` that maximizes `P(new) − P(old)` is the local best. Deeper N-ply search may override if opponent threatens the better line faster.

**Worked example (for Strategy-Architect intuition):** worker at (3,3), choosing PRIME direction:
- PRIME right → worker at (4,3), reachable rightward = 4 empties → `P_best = roll_value(4) = 6`.
- PRIME down → worker at (3,4), reachable downward = 6 empties → `P_best = roll_value(6) = 15`.

Down strictly dominates in the 1-ply approximation. This is exactly what F3 captures at depth 1; at depth N > 1, expectiminimax handles it without explicit rule.

### I.(d) Belief-entropy reduction vs immediate scoring

Covered in §E.2 and §H.3. Synthesized rule:
```
choose_search  iff  6·p − 2 + γ_info · InfoValue(c) − γ_reset · p · H(p_0)
                    >  max_over_moves[ΔF1 + 0.8 · ΔF3]
```
Search wins only when combined immediate-EV + info-gain − belief-reset-cost beats the best prime/roll alternative. The inequality is checked *implicitly* at leaves because F15 competes with F3 in the linear blend.

### I.(e) Tempo — when is setup worth spending a turn?

Expanded from §D.4. "Tempo" in this game has three concrete flavors:

1. **Positional tempo:** moving toward a better cell (higher `P(c)`) for next turn's prime. Cost = 1 turn of 0 pts. Break-even: `P(new) − P(old) > γ⁻¹` (roughly ≥ 1.25 cell-potential units). Captured by F3 going up after PLAIN moves.
2. **Priming tempo:** priming X now to extend at Y next turn, vs priming Y directly. Equal EV if final roll length matches, but priming X first *claims line-of-advance* against opponent blocking. F17 rewards this.
3. **Search tempo:** +EV search now vs prime-then-search-next-turn. Search collapses belief (loses VoI for future). F15 in §H.3 encodes this trade.

**Rule of thumb:** spend a setup turn iff the follow-up move's expected value exceeds `(setup_cost + follow_up_cost) / follow_up_turns` at today's PPT. Concretely: **never spend a turn whose marginal PPT falls below 1.5 (the k=2 floor) — except as a positional/priming investment into a sequence with ≥ 3.0 PPT future value.**

### I.(f) Terminal state evaluation at depth limit

At a **leaf** of expectiminimax:

- **If `board.is_game_over()`:** raw point differential × huge constant, dominating any heuristic signal.
  ```
  H_terminal = (our.points − their.points) · 10_000
  ```
  Ties evaluate to 0 (matches Result.TIE when other tiebreakers are exhausted).
- **If depth limit hit but game not over:** use the linear blend (F1 + w3·F3 − w4·F4 + ...) with **turns-left scheduling**. Weight future-potential features by `turns_left / MAX_TURNS_PER_PLAYER` so late-game leaves lean on score_diff and nearly ignore cell-potential:
  ```
  weight_future = min(1.0, turns_left / 10)   # full weight until last 10 turns, then linear decay
  H = F1 + weight_future · (w3·F3 − w4·F4 + w5·F5 + w9·F9 − w10·F10 + w11·F11 − w12·F12) + (F7/F15 search terms)
  ```
- **Worker-stuck penalty at depth limit:** if `mobility(worker) == 0`, the next turn will be an INVALID_TURN loss. Evaluate as terminal:
  ```
  if mobility(our_worker) == 0 and turns_left > 0:
      return -10_000  # we lose next turn
  ```
  Mirror for opponent stuck (+10_000).

Strategy-Architect to confirm terminal uses `(ours − theirs)·BIG`, not `ours` alone.

### I.(g) Fixed vs learned heuristics — three architectures

Already covered in §F. Cross-reference:

| Item from brief | Matches architecture | See § |
|---|---|---|
| Linear function on hand features | F1 handcrafted + F2 CMA-ES-tuned | §F.1, §F.2 |
| Small NN | F3 (10 → 32 → 1) | §F.3 |
| Regression over self-play data | F2's alternative training path (regress to minimax-eval) | §F.2 |

Three architectures delivered. Recommendation stands: **F2 linear + CMA-ES** is the main bet; F1 fallback; F3 upside-only.

### I.Summary

Every item (a)–(g) is addressed with a concrete formula, feature, or decision rule. Items (b), (e), (f) — thin in v1.1 — are now explicit: extend-until-k=3 rule, marginal-PPT ≥ 1.5 tempo rule, terminal×10k + turns-left-scheduled depth-limit blend. No open questions for Task #5 remain.

---

## References

- `assignment.pdf` §9 (grading) and §7 (bot descriptions) — authoritative on reference-bot levels.
- `docs/GAME_SPEC.md` §1, §2.4, §3.2, §7, §10 (items 5, 7, 14, 17, 20) — source of H.1/H.2/H.3 facts.
- `docs/research/RESEARCH_HMM_RAT.md` — confirms `p_0 = e_0 @ T^1000 ≈ π` (stationary) and mixing times.
- `engine/game/enums.py::CARPET_POINTS_TABLE` — exact scoring table used in §A.
- `engine/game/board.py::apply_move` — confirms prime=+1, roll gives CARPET_POINTS_TABLE[k].
- `engine/game/rat.py` (per CLAUDE.md) — noise model driving F7/F8/F15.
- CS3600 lecture on Expectiminimax (cited in assignment Appendix A).
- Sebastian Lague chess-bot series (referenced in assignment) — move-ordering and heuristic blending patterns.
- General ML literature: CMA-ES (Hansen & Ostermeier 2001) for F2 weight tuning.
