# BATTLE_ROYALE_N10_APR18 — local paired fork rankings

**Date:** 2026-04-18T10:35Z
**Purpose:** rank our forks locally without burning bytefight budget
**Runner:** `tools/paired_runner.py --n 10 --parallel 1 --no-limit-resources`
**Samples:** N=20 each (10 pairs × 2 matches)

## Matchups

### Rollout vs v04 (main) — from prior run (commit 6bcd3db)
- **10-10 = 50.0%** | Wilson 95% CI [29.9%, 70.1%]
- Pairs: 2-2 (6 split-ties)
- Rollout: 0.084s/move max — 80× compute headroom
- Rat gap: rollout 2.35/match vs main 3.65/match (SEARCH disabled in rollout)

### Rollout vs Greedy_opp — N=20
- **10-10 = 50.0%** | Wilson 95% CI [29.9%, 70.1%]
- Pairs: 3-3 (4 split-ties)
- mean_score_diff (rollout − greedy_opp): −0.X (approx even)

### Greedy_opp vs RattleBot (main) — N=20
- **4-16 = 20.0% for greedy_opp** | Wilson 95% CI [8.1%, 41.6%]
- Pairs: 1-7 (2 split-ties) → sign-test p = 0.07 (borderline significant)
- mean_score_diff: **−9.75** (greedy_opp loses by ~10pts on average)
- **Greedy_opp is significantly weaker than v04 main.**

## Ranking (by Elo-equivalent)

```
main (v04/v09) ≈ rollout > greedy_opp
```

- **v04/v09 main line**: reference / currently Current on bytefight
- **rollout**: even with main in self-play, but disabled SEARCH leaves ~5pts/match on table → plausibly could exceed main if SEARCH re-enabled via belief-sampling (rollout-v2-search-fix work ongoing)
- **greedy_opp (BS-2 fork)**: 20% vs main — convincingly worse. The "top-5 teams are simpler than us" contrarian thesis did NOT pan out in practice. BS-2's negamax→greedy replacement at opp plies over-commits us to moves that assume opp won't counter-play.

## Recommendation

- **DO NOT promote v07-greedy_opp** (UUID bd651aba). Demote to tombstone insurance slot.
- **DO NOT promote v08-rollout as-is** (UUID 6f6cc52c). Only if rollout-v2-search-fix closes the SEARCH gap AND paired N=20 shows ≥60%.
- **Current v09 line is the best option** — keep gathering real-ELO data.
- **Insurance submissions locked**: v04, v05, v08. v07 is discouraged.

## Files
- summary: `3600-agents/matches/br_greedy_vs_v04_n10/summary.json`
- summary: `3600-agents/matches/br_rollout_vs_greedy_n10/summary.json`
