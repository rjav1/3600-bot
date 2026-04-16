# RESEARCH_ADVERSARIAL — Adversarial-Search Options for the Carpet/Rat Game

**Author:** researcher-search
**Date:** 2026-04-16 (v1.0); amended 2026-04-16 (v1.1 — GAME_SPEC errata)
**Status:** Research survey. **No final choice made.** Strategy-Architect picks later.

## Errata (v1.1 — post GAME_SPEC.md landing, 2026-04-16)

Three facts from `docs/GAME_SPEC.md` affect this report. None invalidate a
section but each tightens a claim:

1. **`apply_move(SEARCH)` is a no-op for points and rat state.** The
   +4/−2 and the rat respawn happen in `engine/gameplay.py:434-445`,
   *after* `apply_move` returns. `forecast_move(SEARCH)` therefore returns
   a copy with unchanged points and an unchanged belief. **Consequence
   for §B and §F.1a:** any expectiminimax branch on SEARCH must apply
   the EV and the belief-collapse side-effect manually — `forecast_move`
   will silently give the wrong leaf. This **strengthens** the §F.1c
   recommendation to handle SEARCH at root-only with explicit EV math;
   in-tree SEARCH is a footgun.

2. **Tournament time is 240 s; local is 360 s** (per
   `engine/gameplay.py:232-238` when `limit_resources=False`).
   **Consequence for §A.5, §D, §H:** my throughput and depth projections
   were on a local dev machine without `limit_resources`. The 6 s/move
   budget in §D is correct for the tournament (240 / 40). The feasible
   depth table in §H is still valid *if* benchmarks are repeated with
   `limit_resources=True` or divided by 1.5 to convert local → tournament
   wall time. Realistic adjusted projection: **d = 5–7 ply pure Python,
   d = 8–10 with a numba leaf**. Do not ship time-tuning derived from
   uncalibrated local runs.

3. **Spawns can land on blocked cells.** `board_utils.generate_spawns`
   picks y ∈ {2,3,4,5} without checking the corner blocker mask. Also,
   A is always in x ∈ {2,3}, B mirrored at 7−x, same y. **Consequence
   for §A.2:** the branching-factor synthetic boards in the empirical
   appendix used a 2×2 corner pattern and rejected blocked-cell spawns;
   that's still representative of mid-game b, but worst-case early-game
   boards (3×2 or 2×3 corners + spawn-on-blocked) are slightly more
   constrained — likely pushes early-game mean b down by 0.2–0.5, not
   up. No revision to conclusions.

---

> Scope: survey adversarial-search algorithms that could power our `play()`
> decision, with evidence and tradeoffs. This is the Related Work + Methods
> Comparison for a bot whose 4-minute global budget forces careful compute
> accounting. HMM/belief mechanics are covered in RESEARCH_HMM_RAT.md; this
> document treats the belief as an **input** to search.

---

## Section A — Game characteristics (frame the problem)

### A.1 State space

An exact game state is:

- 8×8 board with 4 cell types (SPACE / PRIMED / CARPET / BLOCKED).
  Blocked is immutable per game; the remaining 3 types partition the
  non-blocked cells. Upper bound: 3^64 ≈ 3.4×10^30 board configurations
  (most unreachable).
- 2 worker positions (≤ 64×64 = 4096, minus blocked/coincident).
- Scores (roughly −40…+150 per player — bounded by scoring rules).
- Turn counter 0..80 and who-moves-next (2).
- **Hidden**: 1 rat position (64 cells, but in practice a belief
  distribution over them — a point on the 63-simplex).
- Per-turn history visible to both sides: opponent's last search
  `((x,y), bool)`.

For adversarial search we work with the "information-state" — everything
we can observe — and let the rat enter as a chance element or as a scalar
EV via the belief. The **exact** game tree is doubly infeasible: exponential
in depth, and each chance/observation branch fans out over 64 cells × 3
noises × 4 distance offsets = up to 768 successors if we model
observations as chance branches.

### A.2 Branching factor — measured

I ran `get_valid_moves` on 500 synthetic mid-game boards (18 % PRIMED,
12 % CARPET, 2×2 corners, mirrored spawns in the inner 4×4), 500 early
boards (5 % / 2 %), and 500 late boards (30 % / 25 %). Results:

| Phase       | prime%/carpet% | mean b (no-search) | max | p90 | carpet-moves mean | max |
|-------------|----------------|--------------------|-----|-----|-------------------|-----|
| Early       | 5 / 2          | 6.82               | 9   | 8   | 0.0               | 2   |
| Mid         | 18 / 12        | 6.33               | 9   | 8   | 1.02              | 5   |
| Late        | 30 / 25        | 6.36               | 11  | 8   | 2.5+              | ~8  |

With `exclude_search=False` the count jumps by 64 — mean ≈ **70** moves
(always 64 valid searches, since the engine doesn't validate cells as
"interesting" — any of the 64 squares is a legal search move, even over a
blocked square).

Key insight: **the combinatorial branching is small (≤ ~11) as long as we
keep search moves out of the tree**. Search moves inflate b to ~70 and make
any deep tree 10× wider. This is a structural invitation to treat searches
as a **separate decision layer** (one-ply EV lookup against the belief),
not as moves explored at every tree node.

Worst-case carpet legs: from a corner with a long primed line of length 7,
4 directions × up to 7 lengths = 28 carpet moves, plus 4 plain + 4 prime =
36 total (search excluded). The `p90 = 8` shows this is rare in random
boards, but an adversary can engineer it.

### A.3 Depth intractability

At b ≈ 7 (search excluded), full minimax through the end of the 40-turn
game (≤ 80 plies from ply 0) visits ≈ 7^80 ≈ 10^67 nodes. The game tree
is intractable: we must search to bounded depth with a heuristic leaf
evaluation.

### A.4 Chance & partial info

- **Rat moves** every turn according to `T` (sparse stochastic, ≤ 5
  nonzeros / row).
- **Sensor** returns `(noise ∈ {SQUEAK, SCRATCH, SQUEAL}, distance ∈
  Nat)` with the joint likelihood from CLAUDE.md §1.
- **Opponent search**: we see their guess and its result — dense
  information, often a strong pose-update signal on their belief.

Strictly, this is a partially observable stochastic game (POSG). Practical
simplification (see §F): fold the rat into a scalar belief and
**evaluate** its effect at decision points (EV of search moves, expected
noise-channel info gain) rather than opening chance branches in the
search tree. This makes the search tree deterministic-style (MAX/MIN
only) and keeps branching at ~7.

### A.5 Throughput (measured on Python 3.13, Windows laptop, no numba)

Raw `engine/game/board.py` primitives, no agent logic:

| Op                                                | ops/sec |
|---------------------------------------------------|---------|
| `get_valid_moves(exclude_search=True)`            | ~318 k  |
| `get_copy()`                                      | ~65 k   |
| `forecast_move(..., check_ok=False)`              | ~63 k   |
| Full step (`get_valid_moves` + forecast + reverse)| ~48 k   |
| Non-pruning minimax to depth 4 (no heuristic)     | ~50 k nodes/s |

Raw Python throughput on pure structural traversal is ~50 k node-expansions
per second. A 6-second budget therefore allows **~300 k leaf
evaluations** before we even run a heuristic. Once we add a non-trivial
leaf eval (HMM update, cell-potential score), expect 20–80 k leaves/s
in pure Python, 100–200 k with numpy vectorization, 500 k+ with
numba — but numba JIT warm-up costs real init-time budget.

---

## Section B — Algorithm candidates

For each: (1) concept, (2) pseudocode sketch, (3) time/memory cost in
this game, (4) suitability 1–5.

### B.1 Expectiminimax (MAX / MIN / CHANCE)

**Concept.** Classic Russell-Norvig algorithm. Three node kinds: our
choice (max), opponent's choice (min), and nature (chance node — rat
moves, sensor observation). Leaf eval = heuristic.

**Where chance nodes appear here.**

- Before each ply, the rat moves per `T`. This is a chance branch of
  support ≤ 5 per current cell, but since we don't know where the rat
  *is*, the effective chance fan-out is over the whole belief support
  (up to 64 cells × ~5 successors, collapsing to ≤ 64 posterior cells).
- After each ply the sensor fires — 3 noises × ≤ 4 distance offsets = up
  to 12 observation branches at each level, weighted by their posterior
  probability.

**Naive pseudocode.**

```
function expmm(node, depth):
    if terminal(node) or depth == 0: return eval(node)
    if max_node(node):
        return max(expmm(child, depth-1) for child in moves(node))
    if min_node(node):
        return min(expmm(child, depth-1) for child in moves(node))
    if chance_node(node):
        return sum(p * expmm(child, depth-1) for p, child in outcomes(node))
```

**Cost.** Raw branching with full chance fan-out: b_max × b_min ×
b_chance per 2-ply. With b_max = b_min ≈ 7 and b_chance ≈ 12–64, a
2-ply (one of each) block is 7 × 7 × 12 ≈ 600 nodes, so depth-4 in pairs
(so 4 action-plies with chance between each) ≈ 7^4 × 12^4 = 50 M nodes.
Even at 50 k nodes/s that's 1000 s — infeasible at depth 4.

**Mitigations that make it tractable.**

- Don't open a chance node for the sensor — integrate sensor updates
  **outside** the search (keep the belief as a single "expected" grid,
  updated between real turns). Sensor noise is already observed when we
  call `play()`; we're reasoning about *future* turns where we won't
  know the observation, so treating it as information fold-in (reward
  bonus proportional to expected belief entropy reduction) rather than
  as a branch is defensible.
- Don't open a chance node for the rat's move either — the HMM belief
  grid already represents the rat's distribution, and what we care about
  in search is cell-colouring dynamics, not rat-position-dependent
  state (EXCEPT search moves, which we handle separately).

After these two cuts, expectiminimax **collapses to plain minimax** on
the board-colouring subgame, with the rat handled as a belief potential
at leaves. See §F.

**Suitability:** 3/5 as a "full" expectiminimax; 5/5 in the collapsed
form (which is just minimax + a belief-aware eval).

### B.2 Expectiminimax with alpha-beta pruning (and *-minimax / Star1 / Star2)

**Concept.** α-β on MAX/MIN nodes is standard. Chance nodes **cannot be
pruned naively** because a chance node's value is a weighted average
over its children; you need bounds on *all* children to bound the
average, which is α-β-incompatible.

Ballard's **\*-minimax** and the **Star1 / Star2** algorithms (Ballard
1983, rediscovered by Hauk-Buro-Schaeffer 2006) exploit a **bounded
evaluation function** `v ∈ [L, U]` to prune chance children:

- After exploring k of n chance children with (weighted) partial sum S,
  if the best achievable weighted value `S + (remaining-weight) × U` is
  already ≤ α, cut. Conversely with lower-bounds for β.
- Star2 adds a "probing" phase: cheaply compute a lower bound on each
  chance child before doing the full search, reorder by probe, and
  often prune ≥ 50 %.

**Pseudocode (Star1).**

```
function star1_chance(node, alpha, beta, depth):
    children = outcomes(node)
    L, U = eval_bounds()
    A = (alpha - (total_weight - 0) * U) / weight[0]
    B = (beta  - (total_weight - 0) * L) / weight[0]
    total = 0
    for k, (p, child) in enumerate(children):
        a = max(A, L); b = min(B, U)
        v = expmm_ab(child, a, b, depth-1)
        total += p * v
        if v >= B: return total + (remaining weight)*U  # cut
        if v <= A: return total + (remaining weight)*L  # cut
        # tighten A, B for the next child
```

**Cost.** In principle an order-of-magnitude speedup over naive
expectiminimax; in practice, **only useful if we keep chance nodes in
the tree**. Given §B.1's collapse, we likely don't.

**Suitability:** 2/5 as Star1/Star2 implementation (we won't have
chance nodes if we fold belief into the eval); **5/5 for the α-β part**
which is essential regardless.

### B.3 Iterative deepening + transposition table (with Zobrist hashing)

**Concept.**

- Iterative deepening (ID): search depth 1, then 2, then 3, ..., until
  `time_left()` says stop. Always have a best-move-so-far to return.
- Transposition table (TT): a hash map from state → (score, depth,
  flag ∈ {EXACT, LOWER, UPPER}, best-move). Handles move-order
  collisions *within* a depth (game-tree transpositions) and caches
  shallow-depth results across ID iterations.
- **Zobrist hashing** on the 4 masks + worker positions + turn parity:

```
zobrist_key = 0
for bit_index in 0..63:
    cell_type = read_bit(bit_index)  # 0..3
    zobrist_key ^= Z[bit_index][cell_type]
zobrist_key ^= Z_player_pos[player_bit_index]
zobrist_key ^= Z_opponent_pos[opponent_bit_index]
if is_player_a_turn: zobrist_key ^= Z_side
```

Each move only flips a handful of bits, so Zobrist can be **updated
incrementally** in `apply_move`-like wrappers (XOR out old cell-type
hash, XOR in new one — O(1) per cell touched). Carpet rolls of length k
touch k cells; still O(1) amortized.

TT size: a dict of ~500 k entries fits in Python. We'd key on a 64-bit
Zobrist int. Two-bucket replacement (always-replace + depth-preferred)
is standard chess-engine lore.

**Cost.** TT lookup is ~100–200 ns in Python. Hit rates depend on
transposition density; this game has modest transpositions (the 4 masks
commute across move orderings; PLAIN orderings can reconverge), maybe
5–15 %. Bigger gains come from **ID + TT move ordering**: storing the
PV move and trying it first next iteration typically cuts α-β node
counts by 3–10×.

**Extras enabled by ID.**

- Aspiration windows: search depth d+1 with `[α-δ, β+δ]` around depth-d
  score; re-search on fail-high/fail-low.
- Killer-moves and history-heuristic: save cutoffs' moves per ply; try
  them first at siblings.
- Anytime: we can stop whenever; we always have last-iteration's best.

**Suitability:** **5/5**. This is the backbone of every serious
minimax-family bot. For this project, ID+TT is almost strictly
additive and has the best effort-to-ELO ratio of any single item in
this survey.

### B.4 MCTS (UCT) with random rollouts

**Concept.** Build an asymmetric tree via (Selection with UCB1 →
Expansion → random-rollout Simulation → Backprop). Anytime; returns
the most-visited root-move.

**Rollout policy question.** Random rollouts will be terrible here
because **carpet rewards require multi-step planning** (prime for 3–6
turns, then roll). A random rollout from a primed-heavy state will rarely
execute a 5-roll; the expected utility signal at a node is noisy and
biased toward low-value states where random play still works.

**Possible remedies (each costs compute per rollout):**

- **Light-playout heuristics:** bias rollout policy to prefer PRIME on
  SPACE cells adjacent to existing primes, and CARPET if ≥ 3 in-line
  primes exist. Introduces bias but dramatically improves signal.
- **Shallow-minimax rollouts:** 1–2 plies of greedy heuristic instead of
  random to end-of-game.
- **Early cutoff:** stop rollout at k plies, evaluate heuristic. MCTS +
  heuristic leaf is the "UCT with evaluation" hybrid.

**Cost.** Each rollout in pure Python through `forecast_move` will run
40–80 steps × ~16 µs/step ≈ 0.6–1.3 ms for a full rollout. 6 seconds →
~5–10 k rollouts/move. Not many, especially at branching 7+ where UCB
barely converges past depth 3–4 effective.

**Suitability:** **2/5** with random rollouts (rollout noise dominates).
**3/5** with heuristic-guided rollouts (a lot of effort for uncertain
gain vs. plain α-β+ID).

### B.5 Information-Set MCTS (IS-MCTS)

**Concept.** Cowling, Powley, Whitehouse (2012). Instead of searching a
single state, MCTS is performed over **information sets** — nodes group
states indistinguishable from the agent. For stochastic/partial-info
games (cards, poker, etc.), ISMCTS samples a **determinization** (a
concrete world state consistent with the info set) at each simulation
and performs one selection/rollout on it, aggregating visits across
determinizations at the info-set node.

**Application here.** The rat's true position is the hidden variable.
ISMCTS would, per simulation, sample the rat from the current belief,
roll forward with the `T` transition + a fixed opponent policy, and use
the outcome to update value estimates at info-set nodes.

**Pros.**

- Handles the partial info and stochasticity natively.
- Strategy-fusion-safe unlike naive determinized minimax.

**Cons.**

- Rollouts are expensive and slow.
- Rat position actually matters **only for search moves** — for
  carpet/prime/plain moves, the rat is irrelevant in this turn (it
  doesn't block you, doesn't move you). So ISMCTS spends most of its
  sampling budget on a hidden variable that doesn't affect 95 % of our
  decisions.
- We already plan to maintain the belief exactly; sampling from it
  discards information.

**Suitability:** **2/5**. A nice match for the problem class in
general, a poor match for this specific game where the hidden variable
is weakly coupled to most actions. Good fallback if minimax+eval proves
too shallow.

### B.6 PUCT-style MCTS with handcrafted prior (poor-man's AlphaZero)

**Concept.** AlphaZero's search uses `PUCT(s, a) = Q(s,a) + c_puct ·
P(s,a) · sqrt(ΣN) / (1 + N(s,a))`. A **prior** `P(s,a)` biases selection
toward "probably good" moves; `Q` is learned from rollout returns. With
a neural net, `P, V` come from the net; **without** a net, we can hand-craft
`P(s,a) ∝ heuristic_delta(s, a)` and `V(s)` = our static eval.

**Pros.**

- Focuses compute on promising moves — huge win when b is ~11 but most
  moves are bad (PRIME into a dead area, SEARCH at low-belief cell).
- Anytime; scalable to more compute if we find it.

**Cons.**

- Needs a rollout policy anyway for `Q` to converge (though one can short-circuit
  to `V(leaf)` like AlphaZero-no-rollout).
- Much more code complexity than α-β+ID, for uncertain gain over a
  well-tuned heuristic.

**Suitability:** **3/5**. Attractive if we have spare cycles and our
heuristic is already solid.

### B.7 Beam search / partial-best-first

**Concept.** At each node, keep top-K children by heuristic, recurse.
Loses optimality guarantees but stays blazing fast at depth — O(K^d)
nodes. With K = 3 and d = 8, 3^8 = 6561 nodes — easy.

**Pros.**

- Trivial implementation, easy to tune.
- Works well when good moves are usually in the top-K by shallow
  heuristic (plausible in this game).

**Cons.**

- Zero optimality, no α-β safety. An opponent engineering "trap" moves
  whose signal is below top-K at shallow depth would be missed.
- Less conceptually satisfying as a competitive bot.

**Suitability:** **3/5**. As a *fallback* or as an internal rollout
policy inside MCTS. Not the main engine.

### B.8 Pure policy / one-ply lookahead

**Concept.** No tree. Score every legal move by `immediate_reward +
heuristic(next_state)`. Pick the best. This is essentially how George
plays (per assignment.pdf §9).

**Pros.**

- Trivially fast (thousands of moves/sec per position).
- Very easy to tune the heuristic rigorously with local-search hill
  climbing.
- Latency headroom lets us burn budget on belief updates.

**Cons.**

- No opponent modeling. Blind to traps.
- Grading floor: George is explicitly the "≥ 70 %" bot. If we want ≥ 90
  %, we probably need ≥ 1 real ply of opponent reasoning.

**Suitability:** **2/5** as final answer; **5/5** as an initial baseline
and as our move-ordering policy inside a real search.

---

## Section C — Move ordering

α-β prunes exponentially more when good moves come first. At b = 7, the
theoretical best case is √(b^d) ≈ b^(d/2) — a factor of ~b^(d/2)
speedup, which at d = 6 is 7^3 ≈ 343× over naive. In practice 5–20× is
realistic.

**Candidate ordering schemes** (cheap → expensive):

1. **Hash-move first.** If TT has a previous best-move for this state,
   try it. Cost: O(1). Gain: big (often 2–4× alone).
2. **Immediate-point-delta ordering.** Score each move by the
   point change it produces in one ply: carpet(7) = 21, carpet(6) = 15,
   carpet(5) = 10, carpet(4) = 6, carpet(3) = 4, carpet(2) = 2, prime = 1,
   plain = 0, carpet(1) = −1, search = EV(±2 / +4).
   Cost: already computed by move-gen. Gain: likely 2–4×.
3. **Heuristic-delta after one ply.** Score each child by our full
   static heuristic; sort descending. Cost: one heuristic call per move
   at each tree node (expensive). Gain: 2–3×. **Only worthwhile at
   near-root nodes**; at leaves it's wasted work.
4. **Type priority default.** When the above tie or are unavailable,
   order CARPET > PRIME > PLAIN > SEARCH. Rationale: CARPET is almost
   always the biggest immediate swing; SEARCH is rarely ≥ PRIME in
   point-EV. Cost: zero. Gain: modest.
5. **Killer moves.** Per ply, keep the top 2 moves that caused β-cuts;
   try them first on siblings. Classic chess heuristic.
6. **History heuristic.** Per (move_type, direction, [roll_length])
   bucket, track cumulative depth × (was-cutoff) score; order by this
   globally.

**Recommended default stack** for α-β:

```
order = [ hash_move if TT hit else None,
          ... moves sorted by
                (killer? , history_score, type_priority, immediate_delta) ]
```

### C.1 Dedicated treatment of SEARCH moves

SEARCH is not a board-mutating move (no cell flips, no worker move).
Including all 64 SEARCH moves inflates b ~10×. Strategies:

- **Exclude from the tree entirely.** Compute "best SEARCH" at the root
  as a single candidate whose value is `EV_search = 4 · P(rat at
  best_cell) − 2 · (1 − P(rat at best_cell)) + info_gain_bonus`. Compare
  against the best board-move at the root and pick.
- **Include at root only.** Search tree does board-only moves, but the
  root-move selection compares the best board-move's search score
  against the best SEARCH EV.
- **Threshold gate.** Only include SEARCH at root if
  `max_p(cell) > 1/3` (or near-threshold with information value
  reasoning) — see RESEARCH_HMM_RAT.md for the threshold math.

Empirically, all 3 reference bots evidently do something like "rare
opportunistic SEARCH when EV is high." George is explicit about this.

---

## Section D — Time management

### D.1 Budget shape

- Total: 240 s / 40 moves = **6 s/move average**.
- Hard lower bound: `time_left()` must end > 0 at the end of move 40.
- Safety margin: return early when `time_left() < 0.05 s`; reserve
  0.2–0.5 s for the final few moves to avoid a disastrous endgame
  timeout.

### D.2 Flat vs adaptive allocation

- **Flat (6 s always).** Simple, robust, hard to game.
- **Front-loaded (8 s early, 4 s late).** Bad — late-game moves often
  have the most leverage (carpet rolls, endgame search) and branching
  is widest.
- **Back-loaded.** Save budget for midgame/endgame pivots.
- **Adaptive.** Spend more on **critical** positions.

### D.3 What makes a position "critical"?

Heuristics for critical-move detection:

- **Branching × variance.** If many moves tie near the top of the
  ranking by shallow eval, the position is sensitive — burn more time
  to disambiguate. If one move dominates by a wide margin, settle fast
  and bank the budget.
- **Score-swing potential.** Long primed lines mean big carpet rolls
  possible → high variance → deepen.
- **Opponent has prime line.** Defensive interruption may be needed;
  deepen.
- **Belief entropy high and we're considering SEARCH.** Opportunity
  cost of a bad search is steep (-2 and a wasted turn).

### D.4 Iterative deepening as the controller

ID is the natural adapter:

```
def play(board, sensor, time_left):
    budget = allocate(board, time_left)           # § D.5
    deadline = now() + budget
    best = None
    for d in range(1, MAX_DEPTH):
        if now() + safety_margin > deadline: break
        best_this_depth = search_to_depth(d, deadline)
        if best_this_depth is not None:
            best = best_this_depth
        if score(best) is mate-like: break        # early exit
    if time_left() < 0.2: tighten safety
    return best
```

`search_to_depth` must check `time_left()` periodically (e.g., at every
node-expansion modulo 1024) and raise a `TimeUp` exception — caught by
the ID loop, which returns the previous iteration's best.

### D.5 Concrete allocation scheme

```
def allocate(board, time_left):
    remaining_moves = max(1, board.player_worker.turns_left)
    t = time_left()
    base = t / remaining_moves
    # boost for critical
    if is_critical(board): multiplier = 1.6
    elif is_easy(board):   multiplier = 0.6
    else:                  multiplier = 1.0
    hard_cap = max(0.3, min(t - 0.5, base * 2.5))
    return min(base * multiplier, hard_cap)
```

At 40 moves × 6 s this gives 3.6 s on easy, 6 s normal, 9.6 s on
critical — still leaving positive time-left at the end as long as the
mean across moves ≤ 6 s.

---

## Section E — Bitboard tricks

`Board` state is already 4 × 64-bit ints (`_space_mask`, `_primed_mask`,
`_carpet_mask`, `_blocked_mask`). This unlocks:

### E.1 Fast move generation (already present)

`get_valid_moves` uses bit-shift direction masks; we measured ~318 k
calls/sec. We can potentially do better in pure Python via caching
per-direction prime-run lengths, but 318 k/s isn't the bottleneck.

### E.2 Zobrist hashing — a natural fit

With 64 cells × 4 cell-states, Zobrist needs 64 × 4 = 256 random
64-bit constants, plus 64 × 2 for worker positions and 1 for side-to-move.
XOR updates are native on Python ints (free arbitrary-precision bigints,
~ns). See §B.3.

### E.3 Parallel neighborhood queries

The existing `_shift_mask_*` functions compute whole-board neighbor
lookups in 4–5 ops. For heuristics that need e.g. "how many primed cells
are cardinal-adjacent to SPACE cells?":

```
primed_expand =  shift_up(P) | shift_down(P) | shift_left(P) | shift_right(P)
prime_frontier = primed_expand & space_mask          # candidate prime sites
popcount(prime_frontier)  # cell-potential proxy
```

All 64 bits processed in parallel — Python int `popcount` via
`bin(x).count('1')` is 0.4 µs, or `int.bit_count()` (Py 3.10+) even
faster.

### E.4 Carpet-run detection

To score "if I prime here, what carpet length will it enable?", we can
compute prime-runs per direction with shift-and chains:

```
runs_along_x_at_least_k = P & shift_left(P) & shift_left(shift_left(P)) & ...
```

This lets a heuristic cheaply count "length-≥-4 prime lines available"
as a scalar potential term.

### E.5 Magic bitboards — unnecessary

Magic bitboards speed up sliding-piece attacks in chess by precomputing
hash tables for occupancy patterns. We don't have sliding pieces, and
the shift-and-mask path is already fast. **Do not bring in magic
bitboards.**

---

## Section F — Chance-node handling for the rat

### F.1 The design choice

We have two distinct ways to integrate the rat into search:

**Option F.1a — Chance nodes in-tree.** Every ply's chance node has
fan-out equal to the support of the rat's belief (≤ 64 cells). Each
chance-child has a posterior belief after the rat's next move. Leaf eval
uses the per-child belief.

- Pros: principled expectiminimax; handles search-move EV exactly.
- Cons: blows up branching (×≤64). Memory for per-child belief grids is
  64 × 64 floats per node = 4 KB/node — big.

**Option F.1b — Belief outside the tree.** Maintain a single belief
that evolves with turn_count, and **evaluate the rat's effect as a
potential term at leaf**:

```
leaf_eval(state) = point_diff(state)
                 + α * cell_potential(state)
                 + β * best_search_EV(state, belief_at(depth))
```

The belief is pushed forward by `T^n` where n is the number of plies
from the root; we can precompute `belief_at[d] = belief @ T @ T ... @ T`
at the start of `play()` for d = 0..MAX_DEPTH and reuse at every leaf.

- Pros: branching stays at ~7. Leaf eval is O(1) lookup into a
  precomputed list.
- Cons: ignores the fact that OUR future moves affect cell types (and
  thus future observations); ignores opponent moves doing the same.
  But within a 6-depth search window the error is small — `T` evolves
  belief more than board-type changes alter the noise model for cells
  we haven't observed yet.

**Option F.1c — Hybrid.** Use F.1b for most of the tree; at nodes where
we consider a SEARCH move (root or near-root), compute the exact
conditional posteriors using the current-depth belief and evaluate
search EV precisely.

### F.2 Recommendation (tentative — for architect to decide)

F.1c (hybrid) is cheap and roughly optimal for this specific game
because:

1. The rat doesn't affect board-type transitions.
2. Sensor observations only happen at our real `play()` call, not at
   imagined future turns. Future noise branches are purely modeled, so
   there's no "correct" outcome to branch on — we're summing over a
   uniform expectation, which is exactly what a potential-based eval
   captures.
3. SEARCH moves are rare (≤ a few per game by EV threshold), so
   root-only exact evaluation is enough.

### F.3 Opponent's belief — a separate track

Tracking the **opponent's** belief about the rat is useful when (a)
predicting their SEARCH moves (for minimax min-nodes) and (b) playing
deception (e.g., priming in areas that drive their belief wrong). Since
they see the same public information we do minus their sensor readings,
we can approximate their belief as ours with added entropy. Kept out of
scope here — see RESEARCH_HMM_RAT.md and possibly a later opponent-
model research doc.

---

## Section G — Sebastian Lague / chess-engine optimizations that apply

From the Sebastian Lague "Coding Adventure: Chess" series + Chess
Programming Wiki + the 2022–2023 "Tiny Chess Bot Challenge" discussions,
the following techniques have good transfer to our game, ranked by
applicability:

| Technique                      | Applies? | Why                                                                                   |
|--------------------------------|----------|---------------------------------------------------------------------------------------|
| Iterative deepening             | ✅ High   | Natural time controller; enables everything below.                                   |
| Transposition table (Zobrist)   | ✅ High   | Direct reuse on 4 masks + 2 worker positions + side-to-move.                         |
| Move ordering (hash-move first) | ✅ High   | Often 2–4× node reduction alone; trivial to add.                                     |
| Killer moves                    | ✅ Med    | Cheap, decent gain; move types/directions form a small killer-key space (24 slots).  |
| History heuristic               | ✅ Med    | Same key space as killers; good supplement.                                          |
| Aspiration windows              | ✅ Med    | Useful once heuristic is tuned; skip early when heuristic noisy.                     |
| Late-move reductions (LMR)      | ✅ Med    | Reduce depth on moves after a certain rank in move-order. Effective at b ≈ 7.         |
| Null-move pruning               | ⚠️ Risky  | Chess relies on "skipping a turn is almost always worse"; not true here (search / defensive plays can legitimately be ~zero-value), and Zugzwang-style situations exist with primed cells that must be rolled before opponent rolls them. Apply only with verification. |
| Quiescence search               | ⚠️ Maybe  | In chess quiescence = captures-only deeper search. Here "quiet" = no carpet-rolls pending. Extending depth when a big carpet-roll is imminent is defensible. |
| Principal-variation search (PVS)| ✅ Med    | NegaScout-style. Compatible with α-β and ID; small code addition.                    |
| Magic bitboards                 | ❌        | Designed for sliding-piece occupancy; we have none.                                  |
| Opening book                    | ✅ Low    | First 2–3 moves have very limited state space (fixed corner patterns, 16 spawn cells). Hand-tuned opening likely worth 0.02 ELO at best. |
| Endgame tablebase               | ✅ Maybe  | Last 4 moves have small state. If time permits, a compact lookup. Marginal.         |

### G.1 The single most important takeaway

From Lague's pacing: **start with minimax, then add α-β, then ID, then
TT, then move ordering — in that order**. Each layer is multiplicative
on ELO and on code complexity, and skipping forward breaks debug
ergonomics.

---

## Section H — Runtime projections

Given the measured ~50 k leaf-evaluations/sec in pure Python with our
throughput and a trivial heuristic, and assuming a **production
heuristic costs ~1.5× a baseline leaf** (belief lookup + popcount-based
potential), we expect ~30 k leaves/sec.

At effective branching factor b with α-β:

- Best case (perfect ordering): nodes ≈ 2 · b^(d/2) − 1
- Typical (good ordering):      nodes ≈ b^(3d/4)
- Worst (random):               nodes ≈ b^d

| depth d | typical nodes (b = 7)    | seconds at 30 k nps | feasible in 6 s? |
|---------|--------------------------|---------------------|------------------|
| 2       | 7^1.5 ≈ 19               | 0.001               | trivially        |
| 4       | 7^3    ≈ 343             | 0.01                | yes              |
| 6       | 7^4.5 ≈ 6.5 k            | 0.22                | yes              |
| 8       | 7^6    ≈ 118 k           | 3.9                 | just barely       |
| 10      | 7^7.5 ≈ 2.1 M            | 70                  | no                |

With numba / cython or aggressive numpy vectorization on the
heuristic, 30 k → 100 k nps is reasonable, pushing feasible depth to
~10.

**If branching climbs to b = 11** (late-game with many carpet rolls)
the same table shifts one depth worse:

- depth 6 in 6 s → borderline
- depth 8 → infeasible

With **aspiration windows + killer/history + TT**, empirical
chess-engine gains suggest another 1.5–2× — effectively one more ply
for free.

**Projected search depth at 6 s/move:**

- Pure α-β + ID: **d = 6–8** ply.
- +TT +move-ordering +killers: **d = 7–9** ply.
- With numba-compiled heuristic: **d = 9–11** ply.

For Carrie (90 %), beating a ≥ 4-ply expectiminimax likely needs **d ≥
6** with comparable-or-better eval. The numbers say this is feasible.

**Rollout budget (for MCTS):**
Per above, a single full-game rollout is 0.6–1.3 ms. 6 s → 5–10 k
rollouts. At b ≈ 7 and UCB exploration, useful subtree coverage past
depth 4–5 is limited unless we have a very strong prior.

---

## Section I — Open choices for Strategy-Architect

Concrete decision points, each with a recommended **default** and the
**evidence that would flip it**.

1. **Backbone algorithm** — minimax α-β + ID + TT **or** MCTS/PUCT.
   - **Default:** α-β + ID + TT.
   - **Flip if:** heuristic development stalls and we have a strong
     policy prior cheaply; or if we find we're consistently time-starved
     (anytime property of MCTS becomes a lifeline); or we build a small
     NN in time.

2. **Chance-node modeling (rat)** — in-tree chance nodes vs.
   belief-as-leaf-potential.
   - **Default:** belief-as-leaf-potential (F.1c hybrid).
   - **Flip if:** we discover opponent moves depend strongly on
     belief-evolution timing or we find SEARCH-heavy strategies are
     competitive.

3. **SEARCH inclusion** — root-only EV comparison vs. in-tree moves.
   - **Default:** root-only, threshold-gated by `max_p > 1/3` plus
     information-gain-bonus tuning.
   - **Flip if:** games reveal we miss opportunities where a SEARCH
     mid-sequence would have opened a win.

4. **Move ordering stack** — what to include.
   - **Default:** [hash-move, killer, history, type-priority, immediate-delta].
   - **Flip if:** profiling shows one of these is expensive relative
     to its cut-rate — drop the cheapest win; or TT hit-rate is low,
     in which case hash-move priority loses effectiveness.

5. **Time allocation** — flat 6s/move vs. adaptive.
   - **Default:** adaptive with 0.6× / 1.0× / 1.6× multipliers + ID +
     0.2 s safety margin. Hard cap per-move at 2.5× base.
   - **Flip if:** early local-test games hit timeouts — switch to flat
     5.5 s with stricter cutoffs.

6. **Numba / Cython / JAX for heuristic** — compile the hot leaf path.
   - **Default:** profile first; compile leaf-eval only if it >40 % of
     wall time and >2× speedup expected.
   - **Flip if:** init-time budget or submission zip-size becomes a
     problem, or we need torch/jax already for NN heuristic.

7. **Opponent model** — assume min-node plays our same heuristic
   vs. a dedicated opponent model.
   - **Default:** assume min-node uses our heuristic (self-play
     assumption). Allows tuning single eval fn.
   - **Flip if:** we beat Albert but lose to George consistently —
     implies George-style greedy beats us and we need a pessimistic
     opponent model or eval-bias tuning.

8. **Depth ceiling** — cap at some d vs. ID-without-ceiling.
   - **Default:** cap at d = 16. Mostly defensive against pathological
     infinite deepening if TT bug causes recursion.
   - **Flip if:** never — keep the ceiling.

9. **ISMCTS / determinized minimax as fallback** — include as a
   backup play-mode?
   - **Default:** No. Added complexity for a weak-coupling problem.
   - **Flip if:** we end up with genuinely partial-info opponent reads
     (e.g., tracking opponent's belief matters), then IS-MCTS over
     opponent-belief space may pay off.

10. **Beam-search pruning** — enforce a top-K at each node to cap
    branching at K regardless of b.
    - **Default:** No top-K; rely on α-β. But implement move-ordering
      well enough that deep nodes effectively become top-K by cutoff.
    - **Flip if:** profiling shows deep-node branching dominates
      wall-time and α-β cuts are ineffective.

---

## References

- CLAUDE.md, assignment.pdf (Appendix A, §9), and engine source at
  `engine/game/board.py`, `engine/game/enums.py`, `engine/game/move.py`.
- Ballard, B. W. (1983). *The *-minimax search procedure for trees
  containing chance nodes.* AIJ 21, 327–350.
- Hauk, Buro, Schaeffer (2006). *Rediscovering *-minimax search.* —
  https://www.researchgate.net/publication/220962560_Rediscovering_-Minimax_Search
- Cowling, Powley, Whitehouse (2012). *Information Set Monte Carlo Tree
  Search.* IEEE TCIAIG. — https://eprints.whiterose.ac.uk/id/eprint/75048/1/CowlingPowleyWhitehouse2012.pdf
- Winands (2009). *ChanceProbCut: Forward Pruning in Chance Nodes.* —
  https://dke.maastrichtuniversity.nl/m.winands/documents/CIG2009.pdf
- Expectiminimax, Wikipedia — https://en.wikipedia.org/wiki/Expectiminimax
- Iterative Deepening — https://www.chessprogramming.org/Iterative_Deepening
- Sebastian Lague, "Coding Adventure: Chess" — https://www.youtube.com/playlist?list=PLFt_AvWsXl0cvHyu32ajwh2qU1i6hl77c
- SebLague Tiny Chess Challenge results — https://github.com/SebLague/Tiny-Chess-Bot-Challenge-Results
- AnmolS99 Chess-AI (community implementation of Lague-style engine) —
  https://github.com/AnmolS99/Chess-AI
- Expectimax on 2048 (real-world tuning of chance-α-β) — https://community.latenode.com/t/optimizing-2048-ai-minimax-and-alpha-beta-pruning-for-expectiminimax-trees/16264

---

## Empirical data appendix

All measurements on Windows 11, Python 3.13, single-threaded, pure
Python, no numba, the engine source as of 2026-04-16.

### Branching factor (`engine/game/board.py::get_valid_moves`)

- 500 random boards per phase; workers in inner 4×4, 2×2 blocked corners.

```
Early (5% primed, 2% carpet), no-search:  mean=6.82  max=9   p90=8
Mid   (18% primed, 12% carpet), no-search: mean=6.33 max=9   p90=8
Mid   (18% primed, 12% carpet), +search:   mean=70.44 max=75 p90=72
Late  (30% primed, 25% carpet), no-search: mean=6.36 max=11  p90=8
```

### Throughput

```
get_valid_moves(exclude_search=True)    : 318,157  ops/sec
get_copy()                               :  65,453  ops/sec
forecast_move(PLAIN, check_ok=False)     :  62,975  ops/sec
full step (gen + forecast + reverse)     :  48,002  ops/sec
```

### Minimax depth (no α-β, no eval)

```
depth=1:  6 nodes     in 0.000 s
depth=2:  44          0.001 s   50 k nps
depth=3:  289         0.006 s   50 k nps
depth=4:  1,913       0.038 s   50 k nps
```

Branching factor confirms ≈ 6.5–7 at the 4-ply horizon (consistent with
the mid-game estimate).
