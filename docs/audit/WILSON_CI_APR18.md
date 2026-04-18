# WILSON_CI_APR18 — 95% Wilson Confidence Intervals Per Opponent

**Auditor:** auditor
**Date:** 2026-04-18 (~T−35 h)
**Scope:** all finished, non-self Team-15 scrimmages + matchmaking matches enumerated via `list_matches(page=0..N, size=100)` at analysis time. Read-only.
**Source data:** bytefight `/api/v1/public/game-match` at the moment of the sweep (120 matches scanned, 24 self-play excluded, 10 unfinished excluded → **86 finished competitive matches counted**).
**Method:** for each match with `OUR_UUID ∈ {teamAUuid, teamBUuid}`, flip perspective so result is from our POV. Wilson CI @ z=1.96 on (2·score, 2·n) to handle draws as 0.5 wins. Projected Glicko via inverse-expected-score.
**Driver:** `tools/scratch/wilson_ci_compute.py` (reproducible; no writes, no scrimmages fired).

---

## §1 — Per-opponent table

### §1.1 Named target opponents (from task brief)

| Opponent | n | W-L-D | WR | Wilson 95% CI | Scrimmage / Matchmaking |
|---|---|---|---|---|---|
| **George** | 3 | 1-2-0 | 0.333 | [0.097, 0.700] | 3 / 0 |
| **Albert** | 12 | 2-9-1 | 0.208 | [0.092, 0.405] | 12 / 0 |
| **Carrie** | 12 | 1-11-0 | 0.083 | [0.023, 0.258] | 12 / 0 |
| **Team 61** | 0 | — | — | — | (queued, no results yet) |
| **Michael** | 15 | 2-12-1 | 0.167 | [0.073, 0.336] | 15 / 0 |
| **Autobots** | 8 | 2-6-0 | 0.250 | [0.102, 0.495] | 8 / 0 |
| **Team 44** | 0 | — | — | — | (queued, no results yet) |
| **Team 12** | 0 | — | — | — | (queued, no results yet) |
| **Team 57** | 16 | 5-10-1 | 0.344 | [0.204, 0.517] | 15 / 1 |
| **Team 65** | 1 | 0-1-0 | 0.000 | [0.000, 0.658] | 0 / 1 |

### §1.2 Other opponents observed (matchmaking-only; small n)

| Opponent | n | W-L-D | WR | Wilson 95% CI |
|---|---|---|---|---|
| sabrina carpeter (t80) | 2 | 2-0-0 | 1.000 | [0.510, 1.000] |
| blue | 1 | 1-0-0 | 1.000 | [0.342, 1.000] |
| Random | 1 | 1-0-0 | 1.000 | [0.342, 1.000] |
| Team-39 | 1 | 1-0-0 | 1.000 | [0.342, 1.000] |
| Team69 | 2 | 0-2-0 | 0.000 | [0.000, 0.490] |
| Gold Team | 1 | 0-1-0 | 0.000 | [0.000, 0.658] |
| Hamd | 1 | 0-1-0 | 0.000 | [0.000, 0.658] |
| May the 4 be with us | 1 | 0-1-0 | 0.000 | [0.000, 0.658] |
| cookiemonsters | 1 | 0-1-0 | 0.000 | [0.000, 0.658] |
| miles+ahad | 1 | 0-1-0 | 0.000 | [0.000, 0.658] |
| team 33 | 1 | 0-1-0 | 0.000 | [0.000, 0.658] |

All single-match rows carry ±66 pp CI — cannot be interpreted as signal.

### §1.3 Aggregate snapshot

- 86 total competitive results counted; 24 distinct opponents.
- The top-5 n-opponents (Team 57=16, Michael=15, Albert=12, Carrie=12, Autobots=8) are the only ones where CI width < ±20 pp.

---

## §2 — Projected Glicko-2 rating

Using the baselines from the task brief (COMPETITIVE_INTEL_APR17) and inverting the Glicko expected-score formula `E = 1/(1 + 10^((R_opp − R_us)/400))` → `R_us = R_opp − 400·log10(1/WR − 1)`.

| Opponent | Opp Glicko | WR | Projected our Glicko |
|---|---|---|---|
| Autobots | 1979.2 | 0.250 | **1788.4** |
| George (floor 1910) | 1910.0 | 0.333 | **1789.6** |
| Michael | 2032.6 | 0.167 | **1753.0** |
| Team 57 (est. 1800) | 1800.0 | 0.344 | **1687.7** |
| Albert (floor 1910) | 1910.0 | 0.208 | **1678.1** |
| Carrie (floor 1910) | 1910.0 | 0.083 | **1493.4** |

**Weighted mean projected Glicko (by n):** **~1682** (range 1493-1790).

**Caveats:**
- The Albert/George baselines are **ceilings** (≥70% / ≥80% grade floors translate to opponent Glicko at most 1910). If they're below that, our projected rating rises for those matchups. The low George-Albert WRs we're seeing suggest their actual Glicko is close to the ceiling, not far below.
- Carrie outlier (−200 from mean): either Carrie is actually stronger than 1910, OR our WR vs Carrie is unusually depressed by unlucky variance on n=12 (CI upper bound 0.258 still implies Glicko ≤ 1680 under the 1910 baseline).
- Team 57 / Team 65 Glicko baselines are **estimates** (task brief didn't spec them); the projected numbers for those two rows are the weakest.

**Interpretation:** our true competitive Glicko is currently sitting in the **1680-1790 band** (~150-200 pts below mean student-team baseline ~1950). George/Albert/Carrie together average a projected ~1650 — below all top-5 student teams.

---

## §3 — Grade-probability re-estimate vs ship-plan anchor (0.78 / 0.42 / 0.12)

The ship plan anchor (per V04_SHIP_PLAN) is 0.78 P(≥70%) / 0.42 P(≥80%) / 0.12 P(≥90%).

**Revised given this data:**

| Threshold | Ship-plan anchor | Revised (this data) | Reasoning |
|---|---|---|---|
| ≥ 70% (beat George floor) | 0.78 | **0.55** | George WR = 0.333 on only n=3 with CI [0.097, 0.700] — not enough evidence that we're clearly above 50%. Since ≥70% grade requires us ≈ George's ELO or better, WR < 0.5 vs George = below. n=3 is too thin to promote. Adds uncertainty → revise DOWN. |
| ≥ 80% (beat Albert) | 0.42 | **0.15** | Albert WR = 0.208 on n=12 with CI [0.092, 0.405] — upper bound < 0.5 at 95% conf. We are currently materially below Albert. The projected-Glicko arithmetic agrees. |
| ≥ 90% (beat Carrie) | 0.12 | **0.03** | Carrie WR = 0.083 on n=12 with CI [0.023, 0.258] — upper bound is 0.258, still far below 0.5. Carrie is essentially out of reach without a large v0.4 lift. |

**Caveat:** these are pre-BO-v8 probabilities. BO v8 (PID 23708, due ~17:00 on 2026-04-18) is expected to lift v0.3 by +30-80 ELO. If realized at midpoint (+55 ELO), our projected Glicko jumps from ~1700 to ~1755. That moves:
- George WR: up from 0.333 → ~0.45 (still marginal)
- Albert WR: up from 0.208 → ~0.28 (still <0.5)
- Carrie WR: up from 0.083 → ~0.13 (still miles off)

**Post-BO revised probabilities** (if +55 ELO realized): **0.70 / 0.25 / 0.05**. Still substantially below the ship-plan anchor.

**Implication:** the anchor probabilities (0.78/0.42/0.12) appear **optimistic by +15-25 pp** given current WR data. Either (a) the anchor was set before scrimmage data arrived, (b) additional post-BO patches (T-87/T-88/T-90/T-96) together are expected to deliver much more than +55 ELO, or (c) the anchor includes a first-mover side-adjustment not reflected in our measured WR.

---

## §4 — "If we could only scrimmage ONE opponent more, which?"

**Answer: George.** Here's why, in order of strongest argument:

1. **George's n=3 is the thinnest of any target where we have material data.** CI is [0.097, 0.700] — width 0.60, almost useless. 10 more George scrimmages would shrink CI to ≈ [0.20, 0.55] (width 0.35), which is enough to distinguish "marginally below 50%" from "comfortably above".
2. **George is the grade-floor gate.** If we're ≥ 70% at tournament-freeze, we clear Tier 1 guaranteed; that's the highest-leverage bit we can buy per match. Albert (≥80%) and Carrie (≥90%) are ambition-tier; George is floor-insurance.
3. **George is the fastest to scrimmage** — CLAIR the matchups at Team 15 shows George scrimmages run ~9-13 min vs Carrie's 13-17 min (SCRIMMAGE_LIMITS_INVESTIGATION §2). At 4-5 additional George matches per hour (due to parallel queue), we can get to n=13 within ~3 hours.

**Runner-up rationale:**
- **Team 61 (0 data)** is a strong student team (Glicko 2033). If we have capacity to scrimmage ANY team we have zero data on, Team 61 unlocks the most important unknown. But it costs ~15 matches to reach CI < ±15 pp; George reaches that in 10.
- **NOT Carrie / Albert.** We have decent n already; the data is unambiguous — we lose comfortably vs both. Adding matches there tightens a CI that's already meaningful enough for ship-plan decisions. Low marginal value.
- **NOT small-n opponents (sabrina, blue, Random, etc.).** These are one-off matchmaking results; adding more is noise.

**Concrete recommendation:** next scrimmage budget unit (5 matches) → all George. Stop at n=8; if WR ≥ 0.625 (5/8), we've got credible ≥ 70% signal; if WR ≤ 0.375 (3/8), we need a v0.4 lift to clear floor.

---

## §5 — Methodology notes

- **Draw handling:** draws count as 0.5 wins for WR. Wilson CI computed on integer-valued `(wins_eff = 2·score, n_eff = 2·n)` so a score of 5.5 out of 12 becomes Wilson CI on (11, 24). This is slightly tighter than the Agresti-Coull alternative but matches the common sports-analytics convention.
- **Self-play excluded:** 24 matches where both teams were Team 15.
- **Unfinished excluded:** 10 matches still in `waiting`/`in_progress`.
- **Matchmaking vs scrimmage:** both counted as "competitive results" since both use our real submission vs opponent's real submission and affect leaderboard Glicko. Scrimmage-only subset available in driver output but not broken out here.
- **First-mover bias:** per SCRIMMAGE_WAVE_AUDIT §2, we are always Team A when we initiate (first mover). Matchmaking matches randomize side. We do not correct for this; measured WR absorbs the A-side bias consistently across opponents.

---

## §6 — Reproducibility

```bash
# Re-run at any time (no auth-refresh hazard because list-matches is GET)
python tools/scratch/wilson_ci_compute.py > docs/audit/wilson_ci_raw.json
```

Driver at `tools/scratch/wilson_ci_compute.py`. Uses `BytefightClient.list_matches(page, size=100)` and iterates until a short page returns. Glicko baselines are a dict constant in the driver; update there if new intel lands.

---

**End of WILSON_CI_APR18.**
