"""Consistency check: does `get_valid_moves()` ever return a move
that `is_valid_move()` rejects?

If it does, that's an engine bug and FloorBot's policy (which trusts
get_valid_moves) would return an INVALID_MOVE unknowingly.
"""
import pathlib
import random
import sys


def _bootstrap():
    top = pathlib.Path(__file__).resolve().parents[3]
    for p in (top / "engine", top / "3600-agents"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


def main():
    _bootstrap()
    from game.board import Board
    from game.enums import BOARD_SIZE, Cell

    random.seed(12345)
    mismatches = 0
    tested = 0

    for trial in range(2000):
        b = Board(time_to_play=240.0, build_history=False)
        # Random blockers
        for _ in range(random.randint(6, 14)):
            x, y = random.randint(0, 7), random.randint(0, 7)
            b.set_cell((x, y), Cell.BLOCKED)
        # Random primes
        for _ in range(random.randint(0, 14)):
            x, y = random.randint(0, 7), random.randint(0, 7)
            if b.get_cell((x, y)) == Cell.SPACE:
                b.set_cell((x, y), Cell.PRIMED)
        # Random carpets
        for _ in range(random.randint(0, 10)):
            x, y = random.randint(0, 7), random.randint(0, 7)
            if b.get_cell((x, y)) == Cell.SPACE:
                b.set_cell((x, y), Cell.CARPET)
        # Random worker positions (not on BLOCKED/PRIMED/CARPET ideally)
        while True:
            px, py = random.randint(0, 7), random.randint(0, 7)
            ox, oy = random.randint(0, 7), random.randint(0, 7)
            if (px, py) != (ox, oy):
                break
        b.player_worker.position = (px, py)
        b.opponent_worker.position = (ox, oy)

        moves = b.get_valid_moves(exclude_search=False)
        for m in moves:
            tested += 1
            if not b.is_valid_move(m):
                mismatches += 1
                print(f"trial {trial}: MISMATCH move={m} "
                      f"player={(px,py)} opp={(ox,oy)}")

    print(f"tested {tested} moves, mismatches={mismatches}")


if __name__ == "__main__":
    main()
