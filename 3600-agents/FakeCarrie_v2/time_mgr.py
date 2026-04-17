"""Per-turn time controller for FakeCarrie_v2.

Hard 5 s/move cap with a 0.5 s safety reserve; intentionally simpler
than RattleBot's classification-aware controller.
"""

from __future__ import annotations

import os
from typing import Callable


SAFETY_S = 0.5
DEFAULT_PER_TURN_CEILING_S = 5.0
_MIN_BUDGET_S = 0.05


def _resolved_ceiling(default: float) -> float:
    """Per-turn ceiling override via `FAKE_CARRIE_V2_BUDGET_S` env var.

    Useful for running smoke tests at a faster cadence without touching
    source (e.g. `FAKE_CARRIE_V2_BUDGET_S=1.5 python ...`). Invalid /
    negative values fall back to the default.
    """
    raw = os.environ.get("FAKE_CARRIE_V2_BUDGET_S")
    if not raw:
        return default
    try:
        v = float(raw)
        if v > 0.0:
            return v
    except Exception:
        pass
    return default


class TimeManager:
    def __init__(
        self,
        per_turn_ceiling_s: float = DEFAULT_PER_TURN_CEILING_S,
    ) -> None:
        self.per_turn_ceiling_s = _resolved_ceiling(float(per_turn_ceiling_s))

    def budget_for_turn(self, board, time_left_fn: Callable[[], float]) -> float:
        try:
            time_left = float(time_left_fn())
        except Exception:
            time_left = self.per_turn_ceiling_s + SAFETY_S
        usable = max(0.0, time_left - SAFETY_S)
        turns_left = int(getattr(board.player_worker, "turns_left", 1) or 1)
        turns_left = max(1, turns_left)
        base = usable / turns_left
        budget = min(self.per_turn_ceiling_s, max(base * 1.5, base))
        if budget < _MIN_BUDGET_S:
            budget = min(_MIN_BUDGET_S, usable)
        return budget
