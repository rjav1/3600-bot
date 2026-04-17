"""HMM rat-belief tracker for FakeCarrie_v2.

Forward filter over the 64 rat cells with D-011 first-turn guard. No
snapshot/restore machinery — FakeCarrie_v2 only ever SEARCHes at the
root, so in-tree belief rewinds are never needed.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

from game import board as board_mod
from game.enums import BOARD_SIZE, Noise


_N_CELLS = BOARD_SIZE * BOARD_SIZE

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


class RatBelief:
    """Forward-filter HMM over 64 rat cells. See module docstring."""

    def __init__(self, T: np.ndarray) -> None:
        T64 = np.asarray(T, dtype=np.float64)
        if T64.shape != (_N_CELLS, _N_CELLS):
            raise ValueError(f"T shape {T64.shape} != ({_N_CELLS},{_N_CELLS})")
        self.T = T64
        p = np.zeros(_N_CELLS, dtype=np.float64)
        p[0] = 1.0
        for _ in range(1000):
            p = p @ T64
        s = p.sum()
        self.p0 = p / s if s > 0 else p
        self.belief = self.p0.copy()
        self._first_call = True
        self.max_mass = float(self.belief.max())
        self.argmax = int(self.belief.argmax())
        self.entropy = _entropy(self.belief)

    def update(
        self,
        board: board_mod.Board,
        sensor: Tuple[Noise, int],
    ) -> "RatBelief":
        noise, rd = sensor
        skip_opp = (
            self._first_call
            and bool(getattr(board, "is_player_a_turn", False))
            and int(getattr(board, "turn_count", 0)) == 0
        )
        if not skip_opp:
            self.belief = self.belief @ self.T
            opp = getattr(board, "opponent_search", (None, False))
            self._apply_search_result(opp)
        # Absorb our OWN previous SEARCH result before the rat moves at
        # top of our turn — without this, after a missed SEARCH the peak
        # stays where it was and we fire on the same stale cell forever.
        # V03_REDTEAM §H-1 / T-30e caught the analogous bug in RattleBot.
        our_search = getattr(board, "player_search", (None, False))
        self._apply_search_result(our_search)
        self.belief = self.belief @ self.T
        self._sensor_update(board, noise, rd)
        self._first_call = False
        self.max_mass = float(self.belief.max())
        self.argmax = int(self.belief.argmax())
        self.entropy = _entropy(self.belief)
        return self

    def _apply_search_result(self, search) -> None:
        loc, hit = search
        if loc is None:
            return
        if hit:
            self.belief = self.p0.copy()
        else:
            self.belief[loc[1] * BOARD_SIZE + loc[0]] = 0.0
            self._renorm()

    def _sensor_update(self, board, noise, reported_dist) -> None:
        cell_types = np.empty(_N_CELLS, dtype=np.int64)
        for i in range(_N_CELLS):
            x, y = i % BOARD_SIZE, i // BOARD_SIZE
            cell_types[i] = int(board.get_cell((x, y)))
        noise_f = _NOISE_LIK[int(noise), cell_types]
        wloc = board.player_worker.get_location()
        widx = wloc[1] * BOARD_SIZE + wloc[0]
        true_d = np.minimum(_MANHATTAN[widx], _MAX_TRUE_DIST)
        rd = max(0, min(int(reported_dist), _MAX_REPORTED))
        dist_f = _DIST_LIK[true_d, rd]
        self.belief = self.belief * noise_f * dist_f
        self._renorm()

    def _renorm(self) -> None:
        s = self.belief.sum()
        if s > 1e-18:
            self.belief /= s
        else:
            self.belief = self.p0.copy()


def _entropy(b: np.ndarray) -> float:
    nz = b > 0.0
    if not np.any(nz):
        return 0.0
    v = float(-np.sum(b[nz] * np.log(b[nz])))
    return v if v > 0.0 else 0.0
