"""FakeAlbert — best-guess replica of staff reference bot Albert.

Per assignment.pdf §9: expectiminimax + HMM + VERY simple heuristic.
This is a PROXY used to sanity-check RattleBot against the actual-
gating opponent tier. It is NOT real Albert.

Design (per docs/plan/FAKE_OPPONENTS.md):
- alpha-beta with iterative deepening, depth cap 3.
- Minimal inline HMM rat-belief (forward filter).
- 3-feature linear heuristic:
    v = 2.0 * score_diff + 0.3 * primed_count + 0.2 * carpeted_count
- SEARCH root-only, gated by simple EV threshold (max belief > 1/3).
- Crash-proof fallback (copies FloorBot pattern).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional, Tuple
import math
import random
import time

import numpy as np

from game import board as board_mod
from game.enums import (
    BOARD_SIZE,
    CARPET_POINTS_TABLE,
    Cell,
    MoveType,
    Noise,
)
from game.move import Move


_N_CELLS = BOARD_SIZE * BOARD_SIZE  # 64
_INF = 1e18

# Noise likelihood: rows Noise, cols Cell (SPACE, PRIMED, CARPET, BLOCKED).
_NOISE_LIK = np.array(
    [
        [0.7, 0.1, 0.1, 0.5],  # SQUEAK
        [0.15, 0.8, 0.1, 0.3],  # SCRATCH
        [0.15, 0.1, 0.8, 0.2],  # SQUEAL
    ],
    dtype=np.float64,
)

_DIST_OFFSETS = (-1, 0, 1, 2)
_DIST_PROBS = (0.12, 0.70, 0.12, 0.06)
_MAX_TRUE_DIST = (BOARD_SIZE - 1) * 2
_MAX_REPORTED = _MAX_TRUE_DIST + 2


def _build_dist_lik() -> np.ndarray:
    tbl = np.zeros((_MAX_TRUE_DIST + 1, _MAX_REPORTED + 1), dtype=np.float64)
    for td in range(_MAX_TRUE_DIST + 1):
        for off, p in zip(_DIST_OFFSETS, _DIST_PROBS):
            tbl[td, max(0, td + off)] += p
    return tbl


_DIST_LIK = _build_dist_lik()


def _build_manhattan() -> np.ndarray:
    coords = np.array(
        [(i % BOARD_SIZE, i // BOARD_SIZE) for i in range(_N_CELLS)],
        dtype=np.int32,
    )
    dx = np.abs(coords[:, None, 0] - coords[None, :, 0])
    dy = np.abs(coords[:, None, 1] - coords[None, :, 1])
    return (dx + dy).astype(np.int32)


_MANHATTAN = _build_manhattan()


class _RatBelief:
    """Minimal forward-filter HMM over 64 rat-cells."""

    def __init__(self, T: np.ndarray) -> None:
        self.T = T
        p = np.zeros(_N_CELLS, dtype=np.float64)
        p[0] = 1.0
        for _ in range(1000):
            p = p @ T
        s = p.sum()
        self.p0 = p / s if s > 0 else p
        self.belief = self.p0.copy()
        self._first = True

    def update(
        self,
        board: board_mod.Board,
        sensor: Tuple[Noise, int],
    ) -> None:
        noise, rd = sensor
        skip = (
            self._first
            and bool(getattr(board, "is_player_a_turn", False))
            and int(getattr(board, "turn_count", 0)) == 0
        )
        if not skip:
            self.belief = self.belief @ self.T
            loc, hit = getattr(board, "opponent_search", (None, False))
            if loc is not None:
                if hit:
                    self.belief = self.p0.copy()
                else:
                    self.belief[loc[1] * BOARD_SIZE + loc[0]] = 0.0
                    self._renorm()
        self.belief = self.belief @ self.T

        # Sensor update.
        cell_types = np.empty(_N_CELLS, dtype=np.int64)
        for i in range(_N_CELLS):
            x, y = i % BOARD_SIZE, i // BOARD_SIZE
            cell_types[i] = int(board.get_cell((x, y)))
        noise_f = _NOISE_LIK[int(noise), cell_types]
        wloc = board.player_worker.get_location()
        widx = wloc[1] * BOARD_SIZE + wloc[0]
        true_d = np.minimum(_MANHATTAN[widx], _MAX_TRUE_DIST)
        rd_c = max(0, min(int(rd), _MAX_REPORTED))
        dist_f = _DIST_LIK[true_d, rd_c]
        self.belief = self.belief * noise_f * dist_f
        self._renorm()
        self._first = False

    def _renorm(self) -> None:
        s = self.belief.sum()
        if s > 1e-18:
            self.belief /= s
        else:
            self.belief = self.p0.copy()


def _heuristic(board: board_mod.Board) -> float:
    """3-feature linear heuristic (very simple, per assignment.pdf §9)."""
    score_diff = (
        board.player_worker.get_points()
        - board.opponent_worker.get_points()
    )
    primed = bin(board._primed_mask).count("1")
    carpet = bin(board._carpet_mask).count("1")
    return 2.0 * score_diff + 0.3 * primed + 0.2 * carpet


class PlayerAgent:
    def __init__(
        self,
        board: board_mod.Board,
        transition_matrix=None,
        time_left: Callable = None,
    ) -> None:
        self._rng = random.Random(0xA18E7)
        self._belief: Optional[_RatBelief] = None
        self._init_ok = False
        try:
            if transition_matrix is None:
                T = np.eye(_N_CELLS, dtype=np.float64)
            else:
                T = np.asarray(transition_matrix, dtype=np.float64)
            self._belief = _RatBelief(T)
            self._init_ok = True
        except Exception:
            self._init_ok = False

    def commentate(self) -> str:
        return "FakeAlbert — expectiminimax proxy (depth 3, simple heuristic)."

    def play(
        self,
        board: board_mod.Board,
        sensor_data: Tuple,
        time_left: Callable,
    ) -> Move:
        if not self._init_ok:
            return self._fallback(board)
        try:
            return self._play_internal(board, sensor_data, time_left)
        except Exception:
            return self._fallback(board)

    def _play_internal(
        self,
        board: board_mod.Board,
        sensor_data: Tuple,
        time_left: Callable,
    ) -> Move:
        assert self._belief is not None
        self._belief.update(board, sensor_data)

        # Root SEARCH gate: unconditional +4/-2 break-even at p > 1/3.
        max_mass = float(self._belief.belief.max())
        entropy = _entropy(self._belief.belief)
        deadline = time.perf_counter() + min(0.4, max(0.05, time_left() - 0.1))

        if max_mass > 1.0 / 3.0 and entropy < 0.75 * math.log(64.0):
            argmax = int(self._belief.belief.argmax())
            loc = (argmax % BOARD_SIZE, argmax // BOARD_SIZE)
            search_move = Move.search(loc)
            if board.is_valid_move(search_move):
                # Compare SEARCH EV to best move value.
                search_ev = max_mass * 4.0 - (1.0 - max_mass) * 2.0
                best_move, best_v = self._search_root(board, deadline)
                if best_move is None or search_ev > best_v - _heuristic(board):
                    return search_move
                return best_move

        best_move, _ = self._search_root(board, deadline)
        if best_move is None or not board.is_valid_move(best_move):
            return self._fallback(board)
        return best_move

    # ------------------------------------------------------------------
    # Alpha-beta search

    def _search_root(
        self,
        board: board_mod.Board,
        deadline: float,
    ) -> Tuple[Optional[Move], float]:
        """Iterative-deepening α-β root; returns (best_move, value)."""
        moves = board.get_valid_moves()
        if not moves:
            return None, 0.0
        moves = self._order_moves(moves)
        best_move = moves[0]
        best_val = -_INF
        for depth in range(1, 4):  # depth cap 3
            if time.perf_counter() > deadline:
                break
            try:
                mv, val = self._root_ab(board, moves, depth, deadline)
                if mv is not None:
                    best_move, best_val = mv, val
            except _Timeout:
                break
        return best_move, best_val

    def _root_ab(
        self,
        board: board_mod.Board,
        moves,
        depth: int,
        deadline: float,
    ) -> Tuple[Optional[Move], float]:
        alpha, beta = -_INF, _INF
        best_move = None
        best_val = -_INF
        for m in moves:
            if time.perf_counter() > deadline:
                raise _Timeout()
            child = board.forecast_move(m, check_ok=False)
            if child is None:
                continue
            child.reverse_perspective()
            v = -self._ab(child, depth - 1, -beta, -alpha, deadline)
            if v > best_val:
                best_val = v
                best_move = m
            if v > alpha:
                alpha = v
            if alpha >= beta:
                break
        return best_move, best_val

    def _ab(
        self,
        board: board_mod.Board,
        depth: int,
        alpha: float,
        beta: float,
        deadline: float,
    ) -> float:
        if time.perf_counter() > deadline:
            raise _Timeout()
        if board.is_game_over() or depth <= 0:
            return _heuristic(board)
        moves = board.get_valid_moves()
        if not moves:
            return _heuristic(board)
        moves = self._order_moves(moves)
        v = -_INF
        for m in moves:
            child = board.forecast_move(m, check_ok=False)
            if child is None:
                continue
            child.reverse_perspective()
            s = -self._ab(child, depth - 1, -beta, -alpha, deadline)
            if s > v:
                v = s
            if v > alpha:
                alpha = v
            if alpha >= beta:
                break
        return v

    def _order_moves(self, moves):
        """Rough static ordering: big carpets first, then primes, plains."""
        def key(m: Move) -> float:
            if m.move_type == MoveType.CARPET:
                return -float(CARPET_POINTS_TABLE.get(m.roll_length, -1))
            if m.move_type == MoveType.PRIME:
                return 10.0
            if m.move_type == MoveType.PLAIN:
                return 20.0
            return 30.0
        return sorted(moves, key=key)

    # ------------------------------------------------------------------
    # Fallback

    def _fallback(self, board: board_mod.Board) -> Move:
        try:
            valid = board.get_valid_moves()
            if valid:
                for m in valid:
                    if (
                        m.move_type == MoveType.CARPET
                        and CARPET_POINTS_TABLE.get(m.roll_length, -9) > 1
                    ):
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


class _Timeout(Exception):
    pass


def _entropy(b: np.ndarray) -> float:
    nz = b > 0.0
    return float(-np.sum(b[nz] * np.log(b[nz])))
