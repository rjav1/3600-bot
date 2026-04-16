# RESEARCH_HMM_RAT — Bayesian Filtering for the Hidden Rat

**Author:** researcher-hmm
**Date:** 2026-04-16
**Status:** Draft for Strategy-Architect review
**Scope:** The math, the initial prior, EV of a search action, adversarial-signal handling, and a concrete implementation recipe for the HMM rat-belief tracker. No strategic conclusions — those are the Architect's.

---

## 0. Notation and framing

- State space: `S = {0, 1, …, 63}` where index `i = y*8 + x` for cell `(x, y)`. `BOARD_SIZE = 8`.
- Hidden state `r_t ∈ S` is the rat's cell at the start of turn `t` (i.e., immediately before the agent receives sensor data).
- Transition matrix: `T ∈ R^{64×64}`, row-stochastic. `T[i, j] = P(r_{t+1} = j | r_t = i)`. Each row has 3–5 non-zeros (stay + ≤4 cardinal steps, clipped at edges). `T` is constant within a game; a single `T` is passed into `PlayerAgent.__init__` as `transition_matrix`.
- Observation at turn `t`: `o_t = (n_t, d_t)` where `n_t ∈ {SQUEAK, SCRATCH, SQUEAL}` and `d_t ∈ ℤ_{≥0}` is the reported (noisy) Manhattan distance.
- Belief: `b_t(s) = P(r_t = s | o_1, …, o_t, H_t)` where `H_t` bundles all public game state up to turn `t` (opponent searches, move history — these only matter via the floor-type updates on cells).
- Worker cell on turn `t`: `w_t = (x_w, y_w)`. The observation likelihood depends on `w_t` through the Manhattan-distance factor.

---

## Section A — The Bayesian filtering math

### A.1 Forward recursion

Standard HMM forward pass, one step per game turn:

1. **Predict (a.k.a. time update).** The rat takes one silent step according to `T`:
   $$b_{t|t-1}(s') = \sum_{s \in S} b_{t-1}(s) \cdot T[s, s']$$
   In vector form: `b_pred = b_prev @ T`.

2. **Update (a.k.a. observation correction).** Apply the likelihood of the observation:
   $$b_t(s) \propto b_{t|t-1}(s) \cdot L(o_t \mid s, w_t, \text{board}_t)$$
   where `L(o_t | s, w_t, board_t) = P(n_t | cell_type(s)) · P(d_t | |s - w_t|_1)`.

3. **Normalize.** `b_t ← b_t / sum(b_t)`.

That's the full filter. Nothing fancier is needed unless we also want to smooth backward over past turns (we don't — the action budget only cares about `b_t` at the current turn).

### A.2 Observation likelihood factorization

From `engine/game/rat.py`:

- `make_noise(board)` samples `n_t` from `NOISE_PROBS[cell_type(r_t)]`. Uses the **board cell type at the rat's current cell** — NOT the worker's cell.
- `estimate_distance(worker_pos)` samples `d_t = |r_t - w_t|_1 + ε`, with `ε ∈ {−1, 0, +1, +2}` drawn independently from `DISTANCE_ERROR_PROBS = (0.12, 0.7, 0.12, 0.06)`, then clipped to `max(0, ·)`.

The two samples are drawn from independent `random.random()` calls. So given the rat's cell `s` and board/worker:

$$L(o_t \mid s, w_t) = P(n_t \mid \text{cell\_type}(s)) \cdot P(d_t \mid |s - w_t|_1)$$

**Independence is clean.** No cross-term. Verified: `rat.sample()` returns `(self.make_noise(board), self.estimate_distance(worker))` — the two samples don't share any intermediate state.

**Distance likelihood with clipping.** Because `d` is clipped to `≥0`, the observation `d_t = 0` absorbs all offsets that would give `≤ 0`:

$$P(d_t = 0 \mid \text{true\_dist} = k) = \sum_{\epsilon \in \{-1,0,1,2\}} \mathbf{1}[\max(0, k+\epsilon) = 0] \cdot P(\epsilon)$$

Concretely:
- `k = 0`: `ε ∈ {−1, 0}` both give 0 → `P = 0.12 + 0.70 = 0.82`.
- `k = 1`: `ε = −1` gives 0 → `P = 0.12`.
- `k ≥ 2`: impossible → `P = 0`.

For `d_t ≥ 1`: `P(d_t | k) = P(ε = d_t − k)` if `d_t − k ∈ {−1, 0, 1, 2}`, else 0. (The reported `d_t = 0` case is the only one where clipping changes the math.)

### A.3 Log-space derivation

Belief can underflow fast on a 64-cell grid after ~10 turns in linear space (products of <0.2 per step). Work in log-space.

Let `ℓ_t(s) = log b_t(s)` (with `ℓ_t(s) = −∞` for impossible cells). Per turn:

1. **Predict (log-space, log-sum-exp).** For each `s'`:
   $$\ell_{t|t-1}(s') = \log \sum_{s: T[s,s']>0} \exp(\ell_{t-1}(s)) \cdot T[s, s']$$
   Equivalently `= LSE_{s} (ℓ_{t-1}(s) + log T[s, s'])`.

2. **Update.** Additive:
   $$\ell_t(s) = \ell_{t|t-1}(s) + \log P(n_t \mid \text{cell\_type}(s)) + \log P(d_t \mid |s - w_t|_1)$$

3. **Normalize.** Subtract `Z = LSE_s ℓ_t(s)` so that `sum exp(ℓ_t) = 1`.

**Numerical-stability tricks:**

- **LSE.** `LSE(x_1, …, x_n) = M + log sum exp(x_i − M)` where `M = max x_i`. Subtracting the max prevents overflow; the dominant term becomes `exp(0) = 1`.
- **Underflow guards.** Clamp any precomputed `log P` to `−1e9` for zero-probability transitions so that `exp` doesn't return `NaN` through `−inf + something`. When `T[s,s'] = 0`, skip the term entirely via sparse iteration.
- **Renormalization every step.** Even in log-space, subtract `Z` so `ℓ_t(s) ≤ 0` always. This keeps the max at 0 and prevents slow drift of the absolute scale.

**Practical shortcut:** For this game, linear-space filtering with per-step renormalization is numerically fine because **we renormalize every turn** (so `sum b_t = 1`), and individual entries can go as small as `1e-20` without problems in `float64`. Log-space becomes essential only if we skip normalization or do long unnormalized look-aheads. Recommendation: implement linear-space with per-turn renorm + a numerical floor; keep log-space as a fallback if profiling shows drift.

### A.4 Matrix form

All of the above is a 64-vector and a 64×64 matrix operation. Per turn cost:

- Predict: one `b @ T`. `T` is sparse (≤ 5 entries per row), so dense matmul is 64² = 4096 multiplies (~4 μs in numpy), sparse multiply is ~320 multiplies (~1 μs).
- Observation likelihoods are precomputable tables:
  - `log_noise_likelihood[cell_type][n]` — 4×3 table.
  - `log_dist_likelihood[true_dist][reported_dist]` — a small table (true_dist up to 14; reported_dist up to 16).
- Update: 64 elementwise multiplies.
- Normalize: one sum + 64 divisions.

Total: ~1000 arithmetic ops per turn → sub-millisecond in pure numpy.

---

## Section B — The initial prior from the 1000-step headstart

### B.1 Definition

The rat spawns at `(0, 0)` and makes `HEADSTART_MOVES = 1000` moves *silently* (no observations) before turn 1. So:

$$p_0 = e_{(0,0)} \cdot T^{1000}$$

where `e_{(0,0)}` is a length-64 one-hot at index 0. This becomes the **prior for the very first game turn**, before any sensor update.

Two subtleties:

1. The bot in `__init__` also knows `T`. It can precompute `p_0` during the init budget (10–20 s) — this is NOT deducted from the 4-minute game clock.
2. Every time a search *hits* the rat during the game, the engine calls `rat.spawn()` again (rat.py:127–131) — so the post-catch belief resets to `p_0`, **not** to `δ_{(0,0)}`. We return to this in Section D.

### B.2 Is `T^1000` already stationary?

**Yes, effectively.** Numerical experiment with all four shipped matrices and 3 seeds each (±10% multiplicative noise + row-renorm, matching `gameplay.py::_load_transition_matrix`).

Code used (inlined so the Strategy-Architect can re-run):

```python
import pickle, os, numpy as np
BASE = 'engine/transition_matrices'

def load_base(fn):
    with open(os.path.join(BASE, fn), 'rb') as h:
        return np.asarray(pickle.load(h), dtype=np.float64)

def noisy(T, seed):
    rng = np.random.default_rng(seed)
    u = rng.uniform(-0.1, 0.1, size=T.shape)
    Tn = np.maximum(T * (1 + u), 0)
    rs = Tn.sum(axis=1, keepdims=True)
    rs = np.where(rs == 0, 1.0, rs)
    return Tn / rs

for fn in sorted(os.listdir(BASE)):
    T = noisy(load_base(fn), seed=0)
    # Stationary via power iteration (T^2048 rows all match)
    M = T.copy()
    for _ in range(11):
        M = M @ M
    pi = M[0]
    e0 = np.zeros(64); e0[0] = 1.0
    # TV distance of e_0 @ T^k from stationary
    for k in [1, 16, 64, 128, 256, 512, 1000]:
        p = e0 @ np.linalg.matrix_power(T, k)
        tv = 0.5 * np.abs(p - pi).sum()
        print(f'{fn} k={k:4d} TV={tv:.2e}')
```

**Empirical TV distances `|p_k − π|_{TV}` (seed 0, one per matrix):**

| Matrix          | k=16  | k=64  | k=128 | k=256 | k=512 | k=1000 |
|-----------------|-------|-------|-------|-------|-------|--------|
| `bigloop.pkl`   | 0.676 | 0.334 | 0.154 | 3.3e-2 | 1.6e-3 | 4.5e-6 |
| `hloops.pkl`    | 0.604 | 0.165 | 7.0e-2 | 1.2e-2 | 3.7e-4 | 4.8e-7 |
| `quadloops.pkl` | 0.694 | 0.131 | 2.1e-2 | 7.4e-4 | 7.1e-7 | 9.2e-13 |
| `twoloops.pkl`  | 0.602 | 0.161 | 2.8e-2 | 9.5e-4 | 1.1e-6 | 2.9e-12 |

At `k = 1000`, every matrix has `TV(p_k, π) ≤ 5e-6`. For all practical purposes, **`p_0 ≈ π`**, the stationary distribution of `T`. The `(0, 0)` origin has been fully washed out.

### B.3 Spectral-gap view of mixing

Computed second-eigenvalue magnitudes `|λ_2|` of the noised `T`:

| Matrix          | \|λ_2\|  | 1−\|λ_2\| | mixing time `τ_{0.01}` = ln(0.01)/ln(\|λ_2\|) |
|-----------------|--------|----------|-----------------------------------------|
| `bigloop.pkl`   | 0.9881 | 0.0119   | ~385 steps                              |
| `hloops.pkl`    | 0.9865 | 0.0135   | ~338 steps                              |
| `quadloops.pkl` | 0.9729 | 0.0271   | ~168 steps                              |
| `twoloops.pkl`  | 0.9739 | 0.0261   | ~174 steps                              |

`bigloop` is the slowest-mixing; `quadloops` the fastest. Because `1000 ≫ 3 · τ_{0.01}` for every matrix, 1000 steps is a comfortable overkill — roughly 3–6 mixing-time horizons. No matter the seed, the 1000-headstart gives us effectively-stationary prior.

**Implication:** For the `__init__` precompute, **pick whichever `T^k` computation is convenient** — iterating `p ← p @ T` for 1000 steps, or repeated squaring `T^{1024}`, or running power iteration until convergence. All produce `p_0` to float32 precision.

### B.4 Prior shape (ASCII heatmaps, seed 0)

All heatmaps below are over the 8×8 board, (0,0) at top-left, characters shade by probability (`@` heaviest, space lightest). Entropy listed is `H(p_0)` in bits (uniform = 6 bits). Max entry ≈ 0.03 across the board.

**`bigloop.pkl`, seed 0** — max ≈ 0.0284 at (6, 7), `H = 5.84 bits`. Roughly-uniform with a slight corner bias:

```
++##%%%%**##**++
====::==----++##
====::::::..==##
**++::....::==%%
##++......::++%%
##**::..::::++++
##====++++++--==
******++%%%%@@**
```

**`hloops.pkl`, seed 0** — max ≈ 0.0348 at (1, 2), `H = 5.74 bits`. Concentrated on horizontal bands (rows 2–5):

```
......    ......
::------::==----
--@@%%++++**%%++
--%%**====++**++
==##++**==##**--
==%%++====**##--
::::::--------::
      ........
```

**`quadloops.pkl`, seed 0** — max ≈ 0.0265 at (3, 6), `H = 5.89 bits`. Fast-mixing, near-uniform with mild quadrant patterning:

```
--======++++==--
--::..##**----==
--::--****....++
--==##++++++==**
++%%**##**####++
**++==%%%%----++
##::::@@%%==::##
######++**####**
```

**`twoloops.pkl`, seed 0** — max ≈ 0.0337 at (5, 1), `H = 5.71 bits`. Two clear "loops" in the middle region, with corner suppression:

```
  ..::--====..
  ::====++@@++
  --++==##%%**..
..--****++%%**..
--%%%%++++%%--
--##++::++**..
::++##++++==::
..==++==++--..
```

Results for seeds 1 and 2 are similar in shape and entropy for each matrix (differences at the 3rd decimal place on max value; same visual structure). See `p_0_entropy_summary` below.

**`p_0` entropy across seeds (bits):**

| Matrix          | seed 0 | seed 1 | seed 2 |
|-----------------|--------|--------|--------|
| `bigloop.pkl`   | 5.837  | 5.857  | 5.861  |
| `hloops.pkl`    | 5.737  | 5.705  | 5.723  |
| `quadloops.pkl` | 5.888  | 5.891  | 5.891  |
| `twoloops.pkl`  | 5.714  | 5.677  | 5.691  |

### B.5 Takeaways

- **`p_0` is effectively `π` (stationary).** Don't model it as `δ_{(0,0)}` — that would be wildly wrong.
- **Max belief mass on any cell is ≤ 0.038.** From a cold start (no observations, before turn 1), *no* search is +EV — search threshold is `p > 1/3`, but even the best cell in `p_0` sits around 0.03. Early-game searches are pure information-gathering (see §C.2).
- **Each game has a different `π`.** The noised `T` differs per game, so the bot must compute `p_0` in `__init__` from the passed-in `T`; it cannot be precomputed offline and hard-coded.
- **`bigloop` / `hloops` / `twoloops` give more structured `π` than `quadloops`.** If the bot can identify which base matrix it got (e.g., by sampling a few entries and comparing to the four candidates), it could make sharper priors — but the ±10% noise may make this discrimination unreliable. **Open question for the Architect** (§F).

---

## Section C — EV of a search action

Search costs a turn; scoring is `+4` if correct, `−2` if wrong. Let `p = b_t(s)` where `s` is the guessed cell.

### C.1 Point-EV

$$\text{EV}_{\text{points}}(s) = 4p - 2(1 - p) = 6p - 2$$

Break-even: `p = 1/3 ≈ 0.333`. So a search is "point-positive" iff we believe the rat is on `s` with > 1/3 probability. Given that the cold-start prior puts ≤ 0.04 per cell, **no single search is point-positive without observation-driven concentration.**

Optimal cell under this objective alone: `argmax_s b_t(s)`.

### C.2 Value of information (VoI) from a wrong search

A miss is still informative: the posterior **zeroes out** cell `s` and renormalizes everything else. Specifically, if we search `s` and miss:

$$b_t^{\text{post}}(c) \propto b_t(c) \cdot \mathbf{1}[c \neq s] = \begin{cases} 0 & c = s \\ b_t(c) / (1 - b_t(s)) & c \neq s \end{cases}$$

Entropy reduction from a miss:

$$\Delta H = H(b_t) - H(b_t^{\text{miss}}) = H(b_t) - \left[\frac{1}{1 - p} \sum_{c \neq s} -b_t(c) \log b_t(c) - \log(1 - p)\right]$$

which simplifies (using `H(b_t) = -p log p + sum_{c≠s} -b_t(c) log b_t(c)`) to:

$$\Delta H_{\text{miss}} = -p \log p + \log(1 - p) \cdot (1 - p) / (1 - p) + \text{corrections}$$

Cleaner derivation (all logs natural, `b_c = b_t(c)`):

- Before: `H = -sum_c b_c log b_c = -p log p - sum_{c≠s} b_c log b_c`.
- After (miss): `H' = -sum_{c≠s} (b_c / (1-p)) log(b_c / (1-p)) = (1/(1-p)) (-sum_{c≠s} b_c log b_c) + log(1-p)`.
- `∆H = H - H' = -p log p + (1 - 1/(1-p)) · (-sum_{c≠s} b_c log b_c) - log(1-p)`.
- Using `-sum_{c≠s} b_c log b_c = H + p log p`, the second term simplifies. Final:

$$\Delta H_{\text{miss}} = H \cdot \frac{-p}{1-p} + \log(1-p) \cdot (-1) - p \log p / (1-p) \cdot \text{[recheck]}$$

Easier to just evaluate numerically per candidate `s` in code:

```python
def miss_entropy(b, s):
    p = b[s]
    if p >= 1.0:  # certain hit — miss is impossible
        return 0.0
    post = b.copy()
    post[s] = 0.0
    post /= (1.0 - p)
    return -np.sum(np.where(post > 0, post * np.log2(post), 0.0))
```

**Expected posterior entropy** (weighted over hit/miss outcomes):

$$E[H^{\text{post}} \mid \text{search}(s)] = p \cdot H(p_0) + (1 - p) \cdot H(b_t^{\text{miss}})$$

where `H(p_0)` is the entropy of the post-catch respawn prior (§D.2), because on a hit the belief resets.

VoI in pure bit-entropy terms:

$$\text{VoI}(s) = H(b_t) - E[H^{\text{post}} \mid \text{search}(s)]$$

### C.3 Competing objectives for the search cell

Three candidate rules for "which cell to search":

1. **Max-belief** (`argmax_s b_t(s)`) — pure point-EV, ignoring information gain.
2. **Min expected posterior entropy** (`argmin_s E[H^{post} | search(s)]`) — pure information objective, ignoring points.
3. **Weighted EV** (`argmax_s 6p - 2 + λ · VoI(s)`) — combines both with some `λ` that prices a bit of entropy in points. A reasonable prior: `λ ≈ 1` (one bit is roughly worth one search's-worth of point-shaping), but the Architect should tune this empirically.

**Tradeoff summary** (the Architect owns the choice):

- In **early-game** when belief is near-uniform (`H ≈ 5.7 bits`), max-belief ties many cells and the search is deeply −EV in points. Info-based objectives pick cells that partition belief well (high-mass cells are still best because a miss removes more mass than a low-mass miss).
- In **late-game** when belief has collapsed (`H < 2 bits` and some cell has `p > 0.3`), max-belief and min-entropy converge on the same cell.
- **Min-max regret** is a distinct conservative objective: pick `s` to minimize the worst-case (over the true rat position) loss. In our scoring it collapses to "never search" because the worst case is always −2 points. Not useful here.

**Note on multi-step VoI.** A single search's info reward is entropy reduction; but the *actual* downstream benefit is "will subsequent searches become +EV thanks to this one?" That requires a 2-ply (search-then-later-search) lookahead, which should be handled inside the expectiminimax search tree rather than in a closed-form VoI. The closed-form VoI is a **cheap proxy** to drop into the tree's leaf heuristic — not a replacement for the tree.

### C.4 Search-EV special cases

- **Opponent-caught-the-rat**: your `b_t` just got reset to `p_0` (entropy ≈ 5.7–5.9 bits). Don't search this turn unless you find a `p > 1/3` cell in `p_0` (you won't).
- **High-mass hotspot from a very informative observation (e.g., SQUEAL + tight distance)**: this is when search becomes +EV. Usually possible only 5–10 turns into a stable chase.
- **Endgame (last 2 turns)**: the VoI of a wrong search is near-zero because you won't get to use the information. Objective reduces to pure point-EV.

---

## Section D — Incorporating adversarial signals

The opponent's last search is public: `board.opponent_search = (loc, result)`. Both the positive and negative cases carry information.

### D.1 Order of operations (verified from `engine/gameplay.py`)

The main loop (gameplay.py:372–460) per turn:

1. `rat.move()` — rat takes one silent step (line 386).
2. `samples = rat.sample(board)` — the current player's sensor reading (line 387).
3. Current player's `play()` runs (possibly a search).
4. If search hit: `rat.spawn()` — rat respawns at (0,0) and takes 1000 silent steps (line 439).
5. `board.reverse_perspective()` (line 457), and `board.opponent_search` is updated to the most-recent search info (lines 459–460).

So, from **our** perspective, between "our last turn's belief" and "our current turn's observation":

- Opponent got `samples` (their rat moved once, then they observed).
- Opponent played their move (possibly searched; result is now in `board.opponent_search`).
- If opponent hit, rat respawned.
- Rat moved once more (the `rat.move()` at the top of **our** turn).
- We observe `sensor_data`.

### D.2 Miss update

If `board.opponent_search = (s_opp, False)` (opponent searched `s_opp` and missed), we learn:

> At the moment the opponent searched (i.e., after their turn's `rat.move()` but before the next one), the rat was NOT at `s_opp`.

Let `b^{opp}_{pre\_move}` = our belief right before the rat move that started the opponent's turn. Steps:

1. Predict: `b^{opp}_{post\_move} = b^{opp}_{pre\_move} @ T` (rat moved at start of opp's turn).
2. Opponent observes (we don't see their sensor reading, so no update from it).
3. Opponent searches `s_opp`; misses. Condition `b^{opp}_{post\_move}` on rat ≠ `s_opp`:
   $$b'(c) = \frac{b^{opp}_{post\_move}(c) \cdot \mathbf{1}[c \neq s_{opp}]}{1 - b^{opp}_{post\_move}(s_{opp})}$$
4. Now the rat moves again (start of **our** turn): `b^{our}_{pre\_obs} = b' @ T`.
5. We observe our `sensor_data` and do the update.

**Practical simplification.** Since we're updating for the first time on *our* turn, we can keep a single running `b`. When our `play()` runs:

1. Step-predict: `b ← b @ T` (this folds the opp-turn rat move, because we never updated `b` during opp's turn).
2. Read `board.opponent_search`. If `(s_opp, False)`: zero out `b[s_opp]` and renormalize.
3. Step-predict again: `b ← b @ T` (this is the "our turn" rat move).
4. Apply our sensor likelihood.
5. Normalize.

**Wait — is (1) correct?** Our `b` at end of our last turn already absorbed *our* sensor reading. Since the opponent's turn includes one rat move, we must predict once to catch up. Then the opp-search-miss is observation data for the **post-move** distribution, so it goes on top of the first predict. Then another predict for our-turn's rat move. Then our observation.

**Two-predict-one-miss-one-obs** is the right pattern.

**Edge case**: `board.opponent_search = (None, False)` means the opponent did NOT search last turn. No miss update to apply; just predict once (to account for opp-turn rat move) → predict again (our-turn rat move) → our observation.

### D.3 Hit update (opponent caught the rat)

If `board.opponent_search = (s_opp, True)`, the rat was caught and **respawned**. From rat.py:127–131, `spawn()` sets position to (0,0) and takes `HEADSTART_MOVES = 1000` silent steps. The engine performs this **between** the opponent's turn and the next `rat.move()` at the start of our turn.

So after a hit:

1. The belief we carried from last turn is **obsolete**. Reset to `p_0`.
2. Then the `rat.move()` at start of our turn happens: `b ← p_0 @ T`.

   - *Caveat:* If `p_0` was already near-stationary (§B), `p_0 @ T ≈ p_0`, so this extra predict is ~a no-op. But do it for correctness.

3. Then our sensor reading updates `b`.

**Critical implementation note.** The post-hit belief is `p_0`, **NOT** `δ_{(0,0)}`. A naive implementation that resets to a point mass at (0,0) will be catastrophically wrong after the first 100-ish post-hit turns of silence. This is a common pitfall flagged in `CLAUDE.md` §7 ("Rat's prior distribution") and worth reiterating.

**Caching.** Precompute `p_0` once in `__init__` and store it; reuse on every catch. Cost: zero runtime after init.

### D.4 Information leakage from opponent *not* searching

If the opponent doesn't search, that is also (weakly) informative: it suggests their belief doesn't have any cell with `p > 1/3`. But we don't know the opponent's belief, so this is a higher-order inference (opponent modeling). **Out of scope for the base HMM; reserved for possible Architect-level enhancement.**

### D.5 Our own searches (symmetric)

Our search result `(s_us, result)` is available on `board.player_search` after we search (visible on our *next* turn). But we already know the result at the time we apply the update — we can update `b` immediately upon seeing a miss within the same turn:

- Miss: zero out `b[s_us]`, renormalize.
- Hit: reset `b` to `p_0`.

In our forward pass, our own search is handled as part of the current turn's update, not the next turn.

### D.6 Floor-type changes during opponent's turn

The opponent's move can change the board: prime-step creates a PRIMED cell, carpet-roll converts PRIMED → CARPET. These change `cell_type(·)` and therefore the **noise-likelihood table** for future observations.

**Implementation:** Re-read `cell_type(s)` for each `s ∈ S` at the start of every update (it's O(64)). Do NOT cache a noise-likelihood-per-cell table across turns — it becomes stale as soon as either player primes or rolls. The noise update uses whatever `cell_type` currently evaluates to in `board`.

---

## Section E — Practical implementation recipe

### E.1 Data structure

- **Primary representation:** `numpy.ndarray(shape=(64,), dtype=np.float64)`. Flat, matches `T`'s indexing (`index = y*8 + x`). Access via `b[idx]`, reshape to `(8, 8)` for spatial queries.
- **Why float64, not float32:** Belief entries can drop to `~1e-15` without issue; float32 has only ~7 decimals of mantissa, so a sharp observation can round a valid cell to 0. The 64-dim dot product is so cheap that there's no runtime reason to prefer float32. Use float64.
- **Why not log-space:** Only worthwhile if per-step normalization is skipped or there's unnormalized lookahead. With per-turn normalize, linear-space is simpler and numerically safe.

### E.2 Precomputed tables (`__init__`)

```python
import numpy as np
from engine.game.rat import NOISE_PROBS, DISTANCE_ERROR_PROBS, DISTANCE_ERROR_OFFSETS
from engine.game.enums import Cell, Noise, BOARD_SIZE

class RatBelief:
    def __init__(self, T, board):
        self.T = np.asarray(T, dtype=np.float64)        # (64, 64)

        # Initial prior: p_0 = e_{(0,0)} @ T^1000
        p = np.zeros(64); p[0] = 1.0
        for _ in range(1000):
            p = p @ self.T
        p /= p.sum()   # paranoid renorm against fp drift
        self.p_0 = p
        self.b = p.copy()

        # Noise likelihood: (Cell, Noise) -> P
        self.noise_lh = np.zeros((4, 3))
        for cell_type, probs in NOISE_PROBS.items():
            self.noise_lh[int(cell_type)] = probs

        # Distance likelihood table: (true_dist, reported_dist) -> P
        # true_dist in [0, 14], reported_dist in [0, 16]
        self.dist_lh = np.zeros((15, 17))
        for td in range(15):
            for offset, p in zip(DISTANCE_ERROR_OFFSETS, DISTANCE_ERROR_PROBS):
                rd = max(0, td + offset)
                self.dist_lh[td, rd] += p   # clipping may combine entries at rd=0

        # Precompute Manhattan distance from each worker cell to each rat cell
        # worker-indexed on the fly (cheap: 64 ops per turn), but a full
        # 64x64 table is trivially cheap at init:
        coords = np.array([(i % 8, i // 8) for i in range(64)])
        self.manhattan = np.abs(coords[:, None, 0] - coords[None, :, 0]) + \
                         np.abs(coords[:, None, 1] - coords[None, :, 1])
        # shape: (64, 64), manhattan[i, j] = |cell_i - cell_j|_1
```

### E.3 Per-turn update

```python
def update(self, board, sensor_data, worker_idx, opp_search):
    """
    sensor_data: (Noise, int reported_distance)
    worker_idx: our worker's cell index
    opp_search: (loc_or_None, hit_bool)  — from board.opponent_search
    """
    n_t, d_t = sensor_data

    # 1. Catch up with opponent turn's rat move
    self.b = self.b @ self.T

    # 2. Apply opponent-search update
    opp_loc, opp_hit = opp_search
    if opp_loc is not None:
        opp_idx = opp_loc[1] * 8 + opp_loc[0]
        if opp_hit:
            self.b = self.p_0.copy()
        else:
            self.b[opp_idx] = 0.0
            s = self.b.sum()
            if s > 0:
                self.b /= s
            else:
                # Degenerate: everything we believed was ruled out.
                # Fall back to p_0. Should never happen if math is right.
                self.b = self.p_0.copy()

    # 3. Our turn's rat move
    self.b = self.b @ self.T

    # 4. Observation update
    # 4a. Noise likelihood per cell
    cell_types = np.array(
        [int(board.get_cell((i % 8, i // 8))) for i in range(64)]
    )
    noise_factor = self.noise_lh[cell_types, int(n_t)]     # (64,)

    # 4b. Distance likelihood per cell
    # true_dist from our worker to each cell
    worker_td = self.manhattan[worker_idx]                 # (64,)
    rd = min(d_t, self.dist_lh.shape[1] - 1)
    # Clamp worker_td too
    td_clamped = np.minimum(worker_td, self.dist_lh.shape[0] - 1)
    dist_factor = self.dist_lh[td_clamped, rd]             # (64,)

    self.b = self.b * noise_factor * dist_factor
    z = self.b.sum()
    if z > 0:
        self.b /= z
    else:
        # Observation incompatible with belief — reset to p_0 and reapply obs.
        # Happens only if model is misspecified (e.g., board state out of sync).
        self.b = self.p_0 * noise_factor * dist_factor
        self.b /= self.b.sum()
```

**Note on our own search within the same turn.** Our search (`MoveType.SEARCH`) does not change our worker position or board, but it does reveal hit/miss information immediately. Handle it outside the `update()` call in the agent, after move selection:

```python
# After deciding on a search move and getting its result:
if move.move_type == MoveType.SEARCH:
    s_idx = move.search_loc[1] * 8 + move.search_loc[0]
    if hit:
        self.b = self.p_0.copy()
    else:
        self.b[s_idx] = 0.0
        self.b /= self.b.sum()
```

Actually the engine doesn't return hit/miss to the agent within `play()`; we learn our own result on our next turn via `board.player_search`. So in practice, our-own-search updates happen at the start of our next turn, mirroring the opponent-search path. Treat `board.player_search` identically to `board.opponent_search` in the update pipeline, just with the understanding that it's our previous search (2 turns ago in the opp-turn-then-our-turn sense).

### E.4 Runtime cost per turn (back-of-envelope)

- Two predicts: 2 × 64² = 8192 multiplies → ~8 μs in numpy.
- Observation update: 3 × 64 = 192 elementwise ops → ~1 μs.
- `board.get_cell` × 64: **dominant cost** — ~10 μs in Python if `get_cell` is a pure-Python function. If profiling reveals this to be a bottleneck, cache a bitmask-decode once per turn:
  ```python
  # Vectorize using board's bitmasks (constant-time per mask)
  blocked = np.frombuffer(board._blocked_mask.to_bytes(8, 'big'), dtype=np.uint8)
  # ... similar for primed/carpet ...
  # → cell_types array in ~1 μs
  ```
- Total: **well under 1 ms per turn** in numpy-heavy path. Adds < 40 ms across a full 40-turn game. Satisfies the `<1ms` target by ~50× margin.

If we need JAX (for GPU pipelining into the search tree), the same ops map to jnp trivially. No runtime concern.

### E.5 Initialization cost

- `p_0 = e_0 @ T^1000` via iterative multiply: 1000 × 64² = 4M multiplies. Numpy: ~3 ms.
- Via repeated squaring to `T^{1024}` then left-multiply by `e_0`: 10 × 64³ = 2.6M multiplies. Similar cost.
- Total `__init__` HMM work: **< 10 ms**, well inside the 10–20 s init budget.

### E.6 SEARCH in a lookahead tree — `apply_move` side effects are manual

**Critical integration note** (flagged by game-analyst in `docs/GAME_SPEC.md` §10, cross-referenced in `docs/STATE.md`'s GAME_SPEC takeaways). `engine/game/board.py::apply_move` treats `MoveType.SEARCH` as a **bare `pass`** (board.py:256–258). It neither adjusts points nor resets the rat. The `+RAT_BONUS = +4` / `−RAT_PENALTY = −2` delta and the `rat.spawn()` respawn happen in the game loop at `engine/gameplay.py:434–445`, **after** `apply_move` returns.

Consequence for any expectiminimax / lookahead tree that calls `board.forecast_move(SEARCH)` (which deep-copies then `apply_move`s): the forecasted board has **stale points and the external belief tracker is untouched**. You must apply both side effects by hand at the SEARCH node.

For our HMM tracker this means: a SEARCH node in the tree is a **chance node** with two branches, weighted by the current belief `p = b[s_search]`:

1. **Hit branch, probability `p`:**
   - Our-side: `worker.points += 4`; `tracker.b ← p_0.copy()`.
   - Opponent-side: their worker gets `+4`, but our tracker **still resets to `p_0`** because the rat respawn applies symmetrically to both players' beliefs.
2. **Miss branch, probability `1 − p`:**
   - Acting player's `worker.points −= 2`.
   - Belief update: `tracker.b[s_search] = 0`, renormalize. (No rat move is consumed by SEARCH itself — the rat's one-step move is already applied at the top of each player's turn, before their `play()` runs.)

To keep the tree cheap, the `RatBelief` class should expose lightweight snapshot/restore helpers so that each tree node doesn't copy the full 64-float belief on every expansion:

```python
def snapshot(self) -> np.ndarray:   return self.b.copy()
def restore(self, snap):            self.b = snap

def apply_our_search(self, s_idx, hit: bool):
    if hit:
        self.b = self.p_0.copy()
    else:
        self.b[s_idx] = 0.0
        self.b /= self.b.sum()

def apply_opp_search(self, s_idx, hit: bool):   # symmetric
    if hit:
        self.b = self.p_0.copy()
    else:
        self.b[s_idx] = 0.0
        self.b /= self.b.sum()
```

Caller pattern inside expectiminimax:

```python
snap = tracker.snapshot()
# Hit branch
tracker.apply_our_search(s, hit=True)
value_hit = 4 + evaluate_subtree(...)
tracker.restore(snap)
# Miss branch
tracker.apply_our_search(s, hit=False)
value_miss = -2 + evaluate_subtree(...)
tracker.restore(snap)
# Chance-node combine
return p * value_hit + (1 - p) * value_miss
```

The 64-float copy is ~0.5 μs; not a bottleneck even with thousands of tree nodes.

### E.7 Sanity checks / invariants

After every update:

- `abs(self.b.sum() - 1.0) < 1e-9`.
- `self.b.min() >= 0`.
- `self.b[i] == 0` for any `i` we just ruled out (search miss, opp miss).
- `H(self.b) ≤ log2(64) = 6 bits`, with equality iff uniform.

Cheap assertions at dev-time; strip them (or wrap in `if __debug__`) at submission time — asserts should not cost runtime in the tournament.

---

## Section F — Open questions for the Strategy-Architect

The researcher is NOT making these decisions. Each is a fork the Architect should resolve with evidence (ablation, local scrimmages, or judgment call).

1. **Float precision.** Recommend `float64` for safety. If heuristic-evaluation calls for `float32`/JAX for other reasons and a single unified dtype simplifies the pipeline, `float32` is probably fine with per-turn renorm. **Architect picks.**

2. **Log-space vs linear-space.** Recommend linear with per-turn renorm. Log-space only if profiling shows numeric drift (it shouldn't).

3. **Search-cell objective.** Three competing options laid out in §C.3:
   - (a) Max-belief (pure point-EV).
   - (b) Min expected posterior entropy (pure info).
   - (c) Weighted `6p − 2 + λ · VoI(s)`.

   The Architect should decide whether to compute search utilities inside the expectiminimax leaf (option c, with `λ` tuned on self-play) or as a fixed-rule outer heuristic (option a or b). A common compromise: option (a) when `p > 1/3` is on the table; fall back to option (b) otherwise.

4. **When to search aggressively early vs late.** Two philosophies:
   - *Aggressive-early:* front-load info-gathering searches so belief is sharp by mid-game, enabling point-positive catches in turns 20–40.
   - *Lazy-late:* only search when a single observation produces a >1/3 hotspot, save the action-turns for priming/rolling.

   Both are defensible. A quick ablation in local scrimmage should settle it. Researcher does not pick.

5. **Matrix identification from samples.** Four base matrices, ±10% noise. Could the bot, from `T`'s entries, identify which base it is and use that for a pre-computed finer structure (e.g., high-resolution stationary distribution from offline analysis)? Probably not useful — `T^1000 = π` to 1e-6 regardless of which base, and we have 10 ms of init budget to compute `π` directly. Skip unless profiling says otherwise.

6. **Belief-grid granularity.** 64-cell dense grid is tiny. No need for subsampling, tiling, or particle filtering. If the grid were 20×20 we'd consider particle methods; at 8×8 it's trivially exact.

7. **Belief-grid fusion with search-move reasoning.** Does the expectiminimax search tree need the *full* 64-dim belief at every node, or just summary stats (top-k cells, entropy, max-mass)? The Architect should define the HMM → search interface, not the researcher. **Open.**

8. **Opponent modeling.** We do not currently infer *their* belief about the rat. Tracking it would require a bet on their strategy (naive HMM? prior-only? something weirder). Possibly a Phase 5 enhancement.

---

## Appendix — quick-reference constants

From `engine/game/rat.py` and `engine/game/enums.py`:

- `HEADSTART_MOVES = 1000`
- `NOISE_PROBS[Cell][Noise]`:
  - BLOCKED: (0.5 SQUEAK, 0.3 SCRATCH, 0.2 SQUEAL)
  - SPACE:   (0.7, 0.15, 0.15)
  - PRIMED:  (0.1, 0.8,  0.1)
  - CARPET:  (0.1, 0.1,  0.8)
- `DISTANCE_ERROR_PROBS = (0.12, 0.70, 0.12, 0.06)` for offsets `(-1, 0, +1, +2)`, clipped to `≥ 0`.
- `RAT_BONUS = 4`, `RAT_PENALTY = 2`. Break-even `p = 1/3`.
- `BOARD_SIZE = 8`, `MAX_TURNS_PER_PLAYER = 40`.

From `engine/gameplay.py::_load_transition_matrix`:

- Per-game `T = base * (1 + U)` element-wise, `U ~ Uniform(-0.1, 0.1)`, clamped to `≥ 0`, row-renormalized. `base` is picked uniformly from `{bigloop, hloops, quadloops, twoloops}.pkl`.

End.
