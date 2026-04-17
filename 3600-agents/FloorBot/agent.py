"""FloorBot — crash-proof reactive-policy agent.

Insurance bot: never crashes, never times out, never makes an invalid move.
Not trying to be strong. Trying to be unkillable. Per docs/plan/FLOOR_BOT.md.
"""

from collections.abc import Callable
from typing import List, Optional, Tuple
import random

from game import board as board_mod
from game.enums import (
    BOARD_SIZE,
    CARPET_POINTS_TABLE,
    Cell,
    Direction,
    MoveType,
    loc_after_direction,
)
from game.move import Move


_DIRECTIONS = (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT)


class PlayerAgent:
    def __init__(self, board, transition_matrix=None, time_left: Callable = None):
        try:
            self._rng = random.Random(0xF1008070)
        except Exception:
            self._rng = random

    def commentate(self):
        return "FloorBot: boring, alive, and still on the board."

    def play(
        self,
        board: board_mod.Board,
        sensor_data: Tuple,
        time_left: Callable,
    ):
        try:
            move = self._choose(board)
            if move is not None and board.is_valid_move(move):
                return move
        except Exception:
            pass
        return self._safe_fallback(board)

    # ------------------------------------------------------------------
    # Policy

    def _choose(self, board: board_mod.Board) -> Optional[Move]:
        valid = board.get_valid_moves()
        if not valid:
            return None

        carpet_moves = [m for m in valid if m.move_type == MoveType.CARPET]
        prime_moves = [m for m in valid if m.move_type == MoveType.PRIME]
        plain_moves = [m for m in valid if m.move_type == MoveType.PLAIN]

        # 1. Finish a big carpet roll (k >= 2 only — k=1 is -1 pt).
        best_carpet = self._best_carpet(carpet_moves)
        if best_carpet is not None:
            return best_carpet

        # 2 + 3. Prime to extend a line, else simple prime step.
        prime_choice = self._best_prime(board, prime_moves)
        if prime_choice is not None:
            return prime_choice

        # 4. Plain step toward the half with more open area.
        plain_choice = self._best_plain(board, plain_moves)
        if plain_choice is not None:
            return plain_choice

        # 5. Any valid move (including a -1 carpet if that's all we have).
        return valid[0]

    def _best_carpet(self, carpet_moves: List[Move]) -> Optional[Move]:
        best = None
        best_pts = 1  # require > 1 point to take (skip k=1 which is -1)
        for m in carpet_moves:
            pts = CARPET_POINTS_TABLE.get(m.roll_length, -999)
            if pts > best_pts:
                best_pts = pts
                best = m
        return best

    def _best_prime(
        self, board: board_mod.Board, prime_moves: List[Move]
    ) -> Optional[Move]:
        if not prime_moves:
            return None

        my_loc = board.player_worker.get_location()
        scored: List[Tuple[int, int, Move]] = []
        for m in prime_moves:
            d = m.direction
            line = self._line_potential(board, my_loc, d)
            # Bonus if there's already a PRIMED cell further along the line —
            # we're extending our own carpet-line.
            extension = self._extension_bonus(board, my_loc, d)
            score = line + extension
            scored.append((score, self._dir_tiebreak(d), m))

        scored.sort(key=lambda t: (-t[0], t[1]))
        top_score = scored[0][0]
        if top_score <= 0:
            # No forward space — priming here traps us. Skip.
            return None
        return scored[0][2]

    def _best_plain(
        self, board: board_mod.Board, plain_moves: List[Move]
    ) -> Optional[Move]:
        if not plain_moves:
            return None

        my_loc = board.player_worker.get_location()
        scored: List[Tuple[int, int, Move]] = []
        for m in plain_moves:
            d = m.direction
            next_loc = loc_after_direction(my_loc, d)
            # Prefer moves that head toward more open territory.
            area = self._half_open_area(board, next_loc)
            line = self._line_potential(board, my_loc, d)
            score = area * 2 + line
            scored.append((score, self._dir_tiebreak(d), m))

        scored.sort(key=lambda t: (-t[0], t[1]))
        return scored[0][2]

    # ------------------------------------------------------------------
    # Heuristics

    def _line_potential(
        self, board: board_mod.Board, origin: Tuple[int, int], d: Direction
    ) -> int:
        """Count contiguous SPACE cells in direction d starting from origin+1."""
        count = 0
        loc = origin
        for _ in range(BOARD_SIZE - 1):
            loc = loc_after_direction(loc, d)
            if not board.is_valid_cell(loc):
                break
            try:
                cell = board.get_cell(loc)
            except Exception:
                break
            if cell != Cell.SPACE:
                break
            if loc == board.opponent_worker.get_location():
                break
            count += 1
        return count

    def _extension_bonus(
        self, board: board_mod.Board, origin: Tuple[int, int], d: Direction
    ) -> int:
        """+2 if there's a PRIMED cell 2-3 steps further in direction d
        (potential long-roll setup)."""
        loc = origin
        bonus = 0
        for step in range(1, 4):
            loc = loc_after_direction(loc, d)
            if not board.is_valid_cell(loc):
                break
            try:
                cell = board.get_cell(loc)
            except Exception:
                break
            if cell == Cell.PRIMED and step >= 2:
                bonus += 2
        return bonus

    def _half_open_area(
        self, board: board_mod.Board, target: Tuple[int, int]
    ) -> int:
        """Count SPACE cells in the quadrant containing `target` as a rough
        'how much room is over there' heuristic."""
        if not board.is_valid_cell(target):
            return 0
        tx, ty = target
        x_range = range(0, 4) if tx < 4 else range(4, 8)
        y_range = range(0, 4) if ty < 4 else range(4, 8)
        count = 0
        for x in x_range:
            for y in y_range:
                try:
                    if board.get_cell((x, y)) == Cell.SPACE:
                        count += 1
                except Exception:
                    continue
        return count

    def _dir_tiebreak(self, d: Direction) -> int:
        # Deterministic but arbitrary — just ensures sort stability across runs.
        return int(d)

    # ------------------------------------------------------------------
    # Fallback

    def _safe_fallback(self, board: board_mod.Board) -> Move:
        try:
            valid = board.get_valid_moves()
            if valid:
                return self._rng.choice(valid)
        except Exception:
            pass
        try:
            valid = board.get_valid_moves(exclude_search=False)
            if valid:
                return self._rng.choice(valid)
        except Exception:
            pass
        # Last resort: a search at (0,0). SEARCH only requires in-bounds.
        return Move.search((0, 0))
