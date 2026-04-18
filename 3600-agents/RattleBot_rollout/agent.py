"""RattleBot_rollout — bold-swing 2-ply + Monte Carlo rollout agent.

Per docs/audit/CONTRARIAN_APR18.md §3 "Bold Swing": replace alpha-beta
with 2-ply lookahead against a greedy opponent model + biased Monte
Carlo rollouts. Rollouts inherently handle:
  - belief evolution (belief @ T each ply inside rollout)
  - greedy opp model (softmax-of-delta)
  - opp-carpet exploitation (opp actually walks our carpet in simulation)

This is an insurance fork — does NOT edit RattleBot/. Only promoted via
paired scrims.

Interface matches CLAUDE.md §4 agent contract:
  PlayerAgent(board, transition_matrix=None, time_left=None)
  .play(board, sensor_data, time_left) -> Move
  .commentate() -> str
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional, Tuple
import random

import numpy as np

from game import board as board_mod
from game.enums import BOARD_SIZE, CARPET_POINTS_TABLE, MoveType
from game.move import Move

from .rat_belief import RatBelief
from .rollout import RolloutPlanner
from .move_gen import ordered_moves, immediate_delta


__all__ = ["PlayerAgent"]


# Budget: leave a safety reserve for the belief update, move-validation,
# and python-level bookkeeping. Target per-turn wall ≈ 2.5–4.0 s when
# time is plentiful, but scale down adaptively based on turns_left.
_PER_TURN_CEILING_S: float = 4.0
_PER_TURN_FLOOR_S: float = 0.6
_SAFETY_RESERVE_S: float = 0.5


class PlayerAgent:
    """Rollout-based agent. Crash-proof with greedy fallback."""

    def __init__(
        self,
        board: board_mod.Board,
        transition_matrix=None,
        time_left: Callable = None,
    ):
        self._rng = random.Random(0xBADC0FFEE)
        self._belief: Optional[RatBelief] = None
        self._planner: Optional[RolloutPlanner] = None
        self._T: Optional[np.ndarray] = None
        self._init_ok: bool = False
        try:
            if transition_matrix is None:
                self._T = np.eye(BOARD_SIZE * BOARD_SIZE, dtype=np.float64)
            else:
                self._T = np.asarray(transition_matrix, dtype=np.float64)
            self._belief = RatBelief(self._T, board)
            self._planner = RolloutPlanner(rng=self._rng)
            self._init_ok = True
        except Exception:
            # Never raise from __init__; play() will use emergency fallback.
            self._init_ok = False

    def commentate(self) -> str:
        return (
            "RattleBot_rollout — bold-swing: 2-ply + Monte Carlo rollouts. "
            "If I won, the gamble paid off."
        )

    # ------------------------------------------------------------------
    # Main play loop

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

    def _play_internal(
        self,
        board: board_mod.Board,
        sensor_data: Tuple,
        time_left: Callable,
    ) -> Move:
        assert self._belief is not None
        assert self._planner is not None
        assert self._T is not None

        # Belief update first (always — consumes sensor_data).
        summary = self._belief.update(board, sensor_data)

        # Per-turn budget. Use `time_left()` for remaining, split evenly
        # across remaining turns, clamped to [_PER_TURN_FLOOR_S,
        # _PER_TURN_CEILING_S].
        try:
            tl = float(time_left()) if time_left is not None else 4.0
        except Exception:
            tl = 4.0
        turns_left = int(
            getattr(board.player_worker, "turns_left", 40) or 40
        )
        turns_left = max(1, turns_left)
        usable = max(0.1, tl - _SAFETY_RESERVE_S)
        base = usable / float(turns_left)
        budget = max(_PER_TURN_FLOOR_S, min(base * 1.1, _PER_TURN_CEILING_S))
        # Don't exceed total remaining.
        budget = min(budget, max(0.1, tl - _SAFETY_RESERVE_S))

        # Run the planner.
        try:
            move = self._planner.plan(
                board=board,
                belief_vec=self._belief.belief,
                T=self._T,
                time_left=time_left,
                budget_s=budget,
            )
        except Exception:
            move = None

        if move is None or not self._looks_valid(board, move):
            move = self._greedy_fallback(board)
        if move is None or not self._looks_valid(board, move):
            move = self._emergency_fallback(board)
        return move

    # ------------------------------------------------------------------
    # Fallbacks

    def _looks_valid(self, board: board_mod.Board, move: Move) -> bool:
        try:
            return bool(board.is_valid_move(move))
        except Exception:
            return False

    def _greedy_fallback(self, board: board_mod.Board) -> Optional[Move]:
        """Pick the legal move with highest immediate_delta.

        Filters k=1 carpet unless it's the only option.
        """
        try:
            legal = board.get_valid_moves(exclude_search=True)
        except Exception:
            legal = []
        if not legal:
            return None
        has_non_k1 = any(
            not (int(m.move_type) == int(MoveType.CARPET) and m.roll_length < 2)
            for m in legal
        )
        if has_non_k1:
            legal = [
                m for m in legal
                if not (
                    int(m.move_type) == int(MoveType.CARPET)
                    and m.roll_length < 2
                )
            ]
        try:
            return max(legal, key=immediate_delta)
        except Exception:
            return legal[0] if legal else None

    def _emergency_fallback(self, board: board_mod.Board) -> Move:
        """Crash-proof last resort — FloorBot-style. Never raises."""
        try:
            valid = board.get_valid_moves()
            if valid:
                best = None
                best_pts = 1
                for m in valid:
                    if m.move_type == MoveType.CARPET:
                        pts = CARPET_POINTS_TABLE.get(m.roll_length, -999)
                        if pts > best_pts:
                            best_pts = pts
                            best = m
                if best is not None:
                    return best
                prime_moves = [m for m in valid if m.move_type == MoveType.PRIME]
                if prime_moves:
                    return prime_moves[0]
                plain_moves = [m for m in valid if m.move_type == MoveType.PLAIN]
                if plain_moves:
                    return plain_moves[0]
                return valid[0]
        except Exception:
            pass
        try:
            valid = board.get_valid_moves(exclude_search=False)
            if valid:
                return self._rng.choice(valid)
        except Exception:
            pass
        return Move.search((0, 0))
