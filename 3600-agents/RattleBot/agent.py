"""RattleBot v0.0 — scaffold placeholder.

Real `PlayerAgent` lands in T-18 (integrator wiring). Until then this
placeholder returns a random valid move so the package is runnable end-to-end
and the interface lock-in (`.types`) can be validated.

FloorBot-style emergency fallback is wired in at every `play()` call per
D-006 (RattleBot embeds FloorBot's `emergency_fallback`).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Tuple
import random

from game import board as board_mod
from game.move import Move

from .types import BeliefSummary  # noqa: F401  — interface anchor


class PlayerAgent:
    def __init__(
        self,
        board: board_mod.Board,
        transition_matrix=None,
        time_left: Callable = None,
    ):
        # Placeholder: real init (T-18) will precompute p_0, allocate TT,
        # build Zobrist tables, warm the heuristic JIT. For now we just
        # stash T so the object is well-formed.
        self.transition_matrix = transition_matrix
        self._rng = random.Random(0xBA11A111)

    def commentate(self) -> str:
        return "RattleBot v0.0 placeholder — scaffold only."

    def play(
        self,
        board: board_mod.Board,
        sensor_data: Tuple,
        time_left: Callable,
    ) -> Move:
        try:
            valid = board.get_valid_moves()
            if valid:
                return self._rng.choice(valid)
        except Exception:
            pass
        return self._emergency_fallback(board)

    # ------------------------------------------------------------------
    # Fallback (per D-006 — mirrors FloorBot._safe_fallback)

    def _emergency_fallback(self, board: board_mod.Board) -> Move:
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
        return Move.search((0, 0))
