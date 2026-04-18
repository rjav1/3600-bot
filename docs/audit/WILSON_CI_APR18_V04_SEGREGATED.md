# WILSON_CI_APR18_V04_SEGREGATED — v03 vs v04 per-opponent win-rate audit

**LAST UPDATED:** 2026-04-18 (wilson-ci-v04-segregated, ephemeral)
**Scope:** terminal (A_WIN / B_WIN / DRAW) poller lines in `docs/tests/LIVE_SCRIMMAGE_LOG.md`, dedup'd by short match-UUID, self-play excluded, mapped to RattleBot POV and **segregated by submission**:
- `v03` = any `sub` / `opp_sub` matching `RattleBot_v03_*`
- `v04` = any `sub` / `opp_sub` matching `RattleBot_v04_*`

**Driver:** `tools/scratch/wilson_ci_v04_segregated.py` (pure-stdlib, read-only).
**Method:** draws count as 0.5 wins; Wilson 95% CI computed on `(2w+d, 2n)` with z=1.96 (same convention as `WILSON_CI_APR18_0317Z.md`).

**Side assignment (ab-mapping-verifier):** v04 RattleBot is **Side A in 40/40 terminal matches** (confirmed). v03 is Side A in 118/129 and Side B in 11/129 matchmaking rows. The A/B mapping does not differ between the two submissions — the "v04 = always A" observation just means zero matchmaking-initiated rows for v04 as of this audit (v04 has only been fired by us, Rattle as A).

---

## Table 1 — v03 baseline (RattleBot_v03_pureonly_20260417_1022.zip)

### §1.1 Reference staff bots

| Opponent | n | W-L-D | Score | Wilson 95% CI | Grade relevance |
|----------|---|-------|-------|---------------|-----------------|
| **Carrie** | 23 | 4-19-0 | 0.174 | [0.091, 0.307] | >=90% gate |
| **Albert** | 31 | 2-28-1 | 0.081 | [0.035, 0.175] | >=80% gate |
| **George** | 10 | 3-6-1 | 0.350 | [0.181, 0.567] | >=70% floor |

### §1.2 Student-team opponents

| Opponent | n | W-L-D | Score | Wilson 95% CI |
|----------|---|-------|-------|---------------|
| Michael | 15 | 2-12-1 | 0.167 | [0.073, 0.336] |
| Autobots | 13 | 2-11-0 | 0.154 | [0.061, 0.335] |
| Team 57 | 16 | 5-10-1 | 0.344 | [0.204, 0.517] |
| Caspian | 6 | 1-5-0 | 0.167 | [0.047, 0.448] |
| (single-match mm rows) | 15 | 6-9-1 | n/a | too wide |

**v03 aggregate:** n=129, W-L-D = 24-100-5, score = **0.205 [0.161, 0.259]**.

> Note: this supersedes the prior 03:17Z total of n=76 (W-L-D 18-54-4, score 0.263). The log has since grown — new terminal rows for Albert, Caspian, more Carrie, etc. The prior doc's totals are unchanged in *those* cells; this audit simply counts more recent rows.

---

## Table 2 — v04 up to now (RattleBot_v04_archfix_20260418_003411.zip)

### §2.1 Reference staff bots

| Opponent | n | W-L-D | Score | Wilson 95% CI | Grade relevance |
|----------|---|-------|-------|---------------|-----------------|
| **Carrie** | 12 | 3-9-0 | 0.250 | [0.120, 0.449] | >=90% gate |
| **Albert** | 0 | — | — | — | >=80% gate |
| **George** | 0 | — | — | — | >=70% floor |

### §2.2 Student-team opponents

| Opponent | n | W-L-D | Score | Wilson 95% CI |
|----------|---|-------|-------|---------------|
| Team 44 | 13 | 3-10-0 | 0.231 | [0.110, 0.421] |
| Caspian | 10 | 0-10-0 | 0.000 | [0.000, 0.161] |
| team12 (Team 12?) | 5 | 0-5-0 | 0.000 | [0.000, 0.278] |

**v04 aggregate:** n=40, W-L-D = 6-34-0, score = **0.150 [0.088, 0.244]**.

---

## Table 3 — Delta (v04 − v03) per opponent

Only opponents with data in *both* submissions are comparable. Delta CI is approximate (independent-samples normal approx on effective counts `n_eff=2n`; treats draws as 0.5).

| Opponent | v03 W-L-D (score) | v04 W-L-D (score) | Delta (95% CI of diff) | Interpretation |
|----------|--------------------|--------------------|--------------------------|----------------|
| **Carrie** | 4-19-0 (0.174) | 3-9-0 (0.250) | **+0.076 [-0.129, +0.281]** | Point estimate up ~8 pp, but CI straddles 0 — not statistically significant at n_v04=12. **Directionally consistent with the 1/12 -> 3/12 team-lead read.** |
| **Caspian** | 1-5-0 (0.167) | 0-10-0 (0.000) | **-0.167 [-0.378, +0.044]** | Point estimate down ~17 pp; CI grazes 0. Looks like a real regression but n is small. |

Opponents with **only v03 data** (no v04 matches fired yet): Albert, George, Michael, Autobots, Team 57. These are the largest v03 samples and represent the biggest blind spots for the keep/roll decision.

Opponents with **only v04 data** (new after v04 deploy): Team 44 (n=13), team12 (n=5). No v03 baseline, so delta is undefined.

### Aggregate delta (score-level, opponent mix uncorrected)

- v03 aggregate score 0.205 [0.161, 0.259]
- v04 aggregate score 0.150 [0.088, 0.244]
- Naive delta: **-0.055 [-0.149, +0.039]** — v04 looks ~5.5 pp *worse* aggregate, but CI straddles 0. **Opponent mix is materially different** (v04 has heavy Carrie + Caspian + Team 44 weight, zero Albert/George/Michael/Autobots/Team-57). Aggregate comparison is confounded; per-opponent is the only honest signal.

---

## §Analysis

**Where v04 wins vs v03 (directional signal only, not statistically significant):**
- **Carrie: +7.6 pp** (0.174 -> 0.250). Point-estimate WR triples vs what the prior audit reported (0.083 -> 0.250), consistent with team-lead's read. But n_v04=12 is small; one loss swings 8 pp. CI [-12.9, +28.1] does **not** exclude zero.

**Where v04 regresses vs v03:**
- **Caspian: -16.7 pp** (0.167 -> 0.000). Zero wins in 10 matches. This is the clearest regression in the data.
- **Aggregate: -5.5 pp** (0.205 -> 0.150), but opponent-mix confounded (see Table 3 note).

**What we don't know yet (biggest blind spots):**
- **No v04 data vs Albert, George, Michael, Autobots, Team 57.** These are 85/129 = 66% of v03's sample. Whether v04's Carrie lift generalizes to Albert (v03 floor: 0.081) or holds vs George (v03: 0.350) is completely untested. Without Albert/George data, we cannot assess whether v04 clears the >=70% / >=80% gates.

**Consistency with team-lead read:**
- Team-lead starting point: "v04 vs Carrie 3W/9L = 25%, up from v03 1/12 = 8%." Audit confirms **v04 Carrie is 3-9-0 = 25.0%** exactly. The v03 Carrie denominator has since grown from the 12 cited to **23** in the log (4-19-0 = 17.4%), so the jump is actually from 17.4% -> 25.0% (7.6 pp), not 8% -> 25% (17 pp). Still directional, still not significant.
- Team-lead starting point: "v04 aggregate 6W/34L = 15%, v03 18W/54L/4D = 26.3%." v04 matches exactly (6-34-0 = 15.0%). v03 aggregate grew to 24-100-5 = 20.5% since the cited 76-match snapshot. So the v04 regression is -5.5 pp on refreshed data, not -11 pp. Opponent mix differs.

---

## §Recommendation

**WAIT for rollout data — do not activate v04 as final submission yet.**

Reasoning:
1. **Carrie signal is real but underpowered.** Point-estimate WR up ~8 pp is promising, but n_v04=12 and CI straddles zero. Need n_v04(Carrie) >= ~25 before the 95% CI cleanly excludes v03 baseline. Fire more Carrie scrimmages.
2. **Albert gate is unmeasured for v04.** v03's Albert WR is 0.081 (well below 80% gate target). If v04 doesn't meaningfully improve on Albert, the Carrie signal doesn't matter for grade. **Fire 10+ Albert scrimmages immediately** — this is the highest-leverage uncertainty resolver.
3. **George gate is also unmeasured for v04.** v03 George is 0.350; need to know if v04 holds or beats that (>=70% floor requires beating George consistently at point-estimate level).
4. **Caspian regression deserves a loss-analysis pass** before deciding. If v04's Carrie lift came at the cost of generalization vs non-reference bots, that's a tradeoff the team-lead should see before locking.
5. **Do not ROLLBACK to v03** — v03 is materially below all three grade gates (Carrie 0.174, Albert 0.081, George 0.350). Keeping v03 is a guaranteed sub-70% grade. v04 has a plausible path up.
6. **Do not SHIP v05-k1swap sight-unseen** without Albert/George v04 data — we don't know what we're branching from.

**Concrete next action:** queue `>=8 Albert + >=8 George + >=8 Carrie` scrimmages against v04 (24 matches, ~30-45 min) before the Apr 19 23:59 deadline. Re-run this audit at T+45 min. If v04 Albert WR point estimate > v03 baseline (0.081) and v04 Carrie WR holds >=0.20 on n>=20, **KEEP v04**. Otherwise reassess.

---

## §Caveats

1. **Delta CI is normal-approx on independent samples.** For small n (v04 Carrie = 12) the Wilson-of-difference would be slightly wider. Not a game-changer; the point is "CI straddles zero" which both methods agree on.
2. **Opponent mix is materially different** between v03 and v04 samples — aggregate comparison is confounded, only per-opponent deltas are honest.
3. **Log staleness:** this audit reflects the log file only. Live bytefight may have 1-2 poll cycles more data.
4. **v04 "team12" bucket** (n=5, 0-5-0) appears to be a different spelling of "Team 12". I left it separate to avoid incorrect collapsing; re-map if a human confirms.
5. **Side assignment:** v04 is A in 40/40 matches because we initiated all v04 scrimmages. If bytefight matchmaking fires v04 as B later, recheck the mapping.

---

## §Reproducibility

```bash
python tools/scratch/wilson_ci_v04_segregated.py
```

Read-only, no external deps, pure stdlib.

---

**End of WILSON_CI_APR18_V04_SEGREGATED.**
