"""RattleBot v0.1 — end-to-end wiring.

Entry-point `PlayerAgent` per CLAUDE.md §4 / BOT_STRATEGY.md v1.1 §3.1.

Per-turn pipeline:
    1. belief.update(board, sensor_data) — canonical 4-step HMM filter.
       RatBelief reads `board.opponent_search` / `board.player_search`
       internally to apply opp-search and post-capture-reset updates.
    2. time_mgr.start_turn(board, time_left_fn, belief) -> budget_s.
    3. search.root_search_decision(board, belief, heuristic, budget).
    4. On SEARCH return, the belief reset after a capture is applied on
       the next turn by belief.update via `board.player_search`.

Every `play()` call is wrapped in try/except that falls through to a
locally-duplicated FloorBot-style emergency fallback (D-006 — duplicate,
not import, for submission-isolation so RattleBot.zip has no cross-agent
dependency).
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


__all__ = ["PlayerAgent"]


class PlayerAgent:
    """RattleBot primary agent.

    Alpha-beta + iterative deepening + Zobrist TT over a 7-feature
    linear heuristic (F1/F3/F4/F5/F7/F11/F12), with a forward-filter
    HMM rat belief. SEARCH is root-only, EV-gated via
    `search.root_search_decision`.
    """

    def __init__(
        self,
        board: board_mod.Board,
        transition_matrix=None,
        time_left: Callable = None,
    ):
        self._rng = random.Random(0xBA11A111)
        self._belief: Optional[RatBelief] = None
        self._search: Optional[Search] = None
        self._heuristic: Optional[Heuristic] = None
        self._time_mgr: Optional[TimeManager] = None
        self._zobrist: Optional[Zobrist] = None
        self._init_ok: bool = False

        try:
            if transition_matrix is None:
                # Degenerate graceful fallback: identity T means belief
                # stays put. Realistic path always sees a 64x64 T.
                T = np.eye(BOARD_SIZE * BOARD_SIZE, dtype=np.float64)
            else:
                T = np.asarray(transition_matrix, dtype=np.float64)
            self._belief = RatBelief(T, board)
            self._zobrist = Zobrist()
            self._search = Search(zobrist=self._zobrist)
            self._heuristic = Heuristic()
            self._time_mgr = TimeManager()
            self._init_ok = True
        except Exception:
            # Never raise out of __init__; emergency fallback in play()
            # will still return legal moves.
            self._init_ok = False

    def commentate(self) -> str:
        return "RattleBot v0.1 — alpha-beta + ID + HMM belief."

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
        assert self._search is not None
        assert self._heuristic is not None
        assert self._time_mgr is not None

        belief_summary = self._belief.update(board, sensor_data)
        budget_s = self._time_mgr.start_turn(
            board, time_left, belief_summary
        )
        # SEARCH only when P(rat_in_argmax) > 1/3 (the unconditional
        # break-even on a +4/-2 bet per GAME_SPEC §2.4). Heuristic in v0.1
        # is uncalibrated; without this guard the search-gate fires on
        # near-flat belief because F11/F12 make heuristic leaf-eval
        # very negative -- see RATTLEBOT_V01_NOTES.md.
        if belief_summary.max_mass > (1.0 / 3.0):
            move = self._search.root_search_decision(
                board,
                belief_summary,
                self._heuristic.V_leaf,
                budget_s,
                safety_s=self._time_mgr.safety_s,
            )
        else:
            move = self._search.iterative_deepen(
                board,
                belief_summary,
                self._heuristic.V_leaf,
                budget_s,
                safety_s=self._time_mgr.safety_s,
            )
        if move is None or not self._looks_valid(board, move):
            move = self._emergency_fallback(board)
        self._time_mgr.end_turn(0.0)
        return move

    # ------------------------------------------------------------------
    # Emergency fallback (duplicated from FloorBot per D-006 isolation)

    def _looks_valid(self, board: board_mod.Board, move: Move) -> bool:
        try:
            return bool(board.is_valid_move(move))
        except Exception:
            return False

    def _emergency_fallback(self, board: board_mod.Board) -> Move:
        """Crash-proof move selection. Never raises."""
        try:
            move = self._floor_choose(board)
            if move is not None and self._looks_valid(board, move):
                return move
        except Exception:
            pass
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

    def _floor_choose(self, board: board_mod.Board) -> Optional[Move]:
        """Lightweight FloorBot-style pick — carpet(k>=2) > prime > plain."""
        valid = board.get_valid_moves()
        if not valid:
            return None
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
        prime_moves = [m for m in valid if m.move_type == MoveType.PRIME]
        plain_moves = [m for m in valid if m.move_type == MoveType.PLAIN]
        if prime_moves:
            return prime_moves[0]
        if plain_moves:
            return plain_moves[0]
        return valid[0]
