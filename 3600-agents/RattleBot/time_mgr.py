"""Adaptive time controller for RattleBot v0.2.

Per BOT_STRATEGY.md v1.1 §3.6, D-004 (0.6x/1.0x/1.6x multipliers, 2.5x
surplus cap), D-011 item 4 (0.5 s safety margin matches `check_win`'s
tie-vs-loss band from GAME_SPEC §7), and BOT_STRATEGY_V02_ADDENDUM §2.1
/ §2.2 (T-20a: configurable ceiling 6.0 s; T-20b: `TimeManager` is the
single source of truth for the 0.5 s safety reservation).

Per-turn budget:
    usable  = max(0, time_left - safety_s)
    base    = usable / max(1, turns_left)
    budget  = clamp(base * multiplier, min=MIN, max=base * HARD_CAP_MULT)
    budget  = min(budget, per_turn_ceiling_s)

Classification:
    critical  -- last 4 plies OR max_mass >= 0.35
    easy      -- first 4 plies OR max_mass <= 0.05
    normal    -- everything else
"""

from __future__ import annotations

from typing import Callable, List, Optional
import time as _time

from game import board as board_mod

from .types import BeliefSummary

__all__ = ["TimeManager", "DEFAULT_PER_TURN_CEILING_S"]


SAFETY_S: float = 0.5
HARD_CAP_MULT: float = 2.5
# T-30d (V03 ADDENDUM §3, §12): endgame turns are higher-stakes and the
# board is typically full enough that branching is reduced — reward
# deeper search by lifting the surplus cap from 2.5× to 3.5× when
# `turns_left <= ENDGAME_TURNS_THRESHOLD`. Expected +10–20 ELO.
ENDGAME_HARD_CAP_MULT: float = 3.5
ENDGAME_TURNS_THRESHOLD: int = 5
_MULTIPLIER = {"easy": 0.6, "normal": 1.0, "critical": 1.6}
_MIN_BUDGET_S = 0.05
# v0.2 default per T-20a / AUDIT_V01 M-01: 6.0 s matches the tournament
# base budget (240 s / 40 turns). v0.1 shipped 3.0 s as a provisional
# cap while the heuristic was uncalibrated; with BO-tuned weights the
# premise is gone and the ceiling is lifted.
DEFAULT_PER_TURN_CEILING_S: float = 6.0


class TimeManager:
    """Adaptive iterative-deepening time controller.

    Owns the 0.5 s safety reservation (D-011 item 4). Downstream code
    (`search.iterative_deepen`) should be invoked with `safety_s=0.0`
    so the reserve is not double-subtracted — see T-20b / AUDIT_V01 M-02.
    """

    def __init__(
        self,
        total_budget_s: float = 240.0 - SAFETY_S,
        per_turn_ceiling_s: float = DEFAULT_PER_TURN_CEILING_S,
    ) -> None:
        self.total_budget_s = float(total_budget_s)
        self.safety_s = SAFETY_S
        self.per_turn_ceiling_s = float(per_turn_ceiling_s)
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
        """Compute this turn's budget; store start time; return seconds.

        The returned budget already has `safety_s` reserved — callers
        should pass `safety_s=0.0` into `search.iterative_deepen` to
        avoid double-subtracting.
        """
        try:
            time_left = float(time_left_fn())
        except Exception:
            time_left = float(
                getattr(board.player_worker, "time_left", self.total_budget_s)
            )
        usable = max(0.0, time_left - self.safety_s)
        turns_left = int(getattr(board.player_worker, "turns_left", 1) or 1)
        turns_left = max(1, turns_left)
        base = usable / turns_left

        label = self.classify(board, belief_summary)
        mult = _MULTIPLIER.get(label, 1.0)
        # T-30d: endgame multiplier cap lift. When turns_left is at or
        # below ENDGAME_TURNS_THRESHOLD, lift both (a) the effective
        # multiplier up to ENDGAME_HARD_CAP_MULT and (b) the surplus
        # cap to the same value — endgame turns are higher-stakes and
        # lower-branching, so more time → deeper search → higher-EV.
        # Safety reserve above (`usable = time_left - safety_s`) still
        # applies; we only extend the upward cap, not the floor.
        in_endgame = turns_left <= ENDGAME_TURNS_THRESHOLD
        cap_mult = ENDGAME_HARD_CAP_MULT if in_endgame else HARD_CAP_MULT
        if in_endgame and mult < cap_mult:
            mult = cap_mult
        budget = base * mult
        hard_cap = base * cap_mult
        if budget > hard_cap:
            budget = hard_cap
        if budget > self.per_turn_ceiling_s:
            budget = self.per_turn_ceiling_s
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
