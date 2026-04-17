"""FakeCarrie_v2 — harder proxy for the staff Carrie reference bot.

See `docs/plan/FAKE_CARRIE_V2.md` for design notes. Pipeline per play():
  1. belief.update(board, sensor_data)
  2. time_mgr.budget_for_turn(...)
  3. If `belief.max_mass > SEARCH_MASS_THRESHOLD` and the best-cell
     SEARCH move is legal, take it (root-only, simple threshold).
  4. Otherwise alpha-beta + iterative deepening with the 5-feature heuristic.
  5. Anything raising falls through to `_emergency_fallback`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional, Tuple
import random

import numpy as np

from game import board as board_mod
from game.enums import BOARD_SIZE, CARPET_POINTS_TABLE, MoveType
from game.move import Move

from .heuristic import Heuristic
from .rat_belief import RatBelief
from .search import Search
from .time_mgr import TimeManager
from .zobrist import Zobrist


_N_CELLS = BOARD_SIZE * BOARD_SIZE
SEARCH_MASS_THRESHOLD: float = 0.35


__all__ = ["PlayerAgent"]


class PlayerAgent:
    def __init__(
        self,
        board: board_mod.Board,
        transition_matrix=None,
        time_left: Callable = None,
    ) -> None:
        self._rng = random.Random(0xCA221E2)
        self._belief: Optional[RatBelief] = None
        self._search: Optional[Search] = None
        self._heuristic: Optional[Heuristic] = None
        self._time_mgr: Optional[TimeManager] = None
        self._init_ok: bool = False
        try:
            if transition_matrix is None:
                T = np.eye(_N_CELLS, dtype=np.float64)
            else:
                T = np.asarray(transition_matrix, dtype=np.float64)
            self._belief = RatBelief(T)
            self._search = Search(zobrist=Zobrist())
            self._heuristic = Heuristic()
            self._time_mgr = TimeManager()
            self._init_ok = True
        except Exception:
            self._init_ok = False

    def commentate(self) -> str:
        return (
            "FakeCarrie_v2 — alpha-beta + ID + Zobrist TT, H1 cell-potential "
            "heuristic (5 features, hand-tuned). Harder proxy for Carrie."
        )

    def play(
        self,
        board: board_mod.Board,
        sensor_data: Tuple,
        time_left: Callable,
    ) -> Move:
        if not self._init_ok:
            return self._emergency_fallback(board)
        try:
            return self._play_internal(board, sensor_data, time_left)
        except Exception:
            return self._emergency_fallback(board)

    def _play_internal(self, board, sensor_data, time_left) -> Move:
        assert self._belief is not None
        assert self._search is not None
        assert self._heuristic is not None
        assert self._time_mgr is not None

        self._belief.update(board, sensor_data)
        budget_s = self._time_mgr.budget_for_turn(board, time_left)

        if self._belief.max_mass > SEARCH_MASS_THRESHOLD:
            idx = self._belief.argmax
            loc = (idx % BOARD_SIZE, idx // BOARD_SIZE)
            search_move = Move.search(loc)
            try:
                if board.is_valid_move(search_move):
                    return search_move
            except Exception:
                pass

        move = self._search.iterative_deepen(
            board,
            eval_fn=self._heuristic.V_leaf,
            belief_max=self._belief.max_mass,
            budget_s=budget_s,
        )
        if move is None or not self._looks_valid(board, move):
            return self._emergency_fallback(board)
        return move

    def _looks_valid(self, board, move) -> bool:
        try:
            return bool(board.is_valid_move(move))
        except Exception:
            return False

    def _emergency_fallback(self, board) -> Move:
        try:
            valid = board.get_valid_moves()
            if valid:
                best_carpet = None
                best_pts = 1
                for m in valid:
                    if m.move_type == MoveType.CARPET:
                        pts = CARPET_POINTS_TABLE.get(m.roll_length, -999)
                        if pts > best_pts:
                            best_pts = pts
                            best_carpet = m
                if best_carpet is not None:
                    return best_carpet
                for m in valid:
                    if m.move_type == MoveType.PRIME:
                        return m
                for m in valid:
                    if m.move_type == MoveType.PLAIN:
                        return m
                return self._rng.choice(valid)
        except Exception:
            pass
        try:
            valid = board.get_valid_moves(exclude_search=False)
            if valid:
                return self._rng.choice(valid)
        except Exception:
            pass
        return Move.search((0, 0))
