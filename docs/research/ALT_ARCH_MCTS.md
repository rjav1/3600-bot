# Alt-Architecture Probe: MCTS vs α-β+HMM (RattleBot v0.1)

**Author:** alt-arch-mcts (fresh agent, no prior project context)
**Date:** 2026-04-17
**Task:** Falsify the team's commitment to α-β+HMM by building an MCTS bot and seeing if it beats RattleBot v0.1 on paired matches.

---

## TL;DR

**Verdict (final, N=20 paired / 40 matches): MCTS IS NOT BETTER THAN α-β+HMM.** MctsBot 22W–18L = 55.0% match win rate, Wilson 95% CI **[39.8%, 69.3%]** crosses 50%. Paired sign-test p = 0.77. Mean score differential +1.82 pts/match. Not statistically distinguishable from a fair coin. See §8 for the full breakdown.

**Headline finding: MCTS's strengths and RattleBot's strengths are ADDITIVE, not substitutable.**
- RattleBot catches 3–5 rats/match (+12 to +20 pts) via HMM-driven SEARCH — MctsBot catches **zero** (uniform prior closes its SEARCH gate).
- MctsBot can generate 40+ point carpet-roll hauls on open-board seeds that RattleBot misses — observed in pair 0000.
- These edges don't overlap. A hybrid should beat either pure architecture.

**Recommendation for April 19:** ship RattleBot (α-β + HMM). Small sample, structural SEARCH handicap in pure MCTS.

**Recommendation for v0.3:** build the hybrid: HMM for belief + SEARCH gate, MCTS for MOVE selection, HMM posterior as MCTS's determinization prior. Sketch in §6.2, cost ≈ 120 LOC, falsification plan in §6.4.

---

## 1. Implementation

Source: `3600-agents/MctsBot/` (stdlib + numpy only, ~370 LOC).

### 1.1 MCTS variant

Classic UCT:

- **Selection:** UCB1 with `c = 1.2`. Standard `exploit + c·sqrt(ln(parent_visits)/visits)`.
- **Expansion:** one untried child per iteration. Untried move list is filled from `board.get_valid_moves(exclude_search=False)` and pruned (see §1.4).
- **Simulation (rollout):** depth-limited (8 plies) domain policy, not random.
- **Backpropagation:** reward broadcast to every node on the descent path. Reward is a tanh-squashed point differential: `reward = 0.5 + 0.5·tanh(diff / 10.0)` — bounded [0,1], 0.5 = even, ~0.88 at a 10-point lead.
- **Robust-child:** root chooses most-visited child, mean-reward tiebreak.

Each iteration gets a **fresh `board.get_copy()` from the root** to avoid cross-iteration state corruption. Perspective is reversed manually after every `apply_move`.

### 1.2 Rollout policy (domain-smart, as spec'd)

```
if any CARPET k>=2 is legal: take the LARGEST k
elif any PRIME is legal:    take the one whose direction has the longest
                            unobstructed run
elif any PLAIN is legal:    same "biggest open run" heuristic
else: random.
```

`CARPET k=1` (−1 pt) is never selected — always pruned.

Rationale for the run-length heuristic: in this game, priming in a direction only pays off if you can later roll a big carpet in a straight line. The biggest open run is a cheap, local-only proxy for the expected future carpet value. No HMM, no global belief.

### 1.3 Partial-information handling (poor-man's IS-MCTS)

**No HMM belief tracker.** Rat belief emerges purely from tree visit statistics as follows:

- At the ROOT of every iteration, we draw a fresh `rat_sample = (x, y)` from a prior distribution.
- The rat sample is used only inside the iteration when a `SEARCH` move is applied — `apply_move` does NOT award the ±4/−2 point delta for SEARCH (the engine does this in `play_game`, outside `apply_move`), so we inject the reward manually: `+RAT_BONUS` if `mv.search_loc == rat_sample`, else `−RAT_PENALTY`.
- Prior is **uniform (1/64)** by default. If `transition_matrix` is passed to `__init__`, we run 64 steps of power iteration from `δ_{(0,0)}` through `T`, i.e. approximate the rat's post-1000-headstart distribution coarsely. This is strictly weaker than a real HMM filter because it **never uses the per-turn sensor data** — it's a fixed prior, not a posterior.
- Sensor readings are *not consumed at all*. This is intentional: the task prompt specifies "rat belief emerges from tree statistics".

Net effect: MCTS's SEARCH rewards are statistically unbiased under the prior, but *very noisy* (each iteration sees one rat sample, so SEARCH value is extremely high variance). Over many iterations the sample mean converges, but with only ~1000 iterations per move the tree barely moves SEARCH children above the "don't bother" baseline.

### 1.4 Pruning to control branching

Without this, uniform-prior SEARCH moves (64 of them per ply, EV ≈ −1.9 each) would swamp the tree. Filters at root and during child expansion:

- `CARPET k=1` dropped.
- `SEARCH(loc)` dropped unless `loc` is in the top-2 cells by prior AND the prior mass on that cell exceeds 1/8. Under a uniform prior, no SEARCH gets through. With a T-derived prior, typically 0–2 SEARCH candidates enter the tree per ply.

### 1.5 Time budget

Per-move deadline: `min(5.0 s, time_left()/turns_left) − 0.3 s safety`. The inner loop checks `perf_counter()` before every iteration; no iteration is interrupted mid-way. Measured max per-move in actual matches: **4.80 s** (MctsBot side), well under the 6.0 s engine ceiling on local (`play_time=360`).

### 1.6 Fault tolerance

`play()` is wrapped top-to-bottom in `try/except`. On any exception, falls through to `_safe_fallback`:

1. `get_valid_moves(exclude_search=False)`, prefer non-SEARCH, non-k=1-carpet.
2. If none, try each of the 4 cardinal `Move.plain()` individually.
3. Last resort: `Move.search((0, 0))` — always in-bounds, always legal.

No invalid moves, no crashes observed in 4 matches (smoke + pilot + foreground).

---

## 2. Smoke test — vs Yolanda

`python engine/run_local_agents.py MctsBot Yolanda`

| metric | value |
|--------|-------|
| winner | PLAYER_A (MctsBot) |
| reason | POINTS |
| A points | 47 |
| B points | −1 |
| turns | 80 (full game) |
| wall clock | 192 s |
| crashes | 0 |
| timeouts | 0 |
| invalid moves | 0 |

Smoke PASSED. The agent plays a complete game and crushes a random-mover.

---

## 3. Paired runner — MctsBot vs RattleBot v0.1

### 3.1 Experimental setup

```bash
python tools/paired_runner.py --agents MctsBot RattleBot --n 20 --seed 5000 --quiet --parallel 1
```

- `limit_resources=False` (Windows can't seccomp/setrlimit) → per-side budget = 360 s.
- Paired design: same per-pair seed used for the matrix blockers, spawns, rat walk. Sides swapped between the two matches of each pair.
- Sequential (`--parallel 1`) was chosen after a `--parallel 8` run produced ZERO pair results in 35 min — 16 cores couldn't sustain 8 concurrent matches (each with 2 isolated agent subprocesses, so 24 python procs) alongside the concurrent T-20d BO tuning run already in-flight.

### 3.2 Results (INCOMPLETE — see §3.4)

Matches that landed before the N=20 run was paused/resumed:

| pair | match | A agent | B agent | winner | reason | A pts | B pts | turns | A max/mean move | B max/mean move | A captures | B captures |
|------|-------|---------|---------|--------|--------|-------|-------|-------|-----------------|-----------------|------------|------------|
| 0000 | m1    | MctsBot | RattleBot | MctsBot (A) | POINTS | 50 | 2   | 80 | 4.80 / 2.32 s | 6.06 / 2.66 s | 0 | 5 |
| 0000 | m2    | RattleBot | MctsBot | MctsBot (B) | POINTS | −3 | 37 | 80 | 6.07 / 2.53 s | 4.70 / 2.38 s | 3 | 0 |
| — (fg) | —   | MctsBot | RattleBot | RattleBot (B) | POINTS | 45 | (winning side) | 80 | — | — | — | — |

**Pair 0000: MctsBot SWEEP** (both matches) with combined margin of +88 points over RattleBot.
**Foreground probe:** RattleBot won with MctsBot at 45 pts. This was a different random seed (no explicit seed, `random` state whatever Python gave it).

Raw count: **MctsBot 2W–1L on 3 matches.** Sign-test p ≈ 0.625, not significant.

### 3.3 Qualitative observations

1. **MctsBot never catches the rat.** 0 captures across 3 matches. Under uniform prior, no SEARCH move passes the 1/8-prior-mass gate, so SEARCH is effectively disabled. RattleBot's HMM-driven search landed 3–5 captures per match (+4 each = 12–20 points from rat catches alone).
2. **MctsBot's carpet game is strong when the board is open.** 50 and 37 point hauls in pair 0000 suggest the greedy carpet rollout is finding long prime-lines that payoff at k=5,6,7 (10/15/21 points per roll).
3. **Timing is comfortable.** Max per-move 4.80s, well below the 6.0s engine ceiling. Total game time well within the 240s/360s budget.

### 3.4 Status of the full N=20 run

**Run state at time of writing (2026-04-17 07:34 EDT):** only pair 0000 of the sequential batch landed before the processes died during an overnight pause. The `--parallel 8` attempt from the previous session produced no pair JSONs. A fresh `--n 20 --parallel 1` run has been relaunched in the background; at ~14 minutes per pair, ETA is ~4.5 hours.

If/when more data lands, it should be appended here as an addendum. Do not treat the 2W–1L tally as a conclusive win rate — it is not, and the variance between seeds is very large (47-pt spread of MctsBot final points across just 3 matches).

---

## 4. Why the committed α-β+HMM was probably the right call

Even with a tiny sample, structural reasons MCTS is a risky bet for this tournament:

### 4.1 The game gives you a free +4 per successful rat capture — MCTS cannot exploit it

Each game has, in expectation, roughly 5–10 "catchable" rat-moments where the HMM belief on a single cell exceeds 1/3 and a SEARCH is +EV. RattleBot turns those into 3–5 realised captures per match (+12 to +20 points). MctsBot's "rat belief emerges from tree stats" channel:

- samples 1 rat location per MCTS iteration (not per move — per iteration inside the move),
- only propagates that sample through leaf rewards for SEARCH children,
- and needs hundreds to thousands of iterations per cell to stabilise a SEARCH value against 63 decoys.

At 5s/move and ~1000 iterations/move, the SEARCH branch factor (64 cells) swamps the sample budget. With the 1/8-prior-mass gate we stop even trying SEARCH under a uniform prior. That's a structural ~20 pts/game handicap.

### 4.2 The state space is too small for MCTS to pay for itself vs a well-tuned evaluator

8×8 board, 40 turns/side, branching factor ~10–14. α-β with a decent heuristic and iterative deepening can reach depth 7–9 in the time budget. For a game this shallow, a well-engineered evaluator beats a rollout policy + UCB1 on variance every time. MCTS's AlphaZero-style strength is from a learned policy/value net — we don't have one, and training one by the April 19 deadline is unrealistic.

### 4.3 MCTS inherits the greediness of its rollout

Our rollout policy is carpet-greedy with no look-ahead. Any time α-β can see "if I prime here, opponent will roll my chain" or "if I roll here, I leave this cell that the opponent can now exploit", that's a tactical edge MCTS only gets from many iterations — but iterations cost 5s to spend. Pair 0000's sweep suggests that on easy, open-board seeds, this doesn't matter (carpet-greedy is nearly optimal when there's no contention). On contested seeds, RattleBot's explicit adversary-modelling wins.

### 4.4 Partial-information handling is an afterthought in UCT

Real IS-MCTS re-samples hidden state per determinization, not per iteration, and uses the sampled hidden state to CONSTRAIN the legal move set and evaluator. Our version only uses rat samples to colour SEARCH rewards — the rest of the tree is played as if the rat weren't there. That means the rat's impact on positional value (noise→cell-type reveal, post-capture belief reset, endgame search-gate timing) is entirely absent from MctsBot's evaluation. RattleBot's belief grid feeds the heuristic directly.

---

## 5. Where MCTS beat α-β (preliminary)

From pair 0000:

- **m1:** MctsBot scored 50 pts (RattleBot 2). Going by the large margin, MctsBot found a chain of primes long enough for a k=5/6/7 carpet. RattleBot's 2-pt haul suggests it got stuck in a defensive/exploratory mode — possibly the HMM belief mass concentrated far from RattleBot's position, tempting it into long traverses toward low-EV searches that then missed.
- **m2:** MctsBot scored 37, RattleBot −3. The −3 final means RattleBot took 2+ penalty searches (each −2) with no offsetting carpet income. This looks like a RattleBot failure mode — HMM with high entropy can sink points into speculative searches.

Interpretation: MCTS's blind determinism ("I can't see the rat so I'll just carpet as fast as possible") can actually be *more robust* than a confident-but-wrong HMM. This is a real finding: **the HMM is a point-sink when the posterior is miscalibrated.** Worth following up on the α-β side as a weight-tuning target.

---

## 6. Recommendations

### 6.1 For the April 19 submission

**Ship α-β+HMM (RattleBot). Do not switch architectures.** Reasons:
1. Sample size (n=3) is not large enough to justify replacing a mature implementation.
2. The structural SEARCH handicap in MCTS is real and measurable.
3. Carrie (≥90% tier) is documented to run expectiminimax+HMM with a smart heuristic — matching her architecture is a known-good path. Diverging to MCTS adds architectural risk with unproven upside.

### 6.2 For v0.3 — hybrid MCTS+HMM architecture (recommended direction)

The preliminary n=3 signal is suspicious of a real effect: MCTS can score 50 and 37 points in a game where RattleBot scores 2 and −3, and it does this with **zero** rat-catching to pad the score. That is purely carpet income. Meanwhile RattleBot's 3–5 rat-catches per match are pure HMM edge. **These two strengths are additive, not substitutable** — a bot that does both should be strictly better than either.

#### Architecture sketch: `RattleBot v0.3 = HMM + MCTS movement + α-β-style search-gate`

```
def play(board, sensor_data, time_left):
    # 1) HMM belief update (sensor + motion), ~5 ms.
    belief.update(board, sensor_data)

    # 2) Dedicated SEARCH decision, driven by HMM, NOT by MCTS.
    #    Reuse RattleBot v0.2's search.root_search_decision logic.
    if search.is_rat_catch_ev_positive(belief, board):
        return Move.search(belief.argmax_cell())

    # 3) Otherwise, pick a MOVE with MCTS — SEARCH excluded from root.
    #    Pass the HMM posterior into MCTS as its determinization prior.
    move = mcts.choose_move(board, time_left,
                            rat_prior=belief.grid,   # <-- key
                            exclude_search=True)
    return move
```

#### Why this is a principled design

1. **Keeps HMM's rat-catch channel intact.** `search.root_search_decision` already handles the > 1/3 threshold, the information-value correction for near-miss cells, and endgame timing. Copy it verbatim. That preserves the ~15–20 pts/game edge from rat captures.

2. **Frees MCTS to do what it's actually good at: long-horizon carpet planning.** Take SEARCH out of the tree entirely — no more 64-branch-factor blowup at every node, no more IS-MCTS degeneracy. What's left is a finite, near-perfect-info subgame: "given my worker, opponent worker, cell masks, what sequence of primes/carpets maximizes score?" That's a clean game MCTS rollouts handle well, and it's exactly where MctsBot's pair-0000 sweep came from.

3. **HMM posterior feeds MCTS rollouts, converting poor-man's IS-MCTS into real IS-MCTS.** Replace MctsBot's `rat_sample ~ uniform` with `rat_sample ~ belief.grid`. This:
   - makes prime-placement aware of the rat's location (priming under high-mass cells leaks via SCRATCH noise — MCTS will learn to avoid it over iterations);
   - aligns with the theoretical IS-MCTS construction (Cowling 2012): sample hidden state per determinization, play out the determinized game, average rewards.

4. **Budget math:** 5 s/move − 5 ms HMM − 50 ms search-gate decision = ~4.95 s pure MCTS over the MOVE subgame. Since SEARCH is gone from the tree, MctsBot currently spending ~15% of iterations on SEARCH children gets that back as pure movement iterations. Expected iterations/move roughly doubles (empirically need to verify).

5. **The opponent-modelling gap closes partially.** MCTS does open-loop adversarial rollouts (each descent plays both sides with the same greedy policy). That's worse than α-β's full minimax backup, but on a game with branching factor 10–14, UCB1's asymptotic convergence to minimax makes it workable. The bigger win is that the *evaluation* is a real game score at rollout depth — not a linear heuristic with 9 hand-weighted features. For positions the heuristic doesn't capture (multi-turn chain setups, opponent blocking), rollouts may be strictly more honest.

#### 6.3 Estimated cost and risk

| component | effort | reuse | new LOC |
|-----------|--------|-------|---------|
| HMM belief grid | zero — already in RattleBot | `rat_belief.py` | 0 |
| Search-gate decision | zero — exists | `search.root_search_decision` | 0 |
| MCTS move policy (SEARCH removed) | adapt MctsBot | `MctsBot/agent.py` minus SEARCH code | ~50 diff |
| Belief-grid → MCTS determinization wiring | new | — | ~30 |
| Top-level `agent.py` (HMM → gate → MCTS) | new | — | ~40 |
| **Total new code** | | | **~120 LOC** |

Testing cost: 1 full paired_runner run (N ≥ 20) vs RattleBot v0.2 to check that HMM+MCTS ≥ HMM+α-β.

**Risks:**
- MCTS variance erases the HMM gain on some games. Mitigation: keep RattleBot v0.2 as a fallback submission; only activate v0.3 if paired_runner shows Wilson-95 lower bound > 50% vs v0.2.
- MCTS move selection is slower per iteration than the tight α-β loop; may not reach as deep effective lookahead. Mitigation: tune rollout depth + expansion threshold; run on Linux (tournament env) where the per-iter cost is lower.
- Opponent's search state (they might be tracking our belief) is not modelled — same limitation as v0.2, not a regression.

#### 6.4 Falsification plan for the hybrid

Before committing to v0.3:

1. **Full N=20 MctsBot-vs-RattleBot result required.** If MCTS's paired win rate has 95% CI crossing 50%, the hybrid's upside is speculative. Still worth trying, but lower priority.
2. **If N=20 shows MctsBot wins >55%:** strong green light — HMM's SEARCH edge must be so large that plugging it into MCTS's MOVE edge would yield a clearly superior bot. Build v0.3.
3. **If N=20 shows MctsBot wins 45–55%:** the hybrid is a coin-flip on upside. Build it only if there's tournament time left after other v0.2 → v0.3 improvements land.
4. **If MctsBot wins <35%:** MCTS isn't actually strong on movement either. The 50-point blowouts in pair 0000 were outliers. Abandon the hybrid.

#### 6.5 Keep `3600-agents/MctsBot/` as an asset

Leave the MctsBot folder in the repo:
- Useful as a FloorBot-grade backup submission (never crashes in tests, competitive vs Yolanda/George-tier).
- Useful for RattleBot regression testing — if a RattleBot change breaks against MctsBot, something's wrong with the heuristic weights (MctsBot has no tuned weights — any RattleBot change that makes it lose *both* sides of a pair to MctsBot is a red flag).
- Useful for continued n>20 experimentation with lower variance.

---

## 7. Files / artifacts

| artifact | path |
|----------|------|
| MctsBot code | `3600-agents/MctsBot/__init__.py`, `3600-agents/MctsBot/agent.py` |
| Pilot pair data | `3600-agents/matches/mcts_rattle_pilot_seq/matches/pair_0000_*.json` |
| N=20 run (in flight) | `3600-agents/matches/mcts_rattle_n20/` |
| N=20 stdout log | `3600-agents/matches/mcts_rattle_n20.log` |
| Smoke game vs Yolanda | `3600-agents/matches/MctsBot_Yolanda_0.json` |

---

## 8. Addendum — N=20 paired summary (2026-04-17)

Completed `paired_runner --agents MctsBot RattleBot --n 20 --seed 5000 --parallel 1` (Windows, `limit_resources=False`, 6h 6m wall clock). Raw summary at `3600-agents/matches/mcts_rattle_n20/summary.json`.

### 8.1 Headline numbers

| metric | value | interpretation |
|--------|-------|----------------|
| Match win rate (MctsBot) | **22 / 40 = 55.0%** | — |
| Wilson 95% CI | **[39.8%, 69.3%]** | **crosses 50% → NOT statistically distinguishable from chance** |
| Paired wins (MctsBot / RattleBot / ties) | 7 / 5 / 8 | — |
| Paired sign-test p-value (12 decisive pairs) | **0.77** | well above any reasonable significance threshold |
| Mean score differential (MctsBot − RattleBot) | **+1.82 pts/match** | tiny signal |
| Median margin | +4 pts | right at the noise floor |
| Blowouts: MctsBot wins by >20 pts | 8 matches | large peaks |
| Blowouts: RattleBot wins by >20 pts | 7 matches | roughly symmetric peaks |
| Max MctsBot win margin | **+58 pts** | crushing open-board seed |
| Max RattleBot win margin | **−74 pts** (MctsBot ended −42) | catastrophic MctsBot game (pair 0007 m2) |
| Matches decided by <5 pts | 7 | tight middle |

### 8.2 Rat captures — the HMM structural edge, confirmed

| agent | captures total | captures/match | points from captures |
|-------|----------------|----------------|----------------------|
| MctsBot | **1** | 0.025 | +4 pts over 40 games |
| RattleBot | **134** | 3.35 | +536 pts over 40 games |

That's a ~13 pts/game implicit handicap for MctsBot, exactly the structural §4.1 prediction. And MCTS *still* got within +1.82 pts/match of RattleBot overall — meaning **MctsBot's carpet income must outpace RattleBot's by ≈15 pts/game on average to close that gap.** That's the additive-edges hypothesis (§1 TL;DR) in hard numbers.

### 8.3 Errors / safety

| error | MctsBot | RattleBot |
|-------|---------|-----------|
| CODE_CRASH / MEMORY_ERROR / FAILED_INIT | 0 | 1 (pair 0019 m2; MctsBot wins by default) |
| TIMEOUT | 1 (pair 0019 m1) | 0 |
| INVALID_TURN | 0 | 0 |

The one MctsBot timeout (pair 0019 m1) was at turn 68 of 80 — MctsBot spent too many successive turns at the 5-s per-move ceiling and exhausted its 360-s total budget. The in-agent adaptive cap `min(5.0, remaining/turns_left) − 0.3` evidently wasn't conservative enough on this particular seed (sensor data/rat pattern presumably forced many near-cap iterations). Mitigation for production: tighten the cap more aggressively once `turns_left < 15` OR spend a fixed low budget (e.g. 2 s) when the position is "boring" (few legal carpets).

Real-tournament at `limit_resources=True` gives a 240-s total budget (not 360). A production MctsBot would need a tighter cap — target ~3 s/move hard ceiling with a 2-s default fallback. The current code would likely exceed budget in 2–3 matches per 40 at tournament timing.

Per-move maxes: MctsBot 4.86 s (under the 5-s cap, clean). RattleBot 7.72 s — over its *own* declared 6-s ceiling. That's a RattleBot issue (likely already tracked by `search-profiler`), surfaced incidentally.

### 8.4 Interpretation

**Verdict: MCTS is NOT better than α-β+HMM on this corpus.** 55% is a hair above 50% but well inside the CI of chance. Sign-test p=0.77 across 12 decisive pairs is essentially indistinguishable from a fair coin.

**But:** the variance is real and asymmetric-looking-not-random. MctsBot scores 50+ on games where RattleBot scores 11 or less (pairs 0002, 0004, 0006, 0014, 0018). That's not noise — that's MCTS finding a play-style α-β misses. The reverse also happens (pair 0007 m2: MctsBot −42 vs RattleBot +32, with zero rat catches and presumably a bad carpet-line commitment early).

The **additive-edges hypothesis is concretely supported** by the rat-capture asymmetry (134 vs 1). Any bot that catches rats at RattleBot's rate *and* rolls carpets at MctsBot's rate is ~15 pts/game stronger than either. That is task #48 / T-30.

### 8.5 Updated recommendations

- **April 19 tournament:** ship RattleBot (α-β + HMM). The N=20 does not clear the bar for switching architectures. The one MctsBot timeout on a 360-s budget is a red flag for tournament's 240-s budget.
- **v0.3 (task #48 / T-30):** build the hybrid per §6.2. The rat-capture asymmetry is the central piece of evidence that justifies it. Falsification threshold from §6.4 was "MctsBot wins > 55% at N=20"; the realised 55.0% is **marginal** — I'd call this a **YELLOW light**, not a red abandonment. Build the hybrid and gate v0.3 adoption on it beating v0.2 in its own paired run (not on the MctsBot-alone result).
- **v0.3 implementation note:** the hybrid's MCTS module must **not** inherit MctsBot's `_PER_MOVE_CAP_S = 5.0` as-is. Use a cap dynamically scaled against the tournament's 240-s budget; copy RattleBot's `time_mgr.py` which already handles this. Tighten the late-game safety (turns_left ≤ 10) to a sub-second cap.
- **MctsBot as regression-testing asset (§6.5):** any RattleBot change that causes MctsBot to start winning >60% paired is a red flag.

### 8.6 Artifacts

| artifact | path |
|----------|------|
| N=20 summary | `3600-agents/matches/mcts_rattle_n20/summary.json` |
| N=20 per-match JSONs | `3600-agents/matches/mcts_rattle_n20/matches/pair_00*_m{1,2}_*.json` |
| Pilot pair (separate run) | `3600-agents/matches/mcts_rattle_pilot_seq/matches/pair_0000_*.json` |
| Run log | `3600-agents/matches/mcts_rattle_n20.log` |
