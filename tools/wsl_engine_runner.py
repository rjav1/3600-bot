"""WSL engine match runner for T-62 retest.

Runs N matches between two agents using the real engine (`play_game`)
inside WSL Python 3.12 Linux. Prints one JSON line per match to stdout
with keys: idx, seed, result (ResultArbiter), reason (WinReason), pts_a,
pts_b, turns, elapsed_s. Intended to run inside `tools/sandbox_sim.sh`
under `unshare -r -n` so network is truly dropped.

Usage:
    python3 tools/wsl_engine_runner.py \\
        --a RattleBot --b Yolanda --n 5 --seed-base 600 \\
        [--limit-resources]
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import random
import sys
import time

# JAX under WSL+unshare can hit EAGAIN creating its thread pool on a
# fresh namespace. Reduce the Eigen thread pool at import time. The
# engine's jax use is cosmetic (imported eagerly in gameplay.py) so
# this has no functional impact.
os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false")
os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_ROOT / "engine"
AGENTS_DIR = REPO_ROOT / "3600-agents"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--n", type=int, default=1)
    p.add_argument("--seed-base", type=int, default=0)
    p.add_argument("--limit-resources", action="store_true")
    args = p.parse_args()

    sys.path.insert(0, str(ENGINE_DIR))
    sys.path.insert(0, str(AGENTS_DIR))
    from gameplay import play_game

    # Redirect engine's chatty prints to stderr so stdout stays
    # clean JSONL.
    real_stdout = sys.stdout
    sys.stdout = sys.stderr

    ok = 0
    for i in range(args.n):
        seed = args.seed_base + i
        random.seed(seed)
        t0 = time.perf_counter()
        try:
            result = play_game(
                str(AGENTS_DIR),
                str(AGENTS_DIR),
                args.a,
                args.b,
                display_game=False,
                delay=0.0,
                clear_screen=False,
                record=False,
                limit_resources=args.limit_resources,
                use_gpu=False,
            )
            final_board = result[0]
            winner = int(getattr(final_board, "winner", -1))
            reason = getattr(final_board, "win_reason", None)
            reason_v = int(reason) if reason is not None else -1
            # player_worker/opponent_worker map to A/B depending on
            # is_player_a_turn at game end. Resolve to absolute A/B.
            if getattr(final_board, "is_player_a_turn", True):
                pa = int(final_board.player_worker.points)
                pb = int(final_board.opponent_worker.points)
            else:
                pa = int(final_board.opponent_worker.points)
                pb = int(final_board.player_worker.points)
            turns = int(final_board.turn_count)
            rec = {
                "idx": i,
                "seed": seed,
                "a": args.a,
                "b": args.b,
                "result": winner,
                "reason": reason_v,
                "pts_a": pa,
                "pts_b": pb,
                "turns": turns,
                "elapsed_s": round(time.perf_counter() - t0, 2),
                "ok": True,
            }
            ok += 1
        except Exception as e:
            import traceback
            rec = {
                "idx": i,
                "seed": seed,
                "a": args.a,
                "b": args.b,
                "ok": False,
                "exception": type(e).__name__,
                "message": str(e)[:400],
                "traceback": traceback.format_exc()[-800:],
                "elapsed_s": round(time.perf_counter() - t0, 2),
            }
        print(json.dumps(rec), flush=True, file=real_stdout)

    print(
        json.dumps({"summary": True, "completed": ok, "total": args.n}),
        flush=True,
        file=real_stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
