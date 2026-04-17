# BO v0.3 RUN2 — self-play queued spec

**Status:** queued, waiting on RUN1 completion. Do NOT launch concurrently
with RUN1 — both would compete for the same 16 cores.

**Purpose:** guard against RUN1 overfitting to FloorBot-specific quirks by
running a second BO round with a different opponent (RattleBot self-play)
and a different seed. If RUN1's best weights also win the RUN2 gauntlet,
we have multi-opponent evidence the tuned vector generalises.

## Launch command

Run this AFTER `bo_v03_run1/weights_v03.json` has landed (or been
explicitly ruled out per the fallback policy):

```
python tools/_launch_bo_detached.py -- \
  --opponent RattleBot \
  --n-per-trial 20 \
  --max-trials 40 \
  --max-hours 24 \
  --parallel 15 \
  --catastrophe-penalty 5 \
  --catastrophe-threshold -30 \
  --seed 7 \
  --out 3600-agents/RattleBot/weights_v03_selfplay.json \
  --log-dir 3600-agents/matches/bo_v03_run2
```

Diffs vs RUN1:
- `--opponent RattleBot` — self-play. RUN1 tunes against FloorBot;
  RUN2 tunes against the same agent class, which probes whether the
  weight vector generalises beyond beating one opponent style.
- `--seed 7` — independent seed tree so pair seeds don't collide with
  RUN1 (which used `--seed 0`).
- `--out weights_v03_selfplay.json` — separate output so RUN2 cannot
  accidentally clobber RUN1's winning vector. Neither is named
  `weights.json`, so `agent.py` auto-loader ignores both until we
  explicitly copy the chosen one into place.
- `--log-dir bo_v03_run2/` — separate log directory.

Identical to RUN1:
- `--n-per-trial 20`, `--max-trials 40`, `--max-hours 24`, `--parallel 15`.
- `--catastrophe-penalty 5 --catastrophe-threshold -30` — same
  V01_LOSS_ANALYSIS §6 penalty structure.
- 14-dim search space (F1/F3/F4/F5/F7/F11/F12/F8/F13/F14/F15/F16/F17/F18).

## Self-play caveat

RattleBot-vs-RattleBot pairs the **tuned** candidate (RattleBot as A
with `RATTLEBOT_WEIGHTS_JSON` set) against an untuned reference
(RattleBot as B with no env var → `W_INIT` fallback). Both processes
import the same module, so B always runs with the hard-coded W_INIT.
This is a clean "BO-tuned vs W_INIT" A/B comparison — more informative
than self-play with identical weights, which would produce 50 % by
construction.

## Decision rule when RUN2 lands

Let `w_run1` = RUN1 winner vs FloorBot, `w_run2` = RUN2 winner vs
RattleBot-W_INIT.

1. If `w_run1` wins RUN2's final 50-match paired gate (beats
   RattleBot-W_INIT ≥ +30 ELO, Wilson 95 % lower ≥ +10 ELO):
   **ship `w_run1`** — it generalised.
2. Else if `w_run2` wins a parallel 50-match paired gate vs FloorBot
   (≥ +30 ELO over W_INIT): **ship `w_run2`** — FloorBot-tune was
   overfit; self-play tune is better.
3. Else: neither generalised. **Ship W_INIT** (no weights.json).
   Flag for post-mortem.

The 50-match gates are new runs via `tools/paired_runner.py`, not
artifacts of the BO runs themselves (BO trials use n_per_trial=20 for
speed; the gate uses 50 for Wilson-CI tightness).

## Pre-launch checklist

Before invoking:
1. Confirm RUN1 has exited (`ps` for the v03 detached PID).
2. Confirm `3600-agents/RattleBot/weights_v03.json` exists from RUN1
   (or an explicit decision to skip RUN1 artifacts).
3. Confirm no other heavy jobs are running (MctsBot paired_runner,
   FakeAlbert smoke, sandbox_sim, etc.) — coordinate with tester-local.
4. ETA: same as RUN1 (~5-8 h wall-clock at 15-way parallelism).
