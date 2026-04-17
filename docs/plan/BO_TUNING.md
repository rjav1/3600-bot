# BO_TUNING.md — Bayesian-optimisation weight tuning (T-20d + T-20c.1)

**Status:** v0.2.1 pipeline shipped 2026-04-17. Search space expanded
from 9 → 12 dims with the multi-scale distance-kernel superset per
CARRIE_DECONSTRUCTION §5.
**Owner:** dev-heuristic.
**Source:** `tools/bo_tune.py`, `tools/test_bo_tune.py`.
**Addendum:** `docs/plan/BOT_STRATEGY_V02_ADDENDUM.md` §2.5 and D-009.

---

## 1. What this pipeline does

Searches the 12-dim weight box (`BOUNDS` in `bo_tune.py`) for the values
of `heuristic.W_INIT` that maximise RattleBot's paired win-rate against
a reference opponent (`FloorBot` by default). Dims 9-11 (F14/F15/F16)
are the three parallel distance-kernel features added in T-20c.1; they
let BO allocate mass to whichever decay shape (recip / exp / step) best
matches Carrie's actual heuristic without us needing to know it.

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

12-dim box, sign-preserving bounds. See `BOUNDS` in `tools/bo_tune.py`
for exact values.

| Idx | Feature                  | Lower | Upper | w_init | Notes |
|-----|--------------------------|-------|-------|--------|-------|
| 0   | F1  score_diff           | +0.5  | +2.0  | +1.0   | ground-truth objective |
| 1   | F3  primed_popcount      |  0.0  | +1.0  | +0.3   | board-global approx |
| 2   | F4  carpet_popcount      |  0.0  | +0.8  | +0.2   | banked points |
| 3   | F5  our_cell_potential   |  0.0  | +3.0  | +1.5   | Carrie-style lever |
| 4   | F7  opp_cell_potential   | −3.0  |  0.0  | −1.2   | opp mirror |
| 5   | F11 belief_max_mass      | −5.0  |  0.0  | −3.0   | drives SEARCH gate |
| 6   | F12 belief_entropy       | −2.0  |  0.0  | −0.5   | concentration signal |
| 7   | F8  opp_line_threat      | −3.0  |  0.0  | −0.6   | next-turn opp roll |
| 8   | F13 belief_com_dist      | −0.20 |  0.0  | −0.05  | worker-to-COM |
| 9   | F14 cell_pot_recip       |  0.0  | +0.5  | +0.15  | H1 decay 1/(1+d) |
| 10  | F15 cell_pot_exp         |  0.0  | +0.5  | +0.10  | H2 decay exp(-0.5 d) |
| 11  | F16 cell_pot_step        |  0.0  | +0.5  | +0.10  | H6 decay step at D=5 |

The `w_init` row matches `heuristic.W_INIT` 1-for-1 and is seeded into
BO via `x0=[W_INIT]`, so the first trial is immediately informative.
BO is NOT allowed to flip a sign (bounds enforce it). F14/F15/F16 are
explicitly non-negative: positive weight means "potential near our
worker is good" — flipping would encode the opposite of what the
geometry says.

## 2.1 Why three distance kernels instead of one parametric feature

Per CARRIE_DECONSTRUCTION §5 (fallback path: we have no Carrie replays
per INTEL_PROBE), we can't know Carrie's exact decay form. Three
options were considered:
- **(a) Single parametric feature** with categorical kernel choice and
  continuous λ/D_step. Clean but adds mixed search space which skopt
  handles less well than pure Real boxes.
- **(b) Three weighted features, BO zeros the losers.** Chosen — a pure
  Real box is friendlier to scikit-optimize's GP surrogate and the
  runtime cost (3× O(64) dot products + one shared O(64·4) P_vec
  build) is trivial.
- **(c) Single kernel, hope for the best.** Risk of picking the wrong
  shape is non-recoverable.

(b) subsumes (a)'s expressiveness when any single kernel dominates: BO
can drive two weights to 0 and find the optimum along the remaining
axis. If Carrie blends multiple decays, (b) also captures that.

## 3. Objective function

```
f(w) = -paired_win_rate(RattleBot(w), opponent, N=args.n_per_trial)
       + REG_LAMBDA * ||w - w_init||_2 / ||w_init||_2
       + catastrophe_penalty · catastrophe_fraction
```

- `REG_LAMBDA = 0.01` — light L2 regulariser toward the hand-tuned
  prior. BO can override if signal is strong (> 0.01 improvement in
  win-rate).
- `catastrophe_fraction` = fraction of matches where RattleBot's
  score minus opponent's score is ≤ `--catastrophe-threshold` (default
  −30 per V01_LOSS_ANALYSIS §6). Biases BO away from weight vectors
  that occasionally implode (e.g., SEARCH-gate saturation caused the
  `RattleBot_Yolanda_1.json` −68 pts loss in the v0.1 corpus).
- `catastrophe_penalty` defaults to 0.0 (disabled). For the real BO
  run recommended flags per V01_LOSS_ANALYSIS §6:
  `--catastrophe-penalty 5 --catastrophe-threshold -30`. With
  penalty = 5 and a vector that causes a catastrophe in *every* match,
  the objective gets +5 added — enough to dominate even a 100 %
  win-rate signal and reject the vector.
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

Local tuning (2 hour budget, 25 trials, 10 pairs per trial, 1 worker)
with the V01_LOSS_ANALYSIS §6 catastrophe penalty enabled:

```
python tools/bo_tune.py \
  --opponent FloorBot \
  --n-per-trial 10 \
  --max-trials 25 \
  --max-hours 2 \
  --catastrophe-penalty 5 \
  --catastrophe-threshold -30 \
  --seed 0
```

Omit `--catastrophe-penalty` (default 0.0) to fall back to the simple
win-rate objective — use for A/B testing the penalty's effect.

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
