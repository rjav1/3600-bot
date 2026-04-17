"""Tiny smoke test: play FloorBot vs Yolanda once locally.

Usage (from repo root):
    python 3600-agents/FloorBot/tests/test_selfplay.py
"""
import pathlib
import sys


def main():
    top = pathlib.Path(__file__).resolve().parents[3]
    engine_dir = str(top / "engine")
    agents_dir = str(top / "3600-agents")
    for p in (engine_dir, agents_dir):
        if p not in sys.path:
            sys.path.insert(0, p)

    from gameplay import play_game
    from game.enums import ResultArbiter

    board, *_ = play_game(
        agents_dir, agents_dir, "FloorBot", "Yolanda",
        display_game=False, delay=0.0, clear_screen=False,
        record=False, limit_resources=False,
    )
    w = board.get_winner()
    assert w in (ResultArbiter.PLAYER_A, ResultArbiter.PLAYER_B, ResultArbiter.TIE), \
        f"Unexpected winner: {w}"
    print(f"Smoke test OK. Winner: {w.name}")


if __name__ == "__main__":
    main()
