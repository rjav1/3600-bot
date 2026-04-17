# BO_TUNING.md — Bayesian-optimisation weight tuning (T-20d)

**Status:** v0.2 pipeline shipped 2026-04-17; results pending a full run.
**Owner:** dev-heuristic.
**Source:** `tools/bo_tune.py`, `tools/test_bo_tune.py`.
**Addendum:** `docs/plan/BOT_STRATEGY_V02_ADDENDUM.md` §2.5 and D-009.

---

## 1. What this pipeline does

Searches the 9-dim weight box (`BOUNDS` in `bo_tune.py`) for the values
of `heuristic.W_INIT` that maximise RattleBot's paired win-rate against
a reference opponent (`FloorBot` by default).

Results are emitted in two files:

- **`<log-dir>/tuning_log.json`** — complete per-trial record: weight
  vector, win-rate, Wilson 95 % CI, regularisation term, raw objective,
  elapsed wall-time, N matches. Auditable forever.
- **`<out>` (default `3600-agents/RattleBot/weights.json`)** — the
  best-observed vector. `PlayerAgent.__init__` auto-loads it via
  `_load_tuned_weights()`; if the file is absent the agent falls back
  to hard-coded `heuristic.W_INIT` so the submission zip stays
  functional without this file.

The success-gate evaluation (T-HEUR-3) is **not** run by this script —
it's the job of `tools/paired_runner.py` as a separate 50-pair run.
This keeps tuning and gating cleanly separated.

## 2. Search space

See `BOT_STRATEGY_V02_ADDENDUM.md` §2.5 Table — bounds are sign-
preserving (BO cannot flip a sign). The `w_init` row matches
`heuristic.W_INIT` 1-for-1 and is seeded into BO via `x0=[W_INIT]`, so
the first trial is immediately informative.

## 3. Objective function

```
f(w) = -paired_win_rate(RattleBot(w), opponent, N=args.n_per_trial)
       + REG_LAMBDA * ||w - w_init||_2 / ||w_init||_2
```

- `REG_LAMBDA = 0.01` — light L2 regulariser toward the hand-tuned
  prior. BO can override if signal is strong (> 0.01 improvement in
  win-rate).
- BO minimises; negative win-rate means "lower is better from skopt's
  viewpoint".

## 4. Stopping criteria

Any of:
1. `--max-trials` (default 25) completed.
2. `--max-hours` (default 2.0) wall-clock elapsed.
3. `--early-stop-trials` (default 8) consecutive trials with no
   improvement in the best objective.

## 5. Parallelism

- **BO's core loop is sequential** — each trial depends on the posterior
  from previous ones.
- **Per-trial parallelism**: each trial plays `n_per_trial` paired
  matches. Set `--parallel K` to run K matches concurrently via
  `multiprocessing.Pool(ctx='spawn')`. Default K=1.
- Weight candidates are marshalled to workers via a temp JSON file;
  `agent.py::_load_tuned_weights` reads `RATTLEBOT_WEIGHTS_JSON` in
  the child process.

## 6. Success gate (T-HEUR-3)

From `BOT_STRATEGY_V02_ADDENDUM.md` §2.5:

> BO's best weights beat `w_init` by ≥ **+30 ELO** on a 50-match paired
> evaluation vs FloorBot (Wilson 95 % CI lower bound ≥ +10 ELO).
> **AND** BO's best weights do not **regress** against Yolanda
> (cross-validation): ≥ 90 % vs Yolanda.
> If the gate fails, **ship `w_init`**. Do not force a tuned vector
> that isn't clearly better.

Runner script (not yet implemented — tester-local to add):
```
python tools/paired_runner.py \
  --agents RattleBot FloorBot --n 50 --seed 1 \
  --no-limit-resources
```
and the Yolanda cross-validation:
```
python tools/paired_runner.py \
  --agents RattleBot Yolanda --n 50 --seed 2 \
  --no-limit-resources
```

## 7. How to run

Local tuning (2 hour budget, 25 trials, 10 pairs per trial, 1 worker):

```
python tools/bo_tune.py \
  --opponent FloorBot \
  --n-per-trial 10 \
  --max-trials 25 \
  --max-hours 2 \
  --seed 0
```

Fast smoke test (3 trials × 1 pair, ~5 min):

```
python tools/bo_tune.py \
  --opponent FloorBot \
  --n-per-trial 1 \
  --max-trials 3 \
  --max-hours 0.1 \
  --out /tmp/bo_smoke_weights.json \
  --log-dir /tmp/bo_smoke
```

Parallel (4 workers, n_per_trial=8 ⇒ 8 pairs/trial):

```
python tools/bo_tune.py \
  --opponent FloorBot \
  --n-per-trial 8 \
  --parallel 4 \
  --max-trials 25
```

## 8. Fallback path

If BO fails to beat `w_init` on the success gate, ship `w_init`:
delete (or do not create) `3600-agents/RattleBot/weights.json`.
`_load_tuned_weights()` returns `None`, `Heuristic()` uses
`heuristic.W_INIT`, and RattleBot behaves byte-identically to v0.1/v0.2
pre-tuning.

This is the explicit fallback recorded in BOT_STRATEGY.md §7 row 9 —
"if BO cannot beat `w_init`, ship `w_init`, bank the 6–10 h".

## 9. Tests

`tools/test_bo_tune.py` covers:

- Bounds enclose `w_init` strictly + sign preservation across all 9
  dimensions (sanity).
- `_regularisation(w_init) == 0`, positive away from `w_init`.
- `agent._load_tuned_weights()` behaviour:
  - Reads JSON object `{"weights": [...]}` format.
  - Reads bare JSON list format.
  - Falls back to `None` when file missing OR wrong shape (no crash).
  - Honours `RATTLEBOT_WEIGHTS_JSON` env var.

Run: `python tools/test_bo_tune.py` — 7/7 pass.
