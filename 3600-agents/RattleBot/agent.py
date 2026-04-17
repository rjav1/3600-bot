"""RattleBot v0.2 — end-to-end wiring.

Entry-point `PlayerAgent` per CLAUDE.md §4 / BOT_STRATEGY.md v1.1 §3.1
with v0.2 updates from BOT_STRATEGY_V02_ADDENDUM:
- T-20a: per-turn ceiling lifted 3.0 s -> 6.0 s, configurable.
- T-20b: `time_mgr` is the single owner of the 0.5 s safety reserve;
  `search.iterative_deepen(..., safety_s=0.0)` below.

Per-turn pipeline:
    1. belief.update(board, sensor_data) — canonical 4-step HMM filter.
    2. time_mgr.start_turn(board, time_left_fn, belief) -> budget_s
       (already has safety_s reserved).
    3. search.root_search_decision / iterative_deepen(..., safety_s=0.0)
       -- no double-subtract.
    4. Post-capture belief reset is applied on the next turn by
       belief.update via `board.player_search`.

Every `play()` call is wrapped in try/except that falls through to a
locally-duplicated FloorBot-style emergency fallback (D-006 — duplicate,
not import, for submission-isolation).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional, Tuple
import json
import os
import random

import numpy as np

from game import board as board_mod
from game.enums import BOARD_SIZE, CARPET_POINTS_TABLE, MoveType
from game.move import Move

from .heuristic import Heuristic, N_FEATURES, W_INIT
from .rat_belief import RatBelief
from .search import Search
from .time_mgr import TimeManager
from .zobrist import Zobrist


def _load_tuned_weights() -> Optional[np.ndarray]:
    """Resolve BO-tuned weights if available.

    Resolution order (T-20d §2.5 handoff):
      1. `RATTLEBOT_WEIGHTS_JSON` env var points at a JSON file -> load it.
      2. `weights.json` sibling of this module -> load it.
      3. Otherwise return None (agent falls back to hard-coded W_INIT).

    JSON format: either a bare JSON list of N_FEATURES floats, or an
    object with key "weights" mapping to the same list.
    Any parse/shape error is swallowed (fallback to W_INIT).
    """
    candidates = []
    env_path = os.environ.get("RATTLEBOT_WEIGHTS_JSON")
    if env_path:
        candidates.append(env_path)
    candidates.append(
        os.path.join(os.path.dirname(__file__), "weights.json")
    )
    for path in candidates:
        if not path or not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            if isinstance(raw, dict) and "weights" in raw:
                arr = np.asarray(raw["weights"], dtype=np.float64)
            else:
                arr = np.asarray(raw, dtype=np.float64)
            if arr.shape == (N_FEATURES,):
                return arr
        except Exception:
            continue
    return None


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
            tuned_w = _load_tuned_weights()
            self._heuristic = Heuristic(weights=tuned_w)
            self._time_mgr = TimeManager()
            self._init_ok = True
        except Exception:
            # Never raise out of __init__; emergency fallback in play()
            # will still return legal moves.
            self._init_ok = False

    def commentate(self) -> str:
        ceiling = (
            self._time_mgr.per_turn_ceiling_s
            if self._time_mgr is not None
            else float("nan")
        )
        return (
            "RattleBot v0.2 — alpha-beta + ID + HMM belief "
            f"(ceiling={ceiling:.1f}s)"
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
        # very negative -- see RATTLEBOT_V01_NOTES.md S-1.
        # T-20b: `time_mgr.start_turn` already reserved `safety_s`; pass
        # 0.0 to search so we don't double-subtract.
        if belief_summary.max_mass > (1.0 / 3.0):
            move = self._search.root_search_decision(
                board,
                belief_summary,
                self._heuristic.V_leaf,
                budget_s,
                safety_s=0.0,
            )
        else:
            move = self._search.iterative_deepen(
                board,
                belief_summary,
                self._heuristic.V_leaf,
                budget_s,
                safety_s=0.0,
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
