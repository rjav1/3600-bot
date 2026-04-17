"""Adaptive time controller — STUB.

Easy/normal/critical classifier + surplus rebalancing per
BOT_STRATEGY.md v1.1 §3.6. Owner: dev-integrator.

Safety: 0.5 s below engine timeout (D-011 item 4; matches check_win tie
band, absorbs GC/JIT pauses).
"""

from __future__ import annotations
from typing import Callable

from game import board as board_mod

from .types import BeliefSummary

__all__ = ["TimeManager"]


class TimeManager:
    """Adaptive ID time controller."""

    def __init__(self, total_budget_s: float = 240.0 - 0.5) -> None:
        """0.5 s safety per D-011 item 4."""
        raise NotImplementedError("TBD by dev-integrator")

    def start_turn(
        self,
        board: board_mod.Board,
        time_left_fn: Callable[[], float],
    ) -> float:
        """Returns: turn_budget_s. Multipliers 0.6/1.0/1.6, cap 2.5 (D-004).
        Time: <= 10 us.
        """
        raise NotImplementedError("TBD by dev-integrator")

    def classify(
        self, board: board_mod.Board, belief_summary: BeliefSummary
    ) -> str:
        """Returns: 'easy' | 'normal' | 'critical'. Time: <= 10 us."""
        raise NotImplementedError("TBD by dev-integrator")

    def should_stop(self) -> bool:
        """Elapsed >= budget. Time: <= 1 us."""
        raise NotImplementedError("TBD by dev-integrator")

    def remaining(self) -> float:
        """Seconds left in turn budget; may be negative. Time: <= 1 us."""
        raise NotImplementedError("TBD by dev-integrator")

    def end_turn(self, actual_elapsed_s: float) -> None:
        """Update surplus/deficit pool. Time: <= 5 us."""
        raise NotImplementedError("TBD by dev-integrator")
