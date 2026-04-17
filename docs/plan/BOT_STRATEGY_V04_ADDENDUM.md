# BOT_STRATEGY v0.4 Addendum — Post-Numba, Post-BO-RUN1-v2

**Author:** strategy-architect
**Date:** 2026-04-17 (approximately T − 36 h)
**Status:** Proposed. Extends `docs/plan/BOT_STRATEGY.md` v1.1 + V02 addendum + V03 addendum + V03_ADDENDUM_UPDATE_T20G. Supersedes nothing; overlays.
**Scope:** v0.4 planning. BO RUN1-v2 currently in flight (PID 26652, ~5–8 h ETA) so the BO adoption decision is a TOMORROW question; this doc scopes what v0.4 does after BO resolves.

**Inputs consulted (new since V03_ADDENDUM_UPDATE):**
- `docs/tests/LIVE_UPLOAD_005.md` + `LIVE_UPLOAD_006.md` — numba tournament failure disambiguated.
- `docs/tests/NUMBA_GATE.md`, `V03_UPLOAD_CHECKLIST.md`.
- `docs/audit/V03_REDTEAM.md` — H-1 (belief own-capture reset) + M-1/M-2 findings.
- `docs/plan/FAKE_CARRIE_V2.md` — harder proxy; RattleBot-vs-FC2 not yet run.
- `docs/plan/BO_V03_RUN2_SPEC.md` — RUN2 queue spec.
- `docs/plan/BO_TUNING.md` — 12-dim + F17/F18 → 14-dim BO search space for RUN1-v2.
- `docs/research/ALT_ARCH_MCTS.md` — 2-1 prelim still unchanged (N=20 queued).
- Task list: #44 (BO RUN1) complete, #55 (RUN1-v2) in flight, #45 (RUN2) pending, #50 T-30a in flight, #60 H-1 fixed, #62 WSL retest in flight, #64 George scrimmage pending.

---

## §1 — Evidence summary (what changed)

### 1.1 Numba is out, permanently for this deadline

`LIVE_UPLOAD_006.md` §3–§4 is decisive:
- v0.3-pureonly (`_USE_NUMBA=False`) → **VALID, won the validation match in 27 s.**
- v0.3-numba (`_USE_NUMBA=True`, byte-identical otherwise) → **INVALID, failed validation.**
- T-30f flipped default to `_USE_NUMBA=False` for all submission zips.

**Consequence:** our v0.3 shipping target is **depth ~13 at 2 s (pure-Python)**, NOT the 14–15 the numba pivot banked on. That's a **~30–50 ELO loss** vs the V03_ADDENDUM_UPDATE_T20G projection.

Root-cause hypothesis (LIVE_UPLOAD_006 §4): `@njit(cache=True)` likely tries to write a `__pycache__/*.nbi` compile cache, which seccomp blocks. Even `cache=False` risks per-run ~5 s JIT init on a 10 s `init_timeout` budget. This is not fixable by configuration tweaks in the remaining time.

### 1.2 BO RUN1 landed; RUN1-v2 now covers post-H-1 code

BO RUN1 completed (task #44). RUN1-v2 (task #55, in flight) re-runs the tuning over the patched code (post-H-1 fix, post-F17/F18) — because the fitness surface shifted when the belief-reset bug was fixed and features expanded 12→14 dims. **Adoption decision blocks on RUN1-v2 + optional RUN2 self-play cross-validation.**

### 1.3 FakeCarrie_v2 shipped (task #58)

Per FAKE_CARRIE_V2.md §Why:
- Old FakeCarrie = depth-3/4 α-β + H1 heuristic. We beat it 3-0 — too easy.
- FakeCarrie_v2 = **depth 6–8 α-β + Zobrist TT + PV reordering + H1 `Σ P(c)/(1+d)` heuristic + 5-feature linear eval**. This is a tighter proxy for real Carrie's speculated depth-6-to-8 expectiminimax.
- RattleBot-vs-FakeCarrie_v2 paired has NOT YET run (CPU-queued). **This is the authoritative proxy metric for v0.4 gate.** Beating FakeCarrie_v2 ≥ 50 % = plausibly past real Carrie; < 40 % = not past.

### 1.4 MCTS prelim unchanged; N=20 still queued

Task #31 still in flight. Pair 0000 SWEEP (+88 pts) remains the only decisive data. **If N=20 lands with MCTS ≥ 55 % vs v0.3, hybrid becomes must-build.** No adoption decision here yet.

### 1.5 V03_REDTEAM red-teamed v0.3 before ship

`docs/audit/V03_REDTEAM.md` verdict: YELLOW — CONDITIONAL GO. 0 Critical, 1 High (H-1, fixed in task #60), 6 Medium, 7 Low. M-1 (dead surplus-reallocation) and M-2 (TT `turn_count` exclusion) are in v0.4 scope per §4 below.

---

## §2 — Core v0.4 decision: recovering the numba depth loss

Team-lead's ask (a). Four options:

### (i) numpy vectorization of `_cell_potential_vector` — RECOMMENDED PRIMARY

**Verdict: YES, pursue.**

- The hot path is 60 % of leaf time (SEARCH_PROFILE). Current impl is already numpy-backed but uses per-cell Python loop over 4 directional rays with Python int comparisons. A tighter structure — flatten all 64×4 = 256 rays into a single `(256, 7)` int8 scratch matrix and do the max-ray-value reduction in one `np.max(axis=1)` call — plausibly 2–3× faster.
- **Cost:** 3–5 h dev + unit test (pure-Python kernel + vectorized kernel agree to bitwise equality on 10 k random boards).
- **Upside:** +30–60 ELO. If we recover 50 % of the numba loss, we hit depth 13.5–14 pure-Python. Real-Carrie gap narrows.
- **Risk:** LOW. Pure numpy is sandbox-verified (RattleBot v0.2 and v0.3-pureonly already shipped). No new sandbox surface.
- **Flip-trigger:** if the vectorized path benchmarks < 1.5× speedup on the reference position, abandon and ship pure-Python — preserve the known-good build.

### (ii) Cython AOT compile to `.pyd` — REJECTED (too risky at T−36 h)

- Sandbox unknowns parallel numba: seccomp may block native binary loading, or may not. Zero validation experience with `.pyd` on bytefight.org.
- Would need to ship a Linux `.so` (tournament is Linux Python 3.12; our dev machine is Windows), requiring a cross-compile step via WSL, not currently wired.
- Even if it works, same + functions numba compiles. Strictly redundant with (i) at higher risk.
- **If (i) fails to recover depth, REVISIT Cython as a v0.4.1 stretch** — but only if WSL build is verified first.

### (iii) Python 3.12 subinterpreters + threading — REJECTED (wrong problem)

- Subinterpreters solve concurrency, not per-core throughput. Our search is single-threaded by design (α-β's alpha-beta windows don't parallelize well in Python). Adding threads doesn't help depth-per-core.
- Non-zero chance of GIL contention making things worse.
- Off-scope for remaining time.

### (iv) Accept the loss; lean on heuristic + BO weights — PARTIAL (as insurance)

- BO RUN1-v2 in flight could land +30–80 ELO regardless of depth. That's a parallel bet.
- F17 + F18 already shipped in v0.3 → some of the pre-budgeted +15–45 ELO banked.
- **Position: (iv) is the FALLBACK if (i) fails.** Not a rejection.

### Arbitration

**(i) primary + (iv) fallback.** Schedule: dev-search pivots to numpy vectorization after T-30c-numba's kill-switch landed. If vectorization gate passes, we land ~depth 13.5–14 pure-Python. If not, we ship what v0.3 has + BO weights + features.

---

## §3 — v0.4 Feature roadmap

Team-lead's ask (c). Beyond F17/F18 (already shipped).

### F19 — `rat_catch_threat_radius` — SHIPPED v0.4 (semantic revised)

**Shipped definition (canonical as of T-40b / commit 883dadc):**
`F19 = Σ_c belief[c] · I(Manhattan(worker, c) ≤ 2)`. Range `[0, 1]`.
Probability-weighted "rat is near me right now" signal. High F19 = a lot of
belief mass is within 2 Manhattan steps of our worker → a SEARCH at the
argmax is cheap-to-reach and high-EV; the root-level SEARCH gate in
`agent.py` (which triggers on `belief.max_mass > 1/3`) is tightly coupled
to this exact quantity.

**Why (revised):** RattleBot's SEARCH EV is maximised when belief is
concentrated AND that concentration is near our worker. F19 measures
exactly that. F19 high → good (we can cash in), so the weight is
**positive**.

**Cost:** 1 BLAS dot over the precomputed `_NEAR2_MASK[worker_idx]` 64-entry
row. Constant-time (~0.4 µs/leaf). No precompute of T^1/T^2 needed.

**Expected ELO Δ:** +8 to +20 (unchanged estimate from architect's version).

**`w_init`:** sign **positive** (near-belief + near-worker = good), initial
**`+0.3`**. BO bound: **`[0.0, +1.5]`** — positive-half-axis, sign-locked
per BO doctrine.

**Reconciliation note (resolves AUDIT_V04_CHECKLIST §3):** the earlier draft
of this section had F19 as "rat-dispersion urgency" with a negative weight
(−0.15, bounds `[−1.0, 0.0]`). Shipped code went with the team-lead's
T-40b brief which specified `+0.3`. Post-ship review (team-lead
confirmation on 2026-04-17) resolved the mismatch in favour of the
shipped semantic: F19 is OUR belief, not opp's, so it quantifies OUR
ability to cash in the SEARCH-EV opportunity — not any external threat.
"Opp threat" framing has no kinematic grounding (F19 doesn't use opp
worker position at all). Canonical from this commit forward is the
shipped SEARCH-EV-opportunity semantic + positive sign. AUDIT_V04_CHECKLIST
§3 flag may be marked resolved.

### F20 — `opp_roll_imminence` — SHIPPED v0.4 (definition revised)

**Shipped definition (canonical as of T-40b / commit 883dadc):**
`F20 = max over 4 cardinal directions of longest_run(opp_worker, dir)`,
where `longest_run` counts contiguous PRIMED-or-SPACE cells (blocked by
BLOCKED, CARPET, or either worker). Range `[0, 7]`. Integer count, NOT
a point value.

**Strict superset of F8:** F8 counts only already-PRIMED cells; F20 also
counts SPACE. When opp has no current primes, F8 = 0 but F20 > 0 if
there's an empty corridor they could set up in. Captures looming threats
one or two plies out.

**Why (revised from architect's draft):** a raw-run-length signal BO can
tune against is more useful than a pre-scaled `CARPET_POINTS_TABLE[k]`
value (which would pre-embed our assumption of which k matters most).
Shipping the integer means BO sets the weight that maps "run length"
into "points-of-concern"; it lets BO discover e.g. that threats start
mattering at k ≥ 4 rather than us hard-coding it.

**Cost:** O(4) ray scans from opp worker. ~1-2 µs/leaf.

**Expected ELO Δ:** +10 to +25 (unchanged).

**`w_init`:** sign **negative** (big run length = big opp threat), initial
**`−0.6`**. BO bound: **`[−1.5, 0.0]`** — negative-half-axis, sign-locked
per BO doctrine. (Architect's draft suggested `−0.40` + `[−2.0, 0.0]`;
shipped magnitudes scaled for the integer-count feature vs architect's
points-value proposal.)

### F22 — `prime_steal_bonus` — SHIPPED v0.4 (T-40-EXPLOIT-1, commit f63d28b)

**Shipped definition:** bonus when OUR carpet-placement move turns an
opponent-primed cell into OUR carpet. Mechanically the engine resolves
this as a take-over; F22 rewards the eval for foreseeing it in search.
17th feature slot in the pre-EXPLOIT-2 N=17 vector; slot index 16 in
final N=19 vector.

**`w_init`:** `+0.3` (positive). BO bound: `[0.0, +1.0]`, sign-locked.

### F10 — `primed_endpoint_adjacency` — SHIPPED v0.4 (T-40-EXPLOIT-2, **option (b) adjacency-only**)

**Shipped definition (canonical):** count of primed-line endpoints with
run length `k ≥ 2` that are cardinal-adjacent (Manhattan == 1) to OUR
worker. Line-start dedup'd so each maximal primed run is inspected once;
both endpoints counted if the worker is adjacent to both. `k = 1` lines
skipped. Slot 17 in N=19 vector.

**Why (b) over (a) — design rationale locked in per team-lead on
2026-04-17:** the earlier (a) proposal combined a "mobility-denied base"
term with the adjacency bonus. Option (a)'s base was heuristically
duplicative with F15 mobility + F17 lockout: the same "opponent can't
easily clear this run" signal was already being paid out by those
features, so adding it again in F10 would have double-counted. Option
(b) isolates the novel adjacency signal — "WE are positioned to extend
or block the endpoint" — which nothing else in the feature set
captures. BO gets a cleaner axis to tune, and future feature-prune
passes can reason about F10 independently of F15/F17.

**Locked in:** no more F10 reformulations in v0.4. Any future work on
F10 (e.g. restoring the base term, or weighting by `k`, or threat-tier
scaling) is a v0.5 decision.

**`w_init`:** `+0.15` (positive). BO bound: `[0.0, +0.5]`, sign-locked.

### F24 — `opp_wasted_primes` — SHIPPED v0.4 (T-40-EXPLOIT-3, mirror of F17)

**Shipped definition:** F17 semantic applied to OPPONENT side — primed
cells the opponent is now positionally unable to extend or cash. Slot
18 in N=19 vector.

**`w_init`:** `+0.15` (positive: opp-wasted-primes is good for US). BO
bound: `[0.0, +1.0]`, sign-locked.

### F21 — `belief_concentration_rate` — DEFER (conditional include)

**Definition:** `Δ entropy / Δ turn` over the last 3 turns. Positive = collapsing toward a cell → SEARCH about to flip +EV. Negative = diffusing.

**Why:** signals when to hold SEARCH for one more turn vs take it now.

**Problem:** requires turn-history storage in `RatBelief` (currently stateless across calls). Adding state plus the compute is a ~2 h task for a speculative +3–8 ELO signal. **Skip for v0.4.** Revisit in v0.5 only if (i) vectorization passed and (ii) BO weights adopted cleanly.

### Recommendation

- **Ship F19 + F20 in v0.4** (combined ~18–45 ELO, combined 2.5 h dev).
- **Defer F21** — ROI not justified under time pressure.
- **Retune with BO RUN3** on the expanded 16-dim vector AFTER v0.4 code lands. This is a hard dependency: adding features without retuning wastes 50 %+ of the feature signal.

---

## §4 — MCTS hybrid (task #48/T-30): wait-and-see

Team-lead's ask (b). MCTS N=20 paired result is the gate:

- **If MCTS ≥ 55 % vs v0.3-pureonly on 20 paired matches** → hybrid (ALT_ARCH_MCTS §6.2 bolt-on) is worth building. 8–12 h dev for +0–50 ELO conditional upside. Ship as a PARALLEL candidate to v0.4-tuned; pick whichever performs better on final gate gauntlet.
- **If MCTS < 45 %** → hybrid rejected. MCTS stays as evidentiary artifact only.
- **If 45–55 %** → hybrid deferred; the signal isn't loud enough to justify 12 h of dev in the remaining ~30 h.

**No commitment now.** Revisit within 6 h once N=20 lands.

Interim position: DO NOT start task #48 coding. Dev-search time is better spent on §2(i) numpy vectorization, which has a known-sign upside.

---

## §5 — BO RUN2: YES, when RUN1-v2 lands

Team-lead's ask (d).

**Decision: RUN RUN2 per `BO_V03_RUN2_SPEC.md`.**

Reasoning:
- RUN1 (and RUN1-v2) tune against FloorBot — a reactive policy, not an α-β opponent. Risk of overfitting to FloorBot-specific quirks is real.
- RUN2's self-play objective (tuned-RattleBot vs W_INIT-RattleBot) is orthogonal evidence. If BOTH RUN1-v2 AND RUN2 converge on similar weights → strong multi-opponent signal; adopt.
- If RUN1-v2 and RUN2 diverge by > 20 ELO in which vector wins against which opponent → we have an overfitting signal; pick the more CONSERVATIVE weights (smaller ||w − w_init||) as the submission default.
- **Cost:** 5–8 h wall-clock, 0 h dev (already queued per BO_V03_RUN2_SPEC.md). Starts immediately after RUN1-v2 exits.

**Adoption rule for v0.4:**
1. `w_run1v2` wins ≥ +30 ELO vs `w_init` on FloorBot AND ≥ +20 ELO on FakeCarrie_v2 50-pair gauntlet → adopt `w_run1v2` as v0.4 weights.
2. Same holds for `w_run2` → cross-validate. If both win, prefer the one with higher FakeCarrie_v2 score (that's the gap we're trying to close).
3. Neither wins → ship `w_init` (per BOT §7 row 9 flip). v0.4 then relies purely on §2 vectorization + §3 features for ELO gain.

---

## §6 — Opening book revisit: NO

Team-lead's ask (e). TABLEBASE_FEASIBILITY §A.6 rejected opening book at v0.3 planning. Team-lead asks: does depth-13 at 2 s change the calculus?

**Verdict: NO. Opening book still deferred.**

Revised arithmetic:
- Depth 13 in 2 s means each of the 324 canonical opening positions can now be solved at depth 13 in ~ 2 s → **~11 minutes sequential for 324 positions**, not 2.7 h as TABLEBASE_FEASIBILITY projected.
- That sounds compelling. Why reject?

Three reasons:
1. **Our v0.3 α-β already reaches depth 13 in 2 s at runtime on these exact positions.** Precomputing depth 13 and serving it at runtime gives us zero quality lift (we'd already have computed it in the live search). The only savings is the 2 s of wall-time — worth at most 1 ply of extra depth on move 2, probably +3–5 ELO.
2. **Canonical-ization risk.** 324 positions needs vertical-reflection canonicalization. The reflection helper + inverse map for move coordinates is ~80 LOC of fragile code that — if wrong — plays an invalid move. Invalid move = instant loss. SPEC §8. **This is the same class of risk that killed numba.**
3. **Ply-2+ hit rate is 0** for adversarial opponents. The opening book is useful for exactly 1 move (ply 0) and marginally for ply 1 if opp plays our predicted response. Hit rate beyond ply 1 ≈ 0 %.

Revised expected ELO: **+5–10**, not +20–30. Below the ~20 ELO threshold to justify 4–6 h of careful validation work at T−36.

**DEFER permanently for this deadline.**

---

## §7 — Tournament-time contingency: the T−12h path

Team-lead's ask (f). If deadline bites and we have only 12 h left (≈ T−24 to T−12 window with v0.4 work unfinished):

### Minimum v0.4 patch (ship <= 12 h)
1. **Adopt BO RUN1-v2 weights IF gate passes** (§5 adoption rule item 1). 0 h dev.
2. **Ship v0.3-pureonly as-is** (already validated on bytefight.org per LIVE_UPLOAD_006).
3. Skip §2 vectorization, skip §3 F19/F20, skip §4 hybrid, skip §5 RUN2.
4. Net expected ELO Δ vs v0.3: +30–80 ELO (from BO weights alone). Takes us toward FakeCarrie proxy ≈ 45–55 %.

### What we ship if no more progress possible
v0.3-pureonly is already validated (LIVE_UPLOAD_006). Current leaderboard position (need to check ELO_LEDGER for George scrimmage result post-task #64) is our floor. **If nothing else happens, v0.3-pureonly is the final submission**, which per v0.3 addendum §13 should land us in the 80–90 % band.

### Abort criteria for in-flight work
- If vectorization (§2-i) takes > 5 h or fails sandbox gate → abandon, revert to v0.3.
- If RUN1-v2 fails the +30 ELO bar → ship `w_init`; don't re-run RUN3.
- If MCTS N=20 lands but hybrid would take > 8 h → don't start.

---

## §8 — Ranked v0.4 task table (ELO/h)

Assuming BO RUN1-v2 lands within 8 h and vectorization path is viable.

| Order | Task | Expected ELO Δ | Hours | ELO/h | Owner |
|-------|------|----------------|-------|-------|-------|
| 1 | **T-40-BO-ADOPT** — RUN1-v2 adoption if gate passes | +30–80 | 0.5 (gate verification) | **~110** | dev-heuristic |
| 2 | **T-40a** — numpy-vectorize `_cell_potential_vector` + `_ray_reach` | +30–60 | 3–5 | **~11** | dev-search |
| 3 | **T-40b** — F19 + F20 features (+ heuristic weights update) | +18–45 | 2.5 | **~12** | dev-heuristic |
| 4 | **T-40c** — BO RUN3 on 16-dim post-F19/F20 (cross-validate RUN2 + RUN3) | +10–30 | 0 dev (5–8 h wall) | **∞ (compute-bounded)** | dev-heuristic |
| 5 | **T-40d** — FakeCarrie_v2 paired gauntlet (30 pairs) to measure real gap closing | +0 (measurement) | 1 + 4 h runtime | — (gate) | tester-local |
| 6 | **T-40e** — M-1 `end_turn(elapsed)` wiring fix (from V03_REDTEAM) | +2–8 | 0.5 | **~10** | dev-integrator |
| 7 | **T-40-MCTS** — hybrid bolt-on IF MCTS N=20 ≥ 55 % | +0–50 cond | 8–12 | ~1–5 | alt-arch-mcts |
| **demoted** | Cython AOT | speculative | 6–8 | — | DEFER unless §2 fails |
| **rejected** | Opening book | +5–10 | 4–6 | ~1.5 | NOT scheduled |
| **rejected** | Subinterpreters | ~0 | — | — | NOT scheduled |

**Critical path:** T-40-BO-ADOPT (0.5 h gate eval) → T-40a (3–5 h vectorize) → T-40b (2.5 h features) → T-40c (BO RUN3 parallel) → T-40d (gauntlet, 5 h) + v0.4 gate + ship.

**Total critical-path hours:** ~11–15 h + ~8 h BO RUN3 parallel. Fits within T−36 → T−12 window with slack.

---

## §9 — v0.4 exit gate

Promotion from v0.3 (currently live per LIVE_UPLOAD_006) to v0.4 live requires ALL of:

1. **Paired local vs v0.3:** ≥ 55 % over 100 paired matches, `limit_resources=True`. Regression check.
2. **Paired local vs FakeCarrie_v2:** ≥ 50 % over 30 pairs. **NEW — this replaces v0.3 gate's FakeCarrie_v1 gate.** V2 is closer to real Carrie.
3. **Paired local vs FloorBot:** ≥ 75 % over 100 pairs (unchanged).
4. **Paired local vs Yolanda:** ≥ 98 % over 50 pairs (regression guard).
5. **Crash gate:** 0 INVALID_TURN / TIMEOUT / CODE_CRASH across all above matches.
6. **Live scrimmage (T-LIVE-2):** ≥ 4 wins of 6 vs Albert AND ≥ 2 wins of 5 vs Carrie (new live-Carrie gate — if task #64 George-scrimmage evidence justifies it; otherwise drop to ≥ 1 non-loss vs Carrie).
7. **AUDIT_V04.md:** auditor enumerates §8 tasks + M-1 fix + vectorization-equivalence test pass + sandbox-gate pass.

**If any fails:** hold v0.4; v0.3-pureonly remains live. v0.3 is already validated and probably in the Albert/low-Carrie bracket.

---

## §10 — Risk register delta for v0.4

New risks since V03_ADDENDUM_UPDATE:

| ID | Risk | Mitigation | Owner |
|----|------|-----------|-------|
| R-V04-VECTORIZE-01 | numpy vectorization has subtle int/bool broadcasting bug → wrong leaf values, silent regression | Property test: pure-Python kernel vs vectorized kernel agree to bitwise equality on 10 k random boards. Gate before merge. | dev-search |
| R-V04-BO-OVERFIT-02 | RUN1-v2 + RUN2 both win vs FloorBot but regress vs FakeCarrie_v2 | v0.4 gate condition 2 (≥ 50 % vs FakeCarrie_v2) catches this; if fails, ship `w_init`. | dev-heuristic |
| R-V04-MCTS-SANDBOX | If hybrid is built, MCTS's random-number usage may trip seccomp (LIVE_UPLOAD_005 repeat) | MANDATORY sandbox-gate on WSL before any hybrid zip. Lessons learned from numba. | alt-arch-mcts |
| R-V04-TIME-COMPRESS | < 24 h remaining when v0.4 testing begins | §7 minimum-patch path documented. BO-adopt-only ship is 0.5 h. | orchestrator |
| R-V04-FEATURE-OVERFIT | F19 + F20 + new BO run overtune on proxy; real Carrie may have different signal | Cross-validate BO RUN3 winner on: FloorBot, Yolanda, FakeCarrie_v2. Reject if any regress > 5 pp from RUN1-v2 baseline. | dev-heuristic |

---

## §11 — Grade probability update

| Threshold | Post-V03_UPDATE | Post-LIVE-006 numba-fail | v0.4 target | Reasoning |
|-----------|-----------------|--------------------------|-------------|-----------|
| ≥ 70 % | 0.94 | 0.93 | 0.95 | Floor preserved by v0.3-pureonly's live VALID status. Small v0.4 lift from BO + vectorize. |
| ≥ 80 % | 0.66 | 0.62 | **0.68** | Numba loss cost ~4 pp; vectorize + BO recover most. |
| ≥ 90 % | 0.34 | 0.28 | **0.34** | Back to V03_UPDATE level if BO RUN1-v2 adopts AND vectorize lands AND MCTS hybrid either helps or doesn't hurt. |

Deltas are small because v0.3-pureonly is a strong baseline (LIVE_UPLOAD_006 proved it's tournament-valid). v0.4 is about **closing the FakeCarrie_v2 gap**, which — pending data — is the real Carrie gap.

---

## §12 — Handoff

**Orchestrator to spawn (in this order):**

1. **NOW:** tester-local to queue `RattleBot_v03 vs FakeCarrie_v2` 30-pair gauntlet (unblocks §1.3 evidence; provides v0.4 baseline metric). Blocks BO cross-validation.
2. **WHEN RUN1-v2 EXITS:** dev-heuristic runs T-40-BO-ADOPT gate evaluation. Decides weights_v04.json.
3. **Concurrently with 2:** dev-search begins T-40a numpy vectorization. Unblocked after T-30c-numba kill-switch landed (which it is per #63).
4. **AFTER 2 AND 3 LAND:** dev-heuristic begins T-40b F19+F20 features. Launches T-40c BO RUN3 on completed 16-dim code.
5. **WHEN MCTS N=20 LANDS:** orchestrator decides on T-40-MCTS per §4 gate. If 45–55 %, defer. If ≥ 55 %, spawn alt-arch-mcts.
6. **WHEN T-40a + T-40b LAND:** tester-local runs full v0.4 gauntlet (§9 gates 1–5).
7. **AFTER GAUNTLET PASSES:** auditor writes AUDIT_V04.md. Tester-live uploads.
8. **T-6 h:** orchestrator confirms final submission. v0.4 if gate passes, else v0.3-pureonly.

**Files produced/modified by v0.4:**
- `3600-agents/RattleBot/heuristic.py` (vectorization + F19/F20 + N_FEATURES=13)
- `3600-agents/RattleBot/rat_belief.py` (F19 T^1/T^2 reach sets precomputed in __init__)
- `3600-agents/RattleBot/agent.py` (M-1 fix: `end_turn(elapsed)`)
- `3600-agents/RattleBot/tests/test_heuristic_vectorize.py` (NEW property test)
- `3600-agents/RattleBot/tests/test_heuristic_f19_f20.py` (NEW)
- `3600-agents/RattleBot/weights.json` (updated by BO RUN1-v2 / RUN2 / RUN3)
- `docs/tests/RESULTS_V04.md` (NEW — v0.4 gauntlet)
- `docs/audit/AUDIT_V04.md` (NEW)
- `docs/plan/SUBMISSION_CANDIDATES.md` (update with v0.4 zips)

**Explicit non-goals for v0.4 (binding):**
- No Cython (unless §2-i fully fails AND ≥ 10 h budget remains AND WSL cross-compile is already verified).
- No opening book.
- No subinterpreters.
- No new search architecture (MCTS hybrid is a bolt-on, not a rewrite).
- No F21 belief_concentration_rate.
- No changes to `engine/` files (tournament repo is frozen).
- No removal of `_USE_NUMBA=False` default (permanent per T-30f).

---

## §13 — End of addendum

**v0.4 summary:** 6 primary tracked tasks (T-40-BO-ADOPT → T-40a → T-40b → T-40c → T-40d → T-40e) with combined expected ELO Δ **+60 to +150** over v0.3-pureonly live baseline. MCTS hybrid (T-40-MCTS) is a conditional parallel side-track pending N=20 evidence.

**Key arbitrations:**
- (a) Recover numba loss → numpy vectorization primary (§2-i), accept-loss + BO insurance as fallback (§2-iv). Cython REJECTED at this deadline.
- (b) MCTS hybrid → wait on N=20 gate (§4). No dev time committed yet.
- (c) Feature expansion → F19 + F20 YES; F21 DEFER (§3).
- (d) BO RUN2 → YES, auto-starts on RUN1-v2 exit per existing spec (§5).
- (e) Opening book → NO, permanently deferred (§6).
- (f) T−12 h contingency → minimum-patch is BO weights adoption only, 0.5 h dev (§7).

**Grade probability:** P(≥ 80 %) 0.68, P(≥ 90 %) 0.34 after v0.4 — back to pre-numba-failure levels. v0.3-pureonly is already a strong floor at P(≥ 70 %) ≈ 0.93.

**End of BOT_STRATEGY_V04_ADDENDUM.**
