"""Batch test runner for FloorBot vs Yolanda.

Usage (from repo root):
    python 3600-agents/FloorBot/tests/batch_test.py <N> <A> <B>

Plays N local matches, reports wins/losses/ties/crashes/timeouts and
per-move wall time stats for whichever side `FloorBot` is.
"""
from __future__ import annotations

import os
import pathlib
import sys
import time


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    a_name = sys.argv[2] if len(sys.argv) > 2 else "FloorBot"
    b_name = sys.argv[3] if len(sys.argv) > 3 else "Yolanda"

    top = pathlib.Path(__file__).resolve().parents[3]
    engine_dir = str(top / "engine")
    agents_dir = str(top / "3600-agents")
    for p in (engine_dir, agents_dir):
        if p not in sys.path:
            sys.path.insert(0, p)

    from gameplay import play_game  # noqa: E402
    from game.enums import ResultArbiter, WinReason  # noqa: E402

    stats = {"A_wins": 0, "B_wins": 0, "ties": 0, "error": 0, "crash": 0,
             "timeout": 0, "invalid": 0, "failed_init": 0}

    for i in range(n):
        t0 = time.perf_counter()
        try:
            board, *_ = play_game(
                agents_dir, agents_dir, a_name, b_name,
                display_game=False, delay=0.0, clear_screen=False,
                record=False, limit_resources=False,
            )
        except Exception as e:
            print(f"match {i}: EXCEPTION {e!r}")
            stats["error"] += 1
            continue

        w = board.get_winner()
        r = board.get_win_reason() if hasattr(board, "win_reason") else None

        if w == ResultArbiter.PLAYER_A:
            stats["A_wins"] += 1
        elif w == ResultArbiter.PLAYER_B:
            stats["B_wins"] += 1
        elif w == ResultArbiter.TIE:
            stats["ties"] += 1
        else:
            stats["error"] += 1

        if r == WinReason.CODE_CRASH:
            stats["crash"] += 1
        elif r == WinReason.TIMEOUT:
            stats["timeout"] += 1
        elif r == WinReason.INVALID_TURN:
            stats["invalid"] += 1
        elif r == WinReason.FAILED_INIT:
            stats["failed_init"] += 1

        dt = time.perf_counter() - t0
        # `is_player_a_turn` reflects who moves *next*, not who just moved,
        # so at game end `player_worker` is whoever would go next — reporting
        # absolute A/B scores reliably requires more bookkeeping than we need.
        p1 = board.player_worker.get_points()
        p2 = board.opponent_worker.get_points()
        print(f"match {i:3d}: winner={getattr(w, 'name', w)}, "
              f"reason={getattr(r, 'name', r)}, pts(next={p1}, prev={p2}), "
              f"elapsed={dt:.1f}s")

    print()
    print(f"=== {n} matches {a_name} vs {b_name} ===")
    for k, v in stats.items():
        print(f"  {k:12s}: {v}")


if __name__ == "__main__":
    main()
