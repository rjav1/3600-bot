# Albert Win Pattern — reverse-engineered from 3 A_WIN replays

**Author:** albert-win-analyst (ephemeral)
**Date:** 2026-04-18
**Corpus:** 3 wins (97afd501 v03, bf6447e4 v03, f1a940d9 v04) vs 3 losses (bc4ebed5 v03 blowout, 4902684f v03 medium, 6cab9254 v03 narrow). Losses were picked to span the blowout/medium/narrow margin spectrum so signal is not concentrated at one intensity.
**Sample size warning:** n=3 wins is small. Patterns below rely on effect sizes that are not subtle (~3–6× differentials), not marginal improvements. Treat ELO projection as an upper-ish bound, not a point estimate.

---

## 1. Final-score table

| match | ver | us | opp | margin | notes |
|---|---|---|---|---|---|
| 97afd501 | v03 | **50** | 29 | +21 | clean dominant win |
| bf6447e4 | v03 | **39** | 26 | +13 | steady lead built turn 30 onward |
| f1a940d9 | v04 | **40** | 37 | +3 | **comeback** — down 7-22 at t=30, +28 from 7 walk-catches |
| **WIN mean** | — | **43.0** | 30.7 | **+12.3** | |
| bc4ebed5 | v03 | 2 | 49 | −47 | Albert search-dominant (2 successful searches) |
| 4902684f | v03 | 21 | 47 | −26 | Albert got 3/3 successful searches for +12 |
| 6cab9254 | v03 | 23 | 26 | −3 | narrow; we wasted 2 searches (-4) |
| **LOSS mean** | — | 15.3 | 40.7 | **−25.3** | |

---

## 2. Side-by-side tactical metrics

| metric | WINS (n=3) | LOSSES (n=3) | signal |
|---|---|---|---|
| **Our search attempts** | 4.67 /game | 4.33 /game | ~equal |
| **Our search HITS** | 1 total (3 games) | 0 total (3 games) | equal (bad) |
| **Our search MISSES** | 0 total | 5 total (−10 pts) | **WINS avoid bad searches** |
| **Albert search HITS** | 0 total | 5 total (+20 pts) | **LOSSES: Albert hit-rate spikes** |
| **Albert search MISSES** | 2 total | 4 total | similar |
| **Albert total searches** | 5.0 /game | **12.3 /game** | **~2.5× more** in losses |
| **Our walk-catches** | 4.33 /game (13 total) | 3.33 /game (10 total) | ≈similar count |
| **Albert walk-catches** | 1.0 /game (3 total) | 0.67 /game (2 total) | equal |
| **Our roll-k dist** | {1:1, 2:13, 3:2, 4:1, 5:1} n=18 | {1:4, 2:8, 3:9, 4:2} n=23 | **WINS: fewer k=1 duds** |
| **Our k≥4 rolls** | 2/18 = 11% | 2/23 = 9% | equal |
| **Our k=1 rolls (−1 pts each)** | 1/18 = 5.6% | 4/23 = **17%** | **LOSSES waste carpets** |
| **Albert roll-k dist** | {1:1, 2:11, 3:2, 4:1} n=15 | {2:10} n=10 | losses: Albert does fewer but zero losing rolls |
| **Mean dist (us) to rat** | 4.74 cells | 4.59 cells | ≈equal (not differentiator) |
| **Turns we led at ply 40** | 2/3 (wins) | 0/3 | wins: ahead at halftime except f1a940d9 |

### 2.1 Opening mix (first 8 plies per game, our side)

|  | PLAIN | PRIME | CARPET | SEARCH |
|---|---|---|---|---|
| WINS | 5 | 15 | 3 | 1 |
| LOSSES | 5 | 15 | 3 | 1 |

**Opening is identical.** Albert wins and losses are indistinguishable by opening. So it's **not** an opening-book problem — it's a mid-game problem.

### 2.2 Albert opening (first 8 plies per game)

|  | PLAIN | PRIME | CARPET | SEARCH |
|---|---|---|---|---|
| WINS vs us | 6 | 12 | 1 | 5 |
| LOSSES vs us | 10 | 7 | 2 | 5 |

Albert opens with noticeably **more PRIME and less PLAIN in our wins**. Plausible read: when Albert commits to prime lines early (and we disrupt them by walking on his prime chain endpoints or by out-tempoing him on carpet), he doesn't convert the primes into big rolls. In losses Albert plays more defensively (PLAIN steps) while Albert's HMM converges and lands search-hits later. This is also partially luck-of-the-draw: Albert's move is deterministic given his belief state and the board, so opening differences are driven by board geometry and what our first couple plies force.

---

## 3. Search timing (where in the game does the searching happen?)

| phase | WINS: us | WINS: Albert | LOSSES: us | LOSSES: Albert |
|---|---|---|---|---|
| early (plies 0–25) | 3 | **8** | 2 | 7 |
| mid (plies 26–53) | 7 | 5 | 3 | **13** |
| late (plies 54–79) | 4 | 2 | 8 | **17** |

- **In wins Albert front-loads his searches** (8 early) and **tapers off** (2 late). Plausible reason: his HMM belief never sharpens past the +EV threshold after the early burst, so he stops trying.
- **In losses Albert back-loads** (13 mid + 17 late) — his HMM *does* sharpen, and all three losses have him cranking out 10+ searches mid/late. Every one is a +EV swing.

**Key read: in wins we somehow keep Albert's HMM belief grid *diffuse* — his posterior never has a cell above 1/3 probability, so he stops searching. In losses his belief converges, he searches, and he hits.**

---

## 4. Rat-catch dynamics (the true point engine)

In **all 3 wins** our point lead is driven by walk-catches, not rolls:

- 97afd501: 5 walk-catches × 4 = +20 from rat (final margin +21) — **rat alone = the win**
- bf6447e4: 2 walk-catches = +8 from rat (margin +13) — rat + 1 extra roll = win
- f1a940d9: **6 walk-catches = +24 from rat** (margin +3) — we were *losing rolls 37−16=+21 to Albert* but won on walk-catch volume

In losses, our walk-catch count is similar (1/6/3) BUT Albert's search-hits (+8, +12, +4 = +24) *plus* our missed searches (−2, −6, −4 = −12) create a net +20-point swing toward Albert from rat-related actions.

**The wins are fundamentally "we convert rat mass into +4 walk-catches while Albert's HMM can't find the rat."**

---

## 5. The "secret sauce" — two candidate explanations

### Hypothesis A: **Aggressive rat-chasing worker movement pattern**
In wins our worker spent time in cells with high rat-belief mass. Because we *walked* onto the rat (not searched), we got the +4 without surrendering a turn or paying −2 false-positive tax. Albert's HMM presumably updates off of *our* observed position too (same sensor model for both sides), but our belief-grid-driven walks keep the rat *displaced* — after every walk-catch the rat respawns at (0,0) + 1000 silent steps, resetting Albert's posterior.

### Hypothesis B: **Disrupting Albert's HMM via carpet placement on high-belief cells**
Noise model: rat under CARPET emits SQUEAL with P=0.8; rat under SPACE emits SQUEAK with P=0.7. If we lay carpet on cells with high a-priori rat-belief, the rat's subsequent SQUEAL gives a strong signal to *Albert* too — but rat under *prime* gives SCRATCH with P=0.8, a signal *we both* can use. Unclear directional signal without belief-grid extraction from replays (engine doesn't log per-player belief).

Hypothesis A is the clean one. Hypothesis B is speculative.

---

## 6. Can we code this into the bot?

**Yes — as a heuristic feature on our own move-gen that values plain/prime steps onto cells with high rat-belief mass.**

### Concrete feature to add (or weight up)

In the heuristic eval (or as a move-gen tie-breaker), add the term:

```
RAT_CHASE_BONUS_PLY = belief[worker_after_move] * RAT_BONUS
                    = belief[cell] * 4
```

i.e. when we have a plain/prime step landing on cell (x,y), count `belief[x,y] * 4` toward that move's value (since we capture the rat iff it's in that cell, and the reward is +4).

### Why this is different from search EV

Current implementation (suspected — cannot read code per rules) probably already considers search EV: `search_ev[cell] = 4*P(rat) − 2*(1−P(rat)) = 6*P(rat) − 2`, threshold >1/3 to search.

But the same P(rat)×4 logic applies to any *step* onto that cell — with the crucial difference that a walk-step **also makes a move** (earns +1 if prime step, 0 if plain). So a plain step onto cell with P(rat)=0.2 is worth 0 + 0.2×4 = +0.8 in expectation; a prime step onto that cell is +1 + 0.2×4 = +1.8. Either dominates a search of that cell (search EV at P=0.2 is 6×0.2 − 2 = −0.8).

**Walk-catch dominates search at all P(rat)<1/3**, and walk-catch is strictly better than a dead plain step when P(rat)>0.

### Concrete F-feature for heuristic

Add/boost feature: `F_RAT_CHASE = sum_over_next_move_cells(belief[cell] * 4)` weighted into leaf eval.

Secondary, lower-confidence: in minimax, when enumerating PLAIN/PRIME steps as candidate moves, **re-rank them by expected rat-capture reward** so the search explores rat-chase lines first. This should improve alpha-beta pruning and may surface chase lines that aren't found at low depth today.

Concrete tuning:
- Start with coefficient 4.0 (matches raw reward) for leaf eval term.
- If expectiminimax already propagates rat-capture rewards correctly through its evaluator (it should, since apply_move scores the catch), this change is a **search-ordering hint**, not a heuristic weight change — ordering improvement alone commonly yields 1–3x effective depth in alpha-beta.

---

## 7. Expected ELO impact if we can reliably trigger this

**Scenario baseline:** current Albert WR = 5.9% (1/17), v03 baseline was 17% (3/17).

**If feature triggers reliably** — i.e. we raise the rate of games where our worker ends up on high-belief cells consistently (no regression on rolls):

- **Optimistic (wins-level behavior 40% of games):** WR vs Albert → ~25–35%. This is +15–25 Glicko vs current v04.
- **Realistic (wins-level behavior 20% of games, mid-effort implementation):** WR vs Albert → ~15–20% — basically returns to v03 parity. ~+5–15 Glicko.
- **Pessimistic (feature doesn't transfer because the 3 wins were fluke alignment of initial rat prior):** WR vs Albert unchanged at 5.9%. 0 ELO gain.

Because n=3 wins is small, assign probabilities:
- P(pessimistic/fluke) ≈ 30%
- P(realistic/v03-parity) ≈ 50%
- P(optimistic/breakthrough) ≈ 20%

**Weighted expected ELO gain vs v04: ~+10 Glicko.**

**Does this unlock the 80% tier?** Per `GRADE_PROJECTION_APR18.md`, 80% tier requires ~80% WR vs Albert. A jump from 5.9% to ~25% does **not** clear that gate. It does however:
- Restore our floor inside the 70% tier (tier scaling by ELO distance).
- Projected grade delta: from "low 70s / borderline below-tier" to "mid-to-high 70s". Estimated +3 to +7 points of final grade.

### Sanity check against the f1a940d9 game

f1a940d9 is the cleanest *causal* evidence: we were down 7-22 at t=30, rolled lost 16−37 vs Albert on pure carpet engine (ouch), but **caught the rat 6 times** for +24 and won 40-37. If the bot weren't preferentially chasing rat-belief cells we would have lost that game by 20+. So at least ONE of the wins is explainable *only* via rat-chase behavior.

---

## 8. Risks / caveats

1. **n=3 wins is small.** Confidence interval on "wins driven by walk-catch" is wide. 4902684f (loss) also had 6 walk-catches, so "walk-catches alone" is insufficient — it's walk-catches *combined with* lower Albert search hit-rate.
2. **Albert's HMM convergence is the dark variable.** We can't control it directly; it depends on the noise rolls and on Albert's vs our move sequence. If noise RNG goes against us, we can't stop Albert from searching effectively regardless of our move-gen.
3. **We already walk-catch at similar rates in wins and losses (4.33 vs 3.33 per game).** So walk-catch *volume* by itself isn't the discriminator — what's different is Albert's *search accuracy*. The proposed feature (chase rat-belief with steps) might already be mostly happening — and if so the improvement from this audit is marginal.
4. **F10 heuristic is locked for v0.4** per team-lead directive (`feedback_f10_locked.md`). Any new feature landing has to wait for a v0.5+ or go through team-lead approval.

---

## 9. Recommendation

**Primary:** Propose a move-ordering/eval-bonus feature `F_RAT_CHASE = belief[cell] * 4` for PLAIN and PRIME steps as a v0.5 candidate (post-deadline if F10 is locked). Expected ELO gain ~+10 Glicko, expected grade-delta +3 to +7 points if included pre-lock.

**Secondary:** Before coding, pull 10–15 more Albert wins if the win sample grows (currently tournament has given us only 3). If a larger win-sample maintains the >4×-Albert-search-ratio differential, confidence in the signal rises sharply.

**Anti-recommendation:** Do NOT chase this as a "let's fix Albert to 80%+" silver bullet. The data shows the signal is real but moderate. The 80% tier is out of reach via this or any single feature.

---

## Appendix: raw per-game detail

### Wins

**97afd501** (+21 margin): a_points curve (10,20,30,40,50,60,70,79) = (7, 13, 23, 28, 33, 44, 46, 50). Steady lead built t=20 onward via 5 walk-catches (t=7, 11, 23, 29, 35). One Albert walk-catch at t=62. We searched 6× (1 hit t=40), Albert searched 5× (1 miss). Rolls: us=[2,4,2,3,2], opp=[2,4,2,2,2].

**bf6447e4** (+13): a_points curve (4, 7, 15, 24, 28, 34, 38, 39). Flat early, lead from t=21 first walk-catch. Rolls: us=[2,2,2,2,2,2,2] — 7×k=2, conservative carpet play. We searched 4×, Albert only 2× — our lowest opp-search game.

**f1a940d9** (+3): a_points curve (0, 6, 7, 14, 18, 25, 31, 40). **Losing 7-22 at t=30, 14-21 at t=40.** Walk-catches at t=13, 19, 39, 45, 55, 61 (6 total, +24). Albert got a k=5 roll at t=16 for +10 (rare, Albert rolls are usually k=2). We still won by 3. This is the strongest proof that rat-catch volume can overcome a carpet-engine deficit.

### Losses

**bc4ebed5** (−47 blowout): a_points curve (4, 4, 5, 7, 11, 10, 5, 2). **We end with FEWER points than at t=10 (negative rolls).** 4×k=1 penalty rolls. Albert searched 12× with 2 hits. Our ONE walk-catch came at t=41, way too late.

**4902684f** (−26): a_points curve (-4, -2, 1, 3, 8, 6, 14, 21). Still −4 at t=10 from early penalty rolls. Recovered late (5 walk-catches t=13, 29, 47, 61, 63, 77) but Albert's 3 search-hits (+12) plus our 3 search-misses (−6) was decisive.

**6cab9254** (−3 narrow): a_points curve (5, 8, 7, 9, 13, 14, 20, 23). Flat, 1 k=1 penalty, 2 wasted searches (−4). Rat didn't get caught until t=45 — slowest rat-catch turn in any of 6 games analyzed. In the 3 wins we caught the rat by t=7, 21, 13 respectively.
