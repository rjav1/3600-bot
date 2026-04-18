# ROLLOUT_VS_V042_N20 — paired audit

**Date:** 2026-04-18T08:48Z (runner wall-clock 59 min)
**Runner:** `tools/paired_runner.py --agents RattleBot_rollout RattleBot --n 10 --seed 0 --parallel 1 --no-limit-resources`
**Sample:** 10 pairs × 2 matches = 20 games

## Result

| Side | Agent | Wins | Winrate | Wilson 95% CI |
|------|-------|------|---------|---------------|
| A | RattleBot_rollout | 10 | **50.0%** | [29.9%, 70.1%] |
| B | RattleBot (v0.4.x) | 10 | 50.0% | [29.9%, 70.1%] |

- Paired sign-test: p = 1.0 (no paired-bias signal)
- Pairs: 2 rollout-pair-sweeps, 2 main-pair-sweeps, 6 split-pair ties
- Decisive pairs: 4 / 10
- Mean score diff (A − B): **−2.4 pts** (rollout trails on average by a couple points)

### Errors

- crashes_a (rollout): 0
- crashes_b (main): 1 (minor — one pair errored out for main)
- timeouts / invalid_moves: 0 on both sides

### Rat captures

- rollout: **47** (2.35 / match)
- main:    **73** (3.65 / match)
- Gap: main catches 26 more rats across 20 matches (+26 × 4 = +104 pts of rat-catch lead for main)

### Time-per-move

- rollout `a_max_move_s`: **0.084 s** — massively under budget
- main    `b_max_move_s`: 6.55 s — at the ceiling

## Interpretation

**Rollout is NOT an upgrade over the main α-β+HMM line.** Wilson CI straddles 50% symmetrically; the observed mean-score deficit (−2.4) is driven by the rat-capture gap (rollout 2.35/match vs main 3.65/match) — rollout **disabled in-rollout SEARCH**, so it left points on the table.

That rollout went 50-50 while missing ~5 pts/match in rat captures says: **the rollout core is already tactically competitive with our α-β search, it just self-nerfs on SEARCH**. If the rollout-v2-search-fix variant (sample rat position from belief at rollout start + re-enable SEARCH in rollout) closes that gap, it could move to net-positive vs main.

Key: the rollout uses **0.08 s per move** on its max. Main uses 6.55 s. There is ~80× compute headroom untapped — more rollouts + deeper rollouts are free.

## Recommendation

- **DO NOT set-current v08 rollout (UUID `6f6cc52c-cbcd-4a22-bffb-b730f2ee247b`)**. No advantage over v04.
- **Keep v08 as insurance-fork**. If Current-slot becomes unstable, we have a second crash-free option.
- **Promote rollout-v2-search-fix work** (ongoing via `rollout-v2-search-fix` agent). If that N=6 paired shows rollout-v2 ≥ 55% vs main, run N=20 paired, and if that holds, THEN consider set-current.
- **Don't invest more in the same rollout variant** — search fix is the single change that could unlock it.

## Files

- summary: `3600-agents/matches/rollout_vs_v042_n20/summary.json`
- per-pair matches: `3600-agents/matches/rollout_vs_v042_n20/matches/pair_000{0..9}.json`
- commit of this doc: (see commit log)
