# CARRIE_DECONSTRUCTION — formula hypotheses + test protocol

**Author:** carrie-deconstruct
**Date:** 2026-04-16
**Status:** thinking-only deliverable. Nothing executed. Recommendation at the end of §3 + go/no-go gate.
**Scope:** reverse-engineer the exact coefficients of Carrie's "cell potential × distance from bot" heuristic so RattleBot can dominate her by construction.

**Inputs used (deliberately narrow per the spec):**
- `CLAUDE.md`
- `assignment.pdf` §9 (Grades and Awards) — authoritative Carrie description
- `docs/GAME_SPEC.md` §2 + §4 + §9 (move semantics, scoring, edge cases)
- `engine/game/board.py`, `engine/game/enums.py`

**Deliberately not read (bias-avoidance):** `docs/research/RESEARCH_HEURISTIC.md`, `3600-agents/RattleBot/heuristic.py`, any other synthesis doc that already speculates about Carrie.

---

## 0. What we actually know about Carrie

Direct quote from `assignment.pdf` §9:

> "Carrie uses the same expectiminimax and HMM structure as Albert, but uses a more advanced heuristic that takes into account an **estimate of the potential of each cell** and **its distance from the bot**."

`CLAUDE.md` §5 paraphrases this as `cell potential × distance from bot`. Note what that tells us and what it does not:

- **Tells us:** Carrie's leaf evaluator is a function of (a) a scalar per-cell "potential" value P(c) for each of 64 cells, and (b) a distance-from-worker term d(bot, c). Those two get combined and probably aggregated across cells into a scalar leaf value.
- **Does not tell us:** the exact functional form, how the two worker distances (self vs. opponent) combine, whether the aggregation is a sum or a max, whether P(c) is in score-units or some transformed utility, whether searches-for-rat are part of the heuristic at all, or how Carrie balances heuristic-value vs. concrete `points` on the board.
- **Strong assumption I will carry:** Carrie, like Albert, exposes a *single scalar* v(state) returned to expectiminimax. No multi-objective decomposition. The problem is to determine the pointwise function `v(state) = g(P, d, ...)` where both P and d are per-cell.

The assignment explicitly says "same expectiminimax and HMM structure as Albert" — so search depth, pruning, move ordering and belief-tracking are roughly shared with Albert. What differentiates Carrie is **only** the leaf heuristic. That is where all the signal is.

### What Carrie's heuristic almost certainly includes

Non-negotiable from the game's own point structure (see `enums.CARPET_POINTS_TABLE`, `engine/game/board.py:253`, `engine/gameplay.py:438-445`):

- **Current score differential.** `self.points - opponent.points`. Any non-terrible heuristic has this as the dominant term with weight 1.0 (scores are commensurate with the winning condition itself). This by itself is strong play — rolling a 5-carpet is +10 points, etc.
- **Some "potential" on cells.** From the wording, this is a per-cell scalar that estimates how much score the bot could extract from that cell in the future. The cheapest, most natural form is: `P(c) = max over k ∈ {1..7} of CARPET_POINTS_TABLE[k] if you can roll k starting from/through c`. But there are many closely-related choices.
- **Distance from bot.** The distance term weights cells by reachability. Far cells contribute less than near cells because the bot can't realize their value within the remaining turns.

### What it may or may not include

- HMM belief mass (for SEARCH EV) — Albert has HMM tracking too, so arguably it's factored in for both. Albert's "very simple" heuristic may bolt on a crude search-EV term; Carrie's "more advanced" heuristic probably bolts on a better one.
- Opponent mobility / prime-chain threats.
- Turn-count remaining (endgame bonus for guaranteed points, discount on potential).
- Penalty for PRIMED cells under you (they block future movement).
- Own vs. opponent distance symmetry.

Given §9's wording explicitly names only "cell potential" and "distance from bot" (singular), the **minimal reading** is that Carrie is mainly score-diff + Σ over cells of (potential × distance factor). Everything else is speculation. Our hypotheses should concentrate mass on that minimal form and add a few variants that could plausibly also fit "more advanced than Albert but still simple enough to fit on a slide".

---

## 1. Formula hypothesis space

All hypotheses share a common wrapper:

```
v(state) = α · (self.points - opp.points)            # score term, almost certainly weight ≈ 1
        + β · Φ_self(state)                          # cell-potential term from self's worker
        − γ · Φ_opp(state)                           # same from opponent's worker (maybe weight 0)
        + δ · R(belief, state)                       # optional rat/search term (maybe 0)
        + ε · other(state)                           # opponent mobility, turn count, etc.
```

Hypotheses H1–H8 below differ in the exact functional form of **Φ(state)**, i.e. "cell potential aggregated over the board, weighted by distance from the worker". Parameters vary per hypothesis.

Throughout, let:
- `W` = set of cells on the 8×8 board. `|W| = 64`, minus blocked cells which contribute 0.
- `bot` = position of the worker being evaluated.
- `d(bot, c)` = **Manhattan distance** from `bot` to `c` respecting blocked cells? Or straight Manhattan? Real bots usually just use straight Manhattan because BFS-through-blockers costs 64× more. Assume straight Manhattan unless otherwise noted.
- `P(c)` = a per-cell "potential". Candidate forms below (P1–P6). Each hypothesis pairs one P with one distance-weighting.

### Candidate cell-potential functions `P(c)`

- **P1 (simple roll-max).** `P(c) = max_{k, dir} CARPET_POINTS_TABLE[k]` such that a roll of length `k` from `c` in direction `dir` is legal *right now* given `_primed_mask`. Cells that cannot anchor any legal roll get 0. Range: {0, −1, 2, 4, 6, 10, 15, 21}. Zero when no PRIMED neighbor ray exists.
- **P2 (prime-chain reachable).** `P(c) = max_{k} CARPET_POINTS_TABLE[k]` over all `k`-runs of PRIMED cells *that include c*, not just rays anchored at c. More generous; values the whole board's prime structure.
- **P3 (local prime density).** `P(c) = #PRIMED cells within Manhattan radius r of c` × constant. Cheapest to compute; no directional reasoning. Fast but loses the carpet-point nonlinearity (1→−1, 2→2, 5→10, 7→21 — 7 is 21× as valuable as the unit "primed count", while P3 treats them linearly).
- **P4 (expected future roll).** `P(c) = E[CARPET_POINTS_TABLE[k] | I'm on c and greedy from here for 1 ply]`. Closed-form: look at the 4 rays from c, take max contiguous-PRIMED length in each, pick the max k. Effectively P1 generalized to "best roll reachable *after walking to c*".
- **P5 (per-cell score-if-SPACE-primed).** `P(c) = 1 if c is SPACE (primeable) else 0`, or a cell-type table:
  - SPACE → 1
  - PRIMED → +2 (expected contribution once rolled over in a 2-chain)
  - CARPET → 0 (already spent, but lets you walk)
  - BLOCKED → 0
  This is the "naive" potential — cheap enough that I'd classify "Carrie using this" as a floor for what "more advanced than Albert" means.
- **P6 (conditioned on worker mobility).** `P(c) = P_any(c)` but zeroed out unless `c` is reachable within `(MAX_TURNS - turns_used)` plain-steps respecting blockers. In endgame this sharply cuts P at distance > turns-remaining.

### Candidate distance weightings `f(d)`

- **f_inv (inverse).** `f(d) = 1 / (1 + d)` — Carrie-wording "× distance" flipped to "÷ distance", mathematician's natural first choice. Maxes at d=0.
- **f_exp (exponential).** `f(d) = exp(−λ d)` for some `λ ∈ (0, 1]`. Smooth and well-behaved; classic discounted-future pattern.
- **f_step (step / threshold).** `f(d) = 1 if d ≤ D_max else 0`, with `D_max ∈ {3, 5, 7}`. Carrie-the-student might have written `if d <= 5: ...`; this form matches "I can only realize this within my reach" intuition.
- **f_poly (polynomial decay).** `f(d) = 1 / (1 + d^2)` or `(d+1)^{−α}`. Mid-between inv and exp.
- **f_affine (linear).** `f(d) = max(0, D − d)` for some `D` like 7 or 14. Simple and linear in d.
- **f_neg (negative distance as subtracted penalty).** `f(d) = D − d` allowing negatives. This is literally what a naive reading of "potential × distance" would produce: `P(c) * (something that decreases with d)`. Exact sign unclear from §9 wording.

### The 8 hypotheses

> Each is a pairing (P, f, aggregator, scope). Aggregator ∈ {Σ, max}. Scope ∈ {all cells, reachable cells, PRIMED-only cells}. Parameter vector θ declared.

**H1 — Σ-inverse-all-cells (classic):**
```
Φ(state) = Σ_{c ∈ W, c not blocked} P1(c) / (1 + d(bot, c))
v = (self.pts − opp.pts) + β·Φ_self − γ·Φ_opp
```
Parameters: `θ = (β, γ)`. Reasonable ranges: `β ∈ [0.1, 2.0]`, `γ ∈ [0.0, β]`. No `λ`.

**H2 — Σ-exp-all-cells:**
```
Φ(state) = Σ_c P4(c) · exp(−λ · d(bot, c))
```
Parameters: `θ = (β, γ, λ)`. `λ ∈ [0.1, 1.5]`.

**H3 — max-cell dominant:**
```
Φ(state) = max_c P1(c) · f(d(bot, c))
```
Only the single best cell counts. Picks the one biggest roll Carrie sees and decays it by its distance. Parameter-sparse: just `(β, γ, form-of-f)`.

**H4 — PRIMED-only Σ-inverse:**
```
Φ(state) = Σ_{c ∈ PRIMED} count(c) / (1 + d(bot, c))
```
where `count(c)` = length of the longest PRIMED run passing through c (so you'd multiply-count PRIMED cells that anchor a long chain). Very cheap: 64-cell loop, early-exit at non-PRIMED.

**H5 — reach-in-k-turns tablation:**
```
Φ(state) = Σ_{k=1..K} discount^k · BestCarpetPoints(reachable in k turns)
```
where `BestCarpetPoints(…)` is the max-weighted roll the bot can execute by turn `k`. Parameters: `K ≤ 5`, `discount ∈ [0.5, 0.95]`. This is the most "expectiminimax-like" of the bunch — but probably too expensive as a *leaf* evaluator because it needs inner search to compute. Unlikely Carrie does this unless her expectiminimax depth is only 1.

**H6 — step-threshold Σ:**
```
Φ(state) = Σ_{c: d(bot,c) ≤ D_max} P1(c)
```
Hard cutoff. `D_max ∈ {3, 5, 7}`. Students love step functions. Parameter `D_max` is integer — easy to distinguish experimentally.

**H7 — linear-negative distance:**
```
Φ(state) = Σ_c P1(c) · (D0 − d(bot, c))
```
where `D0` is a board-diameter-like constant (maybe 14 = 2·(BOARD_SIZE−1)). `D0 − d` is positive for near cells, negative for far. A very literal reading of "× distance": the product is potential times a "how reachable" score. `θ = (D0, β, γ)`.

**H8 — additive-potential-with-rat-belief bolt-on:**
H1 + extra term from rat belief:
```
Φ(state) = Φ_H1 + μ · max_c belief(c) · RAT_BONUS   # expected search reward if you did best search
```
i.e. Carrie's "more advanced than Albert" = H1 + a crude search-EV term. `μ ∈ [0.5, 1.5]`. Not distinguishable from H1 unless we control the rat belief, which we can approximate but not know exactly. Treat as a "bolt-on any-of-H1-H7".

### Parameter bounds I'd use for BO search

If (in §4) we decide to fit Carrie's formula numerically, reasonable priors:
- `α` (score weight): fix to 1 (it's in the same units as the win condition).
- `β` ∈ [0.1, 3.0]. Typical ≈ 0.5 — if β is too high, Carrie's heuristic chases mobility and ignores points. If too low, it reduces to score-only.
- `γ` ∈ [0, β]. Symmetric (γ = β) or asymmetric (γ = 0, purely self-centered). Naive implementations use γ = 0.
- `λ` ∈ [0.1, 1.5] for f_exp.
- `D_max` ∈ {3, 5, 7} for f_step.
- `μ` ∈ [0, 2] for any rat-EV bolt-on.

### Hypothesis-ranking intuition (prior belief before any experiments)

My prior credence, before running any of the distinguishing boards in §2:

| Hypothesis | Credence | Reasoning |
|---|---|---|
| H1 (Σ-inv, P1) | 28% | Simplest "potential × 1/distance" reading; what a TA would write fast. |
| H2 (Σ-exp, P4) | 16% | More mathematically pleasant; but `exp` is a few seconds of typing more than `1/(1+d)`. |
| H4 (primed-only Σ) | 14% | Cheap; realistic for a TA optimizing for eval speed. |
| H6 (step threshold) | 13% | Students' intuition about "within reach" often collapses to a step. |
| H3 (max dominant) | 9% | Plausible but loses information — probably too aggressive. |
| H7 (linear-neg distance) | 8% | Literal reading of "× distance". Plausible if TA took §9 very literally. |
| H5 (reach-in-k-turns) | 4% | Too expensive at leaves unless depth=1. |
| H8 (rat-EV bolt-on) | ∈ all above | Treated as orthogonal; probably adds ~5–10% credence to any hyp that already looks right. |

Combined H1 ∪ H2 ∪ H4 ≈ 58% — strong weight on "summation over cells, inverse or exponential decay, with a roll-max potential".

---

## 2. Distinguishing board configurations

Each board below is designed so that Carrie's **best move** differs across at least three of the hypotheses. The goal: observe one move by Carrie and eliminate ≥ 2 hypotheses.

All boards are specified as:
- `P1` = our side (Player A, mover), with `pos = (x, y)`.
- `P2` = opponent, not moving this ply.
- The mask declaration is given as a 8×8 grid of letters where:
  - `.` = SPACE
  - `p` = PRIMED
  - `c` = CARPET
  - `#` = BLOCKED
  - `A` = Player A worker
  - `B` = Player B worker
- For each board, we list the candidate moves we'd expect Carrie to reasonably consider, then the hypothesis-by-hypothesis predicted best move.

**Convention:** all boards assume turn_count midgame (~turn 20 of 80), both scores = 0 (so score-diff term is neutral), both workers have full 20 turns and 100 seconds of time left. This removes alpha–beta noise from time pressure. Carrie with score-diff dominant is boring — we want the heuristic to be *forced to break ties* on cell potential, so we engineer states where several moves have identical score-value deltas but different Φ values.

### Board 1 — "Two equal rolls, different distances"

```
 0  1  2  3  4  5  6  7
 .  .  .  .  .  .  .  .     y=0
 .  .  .  .  .  .  .  .     y=1
 .  p  p  p  .  .  .  .     y=2
 .  .  A  .  .  .  .  .     y=3  (A = Player A, our worker)
 .  .  .  .  .  p  p  p     y=4
 .  .  .  .  .  .  .  .     y=5
 .  .  .  .  .  .  B  .     y=6  (B = opponent)
 .  .  .  .  .  .  .  .     y=7
```

Two primed lines of length 3:
- Line L1 @ y=2, x ∈ {1,2,3}. A adjacent to `(2,2)` (one UP step from A).
- Line L2 @ y=4, x ∈ {5,6,7}. A is 3 Manhattan steps from `(5,4)`.

**Candidate moves for A:**
- M_roll_L1: PRIME(UP) to put a glue on `(2,3)` and then rolling L1 becomes a 2-ply plan — for single-ply Carrie, M_roll_L1 today is just "step toward L1".
- M_step_left: PLAIN(LEFT) — moves A to `(1,3)`, closer to L1 but does not roll.
- M_step_right: PLAIN(RIGHT) — moves A toward L2.
- M_prime_various directions.

**Simplification:** for this ply, the best *immediate* CARPET is illegal (A is not adjacent to the correct end of any primed ray). So candidates reduce to step moves. The question: does A step UP (toward L1) or step RIGHT/DOWN (toward L2)?

**Hypothesis predictions:**
- H1 (Σ-inv): Φ counts both L1 and L2. After stepping UP, d to L1 cells drops; d to L2 rises. Because L1 is already closer and `1/(1+d)` is convex, A gains more by stepping UP. **Best move: PLAIN(UP).**
- H2 (Σ-exp, small λ): Same direction but weaker signal. **PLAIN(UP).**
- H3 (max dominant): Carrie picks the single highest `P(c) · f(d)`. Both lines have identical `P1 = 4` (carpet length 3). The closer line wins. **PLAIN(UP).**
- H4 (primed-only, run-length weighted): L1 and L2 are both 3-run primes, so each contributes `count=3`. After UP step, d-reduction to L1 dominates. **PLAIN(UP).**
- H6 (step, D_max=3): L1 cells are within d=3 already; L2 cells at d=3–5. After UP step, L2 cells (5,4),(6,4),(7,4) have d=3+2=5 (excluded), (6,4) d=4 (excluded), only (5,4) near cutoff. H6 discontinuous.
- H7 (linear-neg): Step UP reduces sum of (D0 − d) over L1 cells. If D0=14, both lines contribute positively. **PLAIN(UP).**

**Differentiation:** this board is weak — everyone predicts PLAIN(UP). Use as a **sanity check** only. If Carrie does something else (e.g., SEARCH or step toward the opponent), it falsifies all of H1–H7 in their self-centered form.

### Board 2 — "Symmetric prime-lines, asymmetric distance"

```
 .  p  p  p  p  p  .  .     y=0
 .  .  .  .  .  .  .  .     y=1
 .  .  A  .  .  .  .  .     y=2
 .  .  .  .  .  .  .  .     y=3
 .  .  .  .  .  .  .  .     y=4
 .  .  .  .  .  .  .  .     y=5
 .  .  .  .  .  .  B  .     y=6
 .  p  p  .  .  .  .  .     y=7
```

Two primed regions of **different potential**:
- Top: 5-in-a-row primed (k=5 gives 10 points) at `y=0, x∈{1..5}`.
- Bottom: 2-in-a-row primed (k=2 gives 2 points) at `y=7, x∈{1..2}`.

A is at `(2,2)`. d(A, top-line) ≈ 2. d(A, bottom-line) ≈ 5.

Note: A cannot roll the top line *this turn* because A is not adjacent to one of its endpoints, so all candidates are step/prime moves.

**Candidate moves** (plain and prime in each direction). Interesting ones:
- M1: PLAIN(UP) → `(2,1)`; now d=1 to top-line. Top-line becomes reachable-to-roll within 1 more ply (PRIME(UP) then roll, but actually the run is length 5, A would need to be at `(0,0)` or `(6,0)` to roll 5 — so this is a 3-ply plan).
- M2: PLAIN(DOWN) → `(2,3)`; moves toward bottom.
- M3: PRIME(UP) → current cell becomes PRIMED, A at `(2,1)`. Immediate +1 score. Now there's a 6th primed cell adjacent to the top line, potentially enabling a 6-roll (which is 15 points).
- M4: PRIME(DOWN) → `(2,3)`. Adjacent to nothing primed.

**Hypothesis predictions (ignoring score-diff since PRIME is +1 to both hypotheses equally):**
- H1: Φ(after UP) > Φ(after DOWN) because top-line's 5 cells each contribute to the sum, and UP reduces each of their distances. But the score-diff delta is 0 for PLAIN moves and +1 for PRIME moves — **PRIME(UP)** dominates both PLAIN moves *by score-diff alone*. Then, between PRIME(UP) and PRIME(DOWN): Φ favors PRIME(UP) because top-line is richer. **Best: PRIME(UP).**
- H2: Same. **PRIME(UP).**
- H3 (max dominant): the single best cell is in the top-line. After PRIME(UP), d to top-line drops to 1, P(top cells) = 15 (if prime extends chain to 6) or 10 (if still 5). Meanwhile bottom-line's P stays at 2. **PRIME(UP).**
- H4 (primed count run-length weighted): After PRIME(UP), run-length around the new PRIMED cell — `(2,2)` is now PRIMED but not contiguous with top-line. The new cell is not part of any 2-run, so run-length 1. Maybe Carrie uses P2 which counts run-length including all PRIMED — then the total count jumps by 1 (unit-weight) but the top-line's contribution stays the same. Decision is driven by distance reduction: **PRIME(UP).**
- H5 (reach-in-k-turns): Only strong hyp whose answer might differ. After PRIME(DOWN), A is at `(2,3)` — d=4 to the bottom pair, and A could realize k=2 roll in 2 more plies (total +1 prime +2 roll = +3). After PRIME(UP), A is at `(2,1)` — to realize k=5 roll, A needs to reach `(5,0)` or `(0,0)`. d≥3 so 3 more plies minimum. At depth K=4, discount^4 · 10 ≈ 0.95^4 · 10 ≈ 8.1. At depth K=2 for bottom: discount^2 · 2 ≈ 1.8. So top still wins but by less. Still **PRIME(UP).**
- H6 (D_max=3, P1): After PRIME(UP), A at `(2,1)`; top-line cells at d∈{1,2,3,4}. Cells at d>3 excluded — so x=4 and x=5 (d=3 and d=4) are included partially. Bottom at d=6 excluded entirely. Still **PRIME(UP)** wins.
- H7 (linear-neg, D0=14): Straightforward, sign is right. **PRIME(UP).**

**Differentiation:** still weak. Board 2 is also a sanity check — Carrie's first move should clearly be toward the richer prime structure. If she does anything else (e.g., SEARCH, or step AWAY from both lines), most of H1–H7 are rapidly falsified.

### Board 3 — "Near-trivial vs. far-huge" (where decay matters)

```
 .  .  .  .  .  .  .  .     y=0
 .  .  .  .  .  .  .  .     y=1
 .  .  .  .  .  .  .  .     y=2
 .  .  A  p  .  .  .  .     y=3
 .  .  .  .  .  .  .  .     y=4
 .  .  .  .  .  .  .  .     y=5
 p  p  p  p  p  p  p  .     y=6
 .  .  .  .  .  .  B  .     y=7
```

- Near: 1 isolated PRIMED cell at `(3,3)`. A is at `(2,3)` — d=1. "Potential" P1(that cell) = CARPET_POINTS_TABLE[1] = −1. It's a **bad** roll.
- Far: a 7-in-a-row primed line at y=6, x∈{0..6}. P1(endpoints) = CARPET_POINTS_TABLE[7] = 21. d(A, (0,6)) = 5, d(A, (6,6)) = 7.

The question: does Carrie weight the far 21-pointer enough to move toward it, or does she get distracted by the nearby primed cell?

**Candidate moves:**
- PLAIN(RIGHT): step to `(3,3)` — **illegal**, primed cell blocks.
- PLAIN(DOWN): step to `(2,4)` — closer to the 7-row.
- PLAIN(LEFT/UP): other moves.
- CARPET(RIGHT, 1): roll the 1-primed into a 1-carpet. Score delta = −1 immediately. Now A is on CARPET at `(3,3)`. d(A_new, far-line) barely changes.
- PRIME(DOWN) → A at `(2,4)`, prime laid at `(2,3)` [+1 score].

**Hypothesis predictions:**
- H1: Φ = 21 term for far-line cells dominates the 1-cell near term. After PLAIN(DOWN), d reduces to all 7 far-cells by 1 — huge swing in Σ P(c)/(1+d). Score-diff delta of PLAIN(DOWN) = 0; of CARPET(RIGHT,1) = −1; of PRIME(DOWN) = +1. Net: **PRIME(DOWN) > PLAIN(DOWN) > CARPET(RIGHT,1)** (the −1 for rolling k=1 plus no Φ gain is clearly bad). **Best: PRIME(DOWN).**
- H2 (exp, λ=0.5): `exp(−0.5·d)` — cells at d=5–7 have weight ≈ 0.08–0.03. Σ over the 7 cells ≈ 7·0.05·21 ≈ 7.4 (rough). This is *comparable* to, not much bigger than, the near-cell term 1·(−1). Carrie may still step toward the far line since the 1-carpet is a −1 immediate + −1 to Φ. **Likely PRIME(DOWN) or PLAIN(DOWN).**
- H2 (exp, λ=1.0): `exp(−5) ≈ 0.007`, `exp(−7) ≈ 0.0009`. Sum over 7 far cells ≈ 7 · 0.004 · 21 ≈ 0.6. Tiny. Then 1-cell near term might dominate. But P(near) = 21 only if we use P1 (which gives the *best* roll from c). P1(3,3) = P1 of a PRIMED cell with a 1-length run (because neighbors are SPACE) = CARPET_POINTS_TABLE[1] = −1. So Φ(near) = −1 · 1.0 = −1, Φ(far) ≈ 0.6. Best move is to step AWAY from the near cell. **CARPET(RIGHT,1) to resolve the −1? No, executing a −1 roll is still −1 net to score.** Probably **PLAIN(DOWN)** or **PLAIN(LEFT)**.
- **Critically different hypothesis: H3 (max dominant).** Φ = max over c of P(c)·f(d). Before move: max is at far-line endpoint, say `(6,6)` with P=21 and d=7, f_inv gives 21/8 = 2.625 — or a nearer far-cell like `(0,6)` d=5, 21/6 = 3.5. After PLAIN(DOWN): `(0,5)` becomes d=4, `(1,5)` d=3, but these are SPACE, not PRIMED — they'd need a different potential. The max cell is still in the far line. Ranking: **PLAIN(DOWN) or PRIME(DOWN).**
- H4 (primed-only): the 1-run contributes count=1, the 7-run contributes count=7 for each of its 7 cells (or count=1 times 7 cells = 7). Overall massive weight on far line. **PRIME(DOWN) or PLAIN(DOWN).**
- H6 (D_max=3): far-line cells all at d≥5 (after PLAIN(DOWN), d=4+ — still outside threshold). So Φ_far = 0 entirely, Φ_near = -1. Only thing that changes the position is avoiding the near cell (which can't be avoided since it's behind us). In H6 Carrie is **blind to the far line** and basically picks by score-diff: **PRIME(DOWN) or PRIME(LEFT)**. *Same answer, different reason.*
- H7 (linear-neg, D0=14): coefficient `(14 − d)` for d=5 gives 9, for d=7 gives 7. Σ over 7 cells ≈ 7·8·21 = 1176 (scaled by β=0.5 → 588). Dominates. Carrie moves toward the far line — specifically, toward `(0,6)` side because that's closer. **PLAIN(DOWN) or PLAIN(LEFT).**

**Key observation:** H6 with `D_max=3` uniquely predicts that Carrie is "blind" to the far line and chooses mostly by score-diff. H2 with `λ=1.0` similarly near-blind. H1, H4, H7 all agree Carrie should move toward the 7-line. **If Carrie doesn't bother moving toward the 7-line, we get strong evidence for short-horizon hyps (H2-λ-large, H6-small-D, or Carrie has a much more different formula).**

**Eliminates ≥ 3 hypotheses in one observation.**

### Board 4 — "Aggregator test: max vs. sum"

```
 .  .  .  .  .  .  .  .     y=0
 .  .  .  .  .  .  .  .     y=1
 p  p  .  .  .  .  .  .     y=2
 p  .  A  .  .  p  p  .     y=3
 p  .  .  .  .  .  .  .     y=4
 p  .  .  .  .  .  .  .     y=5
 p  .  .  .  .  .  .  .     y=6
 p  p  .  .  .  .  .  .     y=7
```

- Cluster C1: column-shaped primed region at x=0, y∈{2..7} (6 primed cells) + connectors — the longest run is 6 (k=6 → 15 points) vertically.
- Cluster C2: 2-run primed at `(5,3),(6,3)` horizontally — k=2 → 2 points.

A is at `(2,3)`. d(A, C1 cells) = 2 to 5. d(A, C2) = 3 to 4.

**Sum vs. max:** the sum over C1 is ~6 cells × 15 / d = big. The sum over C2 is ~2 cells × 2 / d = tiny. But **the "max cell value" in C1 is 15 and in C2 is 2.** For aggregate Σ (H1, H2), direction TOWARD C1 (LEFT) is much better. For max-dominant H3, still C1 because 15 > 2. *So this board alone does NOT distinguish max vs. sum.*

**Make C2 a single cell with a HUGE potential that would dominate max:** change C2 to a 7-primed-run:

```
 .  .  .  .  .  .  .  .     y=0
 .  .  .  .  .  .  .  .     y=1
 p  p  .  .  .  .  .  .     y=2
 p  .  A  .  .  p  .  .     y=3
 p  .  .  .  .  p  .  .     y=4
 p  .  .  .  .  p  .  .     y=5
 p  .  .  .  .  p  .  .     y=6
 p  .  .  .  .  p  .  .     y=7
```

Now C2 = vertical 5-run at x=5, y∈{3..7} (k=5 → 10 points). Both clusters are meaningful. A at `(2,3)`. d(A, (0,3))=2, d(A, (5,3))=3.

**Hypothesis predictions:**
- H1 (Σ): Σ over all primed cells × 1/(1+d). Both clusters contribute. C1 has 6+ primed cells at close distances; C2 has 5 primed cells at slightly farther distances. After PLAIN(LEFT) → A at `(1,3)`. C1 distances drop 1; C2 distances rise 1. **Best: PLAIN(LEFT).**
- H3 (max): single cell. Before move: maxP in C1 = 15 (k=6 roll), maxP in C2 = 10 (k=5). C1's max at d=2 → 15/3=5. C2's max at d=3 → 10/4=2.5. So max lives in C1. After PLAIN(LEFT), C1's cells at d=1, ratio 15/2=7.5; after PLAIN(RIGHT), C2's cells at d=2, ratio 10/3=3.33. **Both steps help; LEFT helps more.** So H3 still predicts **PLAIN(LEFT).**
- H4 (primed count × run-length): longest run passing through `(0,3)` = 6. Contribution ≈ 6 (for each of 6 cells in that column). C2 longest run = 5. **PLAIN(LEFT).**
- H7: same direction.

All hyps say LEFT — this board doesn't differentiate. Scrap it. Need a board where **max-dominant vs. Σ disagree.**

### Board 4 (revised) — "Many small vs. one large"

```
 p  .  p  .  p  .  p  .     y=0
 .  .  .  .  .  .  .  .     y=1
 .  .  A  .  .  .  .  .     y=2
 .  .  .  .  .  .  .  .     y=3
 .  .  .  .  .  .  .  .     y=4
 .  .  .  .  .  .  .  .     y=5
 .  .  .  .  .  .  .  .     y=6
 .  .  .  .  .  .  .  p     y=7
```

- Near distributed: 4 isolated PRIMED cells at `(0,0),(2,0),(4,0),(6,0)`. Each is a 1-cell run → P1 = CARPET_POINTS_TABLE[1] = −1. Σ contribution is negative / zero.
- Far singleton: 1 PRIMED at `(7,7)`. P1 = −1 also. d(A, (7,7)) = 10.

Both are 1-cell primes, both with potential −1. No matter what aggregation or distance function, Φ ≤ 0 everywhere. **Bad test.**

Let me re-do with real structure:

```
 p  p  .  .  .  .  .  .     y=0
 .  .  .  .  .  .  .  .     y=1
 p  p  .  A  .  .  .  .     y=2
 .  .  .  .  .  .  .  .     y=3
 p  p  .  .  .  .  .  .     y=4
 .  .  .  .  .  .  .  .     y=5
 .  .  .  .  .  .  .  .     y=6
 .  .  .  .  p  p  p  p     y=7
```

- Three 2-runs near A (near-left clusters): each contributes P1 = 2. There are 3 × 2 = 6 primed cells.
- One 4-run far from A at y=7, x∈{4..7}: P1 = CARPET_POINTS_TABLE[4] = 6. 4 primed cells. d(A, y=7) = 5.

Aggregate: Σ (near) = 6 cells × 2 / (1+d_avg ≈ 3) = 4. Σ (far) = 4 cells × 6 / (1+d_avg ≈ 6) = 3.4. Close call — H1 would slightly prefer near. Max (H3): near max = 2/(1+2)=0.67, far max = 6/(1+5)=1.0. H3 prefers far.

**Hypothesis predictions for A's move (still at (3,2)):**
- H1: step LEFT (toward near clusters): Σ gains more than step DOWN would.
- H3: step DOWN (toward far 4-run, because max cell dominates): Φ gains more from reducing d to the big potential cell.
- H6 (D_max=3): near-clusters in range, far 4-run out of range entirely. Carrie moves LEFT or stays.

**This board distinguishes H1 vs. H3.** Specifically, if Carrie steps DOWN we have evidence against Σ-style (H1, H2, H4, H7) and for max-style (H3). If she steps LEFT we have the opposite.

### Board 5 — "Distance-shape test: inverse vs. exponential vs. step"

```
 .  .  .  p  p  .  .  .     y=0
 .  .  .  .  .  .  .  .     y=1
 .  .  .  .  .  .  .  .     y=2
 .  .  .  A  .  .  .  .     y=3
 .  .  .  .  .  .  .  .     y=4
 .  .  .  .  .  .  .  .     y=5
 .  .  .  .  .  .  .  .     y=6
 .  .  p  p  .  .  .  .     y=7
```

- Near 2-run at y=0, x∈{3,4}: d(A, (3,0))=3, d(A, (4,0))=4. Cluster center d ≈ 3.5.
- Far 2-run at y=7, x∈{2,3}: d(A, (3,7))=4, d(A, (2,7))=5. Cluster center d ≈ 4.5.

Both clusters have potential P1=2 (k=2 run).

**A at (3,3). Candidate moves:**
- PLAIN(UP) → (3,2): near d drops by 1, far d rises by 1. Asymmetric.
- PLAIN(DOWN) → (3,4): near d rises 1, far d drops 1.
- PLAIN(LEFT/RIGHT) → symmetric, barely changes either distance.

**Δ Φ(PLAIN(UP)) vs Δ Φ(PLAIN(DOWN))** under each hyp:
- H1 (1/(1+d)): near goes from d=3 to d=2 (weight 1/3 → 1/4 *wait no* — closer = higher weight, so 1/4 → 1/3, gain = +1/12). Far goes from d=4 to d=5 (1/5 → 1/6, loss = −1/30). Net positive. **UP preferred.** Sum of two cells in each cluster — near dominates under 1/(1+d).
- H2 (exp, λ=0.5): near goes from e^(−1.5) ≈ 0.22 to e^(−1) ≈ 0.37, gain 0.15. Far goes from e^(−2) ≈ 0.14 to e^(−2.5) ≈ 0.08, loss 0.06. Net positive. **UP preferred.** Similar magnitude.
- H2 (exp, λ=1.5): near decay much steeper. Stepping UP from d=3 (e^(−4.5)=0.011) to d=2 (e^(−3)=0.05), gain 0.04. Stepping DOWN from d=4 (e^(−6)=0.002) to d=5 (e^(−7.5)=0.0006), loss 0.0014. Almost **UP-only** — far cluster invisible.
- H6 (D_max=3): near cells at d=3 (just in) and d=4 (out). After UP: d=2 (in) and d=3 (in). Both in! Gain: +1 primed cell's worth ≈ +2. Far cells: d=4–5 never in range. After DOWN: still not in range. **UP strictly preferred.**
- H6 (D_max=5): near-at-d-{3,4}: both in. After UP: both still in. No delta. After DOWN: (3,0) at d=4 in, (4,0) at d=5 in. No delta. Far-at-d-{4,5}: both in before. After UP: d=5,6 — (2,7) out; after DOWN: d=3,4 — both in. **DOWN preferred** (lose nothing near, gain (2,7) into range).
- **H6 changes answer at D_max=5 vs. D_max=3.** If we see Carrie choose DOWN here and UP on board 3, that rules out D_max ∈ {3}.

**Differentiation power:** UP vs. DOWN maps directly to "does Carrie's decay kernel concentrate weight near d=3 or extend to d=5+". This is the **primary board for fitting `λ` or `D_max`.**

### Board 6 — "Opponent distance symmetry"

```
 p  p  p  .  .  .  .  .     y=0
 .  .  .  .  .  .  .  .     y=1
 .  .  .  .  .  .  .  .     y=2
 .  .  .  A  .  B  .  .     y=3
 .  .  .  .  .  .  .  .     y=4
 .  .  .  .  .  .  .  .     y=5
 .  .  .  .  .  .  .  .     y=6
 .  .  .  .  .  p  p  p     y=7
```

- Two symmetric prime-clusters:
  - TL 3-run at y=0, x∈{0,1,2}: closer to A, farther from B.
  - BR 3-run at y=7, x∈{5,6,7}: closer to B, farther from A.
- A at (3,3), B at (5,3).

**Hypothesis split on whether Φ_opp is active:**
- **If Carrie uses γ > 0** (i.e. subtracts opponent's Φ): A's best move should pull A toward TL (selfishly) AND might prefer moves that don't reduce B's Φ to BR. Specifically, PLAIN(LEFT) helps own Φ by reducing d to TL, and barely changes B's d to BR.
- **If Carrie uses γ = 0** (self-only): A's move is purely about own Φ. Still PLAIN(LEFT) but for only one reason.

**Subtle test:** it's hard to distinguish γ=0 from γ>0 from a single move. Instead, look at Carrie's move when the two decisions disagree. Modify:

```
 p  p  p  .  .  .  .  .     y=0
 p  .  .  .  .  .  .  .     y=1
 p  .  .  .  .  .  .  .     y=2
 p  .  .  A  .  B  .  .     y=3
 p  .  .  .  .  .  .  .     y=4
 p  .  .  .  .  .  .  .     y=5
 .  .  .  .  .  .  .  .     y=6
 .  .  .  .  .  .  .  .     y=7
```

Now the primed column at x=0 is a 6-run. A can't reach the ends in a single ply. For A at (3,3):
- PLAIN(LEFT) → (2,3): A closer to column. Self Φ up. Opponent Φ unchanged (far from column).
- PLAIN(RIGHT) → (4,3): A between A-and-B, moves toward B's side (but there's no primed structure there).

Now add a matching primed structure at x=7 that is equally attractive to B:

```
 p  p  p  .  .  .  p  p     y=0
 p  .  .  .  .  .  .  p     y=1
 p  .  .  .  .  .  .  p     y=2
 p  .  .  A  .  B  .  p     y=3
 p  .  .  .  .  .  .  p     y=4
 p  .  .  .  .  .  .  p     y=5
 .  .  .  .  .  .  p  p     y=6
 .  .  .  .  .  .  .  .     y=7
```

Symmetric. A's Φ maximized by LEFT. B's Φ maximized by RIGHT. If Carrie **is γ>0**, she prefers LEFT (own Φ up, B's Φ unchanged because B stays put). If γ=0 she also prefers LEFT. **Same answer.**

**What actually distinguishes γ=0 vs. γ>0:** set up a state where the two moves trade off. E.g., a move that hurts opponent more than it helps self:

```
 .  .  .  .  .  .  .  .
 .  .  p  p  .  .  .  .
 .  .  .  .  .  .  .  .
 .  .  A  .  .  B  .  .
 .  .  .  .  .  .  .  .
 .  .  .  .  .  p  p  .
 .  .  .  .  .  .  .  .
 .  .  .  .  .  .  .  .
```

If A steps into some cell that reduces B's Φ more than A's own Φ drops — that's a γ>0 signature. But our legal moves may not allow that cleanly. In practice: this is the hardest parameter to fit. **Low priority.** Skip unless we have budget.

### Board 7 — "Rat-belief bolt-on detection"

Setup: use the start of a game where we can manipulate `estimated_distance` / `noise` to concentrate rat belief. If Carrie does SEARCH when belief > ~0.33, she has a search-EV term (H8). If she never searches regardless of belief, her heuristic is pure cell-potential.

**Concrete observation plan (scrimmage):**
- Many students will have witnessed Carrie searching in games where belief concentrates — any scrimmage log shows whether Carrie searches at all. **This is essentially free evidence** once we have even a single Carrie scrimmage log. Just count SEARCH moves per game.
- If Carrie searches ≥ 1 time per game on average, H8-variants gain credence.
- If Carrie never searches (no observed SEARCH move across multiple games), her heuristic does not include search-EV.

**No bitmask needed for this one — it's a population-level observation.**

### Board 8 — "Cell-type coefficient test (are CARPET cells valued?)"

Does Carrie distinguish CARPET from SPACE in her potential?

Setup: Two equal distances, one board with a cluster of CARPETS, one with SPACEs.

```
 .  .  .  .  .  .  .  .
 .  .  .  .  .  .  .  .
 c  c  c  .  A  .  .  .
 c  c  c  .  .  .  .  .
 c  c  c  .  .  .  .  .
 .  .  .  .  .  .  .  .
 .  .  .  .  .  .  .  .
 .  .  .  .  .  .  .  B
```

Nothing primed on the board — so Φ is zero for **all cell-potential forms P1, P2, P3, P4** (P5 differs).

- Under P5 with `CARPET=0`: Carpet cluster contributes 0 to Φ. Carrie should just step toward B or search.
- Under P5 with `CARPET>0` (e.g. Carrie treats carpet as mobility asset with value): Carpet cluster contributes a positive term × 1/(1+d). Carrie should step LEFT (toward carpet).

**Differentiation:** PLAIN(LEFT) vs. PLAIN(RIGHT/DOWN toward B). Strong indicator of whether Carrie values carpet as mobility or only as consumed-prime.

### Board 9 — "Prime-chain-extension bonus test"

Does Carrie value laying a PRIME adjacent to an existing prime chain more than laying one far away?

Setup:

```
 .  .  .  .  .  .  .  .
 .  .  .  .  .  .  .  .
 .  p  p  p  .  .  .  .
 .  .  A  .  .  .  .  .
 .  .  .  .  .  .  .  .
 .  .  .  .  .  .  .  .
 .  .  .  .  .  .  .  .
 .  .  .  .  .  .  .  B
```

A is at `(2,3)`. Existing 3-prime at y=2, x∈{1,2,3}.

**Candidate moves:**
- PRIME(UP) → A at `(2,2)` — **illegal** (`(2,2)` is PRIMED, destination blocked). Skip.
- PRIME(LEFT) → A at `(1,3)`, glue on `(2,3)`. `(2,3)` is now PRIMED, adjacent to `(2,2)` primed but perpendicular to the 3-run (the run is horizontal at y=2). So it does **not extend the run**. Score +1.
- PRIME(DOWN) → A at `(2,4)`, glue on `(2,3)`. Same — doesn't extend. Score +1.
- PRIME(RIGHT) → A at `(3,3)`, glue on `(2,3)`. Same.
- PLAIN moves don't increase score this turn but may position for future extension.

All PRIME moves add +1 score and put a PRIMED at `(2,3)`, which creates a T-shape with the 3-run at y=2. For **maximum future extension**, A wants to position adjacent to an end of the existing run (i.e., at `(0,2)` or `(4,2)`). So the best PLAIN move is one that heads toward `(4,2)`: PLAIN(RIGHT) then PLAIN(UP), or directly TRY to PRIME toward an extension.

**Hypothesis predictions:**
- H1 (Σ, P1): after each PRIME move, Φ counts the new PRIMED cell with P1(2,3) = max k-roll from `(2,3)`. Now the vertical column has 2 primes `(2,2),(2,3)` — k=2 roll possible, P=2. So adding `(2,3)` PRIMED increases Φ by ≈ 2·(1/(1+0))=2. All three directions produce identical Φ delta. Score-diff is identical (+1 each). **All three PRIME moves tied by H1.** In a tie, Carrie's move-ordering breaks it — whichever direction iterated first wins. We can DETECT ties by seeing Carrie's iteration order.
- H3 (max): after PRIME, max cell's P jumps because the longest chain through `(2,3)` is now 2. Same across directions. **Tied.**
- H4 (run-length weighted): count for the 3-run at y=2 stays 3; count for new vertical 2-run is 2. Same tied.
- H6 (D_max=3): all new configurations isomorphic. Tied.

**If Carrie breaks the tie by preferring PRIME(RIGHT)** (direction enum RIGHT=1, second in iteration order `UP, RIGHT, DOWN, LEFT`? No — see §6 of GAME_SPEC, `get_valid_moves` iterates `UP, DOWN, LEFT, RIGHT`). So iteration tie-break is UP, then DOWN, etc. Observed preference for PRIME(UP) = illegal, so next is PRIME(DOWN). If Carrie picks PRIME(DOWN) all tied cases → tie-break-by-iteration. If she picks something else → **she has something other than pure cell-potential; maybe a "prime extension bonus" feature**.

**This board is a good tie-break-signature detector.** Especially useful if all other boards agree but this one differs — it reveals a secondary feature.

### Board 10 — "Endgame: turn budget matters"

Same structure as Board 3, but we set `turns_left = 2`. With 2 turns left, Carrie can at most reach cells within d=2. Far line at d>2 is **unrealizable** regardless of its potential.

- H1/H2/H3 without turn-awareness: still value far cells (incorrectly).
- H5 / H6-with-D_max-dynamic: **correctly** prune far cells.

**Observation:** if Carrie plays toward the far line even with 2 turns left (wasting the roll opportunity), she's not turn-aware. If she plays toward a nearer (lower-P) option she is. This is a **Carrie-version check** and useful for formulating a dominant counter.

### Board 11 — "SEARCH test in isolation"

Crank rat belief to >0.33 on one cell. No other available high-value moves. Does Carrie SEARCH that cell?

Exact belief engineering depends on HMM implementation but the high-level test is clear: repeated SCRATCH+distance-0 readings should sharpen belief to a single cell. If Carrie SEARCHes, H8 holds. If not, it doesn't.

### Board 12 — "Self-sabotage / γ-sign detector"

Give A two symmetric choices:
- Move 1: Increases own Φ by 0.5.
- Move 2: Decreases opponent's Φ by 2.0.

If Carrie picks move 2, she values γ highly (> β/4). If move 1, γ is small. Hard to construct without careful mask engineering; low priority.

---

### Distinguishing-power matrix

| Board | H1 | H2 | H3 | H4 | H5 | H6 | H7 | Notes |
|---|---|---|---|---|---|---|---|---|
| B1 (two-equal-rolls) | UP | UP | UP | UP | UP | UP | UP | Sanity only |
| B2 (prime-lines-asym) | PR(UP) | PR(UP) | PR(UP) | PR(UP) | PR(UP) | PR(UP) | PR(UP) | Sanity only |
| B3 (near-trivial-vs-far-huge) | toward far | toward far OR near (λ-dep) | toward far | toward far | toward far | stay/away | toward far | **λ or D_max signature** |
| B4 (many-small-vs-one-large) | LEFT | LEFT | DOWN | LEFT | DOWN | LEFT | LEFT | **Σ vs max signature** |
| B5 (distance-shape) | UP (mild) | UP or DOWN by λ | UP (mild) | UP (mild) | UP | UP or DOWN by D_max | UP (mild) | **exact distance-kernel shape** |
| B6 (opp-Φ) | LEFT | LEFT | LEFT | LEFT | LEFT | LEFT | LEFT | γ invisible here; skip |
| B7 (rat-belief) | no SEARCH | " | " | " | " | " | " | Bolt-on (H8) detection |
| B8 (carpet-value) | no step | " | " | " | " | " | " | P-function form (P5 variant) |
| B9 (prime-extend-bonus) | tied | tied | tied | tied | tied | tied | tied | Tie-break reveals secondary feature |
| B10 (endgame-turns) | toward far | toward far | toward far | toward far | near | near (dyn) | toward far | Turn-awareness binary detector |

**Top 3 most-diagnostic boards by eliminated-hypothesis-count:**
1. **B3** — eliminates 2–3 hypotheses (near vs. far tradeoff). Highest info.
2. **B4** — eliminates 1 hypothesis cleanly (Σ vs. max). Clean binary split.
3. **B5** — eliminates 1–2 λ/D_max candidates. Second-stage discriminator.

**Skipped/low-value:** B1, B2 (sanity only — no distinguishing power), B6 (γ invisible), B12 (hard to construct).

---

## 3. Execution protocol

**Setup constraint from `docs/plan/BOT_STRATEGY_V02_ADDENDUM.md` convention §F-14 (per the assignment brief):** ≤10–15 scrimmages total for the whole team for the rest of the contest. This is the binding budget.

### Options to expose Carrie to our designed boards

**(a) Live scrimmage + construct the board mid-game.** Play a live game vs. Carrie with a deterministic RattleBot-like opponent that PRIMES specific cells across opening moves. Carrie moves each ply on a stochastic board — the blocker RNG is per-game and we cannot control it. But by spending the first ~10–15 plies priming (our opening half of a scrimmage) we can paint *approximately* the target pattern, then observe Carrie's move on the subset of cells we actually primed.

  - **Cost:** 1 scrimmage slot per target board.
  - **Problem 1: board randomization.** Blocked corners vary each game; our target boards assumed specific corners. Fix: design each target board to be corner-agnostic — use inner cells only.
  - **Problem 2: we cannot control Carrie's moves before the target state.** Carrie will move too, pruning our options. Fix: design targets such that Carrie's first 8–10 plies, under our best-guess of her heuristic, cause her to arrive at the expected spot. If she does something unexpected, we *still* learn — the unexpected move is also a data point.
  - **Problem 3: observation quality.** We get the full replay JSON if bytefight stores it — see `docs/tests/LIVE_UPLOAD_*.md` for the format.
  - **Problem 4: rat belief is shared stochastic info.** If Carrie's heuristic includes H8 (rat-EV), we can't reproduce her belief grid. But we can check: if she SEARCHes on a specific turn, she has an EV term.
  - **Evidence/cost ratio: MEDIUM.** Expensive per slot; messy data.

**(b) Observe replays of other teams vs. Carrie.** Scan bytefight.org/compete/cs3600_sp2026 for publicly-visible replays against Carrie.
  - **Cost:** ≈ 0 scrimmage slots — only web-scraping time.
  - **Quality:** depends on whether replays are public. Per `docs/research/RESEARCH_PRIOR_ART.md` §A, past-winner-writeups are absent and the public tournament page has no leaderboard. **Replays likely require login.** We are logged in as rjavid3@gatech.edu (per CLAUDE.md §6). We can attempt to view scrimmage replays involving Carrie.
  - **If accessible:** goldmine. Dozens of student games × Carrie = dozens of boards per game × 1 Carrie move per turn. Potentially hundreds of Carrie move observations for zero scrimmage cost.
  - **Risk:** replays may only be visible to the team that played the game, not across teams. **This is the highest-leverage cheap option; verify first.**
  - **Evidence/cost ratio: VERY HIGH if accessible; zero if not.**

**(c) Aggregate ELO / win-rate inference.** Play many games across many boards and measure relative win-rate vs. different assumed-Carrie-heuristics in simulation.
  - **Cost:** 0 scrimmage slots.
  - **Quality:** very low. Can distinguish "RattleBot beats Carrie 40% vs. 60%" but not "which formula". ELO signal is too noisy for parameter fitting.
  - **Evidence/cost ratio: LOW.** Basically useless for formula discovery. Useful only for final performance measurement.

### Ranking by evidence/cost ratio

| Rank | Option | Evidence | Cost | Notes |
|---|---|---|---|---|
| 1 | (b) Replay observation | HIGH if accessible | ~0 | Check this first. If bytefight shows per-match replays accessible team-wide or via our own past scrimmages (LIVE_UPLOAD_001–004), we win. |
| 2 | (a) Live scrimmage with board-painting | MEDIUM | 1 slot per board | Use only for the TOP 3 boards (B3, B4, B5). Budget: 3 slots. |
| 3 | (c) ELO aggregate | LOW | 0 | Only useful as a "is our fit working" sanity check post-hoc. |

### Recommended protocol if we get ≤ 3 scrimmage slots

**Step 0 (0 slots):** Check bytefight.org for accessible Carrie replays. Our account has already played 4+ scrimmages (`docs/tests/LIVE_UPLOAD_001–004.md` exist). If any of those were vs. Carrie, **we already have Carrie move data to mine for free**. Even if not against Carrie directly, the replay viewer's existence tells us whether replays are store-and-accessible.

**Step 1 (1 slot):** Play **Board 3 (near-trivial vs. far-huge)**. Construct via: RattleBot primes 7 cells in a row on the far side, leaves a single stranded primed cell near Carrie's worker. Observe Carrie's first 3–5 moves.
- If she walks toward the 7-line → H6-low-D_max falsified, confidence on H1/H2-low-λ/H4/H7 rises to ≈ 80%.
- If she walks away or ignores → H6-low-D_max or H2-high-λ survives.

**Step 2 (1 slot):** Play **Board 4-revised (many-small vs. one-large)**. Engineer three 2-runs close to Carrie and one 4-run far. Observe.
- If Carrie steps toward the 4-run → H3 (max-dominant) survives.
- If toward the 2-runs → H1/H2/H4/H7 (Σ-style) survive.

**Step 3 (1 slot):** Play **Board 5 (distance-shape)**. If Steps 1–2 converged on "Σ-style, moderate decay", Board 5 distinguishes between `λ = 0.3`, `λ = 0.8`, and step-threshold. We design board variants with primes at specifically d=3, d=5, d=7 from our worker.

**After 3 slots, we expect:** credible credence on the top hypothesis ≥ 60%, with uncertainty concentrated on parameter values (β, γ, λ) not on functional form. That's enough to build a dominant counter (see §4).

### What if we get 0 scrimmage slots (worst case)

Pure observational. If we already have logs of RattleBot vs. Carrie from LIVE_UPLOAD_*, we can:
- Extract every board state Carrie acted on.
- For each, predict Carrie's move under each hypothesis. Compare to actual.
- Rank hypotheses by how many of Carrie's moves they correctly predict.

This is a **post-hoc discrimination** rather than an active protocol — lower power but zero cost. If LIVE_UPLOAD_001–004 each contains ~40 Carrie plies, we'd have ~150 data points, which is ample for an offline likelihood-ratio test across H1–H7.

**Action if we go this route:** read the replay JSON files, extract Carrie's boards and moves, and fit. See §4 of this doc for the comparison framework.

---

## 4. Attack plan — strict-dominator counter-heuristic if we confirm the formula

**Assumption for this section:** suppose Steps 1–3 of §3 confirm **H1 with parameters** `(β=0.5, γ=0, P=P1, f=1/(1+d))`. (Any specific confirmed hypothesis works the same way — H1 is just the most likely prior.)

### The strict-dominator construction

A heuristic `v_R` strictly dominates Carrie's `v_C` in our sense iff:
**For every state s reachable by any rational play, `v_R(s) − v_C(s)` has the right sign — preferring states that are actually better for us against Carrie.**

Given Carrie's formula `v_C(s) = (self_C.pts − opp_C.pts) + β · Σ_c P(c)/(1+d(W_C, c))` where `W_C` is Carrie's worker, we can construct a dominator by:

1. **Include all of Carrie's features.** Every cell c contributes `P(c)/(1+d(W, c))` with weight β. No worse than Carrie on states where our features and hers agree.
2. **Add features Carrie ignores.** For each of our extra features f_k, the extra term `μ_k · f_k(s)` is orthogonal to Carrie's features.
3. **Out-search Carrie.** Same expectiminimax+alpha-beta but 1 ply deeper, faster move ordering, and better pruning.

### Specific extra features Carrie likely lacks

Based on §0's "what her heuristic may not include":
1. **`F_opp_mobility`** — count opponent's legal non-search moves. Higher = more options for opponent = bad for us. Weight `μ_1 < 0`.
2. **`F_prime_chain_quality`** — sum over existing PRIMED chains of `CARPET_POINTS_TABLE[len(chain)] if reachable_by_us_in_2_plies else 0`. This is essentially P_reach-1-turn-explicit, a more aggressive form of P1.
3. **`F_endgame_pressure`** — multiply cell-potential by `min(1, turns_left / d)`. When turns_left is low and d is high, the cell is unrealizable. Carrie's `1/(1+d)` doesn't know about turn budget.
4. **`F_rat_ev`** — `RAT_BONUS · max_c belief(c) − RAT_PENALTY · (1 − max_c belief(c))`. Search EV with Bayesian cell. Weight `μ_4 ∈ [0, 1]`.
5. **`F_opp_Φ_penalty`** — subtract `β_opp · Σ_c P(c)/(1+d(W_opp, c))`. Include opponent-side potential as a negative. Equivalent to setting γ > 0 in Carrie's own form, giving us an aggressive-play bias.
6. **`F_center_bias`** — small positive weight for cells near board center (where blockers rarely reach). Encourages mobility over corner-hugging.
7. **`F_primed_penalty_under_worker`** — negative weight if we're standing on PRIMED (we cannot move off except by ROLL). Prevents self-trapping.

### Pseudocode for dominating heuristic

```python
def rattlebot_heuristic(board, belief, turns_left):
    # Score differential
    v = board.player.pts - board.opp.pts

    # Carrie's exact term (copy verbatim once we confirm it)
    for c in all_cells(board):
        if blocked(c): continue
        P = cell_potential(c, board)       # P1: max legal carpet points anchored here
        d_self = manhattan(board.player.pos, c)
        d_opp  = manhattan(board.opp.pos, c)
        v += BETA    * P / (1 + d_self)
        v -= GAMMA   * P / (1 + d_opp)     # Carrie likely has GAMMA=0; we have GAMMA>0

    # Features Carrie lacks
    v -= MU1 * opp_legal_moves_count(board)
    v += MU2 * prime_chain_quality_reachable_in(board, 2)
    v *= endgame_pressure_multiplier(turns_left)   # shrinks unrealizable cells
    v += MU4 * rat_ev(belief)
    v -= MU6 * center_penalty(board.player.pos)
    v -= MU7 * 1.0 if standing_on_primed(board) else 0.0

    return v
```

### Why this dominates Carrie

At equal search depth:
- On states where Carrie's features dominate, our heuristic agrees with hers (first Σ term is identical).
- On states where she's blind (e.g. about to enter endgame with unrealizable far cells, or ignoring opponent threats), our extra features correct the blind spots. Carrie walks into traps that our heuristic sees.

**Dominance is not strict mathematically** (in rare states our extra features might penalize a move Carrie would make that coincidentally was optimal). In expectation over games, though, since our extras are all pointing at actually-useful signals, expected value of following `v_R` ≥ expected value of `v_C`. For tournament play, that's what we need.

**Critical:** we need BO or grid search over `(β, γ, μ_1..μ_7)` to avoid over-weighting extras and becoming too conservative. This is already scoped in task #29 (T-20d Bayesian-opt weight tuning pipeline).

### If we confirm H2, H3, or another form instead

Same recipe:
- **H2 (exponential):** use `exp(−λ · d)` for the Carrie-matching term; everything else unchanged.
- **H3 (max-dominant):** replace Σ with `max_c P(c)·f(d)` for the Carrie-matching term; KEEP our Σ term as an ADDITIONAL feature. Then we have "max feature" (Carrie's strength) + "sum feature" (we see the board-wide prime structure she's blind to).
- **H6 (step threshold):** replace `f(d)` with `1 if d ≤ D_max else 0`, and add an additional term with smooth decay beyond D_max. We capture short-range (matching Carrie) + long-range (her blind spot).

The general principle: **replicate Carrie's signal verbatim, then add signal Carrie ignores**.

---

## 5. Fallback — if we CANNOT determine the formula

If §3's protocol yields inconclusive evidence (e.g., replays inaccessible + ≤3 scrimmage slots inadequate), we build a **structurally-similar but strictly-stronger heuristic by construction**.

### Principle

Even without knowing Carrie's exact formula, we know she has:
- Score differential (guaranteed).
- Some `Σ / max` aggregation of a cell-potential × distance-decay (from §9 wording).
- HMM-compatible search (but probably not a search-EV feature).

Our heuristic can simply be **a union of all plausible Carrie features + extras Carrie almost certainly lacks**, with BO-tuned weights. If *our* feature set is a superset of *her* feature set, and BO finds decent weights, we win by construction in expectation.

### Feature set for fallback (superset strategy)

All the features already listed in §4 plus:
1. **Multi-scale distance kernel:** include three distance kernels simultaneously — `1/(1+d)` (H1), `exp(−0.5·d)` (H2-small-λ), `step at D_max=5` (H6-mid). Carrie must be *one* of these (or close to one); by including all three as weighted features, we dominate any single choice.
2. **Both P1 and P4 potentials:** include both `P1 = max k-roll from c` and `P4 = max k-roll after moving to c`. BO picks the useful weights.
3. **Carpet-mobility feature:** `#CARPET cells reachable within 3 plain-steps`. Captures board-traversal value Carrie likely misses.
4. **Prime-adjacency bonus:** `sum over PRIMED cells of (1 if adjacent_to_another_primed else 0)`. Values contiguous primes over isolated ones.
5. **Anti-self-block:** penalize PRIME moves that end at a cell with no un-PRIMED neighbor on the far side (would trap us).

### Suggested weight magnitudes (pre-BO starting point)

- Score diff: 1.0 (fixed)
- Cell-potential H1-style: 0.4
- Cell-potential H2-style: 0.2
- Cell-potential H6-style: 0.2
- Opponent-mobility penalty: 0.1
- Rat-EV bolt-on: 0.3
- Carpet-mobility: 0.05
- Prime-adjacency bonus: 0.1

### Relationship to `docs/plan/BOT_STRATEGY_V02_ADDENDUM.md`

I was told not to read that addendum to avoid bias, but the task brief itself says "our v0.2 addendum already plans this" — so there's already a BO-tuned-more-features-than-Carrie plan on paper. My recommendation: **keep it, and update the feature list to include the multi-scale distance kernel described in §5.1 above**. The multi-scale kernel is the key: by running three decay forms in parallel we automatically subsume whatever Carrie uses.

If the addendum already includes a multi-scale distance feature, no change. If it uses a single decay function, **upgrade it to three** as above. The cost is 3× the Φ-loop runtime per leaf (still O(64·3) = 192 ops per leaf, trivial).

---

## 6. Go/No-Go gate — what to do next

**IF bytefight replays are accessible team-wide** → immediate high-leverage task: mine existing Carrie replays for Carrie moves. **Cost: zero scrimmage slots.** Outcome: precise hypothesis ranking before any new experiments. **Priority: DO THIS FIRST.**

**IF replays are accessible only for own team's games** → count how many of our LIVE_UPLOAD_001–004 scrimmages were against Carrie. If ≥1, same mining plan at zero cost. If 0, move to option (a).

**IF only option (a) is viable** → spend 3 scrimmage slots on boards B3, B4, B5 in that order. Stop after each and re-rank hypotheses.

**IF scrimmages are exhausted or option (a) fails** → execute §5 fallback: superset-feature BO-tuned heuristic. This path does not require knowing Carrie's formula.

### Decision timeline (with deadline = 2026-04-19 23:59)

- **Today (2026-04-16):** Run §6 go/no-go — check replay accessibility. 30 minutes.
- **Today evening:** If replays accessible, mine them. If not, commit 1 scrimmage to B3.
- **Tomorrow (2026-04-17):** Based on §3 Step 1 outcome, run B4 or B5 or begin BO fitting.
- **2026-04-18:** Lock in counter-heuristic; run local batches vs. FloorBot/Yolanda to verify no regression. Upload final to bytefight.org.
- **2026-04-19:** Final sanity scrimmage. Lock active submission before 23:59.

**Bottom line:** if the replay-mining path opens up, this entire exercise is cheap (zero scrimmage budget). If not, we commit 3 scrimmage slots and guarantee a near-dominance read on Carrie. In the worst case (nothing reveals the formula) we fall back to the superset approach, which the v0.2 addendum already contemplates.

---

## 7. Open questions / things I did not address

- **Exact form of the HMM state in Carrie's heuristic.** She may track the rat and include belief-mass terms in the heuristic I did not enumerate (covered as H8 bolt-on only). More detail possible if we see her SEARCH patterns.
- **Carrie's expectiminimax depth.** §9 says "same structure as Albert" — but Albert's depth is also unknown. A deeper-searching Carrie is harder to distinguish from a shallower-but-smarter-heuristic Carrie. Tests in §2 implicitly assume depth ~3, which fits the ~6s/move budget for a ~30-branching-factor game.
- **Move-ordering tie-break.** Important for boards B1, B2, B9 where all hypotheses predict the same move. Whichever iteration order Carrie uses (likely `get_valid_moves` order = UP, DOWN, LEFT, RIGHT) is fingerprint-able from any handful of tied states.
- **What if Carrie has a non-additive heuristic** (e.g., neural network)? The §9 wording is strong evidence she doesn't, but we should reserve ~5% credence on "something totally different". Our fallback superset-BO approach covers this case by just being better-than-Carrie-in-expectation regardless of her form.
