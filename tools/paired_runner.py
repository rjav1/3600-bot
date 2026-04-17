"""Paired-match batch runner for local bot evaluation.

Per CONTRARIAN_SCOPE §F-14 and BOT_STRATEGY v1.1 §5/§6, every RattleBot
version bump must beat its predecessor in a paired-match test before
promotion. Paired matches use the same seeded transition matrix, the
same corner blockers, the same spawn locations, and the same rat walk;
sides A/B are swapped between the two matches of a pair so board noise
cancels. With N >= 100 pairs, a paired sign-test discriminates a 5pp
win-rate improvement at p<0.05.

Usage (from repo root):
    python3 tools/paired_runner.py --agents FloorBot Yolanda --n 10 --seed 0

See docs/tests/PAIRED_RUNNER.md for the promotion protocol.
"""

from __future__ import annotations

import os as _os_early

# T-40-INFRA fix (2026-04-17): disable JAX's multi-threaded XLA runtime
# BEFORE any engine import triggers `import jax` in `engine/gameplay.py`.
# Rationale: jax's default eigen thread pool is incompatible with
# multiprocessing.spawn on Windows and multiprocessing.fork on Linux
# (JAX prints `RuntimeWarning: os.fork() was called. os.fork() is
# incompatible with multithreaded code, and JAX is multithreaded, so
# this will likely lead to a deadlock.`). The engine spawns a
# PlayerProcess per agent inside play_game, and RattleBot's constructor
# path (which unpickles a jax array from a Queue) can deadlock for
# minutes. Forcing single-thread CPU XLA makes the post-spawn/fork
# state safe. Identical workaround to tools/wsl_engine_runner.py,
# validated there for sandbox-sim. Zero functional impact — engine's
# jax use in _load_transition_matrix is one-shot, not a hot path.
_os_early.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false")
_os_early.environ.setdefault("JAX_PLATFORMS", "cpu")
_os_early.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import argparse
import json
import math
import os
import pathlib
import random
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from multiprocessing import get_context
from typing import Optional


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_ROOT / "engine"
AGENTS_DIR = REPO_ROOT / "3600-agents"


# ---------------------------------------------------------------------------
# Engine shim
# ---------------------------------------------------------------------------


def _import_engine():
    """Import engine modules. Must be called inside the worker process."""
    if str(ENGINE_DIR) not in sys.path:
        sys.path.insert(0, str(ENGINE_DIR))
    import board_utils  # noqa: F401
    import gameplay  # noqa: F401
    from game.enums import ResultArbiter, WinReason  # noqa: F401
    return gameplay, board_utils


def _apply_tournament_budget_patch():
    """Patch engine for tournament-accurate budget (240s play, 10s init)
    without requiring Linux-only seccomp/setrlimit/UID-drop.

    Rationale: the engine's `limit_resources=True` path does TWO things at once —
    (a) sets play_time=240, init_timeout=10 (the budget we care about for T-30a
    time-audit); (b) installs seccomp + setrlimit(RSS) + drops UID to
    player_a_user/player_b_user (isolation we cannot reproduce on Windows,
    and cannot reproduce on WSL without sudo for libseccomp-dev / gcc /
    useradd). This function keeps (a) and skips (b), so we get real
    tournament-budget enforcement on any platform. Use for TIME_AUDIT_V02
    and any other gate that measures clock behavior, not isolation.
    """
    import sys as _sys

    # Ensure engine is importable.
    if str(ENGINE_DIR) not in _sys.path:
        _sys.path.insert(0, str(ENGINE_DIR))

    import player_process as _pp  # noqa: E402

    # Stub out the Linux-only isolation calls. These are called inside the
    # child process's run_player_process. Patches only propagate to children
    # on platforms that use `fork` (Linux/WSL), because fork inherits the
    # parent's sys.modules and attribute state. On `spawn` platforms
    # (Windows, macOS) the child re-imports from scratch, so the parent's
    # monkey-patches are NOT seen. That is why --tournament-budget is
    # Linux/WSL only; we guard the CLI against Windows so we don't silently
    # produce FAILED_INIT TIE summaries.
    _pp.apply_seccomp = lambda: None
    _pp.drop_priveliges = lambda *a, **k: None

    # Skip setrlimit on Linux so RLIMIT_RSS doesn't collide with jax memory
    # arenas. On Windows `resource` doesn't exist; we wouldn't hit this
    # branch because the CLI would have already refused (see
    # --tournament-budget guard in main()).
    if "resource" in _sys.modules:
        _sys.modules["resource"].setrlimit = lambda *a, **k: None


def _run_single_match(
    agent_a: str,
    agent_b: str,
    pair_seed: int,
    limit_resources: bool,
    tournament_budget: bool,
    quiet: bool,
) -> dict:
    """Run one match between agent_a (as player A) and agent_b (as player B).

    `pair_seed` deterministically seeds Python's random module so that
    both matches in a pair (A-vs-B and B-vs-A) see the same transition
    matrix, corner blockers, spawn locations, and rat walk.

    If `tournament_budget` is True, we patch the engine to run with
    play_time=240, init_timeout=10 (the tournament values) without
    engaging the Linux-only seccomp/setrlimit/UID-drop path. This is
    portable across Windows and WSL and gives tournament-accurate time
    enforcement even when the full sandbox isn't available.
    """
    gameplay, board_utils = _import_engine()

    if tournament_budget:
        _apply_tournament_budget_patch()
        # After patching, we force the engine to treat this as
        # limit_resources=True so play_time=240 / init_timeout=10 apply.
        effective_limit_resources = True
    else:
        effective_limit_resources = limit_resources

    # Silence the engine's per-turn prints if requested.
    if quiet:
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    # Seed BEFORE play_game so the engine's random.choice / random.randint /
    # generate_spawns / rat.move calls are reproducible for this pair.
    random.seed(pair_seed)

    t0 = time.perf_counter()
    (
        final_board,
        rat_position_history,
        spawn_a,
        spawn_b,
        message_a,
        message_b,
    ) = gameplay.play_game(
        str(AGENTS_DIR),
        str(AGENTS_DIR),
        agent_a,
        agent_b,
        display_game=False,
        delay=0.0,
        clear_screen=False,
        record=True,
        limit_resources=effective_limit_resources,
    )
    elapsed = time.perf_counter() - t0

    from game.enums import ResultArbiter, WinReason

    winner_code = final_board.get_winner()
    winner_name = ResultArbiter(winner_code).name if winner_code is not None else "UNFINISHED"
    win_reason = WinReason(final_board.win_reason).name if final_board.win_reason is not None else "NONE"

    hist = final_board.history
    # Final scores (last recorded entry, else 0).
    a_points_final = hist.a_points[-1] if hist.a_points else 0
    b_points_final = hist.b_points[-1] if hist.b_points else 0
    rat_caught_total = int(sum(1 for x in hist.rat_caught if x))

    # Attribute rat captures to the side that acted on each turn.
    # hist.left_behind_enums is parallel to rat_caught; pos list order is
    # alternating A, B, A, B... starting with A on turn 0.
    a_rat_captures = 0
    b_rat_captures = 0
    for idx, caught in enumerate(hist.rat_caught):
        if not caught:
            continue
        # Even indices = A's move, odd = B's move.
        if idx % 2 == 0:
            a_rat_captures += 1
        else:
            b_rat_captures += 1

    # Per-move wall time: derive from time_left deltas across same-side moves.
    a_move_times = _time_from_deltas(hist.a_time_left)
    b_move_times = _time_from_deltas(hist.b_time_left)

    history_json = board_utils.get_history_json(
        final_board, rat_position_history, spawn_a, spawn_b, message_a, message_b
    )

    return {
        "agent_a": agent_a,
        "agent_b": agent_b,
        "pair_seed": pair_seed,
        "winner": winner_name,
        "win_reason": win_reason,
        "a_points": int(a_points_final),
        "b_points": int(b_points_final),
        "turn_count": int(final_board.turn_count),
        "rat_caught_total": rat_caught_total,
        "a_rat_captures": a_rat_captures,
        "b_rat_captures": b_rat_captures,
        "elapsed_s": elapsed,
        "a_max_move_s": max(a_move_times) if a_move_times else 0.0,
        "b_max_move_s": max(b_move_times) if b_move_times else 0.0,
        "a_mean_move_s": (sum(a_move_times) / len(a_move_times)) if a_move_times else 0.0,
        "b_mean_move_s": (sum(b_move_times) / len(b_move_times)) if b_move_times else 0.0,
        "a_message": message_a,
        "b_message": message_b,
        "history_json": history_json,
    }


def _time_from_deltas(time_left_series):
    """Convert a time_left timeseries into per-move elapsed times."""
    out = []
    prev = None
    for t in time_left_series:
        if prev is not None:
            dt = prev - t
            if dt >= 0:
                out.append(dt)
        prev = t
    return out


# ---------------------------------------------------------------------------
# Pair driver
# ---------------------------------------------------------------------------


@dataclass
class PairResult:
    pair_index: int
    pair_seed: int
    match1: dict  # A-as-player-a vs B-as-player-b
    match2: dict  # B-as-player-a vs A-as-player-b


def _run_pair(args_tuple):
    """Worker entry point: run both matches of a single pair."""
    # T-40-INFRA defensive: make sure spawn-children still force
    # single-thread XLA even if the top-level module state didn't
    # propagate. Idempotent.
    os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false")
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

    (
        pair_index,
        pair_seed,
        agent_a,
        agent_b,
        limit_resources,
        tournament_budget,
        quiet,
    ) = args_tuple

    # Match 1: agent_a plays as A, agent_b plays as B.
    m1 = _run_single_match(
        agent_a, agent_b, pair_seed, limit_resources, tournament_budget, quiet
    )
    # Match 2: swapped sides.
    m2 = _run_single_match(
        agent_b, agent_a, pair_seed, limit_resources, tournament_budget, quiet
    )

    return {
        "pair_index": pair_index,
        "pair_seed": pair_seed,
        "match1": m1,
        "match2": m2,
    }


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def _binom_two_sided_p(k: int, n: int, p: float = 0.5) -> float:
    """Two-sided binomial test p-value for k successes out of n.

    Uses the "method of small p-values" tail sum (standard two-sided test).
    """
    if n == 0:
        return 1.0

    def pmf(i):
        return math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))

    observed = pmf(k)
    # Sum probabilities of outcomes at least as extreme as k.
    total = 0.0
    for i in range(n + 1):
        pi = pmf(i)
        if pi <= observed + 1e-12:
            total += pi
    return min(1.0, total)


def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% CI for k successes in n trials."""
    if n == 0:
        return (0.0, 0.0)
    phat = k / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def summarise(pairs: list[dict], name_a: str, name_b: str) -> dict:
    n_matches = 2 * len(pairs)
    wins_a = 0
    wins_b = 0
    ties = 0
    crashes_a = 0
    crashes_b = 0
    timeouts_a = 0
    timeouts_b = 0
    invalid_a = 0
    invalid_b = 0
    score_diffs = []  # A - B per match
    rat_captures_a_total = 0
    rat_captures_b_total = 0

    # Paired win counting: in each pair, whose logical identity won that pair
    # on net? A pair "goes to A" if A wins both, "goes to B" if B wins both,
    # and is a tie otherwise.
    pair_wins_a = 0
    pair_wins_b = 0
    pair_ties = 0

    a_max_move_global = 0.0
    b_max_move_global = 0.0

    def _tally(match: dict, a_role_agent: str, b_role_agent: str):
        """Tally a single match, attributing outcomes back to `name_a`/`name_b` logical identities."""
        nonlocal wins_a, wins_b, ties
        nonlocal crashes_a, crashes_b, timeouts_a, timeouts_b
        nonlocal invalid_a, invalid_b
        nonlocal rat_captures_a_total, rat_captures_b_total
        nonlocal a_max_move_global, b_max_move_global

        # Who plays as A/B in this match?
        a_is_name_a = a_role_agent == name_a  # else name_a is playing as B
        winner = match["winner"]  # "PLAYER_A", "PLAYER_B", "TIE", "ERROR"
        reason = match["win_reason"]
        a_pts = match["a_points"]
        b_pts = match["b_points"]

        if winner == "PLAYER_A":
            if a_is_name_a:
                wins_a += 1
            else:
                wins_b += 1
        elif winner == "PLAYER_B":
            if a_is_name_a:
                wins_b += 1
            else:
                wins_a += 1
        else:
            ties += 1

        # Score diff from logical-A perspective.
        diff_a_minus_b = (a_pts - b_pts) if a_is_name_a else (b_pts - a_pts)
        score_diffs.append(diff_a_minus_b)

        # Error attribution: the loser's slot gets the crash/timeout tag.
        if winner in ("PLAYER_A", "PLAYER_B"):
            loser_is_a = winner == "PLAYER_B"  # opposite of winner
            loser_is_name_a = (loser_is_a and a_is_name_a) or ((not loser_is_a) and not a_is_name_a)
            if reason == "CODE_CRASH" or reason == "MEMORY_ERROR" or reason == "FAILED_INIT":
                if loser_is_name_a:
                    crashes_a += 1
                else:
                    crashes_b += 1
            elif reason == "TIMEOUT":
                if loser_is_name_a:
                    timeouts_a += 1
                else:
                    timeouts_b += 1
            elif reason == "INVALID_TURN":
                if loser_is_name_a:
                    invalid_a += 1
                else:
                    invalid_b += 1

        # Rat captures (attribute to logical identity).
        if a_is_name_a:
            rat_captures_a_total += match["a_rat_captures"]
            rat_captures_b_total += match["b_rat_captures"]
        else:
            rat_captures_a_total += match["b_rat_captures"]
            rat_captures_b_total += match["a_rat_captures"]

        # Max per-move time per logical identity.
        a_mx = match["a_max_move_s"] if a_is_name_a else match["b_max_move_s"]
        b_mx = match["b_max_move_s"] if a_is_name_a else match["a_max_move_s"]
        a_max_move_global = max(a_max_move_global, a_mx)
        b_max_move_global = max(b_max_move_global, b_mx)

    for pair in pairs:
        m1 = pair["match1"]  # A-role = name_a
        m2 = pair["match2"]  # A-role = name_b

        _tally(m1, name_a, name_b)
        _tally(m2, name_b, name_a)

        # Pair-level scoring.
        def _winner_of(match, a_role_is_name_a):
            w = match["winner"]
            if w == "TIE":
                return "TIE"
            if w == "PLAYER_A":
                return name_a if a_role_is_name_a else name_b
            if w == "PLAYER_B":
                return name_b if a_role_is_name_a else name_a
            return "TIE"  # ERROR treated as tie for pair-scoring

        w1 = _winner_of(m1, True)
        w2 = _winner_of(m2, False)
        if w1 == name_a and w2 == name_a:
            pair_wins_a += 1
        elif w1 == name_b and w2 == name_b:
            pair_wins_b += 1
        else:
            pair_ties += 1

    n_pairs = len(pairs)
    decisive_pairs = pair_wins_a + pair_wins_b
    sign_p = _binom_two_sided_p(pair_wins_a, decisive_pairs) if decisive_pairs > 0 else 1.0

    winrate_a_matches = wins_a / n_matches if n_matches else 0.0
    wilson_lo, wilson_hi = _wilson_ci(wins_a, n_matches)

    mean_score_diff = sum(score_diffs) / len(score_diffs) if score_diffs else 0.0

    return {
        "agent_a": name_a,
        "agent_b": name_b,
        "n_pairs": n_pairs,
        "n_matches": n_matches,
        "matches": {
            "wins_a": wins_a,
            "wins_b": wins_b,
            "ties": ties,
            "winrate_a": winrate_a_matches,
            "winrate_a_wilson95": [wilson_lo, wilson_hi],
        },
        "pairs": {
            "pair_wins_a": pair_wins_a,
            "pair_wins_b": pair_wins_b,
            "pair_ties": pair_ties,
            "paired_sign_test_p": sign_p,
            "decisive_pairs": decisive_pairs,
        },
        "errors": {
            "crashes_a": crashes_a,
            "crashes_b": crashes_b,
            "timeouts_a": timeouts_a,
            "timeouts_b": timeouts_b,
            "invalid_a": invalid_a,
            "invalid_b": invalid_b,
        },
        "score": {
            "mean_score_diff_a_minus_b": mean_score_diff,
        },
        "rat": {
            "captures_a": rat_captures_a_total,
            "captures_b": rat_captures_b_total,
            "captures_per_match_a": rat_captures_a_total / n_matches if n_matches else 0.0,
            "captures_per_match_b": rat_captures_b_total / n_matches if n_matches else 0.0,
        },
        "timing": {
            "a_max_move_s": a_max_move_global,
            "b_max_move_s": b_max_move_global,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _derive_pair_seed(root_seed: int, pair_index: int) -> int:
    return (root_seed + pair_index) & 0xFFFFFFFF


def main():
    parser = argparse.ArgumentParser(description="Paired-match batch runner for CS3600 bots.")
    parser.add_argument(
        "--agents",
        nargs=2,
        metavar=("A", "B"),
        required=True,
        help="Two agent directory names (e.g. 'RattleBot FloorBot').",
    )
    parser.add_argument(
        "--n",
        type=int,
        required=True,
        help="Number of PAIRS (actual matches = 2*N, sides swapped each pair).",
    )
    parser.add_argument("--seed", type=int, default=0, help="Root RNG seed.")
    parser.add_argument(
        "--limit-resources",
        dest="limit_resources",
        action="store_true",
        default=True,
        help="Enable tournament-grade resource limiting (default True; Linux-only).",
    )
    parser.add_argument(
        "--no-limit-resources",
        dest="limit_resources",
        action="store_false",
        help="Disable resource limiting (required on Windows or without seccomp).",
    )
    parser.add_argument(
        "--tournament-budget",
        action="store_true",
        default=False,
        help=(
            "Enforce tournament-accurate play_time=240s, init_timeout=10s "
            "without requiring Linux-only seccomp/setrlimit/UID-drop. "
            "Portable across Windows and WSL. Use this for the T-30a time "
            "audit — gets the budget right even when --limit-resources "
            "is unavailable. Disables isolation; still trusts the bot."
        ),
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of parallel worker processes (default 1, max 8).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output directory (default 3600-agents/matches/batch_TIMESTAMP/).",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress per-match stdout.")
    args = parser.parse_args()

    agent_a, agent_b = args.agents
    n_pairs = args.n
    root_seed = args.seed

    # Windows fallback for limit_resources: seccomp + setrlimit(RSS) are Linux-only.
    if args.limit_resources and sys.platform.startswith("win") and not args.tournament_budget:
        print(
            "[paired_runner] WARNING: --limit-resources requested on Windows; "
            "engine's seccomp/setrlimit path is Linux-only. Falling back to "
            "--no-limit-resources (play_time=360, init_timeout=20). "
            "Consider --tournament-budget for 240s/10s without isolation.",
            flush=True,
        )
        args.limit_resources = False

    # --tournament-budget implies we're NOT using the engine's limit_resources path,
    # but we still want 240s/10s. The patch applies stubs and then passes
    # limit_resources=True to play_game so the engine picks the tournament values.
    # WARNING: only works on fork-based platforms (Linux/WSL). On Windows the
    # child processes are started via `spawn` and re-import engine modules from
    # scratch, so the parent's monkey-patches do NOT propagate and every child
    # crashes on `import resource` before playing a single ply, silently
    # returning FAILED_INIT TIEs. Guard here rather than produce garbage data.
    if args.tournament_budget and sys.platform.startswith("win"):
        print(
            "[paired_runner] ERROR: --tournament-budget is Linux/WSL only "
            "(Windows multiprocessing uses spawn, which does not inherit our "
            "monkey-patches to engine/player_process.py; every child process "
            "would crash on `import resource`). Re-run under WSL: "
            "`wsl -- bash -c \"cd /mnt/c/...; python3 tools/paired_runner.py --tournament-budget ...\"` "
            "or use --no-limit-resources on Windows (360s budget, tournament-inaccurate).",
            flush=True,
            file=sys.stderr,
        )
        sys.exit(2)

    if args.tournament_budget:
        args.limit_resources = False  # effective flag for CLI reporting only

    # Resolve output directory.
    if args.out is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = AGENTS_DIR / "matches" / f"batch_{stamp}"
    else:
        out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    matches_dir = out_dir / "matches"
    matches_dir.mkdir(exist_ok=True)

    # Validate agents exist.
    for a in (agent_a, agent_b):
        if not (AGENTS_DIR / a).is_dir():
            print(f"[paired_runner] ERROR: agent directory not found: {AGENTS_DIR / a}", flush=True)
            sys.exit(2)

    parallel = max(1, min(8, args.parallel))

    print(
        f"[paired_runner] {agent_a} vs {agent_b} — {n_pairs} pairs "
        f"({2 * n_pairs} matches), seed={root_seed}, "
        f"limit_resources={args.limit_resources}, parallel={parallel}",
        flush=True,
    )

    work = [
        (
            i,
            _derive_pair_seed(root_seed, i),
            agent_a,
            agent_b,
            args.limit_resources,
            args.tournament_budget,
            args.quiet,
        )
        for i in range(n_pairs)
    ]

    t0 = time.perf_counter()
    results: list[dict] = []

    if parallel == 1:
        for item in work:
            pi = item[0]
            pseed = item[1]
            print(f"[paired_runner] pair {pi + 1}/{n_pairs} (seed={pseed}) …", flush=True)
            try:
                results.append(_run_pair(item))
            except Exception as e:
                print(f"[paired_runner] pair {pi} FAILED with {type(e).__name__}: {e}", flush=True)
                results.append({
                    "pair_index": pi,
                    "pair_seed": pseed,
                    "error": f"{type(e).__name__}: {e}",
                })
            _emit_incremental(results[-1], matches_dir, agent_a, agent_b)
    else:
        ctx = get_context("spawn")
        try:
            with ctx.Pool(parallel) as pool:
                try:
                    for r in pool.imap_unordered(_run_pair, work):
                        results.append(r)
                        print(
                            f"[paired_runner] pair {r['pair_index'] + 1}/{n_pairs} complete "
                            f"(seed={r['pair_seed']})",
                            flush=True,
                        )
                        _emit_incremental(r, matches_dir, agent_a, agent_b)
                except KeyboardInterrupt:
                    print("[paired_runner] interrupted; terminating pool…", flush=True)
                    pool.terminate()
                    pool.join()
                    raise
        except Exception as e:
            print(
                f"[paired_runner] parallel mode failed ({type(e).__name__}: {e}); "
                "falling back to sequential for remaining pairs.",
                flush=True,
            )
            done_pairs = {r["pair_index"] for r in results if "pair_index" in r}
            remaining = [w for w in work if w[0] not in done_pairs]
            for item in remaining:
                try:
                    results.append(_run_pair(item))
                except Exception as e2:
                    results.append({
                        "pair_index": item[0],
                        "pair_seed": item[1],
                        "error": f"{type(e2).__name__}: {e2}",
                    })
                _emit_incremental(results[-1], matches_dir, agent_a, agent_b)

    elapsed = time.perf_counter() - t0

    # Drop pairs with errors (count them instead).
    good_pairs = [r for r in results if "error" not in r]
    errored_pairs = [r for r in results if "error" in r]
    good_pairs.sort(key=lambda r: r["pair_index"])

    summary = summarise(good_pairs, agent_a, agent_b)
    summary["seed"] = root_seed
    summary["limit_resources"] = args.limit_resources
    summary["parallel"] = parallel
    summary["wall_elapsed_s"] = elapsed
    summary["errored_pairs"] = [
        {"pair_index": r["pair_index"], "pair_seed": r["pair_seed"], "error": r["error"]}
        for r in errored_pairs
    ]
    summary["output_dir"] = str(out_dir)

    summary_path = out_dir / "summary.json"
    with open(summary_path, "w") as fp:
        json.dump(summary, fp, indent=2)

    _print_summary(summary)
    print(f"\n[paired_runner] summary written: {summary_path}", flush=True)
    print(f"[paired_runner] per-match JSONs in: {matches_dir}", flush=True)


def _emit_incremental(pair_result: dict, matches_dir: pathlib.Path, name_a: str, name_b: str):
    """Write the two per-match JSONs for one pair to disk."""
    if "error" in pair_result:
        err_path = matches_dir / f"pair_{pair_result['pair_index']:04d}_ERROR.json"
        with open(err_path, "w") as fp:
            json.dump(pair_result, fp, indent=2)
        return

    pi = pair_result["pair_index"]
    for label, match in (("m1", pair_result["match1"]), ("m2", pair_result["match2"])):
        out_path = matches_dir / f"pair_{pi:04d}_{label}_{match['agent_a']}_vs_{match['agent_b']}.json"
        # history_json is already a JSON string — parse + re-emit as part of a wrapping object
        try:
            history_obj = json.loads(match["history_json"])
        except Exception:
            history_obj = None
        record = {k: v for k, v in match.items() if k != "history_json"}
        record["history"] = history_obj
        with open(out_path, "w") as fp:
            json.dump(record, fp, indent=2)


def _print_summary(summary: dict):
    print("\n=============== PAIRED BATCH SUMMARY ===============")
    print(f"A = {summary['agent_a']}   B = {summary['agent_b']}")
    print(f"pairs = {summary['n_pairs']}   matches = {summary['n_matches']}   seed = {summary['seed']}")
    print(f"limit_resources = {summary['limit_resources']}   parallel = {summary['parallel']}")
    print(f"wall = {summary['wall_elapsed_s']:.1f}s")
    m = summary["matches"]
    print(
        f"\nMatches:  A wins {m['wins_a']:>4}   B wins {m['wins_b']:>4}   ties {m['ties']:>4}   "
        f"A winrate {m['winrate_a']:.3f} (Wilson95 {m['winrate_a_wilson95'][0]:.3f}–{m['winrate_a_wilson95'][1]:.3f})"
    )
    p = summary["pairs"]
    print(
        f"Pairs:    A sweeps {p['pair_wins_a']:>4}   B sweeps {p['pair_wins_b']:>4}   split {p['pair_ties']:>4}   "
        f"sign-test p = {p['paired_sign_test_p']:.4g}"
    )
    e = summary["errors"]
    print(
        f"Errors:   A crash {e['crashes_a']}  timeout {e['timeouts_a']}  invalid {e['invalid_a']}   "
        f"|   B crash {e['crashes_b']}  timeout {e['timeouts_b']}  invalid {e['invalid_b']}"
    )
    print(f"Score:    mean(A − B) = {summary['score']['mean_score_diff_a_minus_b']:+.2f}")
    r = summary["rat"]
    print(f"Rat:      A caught {r['captures_a']} ({r['captures_per_match_a']:.2f}/match)   "
          f"B caught {r['captures_b']} ({r['captures_per_match_b']:.2f}/match)")
    t = summary["timing"]
    print(f"Timing:   A max per-move {t['a_max_move_s']:.2f}s   B max per-move {t['b_max_move_s']:.2f}s")
    if summary.get("errored_pairs"):
        print(f"\nErrored pairs: {len(summary['errored_pairs'])}")
        for ep in summary["errored_pairs"][:5]:
            print(f"  pair {ep['pair_index']} (seed={ep['pair_seed']}): {ep['error']}")
    print("====================================================")


if __name__ == "__main__":
    main()
