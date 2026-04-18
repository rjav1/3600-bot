# CONTRARIAN_APR18 — Fresh-Eyes Structural Critique

**Author:** `fresh-eyes-contrarian-apr18` (ephemeral, single-shot)
**Date:** 2026-04-18 (T-42h to deadline)
**Method:** Read-only. Consumed `ARCH_CONTRARIAN_APR17.md`, `BOT_STRATEGY.md` (v1.1 + v02/v03/v04 addenda), `COMPETITIVE_INTEL_APR17.md`, `LOSS_ANALYSIS_{CARRIE,MICHAEL}_APR18.md`, and the shipped `3600-agents/RattleBot/{agent,heuristic,search,move_gen,rat_belief,time_mgr}.py`. **No code edits.** No BO disturbance.
**Baseline:** v0.4.1 shipped (F-1 k=1 ban + SEARCH→F-1-forced swap; F-2 mass floor 0.35 w/ endgame ramp to 0.30; F-3 ply-0 prime). Pre-v0.4: 26.3% WR vs real bytefight. Post-v0.4 early signal: 1W/9L vs top-5 student teams.

---

## §0 — Posture

The prior audits nail the **scoring-leakage** problems (k=1 rolls, early SEARCH bleed, PLAIN opening). But if v0.4 still ships 1W/9L vs top-5, those fixes were necessary-but-not-sufficient — the architecture has structural blind spots that stacking more patches on top of α-β+HMM will not close in 42 hours. What follows is the honest list of **what we're not doing that top-5 teams almost certainly are**.

---

## §1 — Top 3 Structural Blind Spots

### BS-1 — Belief is frozen at root; the tree cannot reason about information flow

**What it is.** In `search.py`, `iterative_deepen` sets `self._root_belief = belief` once at entry and passes the *same* `BeliefSummary` to `_eval_leaf` at every leaf. Every belief-derived feature (F11 max_mass, F12 entropy, F13 COM distance, F14/F15/F16 decay kernels, F17 priming_lockout partially, F18 opp_belief_proxy, F19 rat_catch_threat_radius, F20 opp_roll_imminence) reads from this frozen snapshot. Deep in the tree — after hypothetically 8 plies of play — the leaf still sees belief-as-of-root. The rat never "moves" inside our simulation even though in reality it takes 2 T-steps per our-ply round-trip.

**Why this is a structural problem, not a tuning one.**
1. **Leaves at depth d ≥ 2 evaluate against a belief that is wrong by d rat-moves of diffusion.** In the opening when belief is already near-stationary this is fine. In mid/late game after a capture-respawn, or after sharp sensor updates, the belief is concentrated and *will* diffuse — our leaves pretend it stays sharp, so they over-value "move toward current peak" plans that are stale by the time the plan executes.
2. **The leaf can't distinguish "move that lets the rat come to me" from "move that chases the rat."** F19 varies by *worker* position but with fixed belief; it's really a "move me toward current peak" signal. It doesn't know that T@T pushes probability mass around in ways the worker can ambush.
3. **SEARCH's information value is invisible inside the tree.** SEARCH is root-only, gated by 3 hand-designed conditions + 1 EV comparison. The tree never explores "PRIME now → next turn belief becomes more concentrated after sensor update → SEARCH becomes high-EV." The root SEARCH decision is a 1-ply VoI calculation; the tree plays a completely different game.
4. **Consequence under a fixed (frozen) belief:** α-β is effectively doing minimax over a **scoring-only** objective with a position-derived rat bonus that's nearly constant across siblings. 97.9% cutoff-on-first-move (team-lead telemetry) confirms this — the tree is essentially ratifying the move-order's #1 pick. We're paying for depth we don't exploit.

**Why top-5 teams likely do better here.** Not because they run a full chance-node expectiminimax (expensive), but because **they spend less time in-tree and more time on belief-aware root policy**. Their 100+ seconds of unused budget says their search is lightweight; the decision quality comes from a well-tuned one-ply-with-belief-propagation policy, not from α-β depth.

- **Expected ELO impact:** **+20 to +40** if we simply stop trying to pretend belief features have meaning inside the tree (switch to a static-position leaf + belief-aware root policy layered on top), OR do one T-step of belief advance per own-ply in the tree (medium risk).
- **Complexity:** **M** (static variant) / **L** (proper in-tree T-step).
- **Risk of breaking existing play:** **Medium** (static variant removes signal the BO run is currently fitting; L variant risks H-1-class belief-mutation bugs we just crushed).

---

### BS-2 — We search deep against a minimax straw-man opponent who doesn't exist

**What it is.** `_alphabeta` is pure negamax: at every opp ply we compute `max over opp moves of −αβ(child, d−1, ...)`. This assumes the opponent plays the value-minimizing move under *our heuristic*. But:
- **Carrie's replay `err_b` ≈ 12-14 across every match** (loss-forensics §2.1) — she's evaluating a fixed cell-potential heuristic, not running minimax-vs-us. She's expectiminimax with a frozen eval function, effectively a one-ply-or-two-ply greedy in practice.
- **Rusty uses ~120 s of 240 s** (loss-forensics Michael §2) — she's not deep-searching. She grinds k=2/k=3 with high-volume searches.
- **Top-5 teams average 100+ seconds unused** (competitive-intel).

By modeling the opponent as "adversarial-to-our-heuristic," we over-weight tactical threats that the real opponent never sees, and under-weight the opponent's actual behavior (which is often **greedy prime-extension + opportunistic roll**). We pre-empt phantom threats, foregoing +1 primes we should have taken.

**Concrete tell:** 97.9% cutoff-on-first-move. When α-β almost always agrees with the move-order heuristic, the "alpha-beta" part is vestigial — we're really running move-ordering-with-verification. That verification is hurting us because it assumes the opp will play the worst-for-us reply, when in fact they'll play the best-for-them move ≈ a greedy prime extension 70% of the time (competitive-intel §3 P-3).

**Why top-5 likely do better.** They either (a) assume a greedy opponent (correct against George/Yolanda/FloorBot/many student bots) or (b) hedge with an opponent-model mixture. Neither requires depth.

**Fix shape (NOT expectiminimax rewrite):**
- Replace opp's negamax minimization at depths ≤ 2 with a **greedy opp-move model**: pick the opp's move that maximizes their immediate score delta (with k=2+ roll preference). Branch factor at opp plies drops from ~7 to 1 → we gain ~7× effective depth from the same compute, AND the model reflects reality.
- Keep negamax only at deep plies or against "Carrie-tier" opponents (detect via high search rate? unreliable — just default to greedy-opp).

- **Expected ELO impact:** **+15 to +40** against greedy student bots + George/Yolanda/Michael/Rusty. **−5 to −10** against a truly-adversarial opponent (but the data says those don't exist in our bracket).
- **Complexity:** **M** (one-ply greedy at even-parity plies in `_alphabeta`; gated by a `assume_greedy_opp=True` flag).
- **Risk of breaking existing play:** **Medium** — violates the "negamax symmetry" invariant that `test_alphabeta_matches_minimax` was written for. Need new test against a greedy-opp oracle.

---

### BS-3 — Heuristic has the wrong sign convention for opponent carpet exploitation AND under-weights opp-mobility denial

**What it is.** Both loss analyses (Carrie RC-5, Michael RC-3) independently flagged that **we roll big carpets in the middle of the board and the opponent walks on them**. Neither v0.4 nor v0.4.1 touches this. F4 (`ours_carpet_count`) counts carpets perspective-invariantly — in self-play it zeros out, but **against a real opponent carpet is not symmetrically valuable**: the side that *rolled* paid primes to build it; the side that *walks on it* gets free mobility.

**Reinforcement from competitive-intel §4 X-2:** top teams "force us into k=1 rolls by prime-blocking" — they plant primes on our roll trajectory. This says **in the real opponent distribution, opp moves are anti-correlated with our roll plan**, the opposite of what frozen-belief α-β assumes.

**Why this is more structural than it looks.**
- The 19-feature linear heuristic has NO feature for "carpet cells within opp's 2-step reach." It has F3/F4 (global primed/carpet counts, dead in self-play), F17 (our dead primes), F24 (opp's dead primes via mirror), but nothing representing "my big roll just opened a highway for opp."
- Even with F22 (prime-steal), the signal is "I can steal their primes" — not "they can walk my carpet." Asymmetric error — we over-roll in zones opp can exploit, because the eval has no term punishing it.
- **BO can't discover this feature — it can only tune what exists.** This is a missing-feature problem, not a weight problem.

**Impact estimate from data.** Loss analysis Carrie shows we have **more big rolls (21% vs 4%) yet lose**; Michael shows Rusty has **zero big rolls** and beats us. Our k≥4 rolls produced +13 pts/game but lost anyway, meaning the net-of-opp-exploitation value is significantly lower than `CARPET_POINTS_TABLE[k]`. Conservative estimate: **big rolls in opp-reachable zones are worth 40-50% of nominal; we price them at 100%.**

- **Expected ELO impact:** **+10 to +25** from adding F25 "carpet-strip-within-2-of-opp" penalty and/or clamping `immediate_delta` for carpet moves at leaf by `(1 - opp_reach_factor)`.
- **Complexity:** **S-M** (new feature, BO-tunable; OR inline heuristic penalty without feature space change).
- **Risk of breaking existing play:** **Low-Medium** (new feature is additive; inline penalty at leaf is safe but invalidates weights if other features shift).

---

## §2 — Recommended Order (42h Budget)

**Rationale:** deadline proximity, BO-compatibility (PING-FIRST on RattleBot/*.py), and "don't ship an unshippable change with no paired-match data" dominate.

### Phase 1 — Hours 0-8 — Low-risk, high-value (ship-or-die)
1. **BS-3 light**: inline heuristic penalty — at leaf, subtract `0.5 * opp_reach_factor * new_carpet_count` where `opp_reach_factor = popcount(new_carpets within Manhattan-2 of opp_worker) / max(1, popcount(new_carpets))`. 15 LoC, no new feature, no BO disturbance. **Paired-match 40 games vs FloorBot + 15 live scrims vs Carrie**; ship if WR up.
2. **Opening PRIME hardening** (F-3 companion): extend `_ply_zero_prime` to plies 1 and 2 under the same "prime if legal" rule. Loss-forensics shows Carrie/Rusty open PRIME-PRIME-PRIME; we still intersperse PLAIN after F-3. 10 LoC. **Low risk.**

### Phase 2 — Hours 8-24 — The "opponent is not a minimax demon" fix
3. **BS-2**: replace opp's negamax minimization at even-parity depths with a greedy opp-move model (1 ply, pick opp move with max `immediate_delta + cell_potential_bonus_for_opp`). Gate behind `SEARCH_ASSUME_GREEDY_OPP = True`. This is the highest-expected-ELO change that doesn't require belief-structure rewrite. **Must wait for BO exit + need new test `test_greedy_opp_vs_minimax_matches_on_greedy_opp`.**
4. **Kill half the heuristic**: the 19-feature BO is known-noisy (ARCH_CONTRARIAN §2 Challenge 1). Ship a 10-feature variant **as a B-branch submission** post-BO: drop F3, F4, F8, F18; merge F14/F15/F16 into one (pick F15 exp-decay); drop F5 (redundant with F14). Re-run a **short** BO on 10 dims (3-4h budget vs 19-dim's 12h). If time permits.

### Phase 3 — Hours 24-42 — Opportunistic, high-risk/high-reward
5. **BS-1 light (static variant)**: *remove* all belief-derived features from the leaf eval (F11, F12, F13, F14, F15, F16, F18, F19, F20). They're constant-in-tree so they act as per-root bias only. Replace the SEARCH gate with a **proper root-policy layer** that evaluates belief separately. This stops the tree from pretending to reason about information. Complexity is medium but the change is isolated. **Only ship if Phase 1-2 has opened a paired-match gap.**

### DO NOT DO (in 42h)
- Full expectiminimax with rat-chance nodes (ARCH_CONTRARIAN rightly calls this v0.5).
- Any HMM edit. It's the cleanest code we have.
- Any additional BO run on the 19-feature space — we'll fit more noise.
- Opponent-specific exploits (Rusty-profile bot, Michael-profile bot). Too narrow, too few replays.

---

## §3 — One Bold Swing

### The Swing: **Ditch α-β entirely. Ship a 2-ply expectiminimax-lite + rollout-hybrid.**

**What it would look like.**
- At root, enumerate our legal moves (usually 6-10 after k=1 filter).
- For each root move, forecast, then enumerate opp's likely moves (top-3 under a greedy opp model).
- For each `(our_move, opp_move)` pair, forecast and run a **short biased Monte Carlo rollout** (8-12 plies, each side plays greedy + small noise, the rat moves via T each ply, belief is updated inside the rollout).
- Aggregate: value of our_move = `min_opp_move expected_rollout_score_diff`.
- Budget the rollouts by time_left: 40-80 rollouts per `(our, opp)` pair in a 3-6s budget, totaling ~200-400 rollouts per root turn.
- SEARCH is a legal root action, rolled out exactly like other moves (its +4/−2 resolves inside the rollout against the actual sampled rat position).

**Why it might actually work in 42h.**
- **Models the actual game structure**: belief evolves, rat moves stochastically, SEARCH is handled uniformly, opp's real behavior is approximated by greedy-plus-noise (which matches top-5's actual play style per competitive-intel).
- **Doesn't need a good heuristic** — point differential at rollout end IS the value. Heuristic-risk drops to zero.
- **Fixes BS-1, BS-2, BS-3 simultaneously**: belief evolves in rollout (BS-1 ✓), opp is greedy (BS-2 ✓), opp walking on our carpets actually costs us in the rollout (BS-3 ✓).
- **Numeric estimate**: a biased-greedy rollout is ~50-100µs per ply with numpy belief updates, so 8-ply rollout ~0.8ms, ~3000 rollouts/s, ~15k rollouts per 6s turn. With 10 `(our, opp)` pairs that's 1500 rollouts/pair — statistically meaningful.

**Risk/reward.**
- **Risk: HIGH.** Completely new search code. 8-12h implementation minimum. Invalidates all BO work. Testing is hard — no existing test oracle. A bug ships a broken bot on April 19.
- **Reward: could be +100-200 ELO if done right.** Actually matches the game's real structure. Would also generate much cleaner scrimmage signal than tuning 19-dim noise.
- **Mitigation:** ship as a **separate bot** (RattleBot-rollout) alongside v0.4.1; run 30 paired scrims vs FloorBot and 10 vs Carrie; only promote if it beats v0.4.1 head-to-head. Keep v0.4.1 as insurance.

**Recommendation on the swing.** **Attempt it if and only if a dedicated dev-agent with 10h of focused time is available**. One person working on Phase 1-3 in this doc + one person prototyping the rollout bot in parallel is the only configuration where this is rational. A solo effort should do Phase 1-2 and ignore the swing.

---

## §4 — What I'm Not Saying

- Not saying v0.4 is wrong. F-1/F-2/F-3 were correctly identified and correctly shipped.
- Not saying BO is useless. It IS tuning noise on a 19-dim correlated space but would be fine on a 6-8 dim clean space.
- Not saying to rip out α-β before we have a rollout bot beating it. Ship what works; stretch what might.
- Not saying top-5 teams are brilliant — they're *simpler* than us, and that's the lesson. "Solid 1-ply greedy with belief-aware SEARCH gating" seems to be enough to hit Carrie-tier. Complexity for complexity's sake is our failure mode.

---

## §5 — TL;DR For The Team-Lead

| # | Blind Spot | ELO | Fix Effort | Ship by |
|---|------------|-----|-----------|---------|
| BS-1 | Belief frozen in tree — features constant-at-root; SEARCH invisible to search | +20 to +40 | M-L | Phase 3 (hrs 24-42) |
| BS-2 | Modeling opponent as minimax when real opps are greedy | +15 to +40 | M | Phase 2 (hrs 8-24) |
| BS-3 | No opp-reachability penalty on our carpets | +10 to +25 | S | Phase 1 (hrs 0-8) |
| **Bold Swing** | Replace α-β with 2-ply + biased-rollout hybrid | ±100-200 | L (10h+) | Parallel track only, insurance: keep v0.4.1 |

**Do Phase 1 tonight.** It's safe, small, hits the Carrie/Rusty losing pattern directly, and buys the right to do Phase 2.

**End of CONTRARIAN_APR18.**
