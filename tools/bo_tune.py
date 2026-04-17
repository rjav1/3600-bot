"""Bayesian-optimisation weight tuning pipeline for RattleBot (T-20d).

Per `docs/plan/BOT_STRATEGY_V02_ADDENDUM.md` §2.5 + D-009. Searches the
9-dim weight space for `heuristic.W_INIT` to maximise paired win-rate
vs a reference opponent (FloorBot by default). Writes the best-observed
vector to `3600-agents/RattleBot/weights.json` if it beats the hand-tuned
`w_init` baseline by the success gate in §2.5.

Architecture:
    1. A top-level driver runs BO via `skopt.gp_minimize` on the 9-dim
       box bounded by §2.5's sign-preserving priors.
    2. Each candidate `w` is evaluated by N paired matches vs the
       opponent. Workers are spawned as subprocesses (multiprocessing
       context 'spawn' — Windows + mac compat) and each child process
       loads a per-trial weights JSON via the `RATTLEBOT_WEIGHTS_JSON`
       env var; `agent.py::_load_tuned_weights()` picks it up in
       `PlayerAgent.__init__`.
    3. The objective function returns `-win_rate` (skopt minimises).

Output layout:
    <out-dir>/
        tuning_log.json   -- every trial's (w, win_rate, wilson_ci)
        weights.json      -- best-observed weights (copied to
                              3600-agents/RattleBot/weights.json on
                              success-gate pass)

Usage:
    python tools/bo_tune.py \\
        --opponent FloorBot \\
        --n-per-trial 10 \\
        --max-trials 25 \\
        --max-hours 2 \\
        --out 3600-agents/RattleBot/weights.json \\
        --seed 0

CLI flags mirror the addendum's spec verbatim. `--n-per-trial` counts
PAIRS (actual matches = 2*N).

Requires: scikit-optimize>=0.10.2 (added to requirements.txt).
"""

from __future__ import annotations

import os as _os_early

# T-40-INFRA fix (2026-04-17): disable JAX's multi-threaded XLA runtime
# before any engine import triggers `import jax`. JAX's eigen thread
# pool deadlocks under multiprocessing.spawn on Windows and under
# multiprocessing.fork on Linux (JAX emits `RuntimeWarning: os.fork()
# was called. os.fork() is incompatible with multithreaded code, and
# JAX is multithreaded, so this will likely lead to a deadlock.`).
# BO pools 15+ workers each spawning the engine, so this was the
# 0-trial deadlock seen on RUN1-v2/v3. Single-thread CPU XLA is safe.
# Same workaround as `tools/wsl_engine_runner.py` and
# `tools/paired_runner.py`.
_os_early.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false")
_os_early.environ.setdefault("JAX_PLATFORMS", "cpu")
_os_early.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import argparse
import json
import math
import os
import pathlib
import sys
import tempfile
import time
from datetime import datetime
from multiprocessing import get_context
from typing import List, Optional, Tuple


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
AGENTS_DIR = REPO_ROOT / "3600-agents"
ENGINE_DIR = REPO_ROOT / "engine"

# Wire up sys.path so the multiprocessing children can import paired_runner
# directly from `tools/`.
for p in (str(TOOLS_DIR), str(ENGINE_DIR), str(AGENTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


# ---------------------------------------------------------------------------
# Search space (BOT_STRATEGY_V02_ADDENDUM §2.5 table)
# ---------------------------------------------------------------------------
#
# Sign-preserving bounds: BO is not allowed to flip a sign. If BO
# converges to a boundary, we review whether that dim's bound was too
# tight. Every `w_init` entry lies strictly inside its bound.
#
BOUNDS: List[Tuple[float, float]] = [
    (+0.5, +2.0),   # F1  score_diff
    (+0.0, +1.0),   # F3  primed_popcount
    (+0.0, +0.8),   # F4  carpet_popcount
    (+0.0, +3.0),   # F5  our_cell_potential
    (-3.0, +0.0),   # F7  opp_cell_potential
    (-5.0, +0.0),   # F11 belief_max_mass
    (-2.0, +0.0),   # F12 belief_entropy
    (-3.0, +0.0),   # F8  opp_line_threat
    (-0.20, +0.0),  # F13 belief_com_dist
    # T-20c.1 multi-scale distance-kernel superset
    # (CARRIE_DECONSTRUCTION §5). All three aggregate Σ P(c)·decay(d)
    # with P(c) ≥ 0, decay ≥ 0, so the features themselves are ≥ 0.
    # Positive weight = "potential near our worker is good" (correct);
    # BO not allowed to flip sign. Upper bounds scaled by typical
    # feature magnitudes (F14≈150-200, F15≈100-150, F16≈500-800).
    (+0.0, +0.5),   # F14 cell_potential_recip (H1 1/(1+d))
    (+0.0, +0.5),   # F15 cell_potential_exp   (H2 exp(-0.5 d))
    (+0.0, +0.5),   # F16 cell_potential_step  (H6 1 iff d<=5)
    # T-30b (v0.3.1) — F17/F18. F17 is an integer count in [0, 64] with
    # typical mid-game value 0-5; negative weight (we never want more
    # dead primes). F18 is entropy in [0, ln 64 ≈ 4.16]; positive weight
    # (higher opp-entropy = opp can't profitably SEARCH = good for us).
    (-1.5, +0.0),   # F17 priming_lockout  (dead-primes count)
    (+0.0, +0.5),   # F18 opp_belief_proxy (opp-entropy after last search)
    # T-40b (v0.4.0) — F19/F20. F19 is in [0, 1] (fraction of belief
    # within Manhattan-2 of worker); positive weight — closer = better.
    # F20 is an integer in [0, 7] (longest run of PRIMED-or-SPACE the
    # opp could exploit); negative weight — bigger run = bigger threat.
    (+0.0, +1.5),   # F19 rat_catch_threat_radius
    (-1.5, +0.0),   # F20 opp_roll_imminence
    # T-40-EXPLOIT-1 (v0.4.1) — F22 prime_steal_bonus. Sum of
    # CARPET_POINTS_TABLE[k] over primed lines (k≥2, H/V) where our
    # worker is strictly closer to the nearer endpoint than opp's.
    # Positive — steal-able primed lines are good for us. Range
    # typically 0-20 per OPPONENT_EXPLOITS §T-40-EXPLOIT-1.
    (+0.0, +1.0),   # F22 prime_steal_bonus
]

# Hard-tuned default (matches RattleBot.heuristic.W_INIT).
W_INIT: List[float] = [
    1.0, 0.3, 0.2, 1.5, -1.2, -3.0, -0.5, -0.6, -0.05,
    0.15, 0.10, 0.10,
    -0.4, 0.1,
    0.3, -0.6,
    0.3,
]

# Light L2 regulariser pulling toward `w_init`. See §2.5 "Objective".
REG_LAMBDA: float = 0.01


# ---------------------------------------------------------------------------
# Subprocess entry point: evaluate one paired match for a given weight
# vector (written to a temp JSON file that agent.py picks up).
# ---------------------------------------------------------------------------


def _eval_one_pair(task: dict) -> dict:
    """Run a single paired match (2 games) for a given weight vector.

    The child process sets `RATTLEBOT_WEIGHTS_JSON` to the supplied path
    before importing paired_runner, so RattleBot's __init__ picks up
    the BO candidate weights.
    """
    # T-40-INFRA: single-thread XLA inside the child. Must be set BEFORE
    # the child imports engine/gameplay (which imports jax). On spawn
    # the child has already re-executed our top-level block so these
    # are set, but be defensive — idempotent.
    os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false")
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    os.environ["RATTLEBOT_WEIGHTS_JSON"] = task["weights_path"]

    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    import paired_runner  # noqa: E402

    item = (
        task["pair_index"],
        task["pair_seed"],
        task["agent_a"],
        task["agent_b"],
        task["limit_resources"],
        # tournament_budget: False preserves the pre-T-30a behavior
        # (local 360s/20s). BO tunes weights under the same regime as
        # when they'll run locally; if we ever want to tune under
        # tournament-accurate 240s/10s, flip to True here.
        False,
        True,  # quiet — don't spam per-turn board prints
    )
    return paired_runner._run_pair(item)


# ---------------------------------------------------------------------------
# Objective function (BO minimises `-win_rate + reg`)
# ---------------------------------------------------------------------------


def _wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson 95% CI for k successes in n trials. (Duplicated so this
    module is import-light; paired_runner has the same helper.)"""
    if n == 0:
        return (0.0, 0.0)
    phat = k / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    margin = (
        z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    ) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def _regularisation(w: List[float]) -> float:
    """L2 regulariser `REG_LAMBDA * ||w - w_init||_2 / ||w_init||_2`.

    Prefers small moves from the hand-tuned prior; BO can override if
    signal is strong.
    """
    num = math.sqrt(sum((wi - w0) ** 2 for wi, w0 in zip(w, W_INIT)))
    den = math.sqrt(sum(w0 ** 2 for w0 in W_INIT)) or 1.0
    return REG_LAMBDA * (num / den)


class _Evaluator:
    """Bundles the BO objective: paired win-rate minus regulariser.

    Each candidate vector is written to a temp JSON file, then the
    paired pool is fanned out. Tracks every trial in `self.trials` for
    the tuning log.
    """

    def __init__(
        self,
        opponent: str,
        n_per_trial: int,
        limit_resources: bool,
        n_workers: int,
        root_seed: int,
        out_dir: pathlib.Path,
        catastrophe_penalty: float = 0.0,
        catastrophe_threshold: float = -30.0,
    ) -> None:
        self.opponent = opponent
        self.n_per_trial = n_per_trial
        self.limit_resources = limit_resources
        self.n_workers = n_workers
        self.root_seed = root_seed
        self.out_dir = out_dir
        # V01_LOSS_ANALYSIS §6: catastrophic losses (e.g., SEARCH-gate
        # saturation yielding −68 pts) should bias BO away from fragile
        # weight vectors. Objective augmented with
        #   catastrophe_penalty · fraction_of_matches_with_diff <= threshold
        # Penalty of 0 disables (default). V01_LOSS_ANALYSIS recommends
        # 5.0 with threshold −30 pts; we wire both as knobs so they can
        # be tuned per run.
        self.catastrophe_penalty: float = float(catastrophe_penalty)
        self.catastrophe_threshold: float = float(catastrophe_threshold)
        self.trials: List[dict] = []
        self._best_objective = math.inf
        self._best_w: Optional[List[float]] = None
        self._best_winrate: float = 0.0
        self._best_wilson: Tuple[float, float] = (0.0, 0.0)

    def _evaluate_winrate(
        self, w: List[float], trial_index: int
    ) -> Tuple[float, Tuple[float, float], float, float]:
        """Run `self.n_per_trial` paired matches with RattleBot(w) vs
        the opponent. Returns (win_rate, wilson_ci_95, elapsed_s,
        catastrophe_fraction).

        catastrophe_fraction = fraction of matches where RattleBot's
        score minus opponent's score is <= self.catastrophe_threshold.
        Used by `objective()` to penalise weight vectors that occasion-
        ally implode (V01_LOSS_ANALYSIS §6).
        """
        # Write the candidate weights to a disposable JSON file so
        # child processes can load them via agent.py:_load_tuned_weights.
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            dir=str(self.out_dir),
            prefix=f"cand_trial{trial_index:03d}_",
            encoding="utf-8",
        ) as fh:
            json.dump({"weights": list(w)}, fh)
            weights_path = fh.name

        try:
            tasks = [
                {
                    "pair_index": i,
                    "pair_seed": (self.root_seed + trial_index * 1000 + i)
                    & 0xFFFFFFFF,
                    "agent_a": "RattleBot",
                    "agent_b": self.opponent,
                    "limit_resources": self.limit_resources,
                    "weights_path": weights_path,
                }
                for i in range(self.n_per_trial)
            ]

            t0 = time.perf_counter()
            if self.n_workers <= 1:
                results = [_eval_one_pair(t) for t in tasks]
            else:
                ctx = get_context("spawn")
                with ctx.Pool(processes=self.n_workers) as pool:
                    results = pool.map(_eval_one_pair, tasks)
            elapsed = time.perf_counter() - t0
        finally:
            try:
                os.remove(weights_path)
            except OSError:
                pass

        # Tally RattleBot wins across all matches in all pairs.
        # Each pair has 2 matches; RattleBot plays as A in match1, as B
        # in match2. Winner strings are "PLAYER_A", "PLAYER_B", "TIE",
        # or "ERROR".
        # Also count catastrophic matches: those where RattleBot's
        # score minus opponent's score is <= self.catastrophe_threshold.
        # Per-match `a_points`/`b_points` come from paired_runner's
        # _run_single_match (sourced from board.history).
        n_matches = 2 * len(results)
        wins = 0
        catastrophes = 0
        for pair in results:
            m1 = pair["match1"]
            m2 = pair["match2"]
            # match1: RattleBot is A
            if m1["winner"] == "PLAYER_A":
                wins += 1
            r_diff1 = int(m1.get("a_points", 0)) - int(m1.get("b_points", 0))
            if r_diff1 <= self.catastrophe_threshold:
                catastrophes += 1
            # match2: RattleBot is B
            if m2["winner"] == "PLAYER_B":
                wins += 1
            r_diff2 = int(m2.get("b_points", 0)) - int(m2.get("a_points", 0))
            if r_diff2 <= self.catastrophe_threshold:
                catastrophes += 1
        win_rate = wins / n_matches if n_matches else 0.0
        catastrophe_frac = (
            catastrophes / n_matches if n_matches else 0.0
        )
        wilson = _wilson_ci(wins, n_matches)
        return win_rate, wilson, elapsed, catastrophe_frac

    def objective(self, w) -> float:
        """skopt callback. Returns
          `-win_rate + REG_LAMBDA*||w-w0||
            + catastrophe_penalty * catastrophe_fraction`.

        skopt minimises; negating win-rate flips the sense so the best
        vector is the argmin. The catastrophe term biases BO away from
        weight vectors that occasionally implode (V01_LOSS_ANALYSIS §6).
        """
        w = list(map(float, w))
        trial_index = len(self.trials)
        win_rate, wilson, elapsed, cat_frac = self._evaluate_winrate(
            w, trial_index
        )
        reg = _regularisation(w)
        cat_term = self.catastrophe_penalty * cat_frac
        obj = -win_rate + reg + cat_term
        entry = {
            "trial_index": trial_index,
            "weights": w,
            "win_rate": win_rate,
            "wilson95_lo": wilson[0],
            "wilson95_hi": wilson[1],
            "regularisation": reg,
            "catastrophe_fraction": cat_frac,
            "catastrophe_term": cat_term,
            "objective": obj,
            "elapsed_s": elapsed,
            "n_matches": 2 * self.n_per_trial,
        }
        self.trials.append(entry)
        if obj < self._best_objective:
            self._best_objective = obj
            self._best_w = w
            self._best_winrate = win_rate
            self._best_wilson = wilson
        print(
            f"[bo_tune] trial {trial_index:02d}: "
            f"winrate={win_rate:.3f} CI=[{wilson[0]:.3f},{wilson[1]:.3f}] "
            f"reg={reg:.4f} cat={cat_frac:.3f}(+{cat_term:.3f}) "
            f"obj={obj:.4f} best_winrate={self._best_winrate:.3f} "
            f"elapsed={elapsed:.1f}s",
            flush=True,
        )
        return obj


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Bayesian-optimisation weight tuning for RattleBot."
    )
    parser.add_argument(
        "--opponent",
        default="FloorBot",
        help="Agent directory name to use as opponent (default FloorBot).",
    )
    parser.add_argument(
        "--n-per-trial",
        type=int,
        default=10,
        help="Number of PAIRS per BO trial (2N matches). Default 10 "
        "(=20 matches, ~10-15 min at N=1 worker).",
    )
    parser.add_argument(
        "--max-trials",
        type=int,
        default=25,
        help="Max BO trials (default 25). Includes initial random seeds.",
    )
    parser.add_argument(
        "--max-hours",
        type=float,
        default=2.0,
        help="Wall-clock cap in hours (default 2.0).",
    )
    parser.add_argument(
        "--early-stop-trials",
        type=int,
        default=8,
        help="Stop if no improvement in best obj over this many trials.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Root RNG seed.")
    parser.add_argument(
        "--out",
        type=str,
        default=str(AGENTS_DIR / "RattleBot" / "weights.json"),
        help="Target path for the winning weights.json.",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Tuning log directory "
        "(default 3600-agents/matches/bo_tune_TIMESTAMP/).",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Parallel workers for per-trial paired evaluations (default 1).",
    )
    parser.add_argument(
        "--no-limit-resources",
        dest="limit_resources",
        action="store_false",
        default=True,
        help="Disable resource limiting (required on Windows).",
    )
    parser.add_argument(
        "--catastrophe-penalty",
        type=float,
        default=0.0,
        help=(
            "BO objective penalty coefficient for the fraction of matches "
            "with score-diff <= --catastrophe-threshold (V01_LOSS_ANALYSIS "
            "§6). 0.0 disables (default). Recommended for the real BO run: "
            "5.0 (subtracts 5·catastrophe_fraction from win_rate)."
        ),
    )
    parser.add_argument(
        "--catastrophe-threshold",
        type=float,
        default=-30.0,
        help=(
            "Score-diff threshold below which a match counts as a "
            "catastrophe. Default -30 per V01_LOSS_ANALYSIS §6."
        ),
    )
    args = parser.parse_args()

    if sys.platform.startswith("win") and args.limit_resources:
        print(
            "[bo_tune] WARNING: --limit-resources requested on Windows; "
            "engine's seccomp path is Linux-only. Falling back.",
            flush=True,
        )
        args.limit_resources = False

    if args.log_dir is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = AGENTS_DIR / "matches" / f"bo_tune_{stamp}"
    else:
        log_dir = pathlib.Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Lazy import so that `--help` works without skopt installed.
    from skopt import gp_minimize
    from skopt.space import Real

    space = [Real(lo, hi, name=f"w{i}") for i, (lo, hi) in enumerate(BOUNDS)]
    evaluator = _Evaluator(
        opponent=args.opponent,
        n_per_trial=args.n_per_trial,
        limit_resources=args.limit_resources,
        n_workers=args.parallel,
        root_seed=args.seed,
        out_dir=log_dir,
        catastrophe_penalty=args.catastrophe_penalty,
        catastrophe_threshold=args.catastrophe_threshold,
    )

    deadline = time.perf_counter() + args.max_hours * 3600.0
    best_trials_seen = 0

    def callback(res):
        # Stop if we've spent the wall-clock budget OR no-improvement
        # streak exceeded the early-stop threshold.
        nonlocal best_trials_seen
        if time.perf_counter() >= deadline:
            print(
                "[bo_tune] wall-clock budget exhausted; stopping.",
                flush=True,
            )
            return True
        # "No improvement" = the best objective seen in the last
        # `early_stop_trials` is the same as the current global best.
        trials = evaluator.trials
        if len(trials) >= args.early_stop_trials:
            recent_best = min(
                t["objective"] for t in trials[-args.early_stop_trials:]
            )
            global_best = min(t["objective"] for t in trials)
            if recent_best > global_best - 1e-6:
                best_trials_seen += 1
                if best_trials_seen >= args.early_stop_trials:
                    print(
                        "[bo_tune] no improvement for "
                        f"{args.early_stop_trials} trials; early stop.",
                        flush=True,
                    )
                    return True
            else:
                best_trials_seen = 0
        return False

    print(
        f"[bo_tune] opponent={args.opponent} "
        f"n_per_trial={args.n_per_trial} max_trials={args.max_trials} "
        f"max_hours={args.max_hours} parallel={args.parallel} "
        f"seed={args.seed} limit_resources={args.limit_resources}",
        flush=True,
    )
    print(f"[bo_tune] log_dir={log_dir}", flush=True)

    t0 = time.perf_counter()
    # `x0=W_INIT` seeds BO at the hand-tuned prior so the first trial
    # is immediately informative. skopt requires n_calls > n_initial_points,
    # so clamp n_initial_points accordingly.
    n_initial = max(1, min(5, args.max_trials - 1))
    result = gp_minimize(
        func=evaluator.objective,
        dimensions=space,
        n_calls=args.max_trials,
        n_initial_points=n_initial,
        x0=[list(W_INIT)],
        random_state=args.seed,
        acq_func="EI",
        callback=callback,
    )
    elapsed = time.perf_counter() - t0

    # Dump tuning log + best weights.
    log_path = log_dir / "tuning_log.json"
    with open(log_path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "opponent": args.opponent,
                "n_per_trial": args.n_per_trial,
                "max_trials": args.max_trials,
                "seed": args.seed,
                "elapsed_s": elapsed,
                "bounds": BOUNDS,
                "w_init": W_INIT,
                "catastrophe_penalty": args.catastrophe_penalty,
                "catastrophe_threshold": args.catastrophe_threshold,
                "trials": evaluator.trials,
                "best_weights": evaluator._best_w,
                "best_win_rate": evaluator._best_winrate,
                "best_wilson95": list(evaluator._best_wilson),
            },
            fh,
            indent=2,
        )
    print(f"[bo_tune] tuning log -> {log_path}", flush=True)

    # Always write the best-observed weights to the target path so that
    # the downstream success-gate runner can evaluate them. The gate
    # (T-HEUR-3) is a separate command — this script just emits the
    # candidate.
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "weights": evaluator._best_w,
                "win_rate_vs_opponent": evaluator._best_winrate,
                "opponent": args.opponent,
                "wilson95": list(evaluator._best_wilson),
                "trials_evaluated": len(evaluator.trials),
                "seed": args.seed,
                "timestamp": datetime.now().isoformat(),
            },
            fh,
            indent=2,
        )
    print(
        f"[bo_tune] best weights -> {out_path} "
        f"(win_rate={evaluator._best_winrate:.3f}, "
        f"trials={len(evaluator.trials)}, elapsed={elapsed:.1f}s)",
        flush=True,
    )


if __name__ == "__main__":
    main()
