"""HMM rat-belief tracker — STUB.

Forward-filter HMM per BOT_STRATEGY.md v1.1 §3.2. Owner: dev-hmm.
v1.1: `_first_call` guard handles player-A turn_count==0 (D-011 item 1);
no `top8` on BeliefSummary (D-011 item 3).
"""

from __future__ import annotations
from typing import Tuple
import numpy as np

from game import board as board_mod
from game.enums import Noise

from .types import BeliefSummary

__all__ = ["RatBelief"]


class RatBelief:
    """Forward-filter HMM tracker over the 64 rat-cells."""

    def __init__(self, T: np.ndarray, board: board_mod.Board) -> None:
        """Precompute p_0 = e_0 @ T^1000, noise/dist LUTs; init belief.
        Time budget: <= 3 s at init. Raises: ValueError if T malformed.
        """
        raise NotImplementedError("TBD by dev-hmm")

    def update(
        self, board: board_mod.Board, sensor_data: Tuple[Noise, int]
    ) -> BeliefSummary:
        """Apply one 4-step turn (predict, opp-search, predict, sensor).
        Returns: BeliefSummary (belief sums to 1 within 1e-9).
        Time budget: <= 2 ms (target 0.5 ms). Raises: AssertionError on
        renorm failure.
        """
        raise NotImplementedError("TBD by dev-hmm")

    def handle_post_capture_reset(self, captured_by_us: bool) -> None:
        """Reset belief = p_0 after any successful SEARCH. Time: <= 10 us.
        """
        raise NotImplementedError("TBD by dev-hmm")

    def summary(self) -> BeliefSummary:
        """Cheap getter. Returns: BeliefSummary. Time: <= 20 us."""
        raise NotImplementedError("TBD by dev-hmm")
