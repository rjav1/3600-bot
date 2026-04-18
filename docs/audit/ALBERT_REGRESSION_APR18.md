# ALBERT_REGRESSION_APR18 — why v04 regresses vs Albert (−9pp from v03)

**Auditor:** `albert-regression-sherlock` (ephemeral, 2026-04-18)
**Scope:** All terminal RattleBot vs `Albert.zip` scrimmages in `docs/tests/LIVE_SCRIMMAGE_LOG.md`, plus 6 newly-fetched v04 replays and 11 existing v03 Albert replays in `docs/intel/replays/`.
**Data sources:**
- `docs/tests/LIVE_SCRIMMAGE_LOG.md` — W-L-D ledger per match
- `docs/intel/replays/albert_*.json` (v03, n=11)
- `docs/intel/replays/v04/albert_*.json` (v04, n=6 — fetched this session via `tools/bytefight_client.py replay`)
- `docs/audit/WILSON_CI_APR18_V04_SEGREGATED.md` (refreshed v03/v04 aggregates)
- `docs/audit/LOSS_ANALYSIS_CARRIE_APR18.md` (prior Carrie loss forensics for style/method parity)

**Read-only sherlock mode:** No edits to `RattleBot/*.py` or `tools/*.py` (BO session context respected; no PING check required since only replay-fetch touched tools).
**Sample caveat:** 6 v04 replays (5L/1W) + 13 v04 result-lines (1W/12L). Small n. Directional only.

---

## §1 Summary (TL;DR)

**v04 regresses vs Albert by ~9pp relative to v03**, consistent with the task brief:

| Sample | v03 vs Albert | v04 vs Albert |
|--------|---------------|----------------|
| Full log ledger (WILSON_CI audit, n_v03=31) | 2-28-1 = **8.1%** | 1-12-0 = **7.7%** (n=13) |
| Task-cited subset (early-2026-04-17/18 window) | 2-9-1 = 16.7% (n=12) | 1-12-0 = 7.7% (n=13) |
| Win ratio (Wilson 95% CI) | [3.5%, 17.5%] | [2.1%, 33.4%] |

CIs overlap — the regression is **not statistically significant** in isolation. But the direction matches the task finding, and the **mechanism is visible in the replays**. Note v03's full-ledger baseline is already below the 80% Albert grade gate (**8.1%** vs needed ~80%) — v04 has not materially improved on that, and may have made a specific failure mode worse.

**Root-cause finding:** v04's F-3 (forced PRIME on ply 0) successfully fires against Albert (verified in all 6 replays: A's first move is `prime`). But compounding with F-2 (higher SEARCH threshold) produces a **carpet-rolling collapse**:

| Metric (per-game avg) | v03 Albert matches (n=11) | v04 Albert matches (n=6) | Δ |
|-----------------------|---------------------------|---------------------------|---|
| **Our carpet pts** (A) | **22.9** | **9.2** | **−13.7** |
| **Albert carpet pts** (B) | **7.5** | **13.5** | **+6.0** |
| **Our primes placed** (A) | 16.5 | 14.2 | −2.3 |
| **Albert primes placed** (B) | 15.5 | 17.2 | +1.7 |
| **Our search pts** (A) | +6.0 | +4.3 | −1.7 |
| **Albert search pts** (B) | +8.7 | +8.3 | −0.4 |
| **Our score** | 28.7 | 25.8 | −2.9 |
| **Albert score** | 43.8 | 45.3 | +1.5 |

**Carpet pts flipped ownership by ~19.7 pts/game.** v04 used to out-carpet Albert ~23 vs ~8. Now Albert out-carpets us ~14 vs ~9. Our losses are no longer "tempo-bleed" like vs Carrie — they are **Albert out-priming us, out-rolling us, and scoring decisively via length-3/4 rolls while we cash out short k=2 rolls or can't roll at all**.

---

## §2 Evidence — per-match decomposition

Move decomposition uses proper A/B alternation keyed off `a_turns_left`/`b_turns_left` drops (raw `left_behind[0]` is the pre-ply-0 state, not A's first move).

### §2.1 v04 Albert (n=6 replays, we=A)

| Match | Final A / B | Δ | A: prm/srch(h/m)/crp / crp_lens | B: prm/srch(h/m)/crp / crp_lens | Opening |
|-------|-------------|---|----------------------------------|----------------------------------|---------|
| `3ac8e0e3` | 22 / 42 | **−20** | 12 / 6 (2h/1m) / 4   / [2,2] | 18 / 6 (4h/5m) / 18   / **[4,3,2,1,2,2,1,3]** | A: prime-prime-plain |
| `8e7043a0` | 27 / 48 | **−21** | 17 / 6 (2h/1m) / 4   / [2,2] | 15 / 6 (4h/5m) / 27   / **[4,3,1,2,2,2,3,2,2,2,2]** | A: prime-prime-plain |
| `a5095c3e` | 33 / 37 | −4 | 15 / 0 (1h/3m) / 18  / [2,4,3,3,2] | 19 / −2 (3h/6m) / 20 / [4,2,3,2,2,2,2] | A: prime-plain-prime |
| `c6e9aa2d` | 20 / 46 | **−26** | 10 / 6 (2h/2m) / 4   / [2,2] | 20 / 4 (5h/7m) / 22  / [4,4,2,2,3,2] | A: prime-plain-plain |
| `e34ec7ff` | 13 / 62 | **−49** | 13 / −4 (4h/10m) / 4 / [2,2] | 18 / 18 (5h/1m) / 26 / **[5,3,2,4,2,2]** | A: prime-prime-search |
| `f1a940d9`* | 40 / 37 | **+3** (W) | 13 / 20 (6h/2m) / 7  / [1,2,3,2] | 18 / −2 (1h/3m) / 21 / [5,1,2,3,2,2,2] | A: prime-search-plain |
| **loss aggregate (5)** | **23.0 / 47.0** | **−24.0** | avg 13.4 / 2.8 / 6.8 | avg 18.0 / 6.0 / 22.6 | all prime-ply-0 |
| **contrast: 1W** | 40 / 37 | +3 | 13 / 20 / 7 | 18 / −2 / 21 | prime-ply-0 |

The 5 v04 losses share a **catastrophic carpet pattern**: 4/5 games cap out at **two k=2 carpet rolls = 4 pts**. The sole "decent" loss (a5095c3e) had 18 carpet pts but still lost. The 1 win (f1a940d9) is carried by **search EV of +20** (6 hits / 2 miss), not carpets.

### §2.2 v03 Albert (n=11 replays, we=A; 2W / 8L / 1D)

| Match | Final A / B | Δ | A: prm/srch(h/m)/crp / crp_lens | B: prm/srch(h/m)/crp / crp_lens |
|-------|-------------|---|----------------------------------|----------------------------------|
| `063cb0e7` | 18 / 55 | −37 | 16 / 12 (3h/0m) / 27  / **[4,3,3,3,1,2,2,3,2]** | 14 / 0 / 4   / [3] |
| `4902684f` | 21 / 47 | −26 | 21 / 0 / 26  / **[4,3,2,2,3,4,2]** | 11 / 6 / 4 / [2,2] |
| `6a110e87` | 6 / 49 | −43 | 20 / 8 / 21  / **[2,3,1,2,4,2,2,2,2]** | 12 / −12 / 6 / [2,2,2] |
| `6cab9254` | 23 / 26 | −3 | 15 / −2 / 13 / [3,2,1,3,1,3,1,2] | 17 / −2 / 8 / [2,2,2,2] |
| `97afd501`** | 50 / 29 | **+21** (W) | 17 / −6 / 18 / [2,4,2,2,2] | 16 / 20 / 14 / [2,4,2,3,2,2] |
| `a3800b3b` | 42 / 43 | −1 | 17 / 4 / 22  / [3,4,3,3,2,2] | 16 / 16 / 10 / [2,3,2,2] |
| `bc4ebed5` | 2 / 49 | −47 | 20 / −18 / 23 / [2,2,2,2] | 12 / 6 / 8 / [2,2,3,2,3,1,2,3,3] |
| `bf6447e4`** | 39 / 26 | **+13** (W) | 14 / 8 / 14 / [2,2,3,2,2,2] | 17 / −2 / 14 / [2,2,2,2,2,2,2] |
| `ce3eb525` | 31 / 57 | −26 | 13 / 8 / 10 / [2,2,2,3] | 20 / 10 / 27 / **[5,5,3,1,2,2]** |
| `d8f9b19e` | 43 / 53 | −10 | 15 / 26 / 2 / [2] | 16 / 14 / 23 / [4,4,2,3,2,1,3] |
| `dfcfd25b` | 41 / 41 | 0 (D) | 15 / 18 / 8 / [2,2,3] | 16 / 6 / 19 / [2,2,3,2,3,1,2,3] |
| **loss/draw agg (9)** | 25.2 / 45.6 | −20.4 | avg 15.8 / 7.1 / 16.9 | avg 14.9 / 3.8 / 12.1 |
| **contrast: 2W** | 44.5 / 27.5 | +17 | avg 15.5 / 1.0 / 16.0 | avg 16.5 / 9.0 / 14.0 |

Even in v03 LOSSES, we carpet-rolled 16.9 pts/game vs Albert's 12.1. In v04 losses, we carpet-roll **6.8 pts/game vs Albert's 22.6**. **The carpet engine is backwards in v04.**

### §2.3 Delta-open and trajectory

| Sample | Mean delta-open (ply ≥5 gap) | Mean final Δ | Mean our carpet pts | Mean their carpet pts |
|--------|------------------------------|---------------|----------------------|------------------------|
| v04 losses (n=5) | **12.6** | −24.0 | 6.8 | **22.6** |
| v03 losses+draw (n=9) | **14.7** | −20.4 | 16.9 | 12.1 |

Delta opens around ply 13–15 in both, but in v04 the gap is driven by **Albert rolling carpets**, not by small-prime density.

---

## §3 Hypothesis ranking

### H2 (RANKED #1) — F-2 + F-3 together broke carpet-chain productivity vs Albert
**Likelihood: HIGH. Impact: large (~15 pts/game in losses).**

F-3 forces PRIME on ply 0, giving us a "+1 and a worker adjacent to a prime". F-2 raises the SEARCH gate floor from 1/3 to 0.35. The combination creates a specific weakness:

- Our ply-0 prime establishes a prime cell at our spawn. Albert, going second, primes too — but Albert's heuristic (from `errlog_b` = 12.2–13.0, a stable debug float) is an **expectiminimax with cell-potential heuristic** (per CLAUDE.md §5 Carrie profile; Albert is the next-strongest variant below Carrie).
- With F-2 forcing us to skip low-belief searches, we have fewer "free" burn-turns to let primes accumulate before Albert disrupts them. We end up stuck mid-chain with k=2 rolls as the only cashable primes (see all 5 losses: `crp_lens` is a pair of 2s).
- Meanwhile Albert, playing the OPPONENT role, walks across our early prime without needing to extend their own, and builds long chains on the OTHER side of the board where we can't easily interfere. In `8e7043a0`, Albert rolled `[4,3,1,2,2,2,3,2,2,2,2]` for 27 pts — eleven rolls! — while we got 4 pts.
- **Critical observation:** In v03 Albert losses, our carpet roll LEN distribution included multiple k=3, k=4, and occasional k=5 rolls. In v04 Albert losses, we have ZERO k≥3 carpets in 4 of 5 games. The k=2 rolls dominate to the point that something in the F-3 forced-prime placement + F-2 search-suppression is preventing us from extending prime chains to rolalable length.

Mechanism is not 100% identified from replays alone (would need a trace through `move_gen.py`), but the empirical signature is unambiguous: **forced ply-0 prime places the seed in a position that Albert can more easily disrupt our future prime-extension from**, while F-2 removes the fallback "burn a turn on a search" that kept our prime chain coherent in v03.

### H1 (RANKED #2) — F-3 ply-0 PRIME opening itself exploitable, independent of F-2
**Likelihood: MODERATE. Impact: small-to-medium.**

F-3 is confirmed firing in all 6 v04 replays (A's ply-0 move is always `prime`). But in v03 we ALSO opened with prime in some games (`063cb0e7`, `6cab9254`, `97afd501`, `a3800b3b`, `bc4ebed5`, `bf6447e4`, `dfcfd25b`) and outcomes were mixed (we still won 2, drew 1, lost 5). So prime-ply-0 alone doesn't explain the regression — it has to be the COMBINATION with something else. That "something else" is most plausibly F-2.

### H3 (RANKED #3) — Small-sample noise
**Likelihood: MODERATE. Impact: explanatory-alternative.**

n=13 vs n=31: v03 Wilson 95% CI is [3.5%, 17.5%], v04 is [2.1%, 33.4%]. The overlap is wide. The 12L streak at n=13 has p ≈ 0.57 under the v03 baseline assumption (Wilson), so it is NOT surprising. However, the **mechanistic pattern in the replays** (carpet pts flipping from 23/8 to 9/14) is a per-game effect, not a W-L coin-flip — that makes H2 a more plausible explanation than pure noise.

### H4 (RANKED #4) — Albert's uploaded submission was upgraded
**Likelihood: LOW. No supporting evidence.**

`errlog_b` in v03 Albert replays shows values 12.88, 12.95, etc. In v04 Albert replays: 12.2, 12.4, 12.62, 12.65, 12.88, 13.0. Similar range, same "short decimal float" schema. **No version-string difference in `errlog_b`** (only a number is printed). If Albert had been reuploaded, we'd expect a different errlog format. Also, `opp_sub` in the log is still `Albert.zip` in both eras, with no VAL_OK re-upload for Albert_v2 between v03 and v04 windows. **H4 discarded.**

---

## §4 Recommended fix

**Primary (lowest risk, highest leverage): REVERT F-2 SEARCH threshold back to 1/3.**

- Evidence: v04 search EV (+4.3 pts) ≈ v03 (+6.0 pts) — F-2 did NOT meaningfully reduce wrong-search bleed. But F-2 raised the opportunity cost of information-gathering during prime-chain construction. Our one v04 win vs Albert (f1a940d9) came from 6 correct searches (+20 search EV) — not from F-2 suppression.
- CLAUDE.md §7 notes: *"a single search is also an information-gathering action that updates the belief — sometimes worth taking at lower probabilities late in the game."* F-2 contradicts this in the early/mid-game where it matters most for Albert (who extends primes aggressively and needs us to not waste turns on non-actions).
- Reverting F-2 is a one-line change in `_search_mass_threshold(turns_left)` (per the v04 fix description in `LIVE_SCRIMMAGE_LOG.md:443`). Low code risk.

**Secondary (do NOT ship without testing): keep F-3 for now, but A/B test it against a NO-F-3 baseline.**
- F-3 gives a guaranteed +1 on ply 0 but locks placement. The 5 v04 losses all share ply-0 prime, but the 1 v04 win also does — so F-3 is not a clean causal villain in isolation.
- If F-2 revert alone does not close the −9pp gap in a subsequent 10–15-match scrimmage wave, flip F-3 off as the next probe.

**Do NOT:**
- Do NOT change F-1 (it's a no-op already per `LIVE_SCRIMMAGE_LOG.md:442`).
- Do NOT re-tune BO-only weights against Albert as a fix — the regression is mechanistic (forced-prime interacting with search-gate), not weight-tuning.
- Do NOT ship a v05 with both F-2 revert AND F-3 removal simultaneously — you won't know which helped.

**Concrete next scrimmage wave (after revert):** 10–15 Albert scrimmages against v05 = v04 minus F-2. If WR point-estimate ≥ 15% on n=10, F-2 revert is validated; keep F-3, compare to v04. If WR stays ≤10% on n=10, F-3 is the additional culprit; try v06 = v04 minus F-2 minus F-3.

---

## §5 Key data-format gotcha (for future auditors)

The `pgn` dict in bytefight replays has `left_behind[0]` as the **pre-ply-0 state**, not A's first move. A's real move #k is at `left_behind[idx]` where `idx` is the k-th index where `a_turns_left[idx] < a_turns_left[idx-1]`. B's moves are similarly identified via `b_turns_left` drops. Using the naive `left_behind[0::2]` / `[1::2]` alternation **mis-reports the opening move** (I initially thought all v04 openings were `plain`, but proper indexing shows they are all `prime` — F-3 is firing correctly).

Also: `errlog_a` contains the RattleBot version string (`v0.2` = v03, `v0.4-arch-fixes` = v04). `errlog_b` is just a small float (Albert's internal heuristic debug value).

---

## §6 Reproducibility

```bash
# fetch v04 Albert replays (one-time)
for uuid in 3ac8e0e3-375d-4a6d-a882-fc233a13de4c \
            a5095c3e-2bda-4d74-932e-660c0ccfa972 \
            f1a940d9-d3da-4d2a-abc4-fdaef95d15f6 \
            c6e9aa2d-1e44-47f0-8edd-ce9bc408267a \
            e34ec7ff-6395-49d5-af95-fc3f2e27b028 \
            8e7043a0-16c6-4245-a139-ca191c941f53; do
  short=${uuid:0:8}
  python tools/bytefight_client.py replay --match-uuid $uuid \
    --save docs/intel/replays/v04/albert_${short}.json
done

# decompose (pure stdlib, inline)
python <<'EOF'
# (see §2 tables — decomposition uses a_turns_left/b_turns_left drops
#  to identify A vs B moves, and new_carpets[i] length for roll k)
EOF
```

---

**End of ALBERT_REGRESSION_APR18.**
