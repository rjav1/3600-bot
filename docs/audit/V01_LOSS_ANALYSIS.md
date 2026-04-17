# V01_LOSS_ANALYSIS — Where RattleBot v0.1 leaves points on the floor

**Owner:** loss-analyst
**Date:** 2026-04-17
**Source data:** 13 unique RattleBot v0.1 match JSONs under `3600-agents/matches/` (11 solo-runner vs Yolanda matches + 1 paired batch vs FloorBot = pair_0000 two-match). Baseline runs `BASELINE_V01_RUN1/2` are *not yet written* — their `matches/` directories are empty. This document analyzes what we have and prepares the pipeline to run unchanged once those land.
**Pipeline script:** `tools/scratch/v01_loss_analysis.py` (re-run to regenerate `3600-agents/matches/analysis/v01_loss_summary.json` + `v01_narratives.txt`).

---

## 1. Executive summary

- Reviewed **13** RattleBot-involved matches: **11 wins, 1 tie, 1 catastrophic loss**.
- The single loss (`RattleBot_Yolanda_1.json`) is **not a heuristic misplay — it is a degenerate bug** where RattleBot searched on every one of its 40 turns from the spawn cell, scoring −68 pts. This one match contains 40 of the 43 RattleBot SEARCH moves in the entire corpus.
- Among the 12 non-catastrophic matches the dominant mistake category is **low-quality CARPET rolls**: RattleBot picks rolls of length 1 (worth **−1 pt**) at a shocking 42 % frequency (32 of 76 rolls), with another 29 % at k=2 (just +2). **Only 5 rolls across the whole corpus reached k≥4**, and the entire corpus produced exactly **one** roll of k=5 and **zero** rolls of k=6 or k=7.
- Secondary issues: long **plain-step streaks** (up to 16 consecutive plains in one match) indicate the heuristic loses search direction and wanders; **zero searches** in 11 of 13 matches indicates the SEARCH gate is *also* broken in the opposite direction (it fires only in near-degenerate states).
- RattleBot currently scores by **priming** (+189 banked points across all matches) and offsets a **net −32 pt** self-inflicted carpet loss from over-rolling k=1. Were RattleBot to stop rolling k=1 and convert even half of its k=2 rolls to k=3, per-match score would jump ≈ +4–6 pts.

**Dominant mistake:** `roll_len_1_penalty` — 32 instances across the 12 non-bug matches, avg 2.7 per match, directly costing an average 2.7 pts/match. Highest-ROI fix: forbid k=1 rolls unless no other CARPET of k≥2 exists AND no PRIME/PLAIN alternative scores better than −1.

**Runner-up:** `search_gate_saturation` — responsible for the only −68 loss; a single regression of this kind turns a comfortable winning agent into a guaranteed loser. Must be clamped before any v0.2 release.

---

## 2. Methodology

### 2.1 Data ingestion
`tools/scratch/v01_loss_analysis.py` walks `3600-agents/matches/` recursively, de-duplicates by basename (top-level and nested mirrors the same files), and parses each JSON using the schema in `engine/game/history.py` + `engine/board_utils.py::get_history_dict`:

- `pos[]` is flat A,B,A,B,… the position *after* each ply.
- `left_behind[]` gives the move type per ply: `plain | prime | carpet | search`.
- `a_points[]` / `b_points[]` cumulative after each ply.
- `rat_caught[]` boolean per ply.
- `trapdoors[]` rat positions per ply (rat has already moved).
- `spawn_a` / `spawn_b` starting cells.

The full `Move` object (direction, roll_length, search_loc) is **not** logged. We infer:
- CARPET roll_length = `|Δx| + |Δy|` between the acting player's previous position and new position (valid because the roll is always a straight line).
- PRIME / PLAIN direction = the per-ply position delta.
- SEARCH target = **unknown**; we only see hit/miss via `rat_caught[i]`.

### 2.2 Match categorization
Paired-runner files wrap history inside `{agent_a, agent_b, history, …}`; `run_local_agents.py` outputs the raw history. Both shapes are handled.

RattleBot's side is inferred from `agent_a`/`agent_b`. Win/loss is derived from the `winner` string (`PLAYER_A` / `PLAYER_B` / `TIE`).

We focus on losses + narrow wins (`margin < 5`). In this corpus that gives **1 loss + 1 tie = 2 matches**, but because the corpus is small we also characterize the 11 decisive wins for mistake prevalence (they expose missed-upside mistakes that don't flip the result but leave points on the table).

### 2.3 Divergence-point analysis
For the loss match, we walked ply-by-ply and identified the turn where RattleBot's expected value diverged permanently. For narrow wins / ties we identified the per-ply move that gave the opponent their biggest swing.

### 2.4 Taxonomy buckets (counts below)

| Category | Heuristic definition |
|---|---|
| `search_gate_saturation` | SEARCH chosen on ≥10 consecutive RattleBot plies. |
| `roll_len_1_penalty` | CARPET with inferred k=1 (worth −1 pt). |
| `k_geq_4_starvation` | Whole-match count of rolls with k≥4. Target: ≥2. |
| `short_roll_with_pending` | CARPET k=2 while ≥2 other primed cells are still pending on the board. |
| `tempo_plain_streak` | ≥5 consecutive plain steps by RattleBot with no priming / rolling / searching. |
| `stationary_stall` | RattleBot remains on same cell for ≥10 consecutive plies. |

### 2.5 Pipeline re-run instructions
```bash
cd C:/Users/rahil/downloads/3600-bot
py tools/scratch/v01_loss_analysis.py
```
Outputs land in `3600-agents/matches/analysis/v01_loss_summary.json` (aggregated stats) and `v01_narratives.txt` (per-match ply-by-ply trace with tagged mistakes). Both paths are gitignored.

---

## 3. Taxonomy of mistakes

### 3.1 Match-level incidence table

| Match | Result | margin | plain-streak max | k=1 rolls | k≥4 rolls | searches |
|---|---|---:|---:|---:|---:|---:|
| RattleBot_Yolanda_0 | TIE | 0 | 4 | 9 | 0 | 0 |
| **RattleBot_Yolanda_1** | **LOSS** | **−71** | 0 | 0 | 0 | **40** |
| RattleBot_Yolanda_2 | W | +27 | 3 | 3 | 1 | 0 |
| RattleBot_Yolanda_3 | W | +32 | 4 | 1 | 1 | 0 |
| RattleBot_Yolanda_4 | W | +25 | **7** | 1 | 0 | 0 |
| RattleBot_Yolanda_5 | W | +18 | **10** | 2 | 1 | 0 |
| RattleBot_Yolanda_6 | W | +11 | 4 | 4 | 0 | 1 |
| RattleBot_Yolanda_7 | W | +13 | **11** | 2 | 0 | 2 |
| RattleBot_Yolanda_8 | W | +30 | 5 | 3 | 1 | 0 |
| RattleBot_Yolanda_9 | W | +10 | **16** | 2 | 0 | 0 |
| RattleBot_Yolanda_10 | W | +23 | 5 | 3 | 0 | 0 |
| pair_0000_m1 vs FloorBot | W | +20 | 4 | 1 | 0 | 0 |
| pair_0000_m2 vs FloorBot | W | +30 | 3 | 1 | 1 | 0 |

### 3.2 Aggregate category counts (13 unique RattleBot matches, 520 RattleBot plies)

| Category | Count | Rate | Representative match IDs | Description |
|---|---:|---:|---|---|
| `roll_len_1_penalty` | **32** | 42 % of all rolls | RattleBot_Yolanda_0 (9×), _6 (4×), _2/_8/_10 (3×), _5/_7/_9 (2×), _3/_4/pair (1×) | RattleBot routinely rolls k=1 (−1 pt) even when primes for longer lines exist. In 30/32 instances (94 %) ≥1 primed cell remained on the board at roll time — i.e. there was potential to prime further and roll k≥2 instead of burning a single-cell roll. |
| `k_geq_4_starvation` | 12 (matches with 0 rolls of k≥4) / 13 | 85 % | _0, _1, _4, _6, _7, _9, _10, pair_m1 | The point table rewards long rolls aggressively (k=5 is 10 pts, k=6 is 15, k=7 is 21). RattleBot achieved k=5 only once across the whole corpus (in pair_0000_m2) and never got to k=6 or k=7. Even George-class play should see k≥5 multiple times per game. |
| `search_gate_saturation` | 1 match (40 consecutive searches) | 7.7 % | **_1 (the −68 loss)** | RattleBot stood on its spawn cell `(2,3)` and SEARCHed 40 times in a row. Only 2 of 40 searches hit (+8 pts); the other 38 cost −76 pts. Worker never primed, never rolled, never moved. Root cause is almost certainly the `belief.max_mass > 1/3` SEARCH gate in `agent.py:174` firing every turn from a degenerate belief (probably an initial concentration that the opp's moves never disperse because the opp never primes near the peak). |
| `tempo_plain_streak` (≥5 consecutive) | 5 instances in 4 matches | 4/13 matches | _4 (7), _5 (10), _7 (11), _9 (16) | In 4 matches RattleBot entered a plain-step loop of 7+ plies. Match _9 took 16 consecutive plain steps (40 % of the entire game) with no scoring play. Match _5 and _7 similar. This happens when the heuristic finds no move with positive F3/F4/F5 but also doesn't see a profitable PRIME target — the leaf evaluator picks `plain` as a tiebreak. |
| `short_roll_with_pending` | 1 clean instance (many more inferred) | — | pair_0000_m1 | CARPET k=2 while ≥2 other primed cells pending. Our detector is conservative; the real number is likely 5–10 across the corpus. |
| `stationary_stall` | 1 (the bug match) | — | _1 | Spawn-cell parking for 40 plies. |
| `search_whiff` (miss) | 40 in _1, 3 in rest | — | _1, _6, _7 | SEARCH miss rate: 40/43 = 93 %. **Search EV in corpus: −68 pts.** |

### 3.3 Move-type mix across the corpus

- **520 RattleBot plies** total (13 × 40).
- plain **212 (40.8 %)** — high for an agent that should be scoring.
- prime **189 (36.3 %)** — primary point source (+189 pts banked).
- carpet **76 (14.6 %)** — *net* **+114 pts** earned from all rolls (degraded by 32× k=1 rolls costing −32).
- search **43 (8.3 %)** — **net −68 pts** (3 hits × 4 − 40 misses × 2). If we exclude the _1 bug match: 3 searches, 1 hit, net ≈ 0.

Priming is carrying the offense. Rolls should be the lever but the 42 % k=1 rate converts the roll engine into a slight negative.

### 3.4 Deep dive: the catastrophic loss (RattleBot_Yolanda_1)

- Spawn: A=(2,3), B=(5,3). T-pick + spawn-rng produce an initial belief peak near the center of the board.
- Plies 0–79: RattleBot position is constantly `(2,3)`. It never stepped.
- Move types: 40 × SEARCH. Hits on plies 14 and 58.
- Points curve: linear slope of **−2 per own ply** with +8 jumps at rat-capture plies.
- Final score: **A = −68, B = 3** (Yolanda herself is a random mover and barely scores).

This exposes the `belief.max_mass > 1/3` gate in `agent.py:174`. Three plausible failure modes (we cannot distinguish without a belief replay):
1. After the first 2 RattleBot searches miss, the belief should decay the argmax cell to ~0, yet it apparently stays > 1/3. Likely cause: a bug in `apply_our_search` where the miss update doesn't zero-and-renormalize correctly, or it re-inflates after the next `predict(T)`.
2. The belief **sensor update** might be over-concentrating — if sensor + distance likelihood keep pointing back to the same cell, `max_mass` ratchets up each turn.
3. The **post-capture reset** (`p_0`) after plies 14 and 58 resets to `δ_(0,0) @ T^1000`, whose stationary distribution happens to put > 1/3 mass on one cell for this particular T matrix (possible with `bigloop.pkl` / `hloops.pkl`-style low-mixing matrices). A "stationary" T whose stationary distribution has a peak > 1/3 is plausible and would trigger the gate every turn.

**Root fix sketch** (independent of which mode is actually the bug): the SEARCH gate should also require (a) the argmax cell has not been searched on ≥2 of the last 3 own plies AND (b) `max_mass` has *moved* between turns (not just been consistently > 1/3). A sticky / saturating argmax should *not* keep firing — either the belief needs repair, or the agent needs to pivot to non-SEARCH play.

### 3.5 Deep dive: the tie (RattleBot_Yolanda_0)

40-ply trace shows:
- Plies 2 and 3: **back-to-back k=1 rolls** from a two-cell prime line. Net: +2 (prime) + −1 (k=1) + −1 (k=1) = 0. Should have been +2 + 2 (roll k=2) = +4.
- Plies 4–11: 8 consecutive plain steps. No priming, no scoring. Heuristic wandered.
- Plies 16, 17: another +1 prime / −1 k=1 / −1 k=1 sequence.
- Plies 19, 24: more k=1 rolls.
- Plies 26–31: finally primes a 5-cell line…
- Ply 38: rolls it as **k=1** instead of k=2 → +1 instead of +2 points.
- Ply 39 (final): rolls **k=2** correctly for +2.

Final score: **6−6**. RattleBot threw away at least 6 points to k=1 rolls alone — it should have won by a comfortable margin.

### 3.6 Plain-step streak deep dive (RattleBot_Yolanda_9, streak=16)

The 16-plain streak spans plies 14–44. Yolanda was priming away on her half of the board, RattleBot just paced around producing no score. This is the leaf evaluator **returning the same value for many plies in a row** — every plain step keeps F1/F3/F4/F5 roughly constant, so minimax picks plain as the cheapest option. The final score was only **+10**, barely a win, because RattleBot essentially sat out 40 % of the game.

---

## 4. Top-3 root causes with code-level fix sketches

### 4.1 Root cause 1 — Negative-EV short rolls (k=1)

**Symptom:** 32/76 (42 %) of all rolls are k=1 (−1 pt). In 94 % of these, at least one primed cell remained on the board, meaning the agent either (a) couldn't reach it without moving, or (b) the heuristic preferred the immediate −1 over a PLAIN+PRIME+ROLL(k≥2) sequence whose leaf-eval scored higher after bounding.

**Code-level fix sketch (move generator / ordering, `3600-agents/RattleBot/move_gen.py`):**
```python
def generate_carpet_moves(board):
    moves = []
    for direction in (UP, DOWN, LEFT, RIGHT):
        # Existing code finds max_k in this direction
        for k in range(2, max_k + 1):   # <-- START AT 2, not 1
            moves.append(Move.carpet(direction, k))
    return moves
```
K=1 rolls are only ever useful to clear a single stranded primed cell to allow a plain step over it — a rare tactical need. We can *explicitly* add k=1 as a **last-resort** move by tagging the whole move list with a flag and only falling back to k=1 when every other move evaluates worse.

**Alternative (heuristic, `heuristic.py`):** add a feature `F_roll_1_flag` that triggers −2 penalty whenever the current board *contains a primed cell that the current worker CAN reach in plain steps*, so the leaf evaluator sees "you could've saved this prime for a better roll".

**Impact estimate:** eliminating all 32 k=1 rolls and replacing with +0 (plain) or +1 (prime) plays adds +32 pts across 13 matches → **+2.5 pts/match**. That alone shifts 2 games (the tie → win, and makes several narrow wins comfortable). More importantly, it stops the agent from actively losing points on its own primes.

### 4.2 Root cause 2 — SEARCH gate saturation (catastrophic failure mode)

**Symptom:** Once `belief.max_mass > 1/3`, the SEARCH gate in `agent.py:174` fires every single ply. If the belief fails to decay after misses, the agent will search all 40 turns for −76 net pts. This happens in 1/13 matches → 7.7 % of games; at bytefight.org tournament volume this is a near-guaranteed catastrophic loss per player-pair.

**Code-level fix sketch (`agent.py`):**
```python
# In play_internal, replace the raw gate:
# if belief_summary.max_mass > (1.0 / 3.0):

# with a guarded gate:
recent_searches = self._recent_search_results  # deque maxlen=3
consecutive_misses = sum(1 for r in recent_searches if not r)
if (belief_summary.max_mass > (1.0 / 3.0)
        and consecutive_misses < 2
        and belief_summary.argmax != self._last_search_argmax):
    move = self._search.root_search_decision(...)
else:
    move = self._search.iterative_deepen(...)
```
This turns the gate into "search if the belief says so AND we haven't been wrong twice in a row AND the belief peak has moved since our last search." Any of those three breaks the spiral.

**Second fix, non-independent:** also add a **mandatory diagnostic** — if the agent has taken >N plies without stepping, force a PLAIN or PRIME regardless of search-gate. The gate should never lock the worker in place.

**Impact estimate:** catches the one −68 loss. In a 50-match baseline the expected win-rate bump is ≈ +8 % (1 less guaranteed loss). Non-linear impact on ELO because catastrophic losses dominate bracket-tier outcomes.

### 4.3 Root cause 3 — Plain-step wandering / tempo loss

**Symptom:** 5+ plies of consecutive plain in 4/13 matches; one match has 16 consecutive plains. The minimax leaf is picking plain when it has no better scoring move and lookahead can't find a profitable PRIME line within the current depth budget.

**Code-level fix sketch (`heuristic.py`):** add a small penalty per consecutive "idle" ply. The history isn't in the leaf but we can compute a proxy from the board: *"current worker has no primed cell within Manhattan ≤ 3 AND no F5 ≥ 3 in any direction"* → add −0.2 to the leaf. This biases lookahead away from plain-only sequences without forbidding them (since sometimes positioning is correct).

**Alternative (move-ordering):** in the move generator, when PRIME moves and PLAIN moves both have identical leaf evals, prefer PRIME (it banks +1). Already worth it even if the deeper lookahead equalizes.

**Impact estimate:** breaking a 16-plain streak into 8 prime + 8 plain adds +8 pts. Over 13 matches with avg ≈ 3–4 plain-streak-idle plies, that's +3–4 pts/match average.

---

## 5. What BO can fix vs. what needs a new feature

### 5.1 Fixable by BO (Bayesian weight tuning)
The T-20d BO pipeline retunes the 9 weights in `W_INIT`. The following mistakes are **amplitude** problems — the right feature exists but the weight is off:

- `tempo_plain_streak` — adjusting W[F5] (longest_primable_line_ours, currently +1.5) upward will push minimax to prefer priming setups over wandering. Similarly bumping W[F3] (prime count, currently +0.3).
- `k_geq_4_starvation` — reducing the distance-decay on F5 (or increasing `_LAMBDA = 0.3` to value secondary directions more) gives more weight to setting up longer lines. Actually a **hyperparam** inside the cell-potential formula, not a BO weight — see §5.2.
- General carpet quality — W[F4] (carpet count) weight can be retuned.

### 5.2 Needs a new feature / code change (NOT BO-fixable)

- `roll_len_1_penalty` — the k=1 roll is a **move** the generator emits. No leaf weight will stop it from being picked if minimax finds it locally optimal. Fix must be in the move generator or in a feature specifically penalizing "you rolled a line that could have been longer". Candidate new feature `F_missed_length = max_reachable_k - actual_rolled_k` applied at the leaf *after* a carpet move. Ideally we just **don't emit k=1 moves except as last resort** (§4.1).
- `search_gate_saturation` — the root SEARCH gate is a binary decision *outside* the minimax leaf. BO cannot reach it. Must be fixed in `agent.py` (§4.2).
- `stationary_stall` — the leaf doesn't know about "consecutive plies in same cell". Either pass a `plies_since_move` signal into the heuristic, or add a hard stall-breaker in `agent.py`.
- Carrie-style cell potential (F5) uses `_LAMBDA=0.3, _ALPHA=0.3, _BETA=0.5` — these are **hyperparams inside the feature**, not weights. BO can't reach them unless we lift them into the weight vector. Recommended: lift `_LAMBDA` and `_BETA` into two new BO-tunable scalars for T-20d v2.

### 5.3 Cost/benefit call
For the remaining ~72 hours to submission, the priority ordering is:
1. **Fix §4.2 (search saturation)** — code-only, 10 lines, catches the catastrophic −68 loss. Must-ship.
2. **Fix §4.1 (k=1 rolls)** — code-only, 5 lines in move_gen.py, worth +2.5 pts/match and probably the difference between Albert and Carrie tiers.
3. **Add `_LAMBDA` / `_BETA` to BO search space in T-20d** — likely small single-digit gains but essentially free.
4. Only then spend BO cycles retuning W_INIT. Without §4.1/§4.2 the BO landscape is dominated by noise from the bug modes.

---

## 6. Recommendations for T-20d BO objective function

Current presumed objective: `win_rate(candidate, baseline)` or `mean(margin)` over N paired matches.

### Recommendations

**R6.1 — Penalize catastrophic losses asymmetrically.** A single `−68` loss has the same impact on mean-margin as thirty-four `+2` wins. If the BO is optimizing raw mean-margin, it will wash out the catastrophic failure mode entirely. Replace the mean-margin objective with a clipped or saturating version:

```python
def score_match(margin):
    # Clip win-margin at +20 (we don't care about blowouts)
    # Amplify loss-margin below -10 quadratically
    if margin >= 0:
        return min(margin, 20)
    if margin >= -10:
        return margin
    return -10 + 3 * (margin + 10)    # quadratic below -10
```
This pushes BO to prefer weight vectors that *never* produce a catastrophic loss, even if they forfeit some upside. Given that ELO distance-to-tier-boundaries is dominated by loss variance, this is the right bet.

**R6.2 — Paired sign-test, not win-rate.** The paired-runner already emits `paired_sign_test_p`. Use that as the primary promotion gate (as BOT_STRATEGY.md §6.1 requires). For BO objective: use *pair-wise margin difference*, not per-match margin — this controls for board variance and identifies weights that beat the baseline on the same-T+spawn setup.

**R6.3 — Require crash-free AND bug-free (stall-free) matches.** Add a hard constraint on BO candidates:
- Any candidate match with ≥10 consecutive RattleBot searches → reject outright (no match score assigned, counted as a loss of −30 for objective purposes).
- Any candidate match with `stationary_stall` (≥15 plies at same cell) → same treatment.

This forces BO to avoid weight vectors that trigger the pathological modes until the code-level fix (§4.2) lands. After §4.2 lands, drop these constraints.

**R6.4 — Objective on multiple opponents, weighted.** The current baseline plan is RattleBot vs FloorBot + vs Yolanda. Recommend:
- 70 % weight on RattleBot vs George (if reachable) or RattleBot vs FloorBot (as proxy).
- 30 % weight on RattleBot vs Yolanda (catches passive-opponent pathologies).
- Evaluate **both sides of the pair** equally (don't let BO overfit to Player-A advantage).

**R6.5 — Widen BO search space.** Add `_LAMBDA` and `_BETA` from `heuristic.py` to the BO search dimension (§5.2). These are inside-feature hyperparams that currently nobody is tuning. Probably only +1–2 ELO but it's free to include.

**R6.6 — Report per-category breakdowns** in the BO study log so we can see *why* a candidate improved. Save rolling `roll_len_1_penalty`, `k_geq_4_starvation`, `tempo_plain_streak`, and `search_whiff` counts for every 20-match evaluation block. If BO claims a +5 ELO weight vector but its roll-len-1 count *went up*, that's a red flag — it may be overfitting to the opponent mix, not finding a real improvement.

---

## 7. Open threads / next steps

1. **Re-run this analysis when baselines land.** `BASELINE_V01_RUN1/2` directories exist but are empty. The pipeline is idempotent; just rerun `py tools/scratch/v01_loss_analysis.py`. The 50 + 25 = 75 incremental matches will 10× the loss-sample size and likely uncover mistake categories that didn't surface at N=13.

2. **Replay the catastrophic match with belief instrumentation.** Load `RattleBot_Yolanda_1.json`'s T matrix / spawn / rat trace and step the `RatBelief` forward with debug printing. The belief must be misbehaving in a specific way — either `apply_our_search` miss-update is broken, or sensor+distance updates are over-concentrating on (3,4)/spawn-proximate cells.

3. **Verify the k=1 pipeline path.** Open `move_gen.py` and confirm whether the generator currently emits k=1 CARPET moves. If yes → root cause (fix per §4.1). If no → the alpha-beta is somehow synthesizing them, which would be a deeper bug worth investigating.

4. **Quantify Carrie-tier gap.** With the current 45-pt expected score / match (11 wins × ~20 margin), RattleBot is clearly above FloorBot and Yolanda. The real test is vs George/Albert/Carrie — once live scrimmages land, re-analyze with those specific matchups to see which mistake category dominates against *stronger* opponents.
