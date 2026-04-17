"""FakeCarrie_v2 5-feature heuristic.

Uses CARRIE_DECONSTRUCTION §1 hypothesis H1:
    Φ(state) = Σ_c P(c) / (1 + d(worker, c))
with P(c) = max_{k>=2, dir} CARPET_POINTS_TABLE[k] over PRIMED rays
anchored at c. Aggregated into a scalar leaf value:

    v = w1*score_diff + w2*(Φ_self − 0.6·Φ_opp)
        + w3*primed_count + w4*carpet_count + w5*belief_max

Hand-tuned weights, no BO. Intentionally fewer features than RattleBot's
14 — this is a proxy for Carrie's "more advanced than Albert" level.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from game import board as board_mod
from game.enums import BOARD_SIZE, CARPET_POINTS_TABLE, Cell, Direction
from game.enums import loc_after_direction


_N_CELLS = BOARD_SIZE * BOARD_SIZE
_DIRS = (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT)
_TERMINAL_SCALE = 10_000.0


def _build_manhattan() -> np.ndarray:
    coords = np.array(
        [(i % BOARD_SIZE, i // BOARD_SIZE) for i in range(_N_CELLS)],
        dtype=np.int32,
    )
    dx = np.abs(coords[:, None, 0] - coords[None, :, 0])
    dy = np.abs(coords[:, None, 1] - coords[None, :, 1])
    return (dx + dy).astype(np.int32)


_MANHATTAN = _build_manhattan()


# Hand-tuned weights, order matches _feature_vector() below:
#   [score_diff, phi_net, primed_count, carpet_count, belief_max]
W_INIT = np.array([1.0, 0.40, 0.20, 0.15, 2.0], dtype=np.float64)
N_FEATURES = 5


def _cell_potential_vec(board: board_mod.Board) -> np.ndarray:
    """P(c) for all 64 cells: max CARPET_POINTS for k>=2 anchored rays."""
    out = np.zeros(_N_CELLS, dtype=np.float64)
    for i in range(_N_CELLS):
        x, y = i % BOARD_SIZE, i // BOARD_SIZE
        try:
            ct = board.get_cell((x, y))
        except Exception:
            continue
        if ct == Cell.BLOCKED or ct == Cell.CARPET:
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
                if k >= 2:
                    pts = CARPET_POINTS_TABLE.get(k, 0)
                    if pts > best:
                        best = float(pts)
        out[i] = best
    return out


def _popcount(n: int) -> int:
    return bin(n & ((1 << 64) - 1)).count("1")


def _feature_vector(board, belief_max: float) -> np.ndarray:
    score_diff = float(
        board.player_worker.get_points() - board.opponent_worker.get_points()
    )
    P = _cell_potential_vec(board)
    if np.any(P):
        pl = board.player_worker.get_location()
        ol = board.opponent_worker.get_location()
        pi = pl[1] * BOARD_SIZE + pl[0]
        oi = ol[1] * BOARD_SIZE + ol[0]
        dp = _MANHATTAN[pi]
        do = _MANHATTAN[oi]
        phi_self = float(np.sum(P / (1.0 + dp)))
        phi_opp = float(np.sum(P / (1.0 + do)))
        phi_net = phi_self - 0.6 * phi_opp
    else:
        phi_net = 0.0
    primed_count = float(_popcount(board._primed_mask))
    carpet_count = float(_popcount(board._carpet_mask))
    return np.array(
        [score_diff, phi_net, primed_count, carpet_count, float(belief_max)],
        dtype=np.float64,
    )


def evaluate(
    board: board_mod.Board,
    belief_max: float = 0.0,
    weights: Optional[np.ndarray] = None,
) -> float:
    try:
        if board.is_game_over():
            diff = (
                board.player_worker.get_points()
                - board.opponent_worker.get_points()
            )
            return float(_TERMINAL_SCALE * diff)
    except Exception:
        pass
    w = weights if weights is not None else W_INIT
    phi = _feature_vector(board, belief_max)
    return float(np.dot(phi, w))


class Heuristic:
    def __init__(self, weights: Optional[np.ndarray] = None) -> None:
        self.weights = weights if weights is not None else W_INIT.copy()

    def V_leaf(self, board: board_mod.Board, belief_max: float = 0.0) -> float:
        return evaluate(board, belief_max, self.weights)
