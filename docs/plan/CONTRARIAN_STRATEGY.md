# CONTRARIAN_STRATEGY — Red-team of BOT_STRATEGY.md v1.0

**Author:** strategy-contrarian
**Date:** 2026-04-16
**Scope:** red-team `docs/plan/BOT_STRATEGY.md` v1.0 before dev wave. Blocking exit for PIPELINE Phase 1 per PIPELINE.md line 54.
**Inputs consulted:** BOT_STRATEGY.md (v1.0, all sections), SYNTHESIS.md (A/B/C/D/E/F/G), GAME_SPEC.md, CONTRARIAN_SCOPE.md, RESEARCH_HMM_RAT.md (targeted), RESEARCH_ADVERSARIAL.md (§A.5 / §H / §I), RESEARCH_HEURISTIC.md (§F / §G / §H), STATE.md, DECISIONS.md D-004/005/006.
**Citation convention:** `BOT §X` → BOT_STRATEGY.md section; `SYN §X` → SYNTHESIS.md; `HEUR §X`, `SEARCH §X`, `HMM §X`, `PRIOR §X`, `CON §X` → the respective research doc; `SPEC §X` → GAME_SPEC.md.

**Headline verdict:** BOT_STRATEGY.md is **mostly correct**. The architecture commitment (D-004) is evidence-backed and the module decomposition (D-005) is sane. The FloorBot gate (D-006) has two concrete bugs that need fixing before dev starts. The most dangerous single defect is an **internally inconsistent performance-budget envelope**: a 100 μs leaf cap with 30 k nps throughput cannot both be true, and which one is real drives whether we hit depth 5 or depth 8. I flag 3 MUST-CHANGE items, 6 SHOULD-CHANGE items, and explicitly endorse 10 others.

---

## Section A — Evidence audit (D1–D22)

Columns: `D#` → choice; `OK?` = **Endorse** / **Amend** / **Thin** / **Over-reach**; notes cite the evidence.

| D# | Architect default | OK? | Note |
|----|-------------------|-----|------|
| D1 | α-β + ID + TT | **Endorse** | SEARCH §B.3 5/5; SYN §B1 cross-confirmed; branching b ≈ 6.3–6.8 is directly compatible. No fault. |
| D2 | Belief-as-leaf-potential | **Endorse with caveat** | SYN §B9 / SEARCH §F.1. The "symmetric cancels between max and min" argument in BOT §2.b is **weaker than presented**: HMM §F item 7's "~3 % TV over 6 plies" is quoted but applies to *rat-drift-absent-action*. Once we prime/carpet inside the tree, the cell-type mutation changes the **opponent's** future noise model (BOT §2.b admits this) — that effect is NOT symmetric (opponent gets better sensor info near carpets → can search more efficiently). Accept the decision, but BOT should mark it as **provisional** with a flip-trigger (§B below). |
| D3 | Root-only EV-gated SEARCH | **Endorse** | SEARCH §C.1, HMM §C.4, SYN §B8. |
| D4 | Hybrid max-belief / min-entropy / HEUR F15 | **Amend — minor** | BOT §2.d picks `γ_info = 0.3, γ_reset = 0.5`. HEUR §B.2 / F15 suggests **`γ_info = 0.5, γ_reset = 0.3`** (the opposite pairing — see RESEARCH_HEURISTIC line 472). The architect inverted the starting prior. Easy fix. |
| D5 | hash → killer → history → type → delta | **Endorse** | SYN §B15 direct. |
| D6 | Adaptive 0.6×/1.0×/1.6× + cap 2.5× + 0.2 s safety | **Endorse** | SEARCH §D.5; matches SYN §B14. One refinement in §E below (0.2 s may be optimistic). |
| D7 | numpy first; numba only if >40 % wall & >2× | **Endorse** | SYN §F row 6 directly. |
| D8 | Self-play min-node default | **Endorse** | Matches SYN §B3 default-with-escalation. |
| D9 | d=16 cap | **Endorse** | SEARCH §I-8; inert cap for safety. |
| D10 | No ISMCTS | **Endorse** | SYN §B16; opponent-belief not tracked. |
| D11 | No beam | **Endorse** | SEARCH §I-10. |
| D12 | F2 9-feature linear + CMA-ES | **Thin — CMA-ES feasibility contested** | See §F. The "CMA-ES tuning in v0.2 window" is mis-budgeted vs HEUR §F.2 numbers. |
| D13 | 9 features listed | **Endorse with amendment** | Feature list matches SYN §B3. But BOT §3.4 v0.1 scope lists F1+F3+F4+F11+F12 — **that's 5 features** and drops F5 (cell potential), which HEUR §summary calls "THE 80→90 % lever". Shipping v0.1 without F5 means v0.1 is not even Carrie-strength-capable. See §I. |
| D14 | float64 | **Endorse** | HMM §F-1. |
| D15 | Linear HMM | **Endorse** | HMM §A.3. |
| D16 | FloorBot live from T-60h | **Endorse** | CON §C-1 + D-007 shipped. |
| D17 | Opp-exploit pre-scheduled T-36h | **Endorse** | CON §C-6; matches §G-1 revised cost of 1.5–2 days bounded by scrimmage throughput. |
| D18 | No opening book | **Endorse** | CON §C-2; 648 topologies, defer. |
| D19 | Endgame tablebase last-5-turns v0.5 stub | **Endorse** | CON §C-4, + ~3–5 pp. |
| D20 | Skip matrix ID | **Endorse** | HMM §F-5. |
| D21 | Paired match | **Endorse** | CON §B-3. |
| D22 | Summary stats + lazy full belief | **Amend — `top8` is too small** | See §D. If a feature needs top-3 by *threat proximity* (belief ∩ near-worker), the precomputed `top8` is both too narrow in principle (belief density is heavy-tailed near mid-game) and too wide in the common case. BeliefSummary should expose a **callable** that returns top-k by an arbitrary weighting, rather than a precomputed `top8`. |

**Evidence audit summary:** 18 of 22 decisions are directly supported by SYN/research citations. The weak ones are D2 (endorsed but deserves provisional status), D4 (γ inversion), D12 (CMA-ES timeline), D13 (v0.1 feature-set drops the key lever), D22 (interface over-specified in a way that will be costly to change).

**Drifted-beyond-evidence / "I-think" flags:**

- BOT §1 grade-probability bumps (P(≥ 90 %) from CON's 0.25 → architect's 0.28) cite "CMA-ES and opponent-exploit track committed". Neither has run. This is architect optimism, not evidence. **Not worth reverting** — the delta is small and within CON's own 0.15–0.45 CI — but flag it: v1.0 is presenting un-validated probabilities as committed estimates.
- BOT §2.b's "second-order cell-type effect captured via F4" is an **I-think**. The F4 formula (BOT §2.c item 3) is `opp_prime_line_potential`, not a future-noise-model term. F4 does not capture the effect the architect claims it does.
- BOT §2.e hard-stop "200 ms before engine deadline" — `extra_ret_time = 5 s` is IPC slack, but Python GC + JAX JIT (if used) can produce >200 ms stalls. Not evidence-backed. See §E.

---

## Section B — Provisional vs committed

Decisions the architect committed that should be **provisional with a flip-trigger** rather than locked:

**B-1 (MUST).** D-004 D2 (belief-as-leaf-potential) should be marked provisional. Flip trigger: if tester-local sees that games with > 3 rat captures show ≥ 5 pp worse paired win-rate for our bot vs FloorBot (i.e. the belief-reset events that ARE in the tree as side-effects are being mis-valued), switch to "opponent's root SEARCH as min-node chance node within depth ≤ 2" (the patch BOT §2.b already names as a fallback). **Concrete:** log "games where either player captured rat ≥ 2 times" separately from other games during v0.2/v0.3 tests.

**B-2 (SHOULD).** D-004 D12 (F2 CMA-ES) should have an **explicit grid/Bayesian-opt fallback** committed now, not discovered mid-flight. BOT §2.c names `w_init` as the seed and says "CMA-ES converges in ~300 evaluations" — HEUR §F.2 says ~100 evaluations × 50 matches = 5000 matches ≈ 7 h wall-clock at 5 s/match, which is **already tight** and uses optimistic match-length. Under `limit_resources=True` with tree-search at d≥5, actual match time is 30–60 s/match (2× per side × 240 s max), not 5 s. Realistic CMA-ES cost is **30–60 h**. Commit an explicit **Bayesian-optimization fallback with 50 paired matches per trial and a 20-trial budget** (≈ 10 h at 30 s/match) as the v0.2 method, and use CMA-ES only as a v0.3+ stretch if dev-heuristic finishes v0.2 early. This converts a risk into a planned path.

**B-3 (SHOULD).** D-006 promotion gate item 3 (T-LIVE-1 = 5 live scrimmage vs George, ≥ 3 wins). Pick George because it's the grade-floor, sure — but 3-of-5 has **P(pass | true win-rate = 50 %) = 0.5** and **P(pass | true 70 %) = 0.84**. That's too permissive: a bot that's tied with George will get promoted half the time. Make it **≥ 4-of-5 or best-of-7 with ≥ 5 wins**. (Alternative: keep 3-of-5 but require a parallel 50-match paired LOCAL gate vs George at ≥ 55 %.)

---

## Section C — Gate audit (D-006)

BOT §6 gate has 4 conditions:

### C-1 (MUST-CHANGE). ≥ 60 % paired win-rate over 100 matches — statistically thin

SYN §E R-EVAL-01 says 50 unpaired matches has ±14 pp 95 % CI. **Paired** matches (same T/spawn/seed, only agent differs) cut variance by a factor of ~2–3 (CON §B-3). For 100 paired matches at p = 0.60, σ_paired ≈ √(0.60·0.40 / 100) ≈ 0.049 without pairing; with paired-correlation ρ ≈ 0.6 (typical for identical-seed), effective σ ≈ 0.031. 95 % CI ≈ [0.54, 0.66] — **the gate passes with a true improvement anywhere in the 54–66 % range**. That is fine AS A go/no-go heuristic but the doc presents 60 % as if it's a robust signal — it is marginal.

**Fix:** promote the paired-match gate to **200 matches at ≥ 58 %** (tighter CI: ±4 pp), OR keep 100-match but require ≥ 65 %. CON §B-3 says "400 unpaired ≈ 50 paired for 5 pp detection" — we want to detect a 10 pp improvement over FloorBot, and 100 paired is on the edge. This is a single-number fix; the doc should amend Appendix B accordingly.

### C-2 (ACCEPT). ≥ 200 crashless matches

200 matches, 0 crashes, is a ≈ 99.5 % lower bound on crash-freeness at 95 % confidence (one-sided). That's appropriate for a tournament submission where a single crash = instant loss (SPEC §8). **Not too strict; not too generous.** Endorse.

### C-3 (MUST-CHANGE). T-LIVE-1 opponent choice

Architect picked **George** for the live gate. CON §D-2 notes George is the 70 %-tier bot. But the **promotion threshold we care about** is not "beats George"; it's "doesn't regress vs FloorBot, which already beats George". The right opponent for a live promotion gate is the one whose ELO most closely brackets FloorBot's live ELO — which per D-007 is "100 % vs Yolanda, untested vs George" but we expect to be in the 70 %+ band. **Albert is the relevant bracket** (the 80 % bot), since a RattleBot promotion needs to demonstrate it's at least pushing toward Albert — beating George 3-of-5 tells us only that we match the floor, which FloorBot already does.

**Fix:** change T-LIVE-1 to be `3 of 5 vs George AND ≥ 1 non-loss out of 3 vs Albert`. The Albert-touch is cheap (3 more live matches) and it's what we actually want to know.

### C-4 (MUST-CHANGE). "Auditor sign-off" — vague

BOT §6.1 lists "auditor sign-off on v0.3 code" as one of 4 gate conditions. Nowhere in the doc is this defined. **This turns the gate into a subjective veto.** Concretely, auditor sign-off should mean:

- `docs/audit/AUDIT_V03.md` exists.
- It records that: T-HMM-1/2, T-SRCH-1/2/3, T-HEUR-1/2 all pass; no OPEN severity-Critical audit findings; no TIMEOUT or INVALID_TURN across the 200-match crash gate; FloorBot fallback `emergency_fallback` is wired into every `play()` try/except per BOT §6.2.
- Auditor explicitly approves in the doc (one-line confirmation).

**Fix:** replace "auditor sign-off" in BOT §6.1 with the above checklist.

---

## Section D — Module-interface risks (D-005)

### D-1 (SHOULD). `BeliefSummary` is under-spec'd for heuristic threat-proximity

BOT §2.h fixes `top8: List[Tuple[int, float]]` as the precomputed summary. But:

- HEUR §B.2's "cell potential × distance from worker" formula asks for `min_dist(worker, high-belief-cell)` — which needs **top-k by belief ∩ near-worker**, not top-k by raw belief.
- At mid-game entropy ≈ 3–4 bits (HMM §B.2), belief concentrates in 3–5 cells (most mass < 5 cells). `top8` is over-wide.
- Late-game after a hit, belief re-diffuses to `p_0` (entropy ≈ 5.2 bits) — **8 cells is under-wide**; the real belief is spread across 20+ cells.

**Neither extreme is well-served by a fixed `top8`.** The heuristic will *use the full belief array anyway* — which BOT §2.h does expose lazily — but then `top8` is dead freight.

**Fix:** simplify. `BeliefSummary` exposes:
- `belief: np.ndarray (64,)` (by reference, zero-copy).
- `entropy: float`, `max_mass: float`, `argmax: int`.
- Drop `top8`. If a feature needs "top-k by arbitrary weight", compute it in the leaf — it's 5 μs of sorting 64 floats.

This is a minor API change but it avoids over-commitment in v0.1.

### D-2 (MUST). Undo semantics for SEARCH side-effect on belief

BOT §3.8 lists `Undo` as a future `v0.2+` for make/unmake. But **the SEARCH case has a belief side-effect (reset to `p_0` on hit; zero+renorm on miss) that is NOT inside `apply_move`** (SPEC §2.4 / §10 item 20, SYN §A R-SEARCH-01). BOT §2.b commits to root-only SEARCH so this is OK at the root — **but only if the search code truly never lets SEARCH into `_alphabeta`**.

BOT §3.3 says "SEARCH is NOT in this order" (§2.f) — good — but the v0.2 `_make_move / _unmake_move` pattern (BOT §3.3 v0.2 scope) does not mention SEARCH at all, because SEARCH is excluded. **Gap:** if any refactor ever lets SEARCH into the in-tree move list (even accidentally), make/unmake has no correct undo for belief because **belief is not on the Board**. This is a silent-footgun waiting to happen.

**Fix:** add an invariant assertion. In `search._alphabeta`, after `move_gen` returns moves, `assert all(m.move_type != MoveType.SEARCH for m in moves)`. If that ever fires, we've silently broken the root-only contract. Cost: 1 line.

### D-3 (MUST). TT collision math

BOT §2.g: TT size = 2^20 × 2-slot = 2 M entries. Zobrist stores upper 44 bits as hash-tag (BOT §2.g TTEntry).

- Actual collision rate: after N probes, P(false hit) ≈ N / 2^44 ≈ N / 1.76×10^13. At 50 k nps × 6 s × 40 moves = 1.2 × 10^7 probes/game, P ≈ 7×10^-7 per game. **Tag collisions are not a practical concern.**
- **Bucket collisions (different Zobrist full hash that happen to land in the same 2^20 bucket) ARE more frequent**: birthday-bound on 2 M slots with 10^7 insertions → collisions are common. But the upper-44-bit tag catches these — a probe with mismatched tag = miss. So **TT miss-rate elevates**, which is what BOT §2.g's "always-replace backup slot" is designed for.
- Real question: **TT hit-rate**. SEARCH §I-4 expects 10–30 % at 2^20 with good move-ordering. BOT §2.f puts hash-move first which depends on TT. T-SRCH-3 gates at ≥ 15 %. If the bot is profiling below 5 %, BOT §7 row 7 fires. **Architect has this covered.** Endorse.

**No change needed to the TT spec.** But the "R-TT-COLLISION-01" risk in BOT §9 describes the concern slightly wrong — it's not about **collisions causing wrong values** (the 44-bit tag handles that), it's about **elevated miss rate**. Recommend the risk description text be amended for clarity, not urgency.

### D-4 (SHOULD). Perspective-flip — TT key ambiguity

BOT §2.g lists Zobrist inputs including `is_player_a_turn`. That resolves it: the TT is **keyed by absolute board state + whose turn it is**, not "player to move in negamax frame". Good — this is correct for a negamax search that reverses perspective between plies.

But there's an under-spec: BOT §3.3 describes negamax (`v = -_alphabeta(...)`) which is already perspective-agnostic at the node level. The TT key with `is_player_a_turn` mixed in means **A-to-move and B-to-move are stored separately**, doubling TT pressure. That's correct but worth flagging.

**Recommendation:** BOT §2.g should note explicitly that the TT uses absolute-frame keys, not "player-to-move" keys. Currently it's implicit. Not a bug — just a doc clarity fix before dev-search starts implementing.

---

## Section E — Performance budget reality check

This is **the most important critique** in the entire red-team. The numbers in BOT and its sources are inconsistent, and the inconsistency hides whether we will hit depth 5 or depth 8.

### E-1 (MUST). Leaf-eval budget vs throughput are incompatible

- BOT §3.4 / Appendix B: **≤ 100 μs per leaf eval tournament mode**.
- SEARCH §H table (lines 747–753): expects **30 k nps** and projects depth-8 "just barely in 6 s" at **118 k nodes** (typical with good ordering at b=7).
- At 100 μs per leaf, **max leaves/sec = 10 000**, not 30 000. At 10 k leaves/sec, depth 8 at 118 k nodes = **11.8 s — INFEASIBLE in a 6 s budget**.

The 30 k leaves/sec figure is SEARCH §H's projection with a heuristic assumed to cost "1.5× baseline" = ≈ 33 μs/leaf. HEUR §H.2's 100 μs target, committed to Appendix B, is 3× that. Both commitments cannot simultaneously produce depth 8.

**Arithmetic check.** At 100 μs/leaf ceiling:
- Depth 6: 6 500 nodes / 10 k nps = 0.65 s/move — fits. Easy 8 moves/s.
- Depth 8: 118 k nodes / 10 k nps = 11.8 s/move — **does not fit**.

So we will actually land at **depth 5–6**, not 8, at the committed leaf budget. This isn't a disaster — depth 5–6 is still better than Albert (depth 2–3 inferred) and competitive with Carrie — but **BOT §4 milestones (v0.4 implicitly assumes d≥5, v0.5 assumes d≥6) are OK; the confusing thing is BOT §2.a's "depth 6–8 pure Python is enough".** That "6–8" is optimistic under the 100 μs ceiling.

**Fix:** BOT Appendix B "Heuristic leaf budget: ≤ 100 μs" should be accompanied by "Implied nps: ~10 k leaves/s → projected median reachable depth: 5–6 ply pure-Python, 6–8 with numba leaf compile per §F row 6". The flip trigger for numba (SYN §F row 6) becomes more important — without numba, the 100 μs cap binds us below depth 7.

**Alternative fix:** relax the leaf budget to 50 μs with a 9-feature linear + numpy-vectorized F5/F7 formula. HEUR §H.2 says "stretch: ≤ 50 μs" — if dev-heuristic can hit 50 μs, we get 20 k nps and depth 7–8 is back on the table. This should be the stretch goal, not a footnote.

### E-2 (ACCEPT). HMM update budget of ≤ 2 ms

HMM §E.1–E.4 measured sub-1 ms (HMM line 560: "well under 1 ms per turn … < 40 ms across a full 40-turn game"). BOT §3.2 committed ≤ 2 ms target with 0.5 ms stretch. **The architect is being conservative, not buggy.** This is correct hygiene — build in the slack.

**Endorse. No change.**

### E-3 (SHOULD). Time safety — 0.2 s may be optimistic

BOT §2.e "Hard stop 200 ms before engine deadline". Python GC pauses on a 1.5 GB RSS process can be 100–300 ms under pressure. JAX JIT *first-call* (R-INIT-01) can be 1–5 s — that's mitigated by warmup in `__init__` but if anyone accidentally triggers JIT in `play` (e.g. a new code path the warmup didn't cover), we eat the budget.

**Fix:** bump safety to **500 ms**, matching the `check_win` 0.5 s tie-vs-loss band (SPEC §7). The cost is tiny (100 ms/move across 40 moves = 4 s of wall-clock "wasted"; we win that back with zero TIMEOUT losses). CON §E-2 specifically recommended 500 ms reserve.

---

## Section F — CMA-ES viability

### F-1 (SHOULD). The architect's CMA-ES schedule does not pencil out

**BOT §2.c claim (line 135):** "CMA-ES converges on 9 dims in ~300 evaluations; each evaluation = 50 paired matches = 5 CPU-min at pure-Python speeds."

**HEUR §F.2 reality (line 322):** "~20 samples per generation × 5 generations = 100 weight-vector evaluations × 50 matches each = 5000 matches. At ~5 s/match this is ~7 hours wall-clock; feasible but tight."

Two discrepancies:
1. The architect quoted 300 evaluations; HEUR quoted 100. (300 would be ~21 h at HEUR's own rate.)
2. HEUR's "5 s/match" assumes **George-vs-George** fast-eval matches. Under `limit_resources=True` with tree-search at depth 5–6, matches are **30–60 s long** (40 plies per side × ~0.7 s/turn budget avg, much longer on critical turns). So:
   - 100 evaluations × 50 matches = 5000 matches × 30 s = **42 h**.
   - 100 evaluations × 50 matches = 5000 matches × 60 s = **83 h**.

We have ~60 h total until deadline at plan-ratify time (BOT §4 "T − 72 h" minus Phase 2 ≈ 60 h actual). The full CMA-ES run consumes more wall-time than we have left.

**Parallelization rescue:** the paired-match runner could be parallelized (multiprocessing across CPU cores). On a 4-core laptop, 42 h → 11 h; on 8 cores, ≈ 5 h. That's a hard dependency on **T-17 (tester-local's paired-match runner) being parallelized** — which is not currently spec'd as "must parallelize".

**Fix (the one I recommend):**
1. **Amend T-17 brief:** parallel batch runner, configurable `n_workers = cpu_count()-1`. Confirm on the user's machine.
2. **Replace CMA-ES with Bayesian optimization (BO) or grid-plus-hand as the DEFAULT for v0.2.** BO on 9 dims needs ~30–50 trials × 50 paired matches × 30 s = 45–75 CPU-h sequential, 6–10 h parallelized. Lands just inside budget.
3. **Keep CMA-ES as a v0.3 stretch** — if BO finds a good region and we have > 12 h spare at T-24h, run CMA-ES starting from BO's incumbent.

Verdict: BOT §2.c's CMA-ES-first commit is **wish-casting on budget**. The architect quotes 300 evaluations (wrong number vs HEUR) and 5 s/match (too optimistic for tree-search matches). Downgrade to SHOULD-CHANGE (not MUST) because a cheap alternative (BO / hand-tune + small grid) is already endorsed in BOT §8 non-goal commentary (`CMA-ES only if converges within 10 % of w_init → ship F1 w_init`).

### F-2 (ACCEPT). Killing CMA-ES entirely?

Tempting but wrong. HEUR §G.2 notes the SYN §F row 9 flip "if CMA-ES converges near w_init, ship F1" as the correct bailout. The architect **has** this bailout. And 10 h of tuning *could* yield +30 ELO, which at the 80→90 % band is worth it. **Don't kill CMA-ES; demote it to stretch, substitute BO for v0.2.**

---

## Section G — Sneaky bugs

### G-1 (MUST). SEARCH EV under-counted (the bug HEUR §E.6 warned about)

BOT §2.d `V_SEARCH(loc)` is evaluated at the root using **current belief** `b`. Good.

But BOT §2.d says "the SEARCH option is compared with `BestNonSearchRootValue`, where the tree that produced BestNonSearchRootValue is evaluated against the current (pre-root-move) belief." So the tree's leaves assume **same belief as the root sees**. When the tree is considering a carpet-roll, the leaf belief is today's belief. That's correct for today's decision.

**The bug:** BOT §2.d does NOT say what happens when the opponent searches **during the tree**. If the tree considers a depth-4 line where opp searches at depth 2, the leaf at depth 4 **still uses today's belief** (because belief is not propagated in-tree) — missing the fact that opp's successful search collapses OUR belief (in the game engine we'd reset to `p_0`). So:

- The leaf overestimates F11/F12 (belief max is still today's, not post-reset).
- The search tree **under-prunes SEARCH threats from opponent**: opp's SEARCH in the tree doesn't visibly reset belief at the leaf, so the opp's SEARCH move looks like a dead action to our max-node (no immediate delta to F1, no side effect on our leaf feature). This can cause us to *misvalue positions where opp should search*.

BOT §2.b mentions this via the "opp's root SEARCH as explicit chance node within depth ≤ 2" flip trigger (SYN §C7). Fine — but the **current default doesn't close the bug**, it defers it. HEUR §E.6 explicitly called this out: **"search side-effect must be applied manually".**

**Fix:** For v0.1, document the known-error-case explicitly. For v0.2, add a cheap partial mitigation: when the tree emits an opp-SEARCH move at depth ≤ 2 (the only depths where its side-effect could matter within 6 plies), apply a leaf penalty `−γ_opp_search · b(loc) · F_belief_dependent_value` where the cost is the expected loss of belief-dependent leaf value under reset. This is a ~5 μs leaf adjustment, far cheaper than making opp-SEARCH a real chance node.

Actually — re-reading BOT §2.b: "SEARCH is NOT a child in the tree's move generator (B8)". So **opp-SEARCH is never generated inside the tree at all**. The tree only sees carpet/prime/plain moves for both sides.

**That means the tree is mis-modeling opponent behavior**: it assumes opp never searches. Which is wrong — opp will search when it's +EV. The bot is missing the scenario "opp searches and catches the rat, we lose a big F5 lever because belief reset". This is the same bug HEUR §E.6 named, applied to opp-SEARCH rather than own-SEARCH.

**Verdict:** this is a real but small bug, captured by the existing flip trigger (BOT §2.b last paragraph, SYN §F row 5 "opp captures rat > 40 % of games"). As long as that trigger is MONITORED, it's fine for v0.1. **The must-change is ensuring the monitoring is actually in place** — BOT §4/§5 does not currently define "rat captures per match" as a logged metric. Add this.

### G-2 (ACCEPT). Zobrist include turn-count?

BOT §2.g Zobrist inputs: 4 masks + 2 worker positions + parity + 2 search states. **Turn count is NOT included.**

Is that a bug? The architect is treating two identical board positions as same-TT-key regardless of turn number. But different turn numbers have **different turns_left** which means different leaf V (F11/F12 change if `turns_left = 5` vs `turns_left = 35`). Ideally the TT would include turn_count.

**But:** including turn_count would nearly eliminate TT reuse (each TT entry keyed by exact ply). TT hit-rate would drop to ~0.

The correct move is what BOT does: **key without turn_count**, and accept that leaf V is slightly wrong when the same position repeats with different turns_left. In practice: (a) boards rarely repeat exactly in an 80-ply game; (b) when they do, turn_count differs by at most ~4 (two-move loops), and V-vs-turns_left for a stable heuristic is near-flat far from endgame. Error is bounded.

**Endorse. No change.** But add to BOT §2.g a one-line note: "TT deliberately excludes turn_count to maintain hit-rate; leaves trade small V-error for TT reuse".

### G-3 (MUST). Opponent-search update ordering

BOT §2.h update pipeline:
1. predict(T)
2. opp-search-update
3. predict(T)
4. sensor-update

But **read SPEC §3.3 carefully** (authoritative): "Called at the top of each ply, before the current player's agent is invoked. So the sensor readings always reflect the rat after moving." Specifically:

- Opp's ply: rat moves → opp gets sensor → opp plays (maybe searches).
- Our ply: rat moves → we get sensor → we play.

Between opp's sensor draw and our sensor draw, **the rat moves TWICE** (once before opp's sensor, once before ours). When we wake up for our turn and receive `opponent_search`, we've already missed opp's sensor draw (not observable). Our belief at the start of our `play()` should be: `b_t = [belief we had last turn] · T (opp moves) · [update for opp's action] · T (we move next) · [update for our sensor]`.

BOT §2.h's pipeline as written: predict → opp-search → predict → sensor — **has the opp-search update BETWEEN two predicts**. Is that correct?

Yes, actually. Let me re-verify:
- Start of our `play()` call turn t+2 (0-indexed from our last ply at t).
- Between t and t+2: rat moved → opp sensor → opp acted (maybe searched) → rat moved → (now our play is called, our sensor has been drawn).
- So: predict once (rat moves pre-opp-sensor) → opp-action-update (opp's observable action = search result) → predict again (rat moves pre-our-sensor) → our-sensor-update.

**BOT §2.h has it right.** No bug.

However, an edge case: **on the very first call to `play()`**, there has been **only one** rat-move (the 1000-step headstart already accounts for before-first-move). SPEC §3.3 says rat moves at top of every ply, before `play()` is invoked. So at our first `play()` call (turn_count=0 if we're A, turn_count=1 if we're B), the rat has made exactly one extra move beyond headstart (for A) or two (for B: one pre-A's-sensor, one pre-B's-sensor).

Running the BOT §2.h pipeline unconditionally at t=0 predicts TWICE, giving 2 predicts worth of drift. **At t=0 for player A, there has been only 1 rat move beyond `p_0` — the BOT pipeline would over-predict.**

**Fix:** either run the pipeline correctly from turn t=1 (skip first predict-opp-search block for A's first turn), or initialize `self.belief = p_0 @ T` (one predict applied in `__init__` for player A's first play call). This is a small init bug, but it will ship a ~1-step-off belief for the first few turns.

For player B: `p_0` → predict → (A's sensor, not observed) → A plays → predict → (our sensor). Running the full pipeline once gets us to the right place. So: A's very first call needs a **partial pipeline** (skip the opp-search step because no opp ply happened yet — but actually `opponent_search = (None, False)` which is already a no-op in the pipeline step 2). 

So: at t=0 for A, the pipeline runs predict → no-op → predict → sensor, which applies **2 predicts** when only **1** happened. Bug.

**Fix:** add a guard. If `board.turn_count == 0` (first ply of game for A), skip step 1. Or equivalently: initialize `belief = p_0 @ T` if A, `belief = p_0 @ T` if B (no — B gets called with turn_count = 1, which is after A's one ply and B's rat-move, so 2 predicts is right for B).

Cleanest fix: remove step 1 on the very first call, OR pre-apply one predict in `__init__` and then have the pipeline run steps 2-4 only. The architect chose a 4-step pipeline that is right every turn **except the very first call**. Small bug, easy fix.

### G-4 (ACCEPT). BeliefSummary computed once per turn vs. at each leaf

BOT §2.h: "The search code calls leaf eval with a reference to this summary ... Leaf is expected to use the summary for F11/F12." **BeliefSummary is computed once per our-turn** (the belief doesn't evolve during our search), which is correct. The leaf in any tree node (whether the node is a max or min at depth k) sees the same belief. BOT §2.b calls this "monotone in belief shift" — true enough for go/no-go comparisons, and the consequence is that F11/F12 are **constants across a single `play()` call's tree**.

That's a waste of optimization effort — why have F11/F12 as features at all if they're constant per tree? Because they influence **our root SEARCH decision** (§2.d) and because they may be non-constant in future versions where we speculate on post-SEARCH belief. **Endorse as-is for v0.1**, but flag for v0.3+: if F11/F12 are truly constant per `play()` call, they should be computed **once at root** and applied as a constant bonus to every leaf (save the repeated lookup). Tiny optimization.

---

## Section H — Scope creep and time risk

**BOT §4 milestone schedule:**

| Version | ETA | Build hours | Cumulative |
|---------|-----|-------------|------------|
| v0.1 | T − 62 h | 10 | 10 |
| v0.2 | T − 48 h | 14 | 24 |
| v0.3 | T − 30 h | 10 | 34 |
| v0.4 | T − 18 h | 8 | 42 |
| v0.5 | T − 6 h | 10 | 52 |

**Current time at ratify:** 2026-04-16 EOD → T-72 h.

**Reality check:**
- v0.1 hours 0–10 (10 h): dev-hmm + dev-search + dev-heuristic + dev-integrator working in parallel. **Parallelism gives ≤ 4× speed** but hours are clock-hours, not CPU-hours. So "10 h of clock time" requires 4 agents working 10 h each = 40 agent-h. OK at clock-level. But integration (T-16, agent.py wire-up) serializes on all three modules. **Realistic clock time: 12–14 h.**
- v0.2 has 14 h clock; scope is TT + killer + history + 4 more features + CMA-ES harness + time-mgr adaptive. **CMA-ES tuning itself needs 5–10 h wall-time (per §F above)** which is **in addition** to dev-time. Realistic clock: 18 h.
- v0.3 has 10 h: CMA-ES-tuned weights (blocked on v0.2 completing tuning), make/unmake refactor, F8 entropy, time-mgr surplus, live upload (Chrome MCP has friction — CON §G-4). Realistic: 12 h.
- v0.4 (T-18h) and v0.5 (T-6h) are **very tight**. F13', F15, numba leaf, endgame tablebase stub, + opponent-specific Carrie-greedy model + live scrimmage A/B. Realistic: if v0.3 slips by 4 h, v0.4 has only 6 h which is not enough.

**Total realistic clock time: 12 + 18 + 12 + 8 + 10 = 60 h + slack. Architect's plan: 52 h + unbudgeted slack.**

**Slippage risk: HIGH.** The schedule is plausible if nothing slips, but no contingency for (a) integration-bug days, (b) Chrome MCP flakiness, (c) one failed test-gate cycle. CON §B-1 specifically flagged this ("research-first is not free with 3 days on the clock") and CON §F-4 recommended force-shipping minimum viable bot by hour 18.

**The minimum to hit 90 % (P(≥ 90 %) ≈ 0.28):**
1. v0.1 shipped and stable (wins 90 % vs Yolanda, 0 crashes).
2. v0.2 with all 9 features (not 5!) + TT + killer/history, paired-match tested at ≥ 55 % vs George.
3. Weights hand-tuned from `w_init` (skip CMA-ES; bank the 10 h).
4. At least one live scrimmage against Albert (≥ 40 %) to confirm "beats Albert bracket".

Everything beyond — F13', F15, numba, endgame, opp-specific, opening book — is **strictly upside**, not on the critical path to 90 %.

**Fix:** BOT §4 should be amended to **explicitly identify the "if things slip by 10 h, what do we cut" fallback**. Right now the plan reads as "ship all milestones"; the contrarian view is "ship v0.3 as the actual submission candidate; v0.4/v0.5 are stretch".

---

## Section I — What to kill

Ranked by expected-hours-saved, with evidence:

### I-1 (STRONG RECOMMEND). CMA-ES → Bayesian opt or hand-tuning
See §F. Saves ~10 h of wall-clock, reduces risk of bad-fitness signal. Demoting CMA-ES to v0.3+ stretch is the right call.

### I-2 (RECOMMEND). v0.1 should ship with all 9 features, not 5
BOT §3.4 v0.1 scope says "F1, F3, F4, F11, F12" — drops F5 (cell_potential_sum), F7 (opp cell potential), F9 (mobility), F10 (opp denial). Per HEUR §summary, **F5 is THE 80→90 % lever**. Shipping v0.1 without F5 means v0.1 is literally incapable of beating Carrie. Worse, weight-tuning on 5 features does not transfer linearly to 9 features — the v0.2 weight vector has to be re-tuned from scratch.

**Fix:** amend BOT §3.4 v0.1 scope to "F1 + F3/F4 + F5/F7 + F11/F12 = 7 features", add F9/F10 in v0.1.1. This makes the first shipped bot Carrie-competitive in architecture.

Cost: ~2 h of extra v0.1 dev-heuristic work. Benefit: the whole rest of the plan is tuning a complete heuristic rather than incrementally adding key features.

### I-3 (OPTIONAL). Opponent-modeling sidecar track (dev-opponent-model at T-36h)
BOT §2.j pre-schedules dev-opponent-model unconditionally. CON §G-1 revised the opp-exploit cost up to 1.5–2 days. **If we don't have scrimmage data on Carrie's actual behavior, opponent modeling is guesswork.** HEUR §D.3 says F4 (opp_prime_line_potential) already captures "don't let opp roll" implicitly — that's what gives the primary bot its P(beat Carrie) ≈ 0.28.

**Decision point:** opp-modeling is high-upside but has **schedule dependency on scrimmage data that may not exist**. The architect's pre-schedule at T-36h is sensible ("start even if we're not sure") but if scrimmage data hasn't arrived by T-30h we should defer it rather than building against a guessed model.

**Fix:** add trigger condition to BOT §2.j: "dev-opponent-model work is spawned at T-36h but BLOCKED on at least 10 live scrimmage matches vs {George, Albert, Carrie} existing. If no live data by T-30h, dev-opponent-model work is suspended and budget redirected to v0.4 heuristic polish."

### I-4 (DO NOT KILL). 9 heuristic features — they each pull weight
CON's own framing asked "is every feature pulling weight, or should v0.1 start with 5?" Answer from research: HEUR §C/§G evaluates the 9 as a minimum complete set. F5 and F7 are the Carrie-style 80→90 % lever. F9/F10 are cheap and capture carpet-denial. F11/F12 are the SEARCH-gating features. F1/F3/F4 are baseline. **Every feature is load-bearing.**

The question isn't "do we need 9?"; it's "when do we ship each one?". See §I-2 above.

### I-5 (DO NOT KILL). Numba leaf compile (it's behind a flip trigger)
BOT §7 row 6 already makes this conditional on profile evidence. Already well-gated. No cut.

---

## Section J — Prioritized list for orchestrator

### MUST-CHANGE before dev wave (orchestrator blocks T-12/T-13/T-14/T-15 until addressed)

1. **(C-1) Tighten promotion gate 1 from "≥ 60 % paired / 100" to either "≥ 65 % / 100" OR "≥ 58 % / 200".** Evidence: CON §B-3 (50-match ±14 pp unpaired CI; 100-match paired ≈ ±5 pp). Current threshold is marginal. Acceptable alternative: explicit SPRT early-stopping rule.

2. **(C-3) Change T-LIVE-1 opponent mix to include Albert.** "≥ 3 of 5 vs George AND ≥ 1 of 3 vs Albert". Evidence: CON §D-2 (George is floor not threshold); the threshold we care about for primary promotion is "at least brushing Albert". Cost: 3 extra live matches.

3. **(C-4) Define "auditor sign-off" concretely in BOT §6.1.** Specifically: `docs/audit/AUDIT_V03.md` exists, enumerates pass/fail of T-HMM-1/2, T-SRCH-1/2/3, T-HEUR-1/2, zero severity-Critical findings open, try/except + emergency_fallback verified in agent.py. Evidence: current wording turns a 4-condition gate into a 3-condition gate + a subjective veto.

4. **(D-2) Add SEARCH-not-in-tree invariant assertion in `search._alphabeta`.** `assert all(m.move_type != MoveType.SEARCH for m in ordered_moves)`. Evidence: SPEC §2.4 + HEUR §E.6 + SYN R-SEARCH-01 — the root-only contract is load-bearing; silent breakage kills the bot. Cost: one line.

5. **(E-1) Reconcile the 100 μs leaf budget with depth projections.** Amend BOT §2.a "depth 6–8 pure Python" → "depth 5–6 pure Python, 7–8 with numba". Amend Appendix B entry with implied nps. Evidence: arithmetic in §E-1 above — 100 μs × 10 k nps doesn't reach d=8 in 6 s. Cost: doc fix + clearer numba-triggering urgency.

6. **(G-3) Fix the pipeline's first-turn predict-count bug.** Skip step 1 when `turn_count == 0` OR pre-apply one predict in `__init__`. Evidence: §G-3 arithmetic. Cost: a 2-line guard.

7. **(G-1 monitoring) Add per-match "rat captures by each side" metric to tester-local's batch runner.** This enables the SYN §F row 5 flip trigger ("opp captures rat > 40 %") to actually fire. Evidence: the trigger exists but there's no instrumentation to detect it. Cost: one counter in the game-log parser.

### SHOULD-CHANGE before v0.3

8. **(D-4 γ inversion) Swap the starting values to `γ_info = 0.5, γ_reset = 0.3`.** Evidence: HEUR §B.2 / §H.3 F15 (line 472) explicitly states `γ_info = 0.5, γ_reset = 0.3`; BOT §2.d has them inverted. Cost: 2 numbers.

9. **(F-1) Demote CMA-ES to v0.3+ stretch; default v0.2 tuning to Bayesian optimization or hand-grid.** Evidence: §F above — CMA-ES at HEUR §F.2's own numbers is 42–83 h wall-clock under tournament-time matches; plan only has ~10 h to allocate. BO with 30–50 trials × 50 paired matches parallelized is 6–10 h. Cost: replan T-20's harness.

10. **(D-1 BeliefSummary) Drop `top8`; keep `belief + entropy + max_mass + argmax`.** Evidence: §D-1 — `top8` is over- or under-wide depending on belief entropy; leaf can compute top-k in 5 μs. Cost: minor API simplification.

11. **(E-3) Raise time safety from 0.2 s to 0.5 s.** Evidence: CON §E-2 recommended 500 ms; GC + JIT pauses can exceed 200 ms; `check_win`'s 0.5 s tie-vs-loss band (SPEC §7) is the natural boundary. Cost: 4 s of wall-clock per game; benefit: zero TIMEOUT losses.

12. **(I-2) Move F5/F7 into v0.1 scope.** Evidence: §I-2 — F5 is THE 80→90 % lever per HEUR §summary; v0.1 without it can't become Carrie-competitive. Cost: ~2 h of extra v0.1 dev-heuristic.

13. **(I-3) Gate dev-opponent-model spawn on existence of live scrimmage data.** Evidence: §I-3 — opp-modeling without scrimmage data is building against a guess. Cost: add one precondition to T-24.

### ACCEPT-AS-IS (architect was right)

- **D1 α-β+ID+TT:** evidence-strong (SEARCH §B.3, SYN §B1). Endorse.
- **D-004 core decision:** architecture choice is well-supported; the issues are in calibration, not direction.
- **D-005 module decomposition:** interfaces are sensible; auditability is good; dev can work in parallel.
- **D-006 FloorBot strategy (promotion model):** the concept is right — live from T-60h, primary promoted behind gate. Only the gate numbers and "auditor sign-off" need sharpening (MUST above). The FloorBot-embedded emergency_fallback is genuinely good defense-in-depth.
- **D2 belief-as-leaf-potential:** correct for branching factor. The symmetry argument is weaker than presented but the decision is still right at 6-ply horizon.
- **D3 SEARCH root-only EV-gated:** correct; no in-tree SEARCH chance-node needed for primary.
- **D5–D11 ordering, time, numba-conditional, opp-model, depth cap, ISMCTS, beam:** all endorsed with direct citation.
- **D14 float64, D15 linear HMM, D17–D20 opening/endgame/matrix-ID:** all directly supported.
- **D21 paired-match:** non-negotiable, correctly mandated.
- **§8 non-goals list:** the "NO X without Y" discipline is exactly what the pipeline needs. Endorse fully.
- **§9 risk register:** coverage is thorough; new NEW-risks added by architect (R-CMA-HARNESS-01, R-TT-COLLISION-01, R-HEUR-INIT-01, R-DEV-COUPLING-01) are well-placed. Only R-TT-COLLISION-01's text could be clearer (see §D-3).

---

## Section K — Overall verdict

BOT_STRATEGY.md v1.0 is a **strong foundation with calibration issues**. The architect correctly synthesized SYNTHESIS.md §G's 10-step agenda into committed decisions, didn't invent architecture out of nothing, and stuck close to the evidence for the big calls (D-004, D-005, D-006 are all defensible). The defects are in:

- **Budget calibration** (§E-1, §F-1): the 100 μs leaf + 30 k nps + 100-eval CMA-ES + 14 h v0.2 window do not all fit. One of them has to give. I recommend: (a) accept depth 5–6 pure-Python + numba flip, (b) replace CMA-ES with BO for v0.2, (c) hold the leaf budget and let depth be the dependent variable.
- **Gate rigor** (§C): the 4-condition promotion gate has three sharp conditions and one vague one ("auditor sign-off"); fix that, and bump gate 1 threshold or sample size.
- **Small bugs** (§G-3, §D-2): first-turn predict-count, missing invariant assertion.
- **Feature-set sequencing** (§I-2): v0.1 drops F5, which is the 80→90 % lever. Fix before dev starts.

Overall: **proceed to dev wave after the 7 MUST-CHANGE items are addressed.** No pipeline halt. The 6 SHOULD-CHANGE items can be addressed mid-flight but should be on the team's radar. The remaining 10+ decisions are endorsed.

My confidence-interval estimate on the architect's grade-probabilities (BOT §1) after factoring the critiques: **P(≥ 70 %) ≈ 0.91 (−0.01 vs architect), P(≥ 80 %) ≈ 0.55 (−0.03), P(≥ 90 %) ≈ 0.25 (−0.03).** The small downward drift reflects CMA-ES budget slippage and the first-turn predict bug; it's within the architect's stated CIs.

**The bot will be stronger because these risks got flagged before code. That's the point.**

---

**End of CONTRARIAN_STRATEGY v1.0.**
