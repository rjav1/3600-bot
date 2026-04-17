"""Adaptive time controller for RattleBot v0.1.

Per BOT_STRATEGY.md v1.1 §3.6, D-004 (0.6x/1.0x/1.6x multipliers, 2.5x
cap), and D-011 item 4 (0.5 s safety margin matches `check_win`'s
tie-vs-loss band from GAME_SPEC §7, absorbs GC/JIT pauses).

Per-turn budget:
    base = max(0, time_left - SAFETY) / max(1, turns_left)
    budget = clamp(base * multiplier, min=0.05, max=base * HARD_CAP_MULT)

Classification:
    critical  -- last 8 plies of the game OR max_mass >= 0.35 (near-cert
                 rat candidate -- usually our last call to convert info)
    easy      -- first 4 plies OR max_mass <= 0.05 (very flat belief, no
                 payoff from deep search)
    normal    -- everything else
"""

from __future__ import annotations

from typing import Callable, List, Optional
import time as _time

from game import board as board_mod

from .types import BeliefSummary

__all__ = ["TimeManager"]


SAFETY_S: float = 0.5
HARD_CAP_MULT: float = 2.5
_MULTIPLIER = {"easy": 0.6, "normal": 1.0, "critical": 1.6}
_MIN_BUDGET_S = 0.05
# Per-turn absolute ceiling. Even with surplus available, v0.1 doesn't
# benefit from deeper search because the heuristic isn't BO-tuned yet
# (D-009: BO tuning lands in v0.2). Keeping this ≤ 3 s also makes
# local self-play ~3× faster for iteration.
_PER_TURN_CEILING_S: float = 3.0


class TimeManager:
    """Adaptive iterative-deepening time controller."""

    def __init__(self, total_budget_s: float = 240.0 - SAFETY_S) -> None:
        self.total_budget_s = float(total_budget_s)
        self.safety_s = SAFETY_S
        self.cumulative_used: float = 0.0
        self.turn_budgets_planned: List[float] = []
        self.classification_log: List[str] = []
        self._turn_start: float = 0.0
        self._turn_budget: float = 0.0

    def start_turn(
        self,
        board: board_mod.Board,
        time_left_fn: Callable[[], float],
        belief_summary: Optional[BeliefSummary] = None,
    ) -> float:
        """Compute this turn's budget; store start time; return seconds."""
        try:
            time_left = float(time_left_fn())
        except Exception:
            # Best-effort fallback: use the worker's remaining budget.
            time_left = float(
                getattr(board.player_worker, "time_left", self.total_budget_s)
            )
        usable = max(0.0, time_left - self.safety_s)
        turns_left = int(getattr(board.player_worker, "turns_left", 1) or 1)
        turns_left = max(1, turns_left)
        base = usable / turns_left

        label = self.classify(board, belief_summary)
        mult = _MULTIPLIER.get(label, 1.0)
        budget = base * mult
        hard_cap = base * HARD_CAP_MULT
        if budget > hard_cap:
            budget = hard_cap
        if budget > _PER_TURN_CEILING_S:
            budget = _PER_TURN_CEILING_S
        if budget < _MIN_BUDGET_S:
            budget = min(_MIN_BUDGET_S, max(0.0, usable))

        self.turn_budgets_planned.append(budget)
        self.classification_log.append(label)
        self._turn_start = _time.perf_counter()
        self._turn_budget = budget
        return budget

    def classify(
        self,
        board: board_mod.Board,
        belief_summary: Optional[BeliefSummary] = None,
    ) -> str:
        turns_left = int(getattr(board.player_worker, "turns_left", 40) or 40)
        if turns_left <= 4:
            return "critical"
        if belief_summary is not None and belief_summary.max_mass >= 0.35:
            return "critical"
        if turns_left >= 36:
            return "easy"
        if belief_summary is not None and belief_summary.max_mass <= 0.05:
            return "easy"
        return "normal"

    def should_stop(self) -> bool:
        return (_time.perf_counter() - self._turn_start) >= self._turn_budget

    def remaining(self) -> float:
        return self._turn_budget - (_time.perf_counter() - self._turn_start)

    def end_turn(self, actual_elapsed_s: float) -> None:
        self.cumulative_used += max(0.0, float(actual_elapsed_s))
