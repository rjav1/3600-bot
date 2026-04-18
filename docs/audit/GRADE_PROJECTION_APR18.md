# Grade Projection — v04 as-of 2026-04-18

**Author:** grade-projection-apr18 (ephemeral)
**Question:** If the submission lock happened right now with v04 active, what grade would we get?
**Deadline:** 2026-04-19 23:59 (~38h remaining)

## 1. Grade-band projection (current v04 data)

| vs | W/L (n) | Rate | Tier threshold | Status |
|---|---|---|---|---|
| George | 9/6 (15) | **60%** | ~70% for 70-tier floor | **BELOW** |
| Albert | 1/16 (17) | **5.9%** | ~80% for 80-tier floor | **FAR BELOW** |
| Carrie | 5/17 (22) | **23%** | ~90% for 90-tier floor | **FAR BELOW** |

Tier probabilities (heuristic, from Wilson CIs):

- **P(≥90% tier): ~0%.** Requires ~90% vs Carrie; 23% observed, n=22. Unreachable.
- **P(≥80% tier): ~0%.** Requires ~80% vs Albert; 5.9% observed, n=17. Unreachable without the F-2 revert landing.
- **P(≥70% tier): ~25–35%.** Needs ~70% vs George; 60% observed. Wilson 95% CI roughly [0.36, 0.81] — straddles the line. A modest true-winrate upward correction or more samples could confirm it, but we are **not** comfortably over the threshold.
- **P(below 70% tier, graded at floor): ~65–75%.** Most likely outcome as-is.

Expected grade band: **low end of the 70% tier or slightly below** — roughly 65–72 out of 100 equivalent, well short of the ≥80 we should be aiming for.

## 2. Why the Albert problem dominates

Even though George is the gating bot for the 70% tier, **Albert at 5.9%** is the real problem:

1. **ELO within-tier scaling.** Grade inside the 70% band is scaled linearly by ELO distance to George and Albert. A 5.9% rate vs Albert pins our Glicko well below Albert's rating, so even if we clear George we land near the **floor** of the 70% tier (~70 pts), not near the top (~80).
2. **Top 5 student teams are all Glicko > Carrie (1910).** Losing 94% of Albert games means our ELO is capped far below every student competitor and both upper reference bots, so there is no path to cross into the 80 tier via ELO drift alone.
3. **v03 baseline was 17% vs Albert** — v04 regressed ~11 pts vs Albert. This is a real regression, not noise (n=17, p < 0.05 vs a 17% baseline).

## 3. v06 F-2 revert — expected impact

If F-2 revert restores Albert to ~17% (the v03 baseline) while preserving v04's George/Carrie gains:

- Albert 5.9% → 17%: lifts us off the absolute Albert floor; ELO recovers ~30–50 Glicko points. Still well short of 80% needed for 80-tier.
- George 60% → assumed ≥60% preserved: close to the 70% gate but still CI-straddling.
- Carrie 23% → assumed ≥23% preserved.
- **Net:** probably moves us from "low-70-tier-or-below" to "comfortably mid-70-tier" — realistic grade 73–78. **Does NOT unlock the 80 tier.** Unlocking 80 requires a genuine Albert-beating strategy (expectiminimax depth / heuristic upgrade), not a regression fix.

## 4. Recommendation (38h left)

**Ship the F-2 revert immediately and lock v06 as the submission candidate.** Reasoning:

- F-2 revert is the single highest-EV change available: low risk (known-good v03 behavior), directly attacks the catastrophic Albert regression, and preserves v04 gains.
- With 38h, there is **not enough time** to design + tune + validate a new Albert-beating heuristic to statistical confidence. Anything aimed at the 80 tier in this window is high-variance and likely lands us *worse* than the F-2 revert.
- **Priority order for remaining 38h:**
  1. (0–4h) Ship F-2 revert, confirm Albert ≥15% on n≥30 scrimmage.
  2. (4–24h) Run **continuous** bytefight scrimmages 24/7 per standing directive — real ELO is the only signal that counts.
  3. (24–36h) If and only if Albert is stable ≥15% AND George ≥65% AND Carrie ≥20%, consider one small heuristic tweak — otherwise **freeze**.
  4. (36–38h) Final activation check on bytefight.org. Do not touch code in the last 2 hours.

**Bold call:** stop chasing the 80 tier. Lock in a solid 75-ish grade instead of gambling it away.
