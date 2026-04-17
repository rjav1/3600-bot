"""HMM rat-belief tracker — v0.1.

Forward-filter HMM over the 64 rat-cells per BOT_STRATEGY.md v1.1 §3.2
and RESEARCH_HMM_RAT.md §A–§E. Owner: dev-hmm.

Design summary:
- Linear-space float64 belief vector of shape (64,), flat index y*8 + x.
- `p_0 = e_{(0,0)} @ T^1000` precomputed in `__init__` (~3 ms).
- `update()` runs the canonical 4-step pipeline per turn:
    1. predict(T)               -- rat moved during opp's ply
    2. opp-search-update         -- miss: zero+renorm; hit: reset to p_0
    3. predict(T)               -- rat moved at top of our turn
    4. sensor-update            -- factorized noise * distance likelihood
- First-turn guard (D-011 item 1 / CON-STRAT §G-3): on player A's very
  first `update()` call (`is_player_a_turn and turn_count == 0`), only
  one rat-move has happened and opp hasn't acted. Steps 1-2 are skipped;
  only steps 3-4 run. Subsequent calls always run the full pipeline.
- Cell types re-read every turn (opponent prime/carpet mutates the
  noise-likelihood landscape — HMM §D.6).

Public helpers for search.py SEARCH-root chance node (§E.6):
  `snapshot`, `restore`, `apply_our_search`, `apply_opp_search`.

All entries of `self.belief` are float64 in [0, 1] and sum to 1.0 within
1e-9 after every public state-mutating call.
"""

from __future__ import annotations

from typing import Tuple
import numpy as np

from game import board as board_mod
from game.enums import Cell, Noise, BOARD_SIZE

from .types import BeliefSummary

__all__ = ["RatBelief"]


_N_CELLS = BOARD_SIZE * BOARD_SIZE  # 64

# Noise likelihood table: rows = Noise, cols = Cell.
# P(noise | cell_type) from engine/game/rat.py NOISE_PROBS.
# Cell order:  SPACE=0, PRIMED=1, CARPET=2, BLOCKED=3
# Noise order: SQUEAK=0, SCRATCH=1, SQUEAL=2
_NOISE_LIK = np.array(
    [
        [0.7, 0.1, 0.1, 0.5],  # SQUEAK
        [0.15, 0.8, 0.1, 0.3],  # SCRATCH
        [0.15, 0.1, 0.8, 0.2],  # SQUEAL
    ],
    dtype=np.float64,
)

# Distance-error table: offset in {-1, 0, +1, +2}, clamped to >= 0.
_DIST_OFFSETS = (-1, 0, 1, 2)
_DIST_PROBS = (0.12, 0.70, 0.12, 0.06)

# Max true distance on an 8x8 grid: (0,0) <-> (7,7) = 14.
_MAX_TRUE_DIST = (BOARD_SIZE - 1) * 2  # 14
# Max reported distance = 14 + 2 (offset) = 16.
_MAX_REPORTED_DIST = _MAX_TRUE_DIST + 2


def _build_dist_lik() -> np.ndarray:
    """P(reported | true) table with clamp-to-0.

    Shape: (_MAX_TRUE_DIST + 1, _MAX_REPORTED_DIST + 1).
    dist_lik[true, reported] = P(reported | true).
    """
    tbl = np.zeros(
        (_MAX_TRUE_DIST + 1, _MAX_REPORTED_DIST + 1), dtype=np.float64
    )
    for true_d in range(_MAX_TRUE_DIST + 1):
        for off, p in zip(_DIST_OFFSETS, _DIST_PROBS):
            reported = max(0, true_d + off)
            tbl[true_d, reported] += p
    return tbl


_DIST_LIK = _build_dist_lik()


def _build_manhattan_lut() -> np.ndarray:
    """64x64 Manhattan-distance lookup. index = y*8 + x."""
    coords = np.empty((_N_CELLS, 2), dtype=np.int32)
    for i in range(_N_CELLS):
        coords[i, 0] = i % BOARD_SIZE  # x
        coords[i, 1] = i // BOARD_SIZE  # y
    dx = np.abs(coords[:, None, 0] - coords[None, :, 0])
    dy = np.abs(coords[:, None, 1] - coords[None, :, 1])
    return (dx + dy).astype(np.int32)


_MANHATTAN = _build_manhattan_lut()


def _compute_p0(T: np.ndarray, steps: int = 1000) -> np.ndarray:
    """p_0 = e_{(0,0)} @ T^steps via iterative left-multiply.

    1000 x (64x64) ~ 4M multiplies, ~3 ms in numpy. Matches §B.5.
    """
    p = np.zeros(_N_CELLS, dtype=np.float64)
    p[0] = 1.0
    for _ in range(steps):
        p = p @ T
    s = p.sum()
    if s <= 0.0:
        raise ValueError("p_0 computation produced zero mass; T degenerate.")
    return p / s


class RatBelief:
    """Forward-filter HMM tracker over the 64 rat-cells."""

    def __init__(self, T: np.ndarray, board: board_mod.Board) -> None:
        T64 = np.asarray(T, dtype=np.float64)
        if T64.shape != (_N_CELLS, _N_CELLS):
            raise ValueError(
                f"T must be shape ({_N_CELLS}, {_N_CELLS}); got {T64.shape}"
            )
        self.T: np.ndarray = T64
        self.p_0: np.ndarray = _compute_p0(T64, steps=1000)
        self.belief: np.ndarray = self.p_0.copy()
        self._first_call: bool = True

    # ------------------------------------------------------------------
    # Core forward filter

    def update(
        self,
        board: board_mod.Board,
        sensor_data: Tuple[Noise, int],
    ) -> BeliefSummary:
        """Apply one turn of the canonical 4-step HMM pipeline.

        Reads `board.opponent_search` and `board.player_search` directly.
        Returns an immutable `BeliefSummary` snapshot for the heuristic.
        """
        noise, reported_dist = sensor_data

        # First-turn guard (D-011 item 1): on player A's first call, only
        # one rat-move has happened and opp hasn't acted. Skip steps 1-2.
        skip_opp_phase = (
            self._first_call
            and bool(getattr(board, "is_player_a_turn", False))
            and int(getattr(board, "turn_count", 0)) == 0
        )

        if not skip_opp_phase:
            # Step 1: predict -- catch up with opp's rat-move.
            self.belief = self.belief @ self.T

            # Step 2: opp-search-update (if any).
            opp_search = getattr(board, "opponent_search", (None, False))
            self._apply_search_result(opp_search)

        # Step 3: predict -- rat moves at top of our turn.
        self.belief = self.belief @ self.T

        # Step 4: sensor update (factorized likelihood).
        self._sensor_update(board, noise, reported_dist)

        self._first_call = False
        return self.summary()

    def _apply_search_result(
        self, search: Tuple[Tuple[int, int] | None, bool]
    ) -> None:
        loc, result = search
        if loc is None:
            return
        if result:
            # Rat was caught and respawned with 1000-step headstart.
            self.belief = self.p_0.copy()
        else:
            idx = loc[1] * BOARD_SIZE + loc[0]
            self.belief[idx] = 0.0
            self._safe_renorm()

    def _sensor_update(
        self,
        board: board_mod.Board,
        noise: Noise,
        reported_dist: int,
    ) -> None:
        # Re-read cell types every turn (HMM §D.6).
        cell_types = np.empty(_N_CELLS, dtype=np.int64)
        for i in range(_N_CELLS):
            x = i % BOARD_SIZE
            y = i // BOARD_SIZE
            cell_types[i] = int(board.get_cell((x, y)))
        noise_factor = _NOISE_LIK[int(noise), cell_types]  # (64,)

        worker_loc = board.player_worker.get_location()
        worker_idx = worker_loc[1] * BOARD_SIZE + worker_loc[0]
        true_dists = _MANHATTAN[worker_idx]  # (64,), ints

        rd = int(reported_dist)
        if rd < 0:
            rd = 0
        elif rd > _MAX_REPORTED_DIST:
            rd = _MAX_REPORTED_DIST
        td_clamped = np.minimum(true_dists, _MAX_TRUE_DIST)
        dist_factor = _DIST_LIK[td_clamped, rd]  # (64,)

        self.belief = self.belief * noise_factor * dist_factor
        self._safe_renorm()

    def _safe_renorm(self) -> None:
        s = self.belief.sum()
        if s > 1e-18:
            self.belief /= s
        else:
            # Observation incompatible with belief -- model misspecified.
            # Fall back to the post-capture prior. Should never fire.
            self.belief = self.p_0.copy()

    # ------------------------------------------------------------------
    # Public API required by BOT_STRATEGY §3.2 and RESEARCH §E.6

    def handle_post_capture_reset(self, captured_by_us: bool) -> None:
        """Reset belief to p_0 after any successful SEARCH. O(64)."""
        self.belief = self.p_0.copy()

    def summary(self) -> BeliefSummary:
        """Immutable snapshot for heuristic / leaf evaluation."""
        b = self.belief
        # Shannon entropy in nats. Use xlog(x) with mask so that cells
        # with probability 0 contribute 0 exactly (0*log(0) := 0), and
        # a concentrated belief (max ~ 1) yields entropy 0 without
        # numerical undershoot from an additive log-floor.
        nz = b > 0.0
        entropy = float(-np.sum(b[nz] * np.log(b[nz])))
        if entropy < 0.0:  # guard against fp rounding at the 0 boundary
            entropy = 0.0
        return BeliefSummary(
            belief=b,
            entropy=entropy,
            max_mass=float(b.max()),
            argmax=int(b.argmax()),
        )

    # ------------------------------------------------------------------
    # SEARCH-node side-effect helpers (§E.6)

    def snapshot(self) -> np.ndarray:
        """Capture current belief for in-tree restore (O(64) copy)."""
        return self.belief.copy()

    def restore(self, snap: np.ndarray) -> None:
        """Restore from a snapshot previously returned by `snapshot`."""
        self.belief = snap

    def apply_our_search(self, cell: Tuple[int, int], hit: bool) -> None:
        """In-tree SEARCH by us: miss = zero+renorm; hit = reset to p_0."""
        self._apply_search_result((cell, hit))

    def apply_opp_search(self, cell: Tuple[int, int], hit: bool) -> None:
        """Symmetric helper for an opponent SEARCH in the tree."""
        self._apply_search_result((cell, hit))
