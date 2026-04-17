"""F2 linear leaf evaluator — STUB.

9-feature linear heuristic per BOT_STRATEGY.md v1.1 §3.4 + D-004.
v0.1 features: F1, F3, F4, F5, F7, F11, F12 (CON-STRAT §I-2).
v0.1.1+: F9, F10. v0.3+: F8, F13', F15.
Hyperparams (D-011 item 5): gamma_info=0.5, gamma_reset=0.3.
Owner: dev-heuristic.
"""

from __future__ import annotations
import numpy as np

from game import board as board_mod

from .types import BeliefSummary

__all__ = ["Heuristic"]


class Heuristic:
    """Linear combination of hand-crafted features; weights tuned via BO."""

    def __init__(self, weights: np.ndarray) -> None:
        """Store (9,) float64 weight vector. Raises: ValueError on shape."""
        raise NotImplementedError("TBD by dev-heuristic")

    def V_leaf(
        self, board: board_mod.Board, belief_summary: BeliefSummary
    ) -> float:
        """Leaf evaluation from player_worker's perspective (negamax sign).
        Time budget: <= 100 us tournament (D-005 / SYN §B20).
        """
        raise NotImplementedError("TBD by dev-heuristic")

    def set_weights(self, new_w: np.ndarray) -> None:
        """Hot-swap weights (BO tuning). Raises: ValueError on shape."""
        raise NotImplementedError("TBD by dev-heuristic")
