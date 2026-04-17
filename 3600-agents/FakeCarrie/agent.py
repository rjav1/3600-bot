"""FakeCarrie — best-guess replica of staff reference bot Carrie.

Per assignment.pdf §9: expectiminimax + HMM + "more advanced
heuristic that takes into account an estimate of the potential of
each cell and its distance from the bot."

Uses hypothesis H1 from docs/research/CARRIE_DECONSTRUCTION.md §1:
    Φ(state) = Σ_c P(c) / (1 + d(bot, c))
with P(c) = best-roll value reachable by rolling through PRIMED cells
in any of the 4 cardinal directions anchored at c.

This is a PROXY. It is NOT real Carrie. Used to stress-test RattleBot
against the actual-gating-opponent tier before scrimmage budget runs out.
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
    Direction,
    MoveType,
    Noise,
    loc_after_direction,
)
from game.move import Move


_N_CELLS = BOARD_SIZE * BOARD_SIZE
_INF = 1e18

_NOISE_LIK = np.array(
    [
        [0.7, 0.1, 0.1, 0.5],
        [0.15, 0.8, 0.1, 0.3],
        [0.15, 0.1, 0.8, 0.2],
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
_DIRS = (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT)


class _RatBelief:
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


def _cell_potential_vec(board: board_mod.Board) -> np.ndarray:
    """P(c) for all 64 cells — fast approximation of best-roll value.

    For each cell c, scan 4 cardinal directions. In each direction,
    count contiguous PRIMED cells (engine semantics: a carpet roll of
    length k from a worker on c would carpet k primed cells in that
    direction). Take the max CARPET_POINTS_TABLE[k] over directions
    and k in [2, 7]. Cells where c itself is BLOCKED/CARPET get 0.
    """
    out = np.zeros(_N_CELLS, dtype=np.float64)
    for i in range(_N_CELLS):
        x, y = i % BOARD_SIZE, i // BOARD_SIZE
        try:
            if board.get_cell((x, y)) in (Cell.BLOCKED, Cell.CARPET):
                continue
        except Exception:
            continue
        best = 0.0
        for d in _DIRS:
            loc = (x, y)
            k = 0
            for _ in range(BOARD_SIZE - 1):
                loc = loc_after_direction(loc, d)
                if not board.is_valid_cell(loc):
                    break
                try:
                    if board.get_cell(loc) != Cell.PRIMED:
                        break
                except Exception:
                    break
                k += 1
                pts = CARPET_POINTS_TABLE.get(k, -99)
                if pts > best:
                    best = float(pts)
        out[i] = best
    return out


def _heuristic(board: board_mod.Board) -> float:
    """Carrie-style heuristic: score_diff + cell-potential × distance.

    H1 from CARRIE_DECONSTRUCTION §1:
        Φ(worker) = Σ_c P(c) / (1 + d(worker, c))
        v = (self.pts - opp.pts) + β · Φ(self) - γ · Φ(opp)

    β=0.5, γ=0.3 as a reasonable mid-range guess (docs/research
    CARRIE_DECONSTRUCTION parameter bounds).
    """
    score_diff = (
        board.player_worker.get_points()
        - board.opponent_worker.get_points()
    )
    P = _cell_potential_vec(board)
    if not np.any(P):
        return 2.0 * score_diff
    pl = board.player_worker.get_location()
    ol = board.opponent_worker.get_location()
    pi = pl[1] * BOARD_SIZE + pl[0]
    oi = ol[1] * BOARD_SIZE + ol[0]
    dp = _MANHATTAN[pi]
    do = _MANHATTAN[oi]
    phi_self = float(np.sum(P / (1.0 + dp)))
    phi_opp = float(np.sum(P / (1.0 + do)))
    return 2.0 * score_diff + 0.5 * phi_self - 0.3 * phi_opp


class PlayerAgent:
    def __init__(
        self,
        board: board_mod.Board,
        transition_matrix=None,
        time_left: Callable = None,
    ) -> None:
        self._rng = random.Random(0xCA881E)
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
        return (
            "FakeCarrie — expectiminimax proxy with cell-potential × "
            "distance heuristic (H1)."
        )

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

        max_mass = float(self._belief.belief.max())
        entropy = _entropy(self._belief.belief)
        deadline = time.perf_counter() + min(0.45, max(0.05, time_left() - 0.1))

        if max_mass > 1.0 / 3.0 and entropy < 0.75 * math.log(64.0):
            argmax = int(self._belief.belief.argmax())
            loc = (argmax % BOARD_SIZE, argmax // BOARD_SIZE)
            search_move = Move.search(loc)
            if board.is_valid_move(search_move):
                search_ev = max_mass * 4.0 - (1.0 - max_mass) * 2.0
                best_move, best_v = self._search_root(board, deadline)
                base = _heuristic(board)
                if best_move is None or search_ev > (best_v - base):
                    return search_move
                return best_move

        best_move, _ = self._search_root(board, deadline)
        if best_move is None or not board.is_valid_move(best_move):
            return self._fallback(board)
        return best_move

    def _search_root(
        self,
        board: board_mod.Board,
        deadline: float,
    ) -> Tuple[Optional[Move], float]:
        moves = board.get_valid_moves()
        if not moves:
            return None, 0.0
        moves = self._order_moves(moves)
        best_move = moves[0]
        best_val = -_INF
        for depth in range(1, 4):
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
        def key(m: Move) -> float:
            if m.move_type == MoveType.CARPET:
                return -float(CARPET_POINTS_TABLE.get(m.roll_length, -1))
            if m.move_type == MoveType.PRIME:
                return 10.0
            if m.move_type == MoveType.PLAIN:
                return 20.0
            return 30.0
        return sorted(moves, key=key)

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
