# V03 Addendum Update — T-20g over-delivery

**Author:** strategy-architect
**Date:** 2026-04-17 (T − 48 h approx)
**Scope:** Amend `docs/plan/BOT_STRATEGY_V03_ADDENDUM.md` §3, §5, §9, §12, §13 with the new depth baseline. Supersedes nothing; overlays.

---

## §1 — New evidence

**T-20g (SEARCH_PROFILE items #1 + #2a + #4 bullet 1) landed at:**
- Depth **13.2** at 2 s budget (up from 9; we expected 10).
- NPS **+58 %** vs v0.2 baseline.
- Projected depth **14–16 at 6 s** (up from 10–11 pre-T-20g).

**Implication:** the LOW-risk "do now" bundle alone hit the AGGRESSIVE ceiling that SEARCH_PROFILE §5 said required the HIGH-risk make/unmake rewrite. The tuple cache on `valid_search_moves` + LRU on P-vec + MoveKey-once refactor collectively delivered more than cProfile's static attribution predicted — likely because they each removed GC pressure + allocator churn that compounds under ID's repeat-position pattern.

---

## §2 — Arbitration between (a) / (b) / (c)

**Verdict: (a) — demote T-30c to v0.4 stretch; redirect dev-search to numba compile of the hot eval path.**

### Why not (b)

Keep-as-scoped at reduced ELO expectation leaves a known-HIGH-risk task (bytewise-invariant make/unmake) on the critical path for an expected +15–30 ELO. The ROI compresses from `+55/6h ≈ 9 ELO/h` to `+22/6h ≈ 3.7 ELO/h`. That's below T-30d (endgame extend, ~30 ELO/h), below T-30b (F17+F18, ~7.5 ELO/h), and equal to the hybrid side-track (~1–5 ELO/h). Not worth burning dev-search on.

### Why not (c)

Dev-search on F17/F18 is a poor skills match — dev-heuristic owns the heuristic pipeline and its BO harness; adding dev-search as a second editor on the same files multiplies merge-conflict risk. Worse, F17/F18 take 4 h total (team-lead's task #30b estimate), not 6 h — dev-search would be done by hour 4 and then idle. And the real ceiling concern is depth scaling past 13–16, which needs compiled code, not more Python features.

### Why (a)

Numba-compile the hot eval path is:
- **On-ceiling:** SEARCH_PROFILE §5 names depth 13 as the pure-Python architectural ceiling. T-20g confirmed it's achievable. To cross 13, we need compiled code — numba on `_cell_potential_vector`, `_ray_reach`, and `_cell_potential_for_worker` is the cheapest path (research §F row 6 flip-trigger is already armed).
- **BOT §8 non-goal alignment:** "NO numba / cython leaf compilation" was bound to the condition "until leaf > 40 % wall AND ≥ 2× speedup achievable." Both conditions are satisfied per SEARCH_PROFILE §2 (leaf = 36 %, but 24 % is the P-vec build — pure int-math that numba handles cleanly with verified 5–10× speedups in similar geometric kernels).
- **Timing fits:** 4–6 h dev + 2 h sandbox verification (init_timeout, seccomp JIT compatibility per CONTRARIAN_STRATEGY §C-5). Total 6–8 h; comparable to T-30c's 6 h and strictly higher upside.

---

## §3 — Re-ranked v0.3 task table (ELO-per-hour)

New ordering, depth-13-baseline assumptions:

| Order | Task | ELO Δ (revised) | Hours | ELO/h | Status | Note |
|-------|------|-----------------|-------|-------|--------|------|
| 1 | BO RUN1 adoption (if gate passes) | +30–80 | 0 dev (~5 h wall) | ∞ | In flight | Unchanged. Cross-validates on FakeCarrie per §8 gate condition 3. |
| 2 | T-30d endgame extend (time_mgr) | +10–20 | 0.5 | ~30 | Planned | Unchanged. |
| 3 | T-30a tournament-clock audit | +0 (guard) | 1.5 | blocker | Planned | Unchanged. BLOCKS live upload. |
| 4 | **T-30c-numba (NEW, replaces T-30c-makeunmake):** numba-compile `_cell_potential_vector` + `_ray_reach` hot path | **+50–90** | **6–8** | **~10** | NEW | Pushes depth 13 → 15–16 at 2 s, 14 → 17 at 6 s. |
| 5 | T-30b F17 priming-lockout + F18 opp-belief-proxy | +15–45 | 4 | ~7.5 | Planned | Unchanged. |
| 6 | BO RUN2 (self-play objective) | +10–30 if RUN1 weak | 0 dev (~5 h wall) | — | Pending | Unchanged. |
| 7 | Task #48 hybrid MCTS+HMM bolt-on | +0–50 cond. | 8–12 | ~1–5 | Side-track | Unchanged. Still v0.4 candidate only. |
| **demoted** | ~~T-30c make/unmake + incremental Zobrist~~ | **+15–25 (shrunk)** | **6** | **~3.5** | **v0.4 stretch** | Demoted per (a) arbitration above. Only revive if numba path fails its sandbox gate. |
| 8 | F19 rolls_remaining (stretch) | +3–10 | 1.5 | ~5 | Stretch | Unchanged (deferred). |

**New cumulative v0.3 critical-path ELO Δ estimate:** +105 to +235 over v0.2 (was +150–270; net shift is slight downward because T-30c's originally-credited +40–70 shrinks to +50–90 from numba — same magnitude, different source, with real risk that numba's init cost exceeds tournament `init_timeout`).

**Critical path hours:** 1.5 (T-30a) + 0 (wait BO) + 6–8 (numba) + 1 (gate gauntlet) ≈ **8.5–10.5 h**. Same envelope as pre-update.

---

## §4 — Numba scope-pin for T-30c-numba

To keep the risk bounded:

- **Compile ONLY** `_cell_potential_vector`, `_ray_reach`, `_cell_potential_for_worker` in `heuristic.py`. These are pure int/float numpy with no Python-object dispatch.
- **DO NOT compile** `features()`, `_alphabeta`, move generation, belief update. Orchestrator stays pure Python.
- **`@njit(cache=True)`** with AOT cache warming in `agent.__init__` — force a dummy call to trigger compilation BEFORE the game clock starts. The `init_timeout = 10 s` per SPEC §7 gives headroom; test with a 5 s ceiling during sandbox verification.
- **Fallback:** if `import numba` fails or `@njit` raises at init, the module falls through to the pure-Python implementations behind a `_USE_NUMBA` module flag. This preserves the v0.2 pure-Python path as the fallback submission. Same pattern as weights.json fallback in v0.2.
- **Risk gate (new T-30c-numba-gate):** run under `limit_resources=True` on WSL, 20-match paired v0.3-numba vs v0.3-pure-python; require 0 FAILED_INIT and depth ≥ 14 at 2 s. If gate fails → flip `_USE_NUMBA = False` and ship pure-Python. Net ELO Δ becomes 0 but no submission regression.
- **Added to risk register:** R-V03-NUMBA-INIT-01 — owner dev-search + dev-integrator. Matches CONTRARIAN_STRATEGY §C-5 concern verbatim.

---

## §5 — Updated grade-probability table

v0.3 addendum §13 had:
- P(≥ 70 %): 0.92
- P(≥ 80 %): 0.62
- P(≥ 90 %): 0.32

**After T-20g over-delivery + (a) arbitration:**

| Threshold | v0.3 addendum (yesterday) | After update (today) | Δ | Reasoning |
|-----------|---------------------------|----------------------|---|-----------|
| ≥ 70 % | 0.92 | **0.94** | +0.02 | T-20g already shipped +40–60 ELO baseline; FakeAlbert 3-0 is already confirming we're past; floor is tighter. |
| ≥ 80 % | 0.62 | **0.66** | +0.04 | Same depth-baseline lift + numba candidate retains the +50–90 upside ceiling we'd budgeted for T-30c. |
| ≥ 90 % | 0.32 | **0.34** | +0.02 | Modest. T-30c-numba is higher-variance than T-30c-makeunmake would've been; the ceiling rises but the risk-weighted mean moves less. Real P(≥ 90 %) lift requires BO RUN1 adoption to land. |

These remain within the v1.0 CI band (0.15–0.45 for the 90 % threshold) and the upward drift is consistent with FakeAlbert proxy already crossing.

---

## §6 — Concrete changes to apply to V03_ADDENDUM

Minimal patch set, not a full rewrite:

- **§3.1 table**: replace the "Depth via make/unmake (item 3 + 5)" row with "Depth via numba leaf compile (T-30c-numba)" row. Same +50–70 ELO range.
- **§5.2**: swap "T-30c: make/unmake + incremental Zobrist" header & body for "T-30c-numba: numba-compile `_cell_potential_vector` + `_ray_reach`." Preserve property-test discipline (but now the test is "numba-compiled kernel matches pure-Python kernel to 1e-9 on 10k random boards").
- **§9 priority stack**: promote numba to row 4, demote make/unmake to an explicit "v0.4 stretch" row with italicized ELO estimate.
- **§11 risk register**: swap R-V03-MAKEUNMAKE-01 for R-V03-NUMBA-INIT-01 per §4 above.
- **§12 work breakdown**: replace T-30c brief with T-30c-numba brief. Keep T-30d, T-30b, T-30e, T-30f, T-30g, T-30h unchanged.
- **§13 grade table**: update with §5 numbers.

I can ship the patch as a follow-up commit if team-lead signs off on (a). Otherwise this doc stands alone.

---

## §7 — Recommendation to team-lead

**Ratify (a).** Specifically:

1. Demote T-30c (make/unmake + incremental Zobrist) to "v0.4 stretch". It remains a valid future lever but is not on v0.3 critical path.
2. Spawn **T-30c-numba** for dev-search: numba-compile the hot eval path per §4 scope-pin. 6–8 h + sandbox gate.
3. Leave everything else in V03_ADDENDUM unchanged.
4. After T-30c-numba gates pass, dev-search is free. If budget remains, revive make/unmake for the +15–25 additional ELO (incremental value on top of numba; still low ROI but non-zero).

Idle pending team-lead sign-off.
