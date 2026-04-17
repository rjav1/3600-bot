"""Microbench: invoke FloorBot.play() many times on a freshly-initialized
board-state and measure per-move wall time.

Usage (from repo root):
    python 3600-agents/FloorBot/tests/bench_play.py
"""
from __future__ import annotations

import pathlib
import random
import sys
import time


def main():
    top = pathlib.Path(__file__).resolve().parents[3]
    engine_dir = str(top / "engine")
    agents_dir = str(top / "3600-agents")
    for p in (engine_dir, agents_dir):
        if p not in sys.path:
            sys.path.insert(0, p)

    from game.board import Board  # noqa: E402
    from game.enums import BOARD_SIZE, Cell, Direction, Noise, MoveType  # noqa: E402
    from FloorBot.agent import PlayerAgent  # noqa: E402

    random.seed(42)

    durations = []
    crashes = 0
    invalids = 0
    n_games = 50
    for g in range(n_games):
        board = Board(time_to_play=360.0, build_history=False)
        # Simulate some blockers + priming + player locations
        shapes = [(2, 3), (3, 2), (2, 2)]
        for ox, oy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
            w, h = random.choice(shapes)
            for dx in range(w):
                for dy in range(h):
                    x = dx if ox == 0 else BOARD_SIZE - 1 - dx
                    y = dy if oy == 0 else BOARD_SIZE - 1 - dy
                    board.set_cell((x, y), Cell.BLOCKED)
        board.player_worker.position = (2, 3)
        board.opponent_worker.position = (5, 3)

        agent = PlayerAgent(board)

        # play 40 moves and time each
        for turn in range(40):
            sensor = (random.choice(list(Noise)), random.randint(0, 10))
            t0 = time.perf_counter()
            move = agent.play(board, sensor, lambda: 999.0)
            dt = time.perf_counter() - t0
            durations.append(dt)
            if move is None:
                crashes += 1
                break
            if not board.is_valid_move(move):
                invalids += 1
                break
            ok = board.apply_move(move, timer=dt, check_ok=True)
            if not ok:
                invalids += 1
                break
            if board.is_game_over():
                break
            board.reverse_perspective()
            # sprinkle some random floor changes to simulate game variance
            for _ in range(1):
                rx, ry = random.randint(0, 7), random.randint(0, 7)
                if board.get_cell((rx, ry)) == Cell.SPACE and \
                   (rx, ry) != board.player_worker.position and \
                   (rx, ry) != board.opponent_worker.position:
                    board.set_cell((rx, ry), Cell.PRIMED)

    durations.sort()
    n = len(durations)
    p = lambda q: durations[int(q * (n - 1))]
    print(f"calls           : {n}")
    print(f"mean (ms)       : {1000 * sum(durations) / n:.3f}")
    print(f"p50  (ms)       : {1000 * p(0.50):.3f}")
    print(f"p90  (ms)       : {1000 * p(0.90):.3f}")
    print(f"p99  (ms)       : {1000 * p(0.99):.3f}")
    print(f"max  (ms)       : {1000 * durations[-1]:.3f}")
    print(f"crashes         : {crashes}")
    print(f"invalids        : {invalids}")


if __name__ == "__main__":
    main()
