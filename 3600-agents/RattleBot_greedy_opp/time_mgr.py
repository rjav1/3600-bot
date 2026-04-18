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

import math as _math
from typing import Callable, List, Optional
import time as _time

from game import board as board_mod

from .types import BeliefSummary

__all__ = [
    "TimeManager",
    "DEFAULT_PER_TURN_CEILING_S",
    "CONTEXT_ENTROPY_COEF",
    "CONTEXT_VARIANCE_COEF",
    "CONTEXT_VARIANCE_HIGH_THRESHOLD",
    "SEARCH_OVERHEAD_PAD_S",
]


SAFETY_S: float = 0.5
HARD_CAP_MULT: float = 2.5
# T-30d (V03 ADDENDUM §3, §12): endgame turns are higher-stakes and the
# board is typically full enough that branching is reduced — reward
# deeper search by lifting the surplus cap from 2.5× to 3.5× when
# `turns_left <= ENDGAME_TURNS_THRESHOLD`. Expected +10–20 ELO.
ENDGAME_HARD_CAP_MULT: float = 3.5
ENDGAME_TURNS_THRESHOLD: int = 5
# T-30e M-7 fix (V03_REDTEAM): under the default 6 s ceiling, the 3.5×
# endgame lift was silently clamped — at base≈5-10 s, 3.5× = 17-35 s
# all pinned to 6 s. Give the endgame a dedicated ceiling that still
# respects `time_left - safety_s` and doesn't remove the ceiling
# entirely. 20 s is the V03_REDTEAM recommendation.
ENDGAME_HARD_CEILING_S: float = 20.0
_MULTIPLIER = {"easy": 0.6, "normal": 1.0, "critical": 1.6}
_MIN_BUDGET_S = 0.05
# T-40c-prereq (see docs/audit/TIME_OVERRUN_TRIAGE.md §4.3): subtract
# a pad from the final budget so total play() wall — which includes
# belief update, TT probe for T-40c root-value history, GC pauses,
# and search-side overshoot between node-count deadline checks —
# stays inside the declared ceiling.
SEARCH_OVERHEAD_PAD_S: float = 0.3
# v0.2 default per T-20a / AUDIT_V01 M-01: 6.0 s matches the tournament
# base budget (240 s / 40 turns). v0.1 shipped 3.0 s as a provisional
# cap while the heuristic was uncalibrated; with BO-tuned weights the
# premise is gone and the ceiling is lifted.
DEFAULT_PER_TURN_CEILING_S: float = 6.0

# T-40c context-adaptive coefficients.
#   multiplier = 1.0 + CONTEXT_ENTROPY_COEF · (entropy / ln 64)
#                    + CONTEXT_VARIANCE_COEF · sign(variance - threshold)
# High entropy (rat uncertain) → spend MORE time on positional search.
# Low entropy (rat concentrated) → spend LESS time (SEARCH is the
# obvious call). High root-move-value variance (measured by the agent
# as the spread of PV scores across completed ID iterations) signals a
# complex position → spend more. Both coefficients are intentionally
# small because T-20e measured 97.9 % cutoff-on-first; we're trimming
# the remaining ~2 % of wasted search.
CONTEXT_ENTROPY_COEF: float = 0.3
CONTEXT_VARIANCE_COEF: float = 0.2
# Variance threshold above which we call the position "complex". Units
# are heuristic leaf values (linear W·features, unitless); 0.5 is a
# hand-picked floor that corresponds to roughly one carpet-point of
# spread in leaf valuation across sibling root moves.
CONTEXT_VARIANCE_HIGH_THRESHOLD: float = 0.5
# Hard bounds on the total context multiplier so no pathological
# entropy or variance estimate can push the budget outside
# [0.5, 1.5] of the baseline.
_CONTEXT_MULT_MIN: float = 0.5
_CONTEXT_MULT_MAX: float = 1.5
_LN_64: float = _math.log(64.0)


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

    def adjust_for_context(
        self,
        belief_summary: Optional[BeliefSummary],
        prev_eval_variance: Optional[float] = None,
    ) -> float:
        """T-40c: compute the context-adaptive multiplier.

        Formula:
            mult = 1.0
                 + CONTEXT_ENTROPY_COEF · (entropy / ln 64)
                 + CONTEXT_VARIANCE_COEF · sign_high
        where `sign_high` is +1 if `prev_eval_variance` exceeds
        `CONTEXT_VARIANCE_HIGH_THRESHOLD`, -1 if it is strictly below
        half that threshold (clearly-easy position), and 0 if
        variance is None or in the mid-band.

        The result is clamped to `[_CONTEXT_MULT_MIN, _CONTEXT_MULT_MAX]`
        (default 0.5..1.5) so no pathological belief/variance value can
        double or halve the budget beyond reason.

        Returns: float multiplier, never <= 0.

        Callable directly from `agent._play_internal` (the brief's
        requirement) OR consumed internally by `start_turn` when the
        caller passes `prev_eval_variance`. Callers that want the
        pre-adjustment budget can use `start_turn(...)` without the
        variance kwarg and then multiply externally.
        """
        ent = 0.0
        if belief_summary is not None and belief_summary.entropy is not None:
            ent = max(0.0, float(belief_summary.entropy))
        # Entropy normalized to [0, 1] against the maximum ln 64 ≈ 4.159.
        ent_frac = min(1.0, ent / _LN_64) if _LN_64 > 0 else 0.0
        ent_term = CONTEXT_ENTROPY_COEF * ent_frac

        var_term = 0.0
        if prev_eval_variance is not None:
            v = float(prev_eval_variance)
            if v > CONTEXT_VARIANCE_HIGH_THRESHOLD:
                var_term = CONTEXT_VARIANCE_COEF
            elif v < 0.5 * CONTEXT_VARIANCE_HIGH_THRESHOLD:
                var_term = -CONTEXT_VARIANCE_COEF

        mult = 1.0 + ent_term + var_term
        if mult < _CONTEXT_MULT_MIN:
            mult = _CONTEXT_MULT_MIN
        elif mult > _CONTEXT_MULT_MAX:
            mult = _CONTEXT_MULT_MAX
        return mult

    def start_turn(
        self,
        board: board_mod.Board,
        time_left_fn: Callable[[], float],
        belief_summary: Optional[BeliefSummary] = None,
        prev_eval_variance: Optional[float] = None,
    ) -> float:
        """Compute this turn's budget; store start time; return seconds.

        The returned budget already has `safety_s` reserved — callers
        should pass `safety_s=0.0` into `search.iterative_deepen` to
        avoid double-subtracting.

        T-40c: when `prev_eval_variance` is supplied (typically the
        variance of root-move values from the previous ID iteration),
        the budget is additionally scaled by
        `adjust_for_context(belief_summary, prev_eval_variance)`. The
        context multiplier composes with the endgame multiplier — it
        does not override it.
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
        # T-40c: context-adaptive scale (entropy + eval variance). Applied
        # AFTER the endgame cap so the two multipliers compose; the
        # resulting budget is then re-clamped by the remaining
        # ceiling/usable invariants below.
        context_mult = self.adjust_for_context(
            belief_summary, prev_eval_variance
        )
        budget *= context_mult
        # T-30e M-7: endgame uses a dedicated (higher) ceiling so the
        # T-30d lift actually delivers. Non-endgame still clamps at
        # `per_turn_ceiling_s` (default 6 s). In endgame we take the
        # max of (user-supplied ceiling, dedicated endgame ceiling) so
        # callers who explicitly raise `per_turn_ceiling_s` are not
        # silently clamped DOWN by the endgame constant.
        if in_endgame:
            effective_ceiling = max(
                self.per_turn_ceiling_s, ENDGAME_HARD_CEILING_S
            )
        else:
            effective_ceiling = self.per_turn_ceiling_s
        if budget > effective_ceiling:
            budget = effective_ceiling
        # Safety invariant: never allocate more than `usable` so the
        # 0.5 s reserve stays intact regardless of the upper caps.
        if budget > usable:
            budget = usable
        # T-40c-prereq: subtract the search-overhead pad AFTER all
        # other caps so total play() wall stays inside the ceiling
        # even when search overshoots its per-deadline check by a few
        # ms and outside-search work (belief update, TT probe, GC)
        # adds its own overhead. Floor at _MIN_BUDGET_S so the pad
        # can't starve the search entirely when time is already short.
        if budget > _MIN_BUDGET_S + SEARCH_OVERHEAD_PAD_S:
            budget -= SEARCH_OVERHEAD_PAD_S
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
