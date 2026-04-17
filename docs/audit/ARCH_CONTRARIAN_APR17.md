# ARCH_CONTRARIAN_APR17 — Fresh-Eyes Architecture Challenge

**Author:** arch-contrarian (spawned by team-lead; single-shot)
**Date:** 2026-04-17
**Scope:** Challenge the `RattleBot` architecture from first principles. No prior bias. Treat α-β + 19-feature linear + HMM as a hypothesis, not a foundation.
**Method:** Static read of CLAUDE.md, HANDOFF.md, agent.py, heuristic.py, search.py, rat_belief.py, move_gen.py, time_mgr.py, AUDIT_V03.md, BOT_STRATEGY v1.1, V04 addendum. No code edits (BO live @ PID 8868).
**Hard constraint acknowledged:** ≤ 56 h to deadline; shipping v0.3-pureonly is already the known-good floor.

---

## §1 — Summary: is the architecture right?

**Mostly yes. The search-depth story is half a lie.** α-β + iterative deepening + Zobrist TT + HMM is the textbook-correct spine for this game, and the audit (AUDIT_V03) shows the plumbing is clean (92/92 tests, leaf p99 = 96 µs, TT hit-rate > 30 % late, emergency fallback verified). The rat's hidden-Markov structure with discrete noise makes a forward filter the obviously correct tool. No contrarian fresh-eyes pass would rip any of this out in 56 hours.

**But the "depth 13.4" number is misleading.** AUDIT_V03 § 3.17 cites leaf p99 = 96 µs pure-Python — that maps to ≈ 10 k leaves/s, or **~10 k × 2 s = 20 k leaves/move budget**. Effective branching post-SEARCH-exclusion and post-k=1-filter is ~7–9. `log_7(20_000) ≈ 5`. Getting to depth 13.4 requires either a TT hit-rate and α-β cutoff-on-first rate near 97 %+ (the telemetry says yes — `test_tt_hit_rate_20_calls` asserts late rate > 30 %, cutoff_on_first > 60 %, team-lead reports 97.9 % cutoff-on-first) OR the "depth" is a PV-length under aggressive reduction, not a full-width tree. Either way, the PRACTICAL expansion is maybe 4–5 full-width plies + TT-assisted PV extensions. **This matters because the heuristic's quality at those shallow full-width plies dominates — we are not deep-searching enough to forgive a bad heuristic.**

**The 19-feature linear heuristic is the place where fresh eyes spot the most hidden assumptions.** Four features are almost certainly dead or actively harmful in self-play (F3/F4 are board-global popcount, perspective-invariant = literally constant in self-play; F18 is constant-per-tree per V03_REDTEAM M-4; F8 is a subset of F20). The remaining 15 are correlated (F5 is in F14/F15/F16; F13 is in F14/F15/F16; F11/F12 are both summaries of the same belief vector). With 40-turn horizons on an 8×8 board, a **small, uncorrelated feature set** + tighter search is a better bet than a big correlated one + BO. BO on 19 dims with 40 trials and noisy 20-paired-match fitness (95% CI ≈ ±10 pp per eval) is fitting noise as much as signal.

---

## §2 — Top 3 challenges to the current design (ranked by ELO delta)

### Challenge 1 (biggest lever): **the heuristic is over-parameterized and under-calibrated. BO on 19 dims won't fix it in 40 trials.**

**Evidence:**
- F3/F4 are board-global popcount (AUDIT_V03 V01-M-03). They are perspective-invariant by design and `test_symmetry` asserts this. In self-play, F3 and F4 contribute an identical constant to both sides and subtract to zero in the search's negamax framing. **Two dead features.**
- F18 is constant-per-tree (V03_REDTEAM M-4 / AUDIT_V03 V03-M-B). It only reads `board.opponent_search` (immutable in-tree) and `belief_summary.belief` (also immutable — not mutated inside the tree per AUDIT_V03 §3.6). So it adds a per-root bias and cannot discriminate between two child leaves. **One non-discriminative feature.**
- F8 is a strict subset of F20. F20 already counts PRIMED+SPACE; F8 only PRIMED. F8 contributes no information F20 doesn't. **One redundant feature.**
- F14, F15, F16 are three different kernels over the SAME `P(c)` vector. Any one of them dominates the others in representational reach if BO sets the weights right; shipping all three with small individual weights is a BO-fitting trap — the three kernels are collinear on typical board states (correlation ≈ 0.8+ in a random-board sample would be my bet), so BO sees a flat ridge of equivalent weight combinations and the resulting weights are unstable between runs.
- F5 is already the worker-position slice of F14/F15/F16. Redundant.

**So of 19 features: 2 are dead (F3, F4), 1 is non-discriminative (F18), 1 is strictly redundant (F8 vs F20), 3 are collinear (F14/F15/F16), 1 is partially covered (F5). Effective informational rank is ≈ 10–12, not 19.**

**Why this matters more than search depth:** with a clean 8–10-dim feature set, BO over 40 trials reaches a tight optimum in the fitness landscape (`skopt` rule of thumb is ~4× dims). With 19 correlated dims, BO sprays noisily.

**Missing features I'd expect to see:**
- **"Turns-left-aware roll feasibility"** — can I actually convert my existing primes to a k≥4 roll in the remaining turns, accounting for the walk to an endpoint? The heuristic has F5 (local) + F14–F16 (distance-weighted), but nothing explicitly connects "primes I own" × "turns-left" × "is the opponent blocking my endpoint walk." In the endgame (turns_left ≤ 10) this matters a lot.
- **"Incremental eval delta from the last move"** — the engine exposes enough state to keep a running score. Current eval re-scans all 64 cells every leaf. `_cell_potential_vector_cached` helps but the LRU key is 4 large ints (~4096 entries × small benefit when trees deviate).
- **A single belief-weighted "best-SEARCH-cell EV" feature** that represents what the root gate already computes. Currently the tree is oblivious to the fact that a near-future SEARCH will be +EV; F19 approximates this but with a radius-2 indicator, not actual EV.

**Expected ELO:** **+30–60** from a cleaner 10-dim feature set + post-BO-run on the smaller set. Risk: medium (feature-set change invalidates a running BO, and we've been burned by this 3+ times per HANDOFF §2). **Time cost:** 6–10 h (drop dead features, merge collinear ones, re-BO; must coordinate with live BO PID 8868).

### Challenge 2: **search shape is wrong for this game. We're running chess-style α-β on an expected-value game with noise and short horizon.**

**Evidence:**
- The game has a **40-turn hard horizon**. Unlike chess, there's no need for depth-20 tactical lines. What matters is the value of position at 4–8 plies out, because `turns_left` truncates everything beyond.
- Rat moves stochastically. The engine exposes `T` but the search tree treats the rat as a **fixed leaf-potential term** (belief at root, passed down immutably per AUDIT_V03 §3.6). So α-β is doing NOT expectiminimax — it's minimax over a position where the chance nodes are collapsed to a scalar at the leaf. This is a known simplification (D-004, documented) but it means the tree never explores "what if the belief concentrates by T+2?" scenarios.
- α-β move ordering is 97.9 % cutoff-on-first per team-lead. That's great for α-β but it says something else: **our heuristic + ordering is so confident about move 1 that the tree almost never explores alternatives.** Equivalent to: "we're mostly playing the 1-ply greedy move with confirmation from a pretty-deep TT-assisted lookup." If the heuristic is wrong, the tree doesn't save us.
- SEARCH is root-only and gated on 3 heuristic conditions (mass > 1/3 + entropy < 0.75·ln 64 + consec_misses ≤ 2). This is a hand-designed filter, not a Bayesian EV comparison. `root_search_decision` DOES compute a Bayesian EV (`EV_search = 6p - 2 + γ_info·dH - γ_reset·p·H(p_0)`) but compares it via `eps_tiebreak = 0.25` to the TT root value — which per V03-L-3 can be 0.0 on time-starved 1-ply budgets.

**What fresh eyes would propose instead:**
- A **depth-capped expectiminimax with an explicit chance node for SEARCH and for the rat's T-step transition between our turns.** The rat's transition is just T^2 between our own plies (T predicts opp → opp ply → T predicts us → our ply). This is a ~5 ms batch operation on a 64-vector. We could afford 10–20 of these per turn. That means the tree could look 2–4 plies ahead while tracking belief evolution, instead of freezing belief at root.
- **PVS (principal-variation search)** with aspiration windows instead of the current full-window root search. The 97.9 % cutoff-on-first says we already believe the PV heavily; PVS exploits this for free.
- **Quiescence-style extension on "prime-and-walk" positions** where a big carpet roll is one step away. These are the critical tactical points — they should not be cut off by depth truncation.

**Expected ELO:** **+20–40** from expectiminimax over the rat (if implemented cleanly) or **+5–15** from PVS + aspiration windows alone (easier, safer). Risk: high for expectiminimax (invariants change; belief-in-tree mutation is the bug class that bit AUDIT_V01 → V03_REDTEAM H-1); low for PVS. **Time cost:** 3 h for PVS, 12–20 h for expectiminimax-over-rat. At 56 h to deadline **only PVS is realistic**; expectiminimax is a post-deadline idea.

### Challenge 3: **time budget is upside-down. We spend most time in early-game normal turns where the heuristic is weakest and the search matters least.**

**Evidence:**
- `time_mgr.classify` marks turns 1–4 as "easy" (0.6× multiplier), turns ≥ 36 as "easy" too. Everything in between is "normal" (1.0×) unless `max_mass ≥ 0.35` (critical, 1.6×) or turns_left ≤ 4 (critical).
- So a typical 40-turn game spends ≈ 32 turns at multiplier 1.0, 4 turns at 0.6, and a few at 1.6. With base = `usable / turns_left` ≈ 6 s, the clock burns roughly evenly.
- **But:** the early game (turns 1–10) has an **almost uniform belief** (entropy near ln 64 = 4.16 nats) — F11/F12/F14/F15/F16 all approach constants. Cell-potential features dominate, and those features have no time-dependence on search depth — a 2-ply search will pick the same prime-extension move as a 6-ply search in the opening. **Deep search buys nothing in the first 10 turns.**
- **And:** the endgame (turns_left ≤ 5) has the 3.5× multiplier and 20 s dedicated ceiling (T-30d/T-30e). Good. But the mid-game (turns 10–30), where both workers are maneuvering around primed lines and the tactical decision space peaks, runs at 1.0× — which means ~6 s per turn, same as a low-information opening turn.

**What fresh eyes would propose:**
- Spend **0.5–1 s** on turns 1–5 (pick the greedy prime-extension, move on).
- Redirect the saved ~20 s into the **tactical mid-game** (turns 12–28) where branching and decision value both peak. That's +0.7 s/turn for 16 turns, ≈ +0.3 ply at d ≈ 5 (branching 7, leaf ≈ 100 µs).
- Tie the multiplier to the **board's prime/carpet density** (a cheap proxy for tactical complexity) rather than turns-left alone.

**Expected ELO:** **+10–25**. Risk: low (time_mgr changes are isolated, AUDIT_V03 §3.5 shows safety reservation is architected). **Time cost:** 2–3 h.

---

## §3 — Top 3 things NOT to touch (clearly working)

### Keep: **HMM forward filter (rat_belief.py).**

Crisp, correct, <200 LOC, p0 precomputed from T^1000 so the rat prior matches the engine, 4-step canonical pipeline with first-turn guard, post-capture reset, 13/13 passing tests. H-1 fix is in place and tested. This is the highest-quality code in the repo. **Do not touch.** Any change here is a credit-card-on-a-hot-stove risk.

### Keep: **Emergency fallback + invariant-based code.**

`agent._emergency_fallback` 4-tier cascade, `_USE_NUMBA=False` default, `_load_tuned_weights` try/except, `search.py:352-354` invariant assertion, the whole "invalid move = instant loss → fail-closed" architecture. With 56 h to go and unknown student opponents on the tournament site, this is the single most valuable property we have. A crash-proof 80%-bot beats a 85%-bot that loses 1 in 50 matches to a timeout. **Do not weaken.**

### Keep: **Bytefight scrimmage pipeline.**

The `tools/bytefight_client.py` auto-refresh flow + CAPSOLVER + 24/7 poller is the ONLY source of real-ELO signal vs reference bots. Per §F-14 directive (memory: "Run bytefight scrimmages 24/7 — never let this sit idle"), this is the only grade-proxy that matters. Any contrarian change should be gated on "did it move the scrimmage-WR needle?", not on local fitness. **Do not redirect the tester off this.**

---

## §4 — Concrete experiments for the next 36 hours

Each: what, expected ELO, risk, time-cost, compatibility with live BO.

### Experiment A: **ablate F3, F4, F8, F18 — ship a 15-feature v0.4a**
- **What:** drop the 4 dead/redundant features; keep W_INIT signs the same, redistribute F8's negative weight into F20. Zero new code — just a shorter vector and a renumbered W_INIT.
- **Expected ELO:** +5 to +15 (removes noise; doesn't add signal).
- **Risk:** low-medium. Invalidates running BO (BO PID 8868 must be killed/restarted with a 15-dim search space). **This collides with PING-FIRST rule.**
- **Time cost:** 3 h (refactor + test + restart BO).
- **Recommendation:** queue this for AFTER BO RUN1-v7 lands. Killing BO now to re-run on 15 dims trades 5 h of BO work for a cleaner fitness landscape. Only do this if BO RUN1-v7 converges with weights that have F3/F4/F8/F18 near zero — that's empirical evidence the features are dead, AND you've already paid the BO compute cost.

### Experiment B: **PVS (principal variation search) + aspiration windows**
- **What:** in `search._alphabeta`, first child uses full window; subsequent children use `(alpha, alpha+1)` zero-window with re-search on fail-high. Aspiration window at root: use prev-iteration value ± 0.5 as (alpha, beta) seed.
- **Expected ELO:** +5 to +15 (pure search speedup; doesn't change eval).
- **Risk:** low. Byte-identical to α-β in principle; well-understood idiom; exact test `test_alphabeta_matches_minimax` can be extended.
- **Time cost:** 3 h + 1 h testing.
- **Compatibility with BO:** PVS edits search.py which is PING-FIRST-protected. Must land AFTER current BO exits.

### Experiment C: **re-skew time budget (easy openings → mid-game)**
- **What:** override `time_mgr._MULTIPLIER` so `turns_left ≥ 30` uses 0.3× (not 0.6×) and turns 30 ≥ `turns_left` ≥ 10 uses 1.3×. Net zero on total time; shifts ~30 s into mid-game.
- **Expected ELO:** +10 to +25.
- **Risk:** low. Well-isolated change in time_mgr.py, testable with existing time_mgr tests.
- **Time cost:** 2 h + 4 h local A/B paired gauntlet.
- **Compatibility with BO:** time_mgr is NOT in PING-FIRST scope per HANDOFF §5 (only agent.py/heuristic.py/search.py and bo_tune.py are). **Can land during live BO.** Verify by re-reading HANDOFF.

### Experiment D: **tighten SEARCH gate to Bayesian EV directly (kill the 3-condition hand-gate)**
- **What:** remove the entropy_ceil + consec_misses + mass_floor conditions in agent.py; always run iterative_deepen + always compute `_best_search_ev`; take SEARCH iff `ev > best_value + eps_tiebreak`. The 3-condition gate was T-20f damage-control for a known search-gate-saturation bug that has since been addressed by `_consec_search_misses` + `apply_our_search` in the belief update (H-1 fix).
- **Expected ELO:** +5 to +15 (correctly SEARCHes at lower-mass, peaked posteriors that the hand-gate blocks).
- **Risk:** medium. V03-L-3 shows `best_value = 0.0` on time-starved 1-ply budgets. The hand-gate is a safety net against SEARCH over-firing in those cases. Must plumb best_value properly (V03-L-3 fix is a prereq).
- **Time cost:** 4 h.
- **Compatibility with BO:** edits agent.py → PING-FIRST blocked.

### Experiment E: **opponent-model-aware search — one ply of "opp plays greedy"**
- **What:** at nodes where it's the opp's turn AND depth ≤ 2, replace full-width α-β child enumeration with a 1-ply lookahead that assumes opp plays the greedy move (like FloorBot / George). This branches only 1 instead of ~7, saving factor-7 at that layer.
- **Expected ELO:** −5 to +20 depending on opponent. Wins against George/Yolanda/FloorBot (who are greedy); likely loses against Carrie (who isn't).
- **Risk:** high. Two mental models of the opp introduce inconsistency in α-β bounds.
- **Time cost:** 6 h.
- **Recommendation:** DON'T DO THIS. Too risky at 56 h. This is a v0.5 idea.

### Experiment F (insurance play, no-risk): **keep shipping v0.3-pureonly + adopt BO weights whenever RUN1-v7 converges**
- **What:** do nothing architectural. Let the BO finish, drop weights into `weights.json`, upload a new zip, run scrimmages. Use any remaining hours on loss-forensics (task #83) and bug-hunts in currently-shipped code.
- **Expected ELO:** +10 to +40 (from BO weights alone, if RUN1-v7 converges).
- **Risk:** minimal.
- **Time cost:** 0.5 h for the adoption gate per V04 §7 contingency plan.
- **This is the strategic baseline.** Everything else must beat this baseline's risk-adjusted EV.

---

## §5 — If I had to pick ONE highest-leverage change

**Experiment C: re-skew the time budget from openings to mid-game.**

Why this over A, B, D:
- **BO-compatible.** Edits `time_mgr.py` which is outside PING-FIRST scope. Can land while BO runs. No wasted compute.
- **Independent of heuristic quality.** Even if BO adopts bad weights, redirecting time from low-information openings to high-information mid-game helps — both settings of the heuristic see the lift.
- **Lowest risk of the high-upside options.** `time_mgr.py` has 12 passing tests. The change is a literal constant-multiplier edit + 2 new tests. No new state, no new invariants, no interaction with the HMM belief or the TT.
- **Empirically testable in 4 h.** Run 100 paired matches vs FloorBot and Yolanda locally; if WR doesn't move, revert. With cheap local validation, the downside is time-cost, not risk.
- **Addresses the architectural mis-fit that fresh eyes notice first.** A 40-turn game with a 240 s budget on a board where the first 5 turns have near-uniform belief and near-identical prime choices should not be spending 6 s × 5 = 30 s (= 1/8 of the global budget) deciding between equivalent opening moves.

**Fallback pick if time budget edits don't move the needle:** Experiment F (ship v0.3 + BO weights + scrimmage 24/7). The architecture is good enough to grade ≥ 80% as-is per V04 §11 grade probabilities; don't rip anything out in the final 36 h.

---

## §6 — What I'm NOT saying

- Not saying expectiminimax is wrong. It's the right long-term answer. Just not in 56 h.
- Not saying to kill α-β. Kept; just noting it's shallower than "depth 13.4" implies.
- Not saying to rewrite the HMM. It's the cleanest code in the repo.
- Not saying BO is useless. It's the right tool for a 6–10-dim problem. It's overmatched by 19 correlated dims.
- Not saying to skip scrimmages for experimentation. The §F-14 directive stands — real ELO is the grade, local proxies are not.

**End of ARCH_CONTRARIAN_APR17.**
