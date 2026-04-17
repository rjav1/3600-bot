"""Tests for RattleBot.time_mgr -- T-20a (configurable ceiling) + T-20b
(safety_s single-source) per BOT_STRATEGY_V02_ADDENDUM §2.1 / §2.2.

Run directly:
    python3 3600-agents/RattleBot/tests/test_time_mgr.py

Or via pytest:
    python3 -m pytest 3600-agents/RattleBot/tests/test_time_mgr.py -v
"""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
for p in (
    os.path.join(_REPO_ROOT, "engine"),
    os.path.join(_REPO_ROOT, "3600-agents"),
):
    if p not in sys.path:
        sys.path.insert(0, p)

from game.board import Board

from RattleBot.time_mgr import (
    TimeManager,
    DEFAULT_PER_TURN_CEILING_S,
    ENDGAME_HARD_CAP_MULT,
    ENDGAME_TURNS_THRESHOLD,
    HARD_CAP_MULT,
    SEARCH_OVERHEAD_PAD_S,
)


def _board() -> Board:
    return Board(time_to_play=240)


# --- T-20a: configurable ceiling ----------------------------------------


def test_default_ceiling_is_six_seconds():
    """Default constructor yields the v0.2 6.0 s ceiling (T-20a)."""
    tm = TimeManager()
    assert tm.per_turn_ceiling_s == 6.0
    assert DEFAULT_PER_TURN_CEILING_S == 6.0


def test_ceiling_configurable():
    """Custom ceiling is stored and used."""
    tm = TimeManager(per_turn_ceiling_s=4.5)
    assert tm.per_turn_ceiling_s == 4.5


def test_start_turn_respects_six_second_ceiling():
    """With generous time_left on a midgame turn, the 6 s
    per_turn_ceiling_s pins the budget. (Use turns_left=10 to stay
    out of the T-30e endgame ceiling regime.)
    """
    b = _board()
    b.player_worker.turns_left = 10  # > ENDGAME_TURNS_THRESHOLD=5
    # 120 s remaining / 10 turns -> base = 11.95 s * 1.0 = 11.95 s;
    # 6 s ceiling pins it.
    tm = TimeManager(per_turn_ceiling_s=6.0)
    budget = tm.start_turn(b, lambda: 120.0)
    # T-40c-prereq: pad subtracts 0.3s AFTER ceiling clamp.
    assert abs(budget - (6.0 - SEARCH_OVERHEAD_PAD_S)) < 1e-6, (
        f"expected ceiling - pad, got {budget}"
    )


def test_start_turn_below_ceiling_is_untouched():
    """When the adaptive budget is below the ceiling, no clamp kicks in.
    Still subject to the T-40c-prereq 0.3 s pad; classify() with
    turns_left>=36 labels this "easy" (0.6× multiplier).
    """
    b = _board()
    b.player_worker.turns_left = 40
    # time_left=40s, turns_left=40 -> base ≈ 0.99 s, easy×0.6=0.59s,
    # pad-0.3 ≈ 0.29 s.
    tm = TimeManager(per_turn_ceiling_s=6.0)
    budget = tm.start_turn(b, lambda: 40.0)
    assert 0.05 < budget < 1.5, f"expected ~0.3s, got {budget}"


def test_custom_ceiling_overrides_default():
    """A user-configured 3.0 s ceiling still works at midgame.
    Post-T-30e the endgame ceiling is max(per_turn_ceiling_s, 20 s), so
    this test pins `turns_left=10` to exercise the non-endgame path.
    """
    b = _board()
    b.player_worker.turns_left = 10  # > ENDGAME_TURNS_THRESHOLD=5
    tm = TimeManager(per_turn_ceiling_s=3.0)
    budget = tm.start_turn(b, lambda: 120.0)
    # T-40c-prereq: pad subtracts 0.3 s AFTER ceiling clamp.
    assert abs(budget - (3.0 - SEARCH_OVERHEAD_PAD_S)) < 1e-6


# --- T-20b: single-source safety_s --------------------------------------


def test_time_mgr_reserves_safety():
    """time_mgr.start_turn subtracts safety_s from time_left before
    computing base budget (owner of the reserve)."""
    b = _board()
    b.player_worker.turns_left = 1
    tm = TimeManager(per_turn_ceiling_s=100.0)  # disable ceiling
    # time_left=0.4s; safety=0.5 -> usable=0, so min-budget kicks in.
    budget = tm.start_turn(b, lambda: 0.4)
    assert budget <= 0.1


def test_safety_s_attribute_exposed_for_sentinel():
    """agent.py used to read `self._time_mgr.safety_s`; keep that
    attribute available even though agent now passes 0.0 downstream."""
    tm = TimeManager()
    assert tm.safety_s == 0.5


def test_search_accepts_safety_zero():
    """Calling iterative_deepen with safety_s=0.0 (the T-20b contract)
    does not crash and respects the caller-supplied budget."""
    import time as _time

    from game.enums import Cell
    import numpy as np

    from RattleBot.search import Search
    from RattleBot.types import BeliefSummary

    b = _board()
    # place minimal blockers so spawn/mobility is normal
    for x in range(3):
        for y in range(3):
            b.set_cell((x, y), Cell.BLOCKED)
    b.player_worker.position = (4, 4)
    b.opponent_worker.position = (5, 5)

    bs = BeliefSummary(
        belief=np.ones(64, dtype=np.float64) / 64.0,
        entropy=0.0,
        max_mass=1.0 / 64.0,
        argmax=0,
    )

    s = Search(tt_size=1 << 16)
    t0 = _time.perf_counter()
    mv = s.iterative_deepen(
        b, bs, lambda bb, _bs: 0.0, time_left_s=0.5, safety_s=0.0
    )
    elapsed = _time.perf_counter() - t0
    assert mv is not None
    # With safety_s=0 and time_left=0.5s, wall must stay under 0.7s.
    assert elapsed < 0.7, f"elapsed={elapsed}"


# --- classify smoke -----------------------------------------------------


def test_classify_buckets():
    """AUDIT_V01 §3.10 gap #4: exercise classify()."""
    import numpy as np
    from RattleBot.types import BeliefSummary

    b = _board()

    flat = BeliefSummary(
        belief=np.ones(64) / 64.0, entropy=4.159, max_mass=1.0 / 64.0, argmax=0
    )
    hot = BeliefSummary(
        belief=np.zeros(64), entropy=0.0, max_mass=0.5, argmax=0
    )

    tm = TimeManager()

    b.player_worker.turns_left = 2
    assert tm.classify(b, flat) == "critical"  # late-game

    b.player_worker.turns_left = 40
    assert tm.classify(b, flat) == "easy"  # opening

    b.player_worker.turns_left = 20
    assert tm.classify(b, hot) == "critical"  # hot belief

    b.player_worker.turns_left = 20
    assert tm.classify(b, flat) == "easy"  # flat belief (<= 0.05)

    mid = BeliefSummary(
        belief=np.zeros(64), entropy=1.0, max_mass=0.1, argmax=0
    )
    b.player_worker.turns_left = 20
    assert tm.classify(b, mid) == "normal"


# --- T-30d: endgame multiplier cap lift ---------------------------------


def test_endgame_multiplier_extended_at_low_turns_left():
    """With turns_left <= ENDGAME_TURNS_THRESHOLD, the surplus hard-cap
    should be ENDGAME_HARD_CAP_MULT (3.5x), not the default 2.5x.

    Post-T-30e the budget is bounded by
      min(base * 3.5, effective_ceiling, usable)
    where effective_ceiling = max(per_turn_ceiling_s, ENDGAME_HARD_CEILING_S).
    With per_turn_ceiling_s=1e6, ceiling is 1e6, so the remaining
    binding upper bound is min(base*3.5, usable).
    """
    assert ENDGAME_TURNS_THRESHOLD >= 3
    assert ENDGAME_HARD_CAP_MULT > HARD_CAP_MULT

    b = _board()
    b.player_worker.turns_left = 3
    tm = TimeManager(per_turn_ceiling_s=1e6)  # ceiling effectively off
    # Use time_left large enough that `usable` dominates neither:
    # time_left=300 → usable=299.5, base=99.83, base*3.5=349.4 → clamp
    # to usable=299.5 — budget above 2.5×base=249.58 confirms the lift.
    budget = tm.start_turn(b, lambda: 300.0)

    usable = 300.0 - tm.safety_s
    base = usable / 3
    old_cap = base * HARD_CAP_MULT       # 249.58 s
    new_cap = base * ENDGAME_HARD_CAP_MULT  # 349.42 s
    # T-40c-prereq: pad subtracts 0.3 s from the clamped budget.
    bounded = min(new_cap, usable) - SEARCH_OVERHEAD_PAD_S

    assert budget > old_cap + 1e-6, (
        f"budget {budget:.3f}s did not clear 2.5x base={old_cap:.3f}s"
    )
    assert abs(budget - bounded) < 1e-6, (
        f"expected {bounded:.3f}s, got {budget:.3f}s"
    )


def test_non_endgame_uses_default_cap():
    """turns_left > ENDGAME_TURNS_THRESHOLD keeps the 2.5x cap."""
    b = _board()
    b.player_worker.turns_left = ENDGAME_TURNS_THRESHOLD + 5  # midgame
    tm = TimeManager(per_turn_ceiling_s=1e6)
    budget = tm.start_turn(b, lambda: 100.0)
    usable = 100.0 - tm.safety_s
    base = usable / (ENDGAME_TURNS_THRESHOLD + 5)
    default_cap = base * HARD_CAP_MULT
    # Critical mult doesn't apply at turns_left=10, so label is normal
    # (1.0x) -> budget == base. Either way, budget must not exceed 2.5x.
    assert budget <= default_cap + 1e-6


def test_endgame_safety_s_still_reserved():
    """T-30d must not eat into the 0.5s safety reserve."""
    b = _board()
    b.player_worker.turns_left = 2
    tm = TimeManager(per_turn_ceiling_s=1e6)
    # time_left=0.4s < safety_s: usable==0, budget collapses to min.
    budget = tm.start_turn(b, lambda: 0.4)
    assert budget <= 0.1, f"safety_s violated: budget={budget}"


# --- T-40c-prereq: search-overhead pad --------------------------------


def test_start_turn_pad_reserved_for_search_overhead():
    """T-40c-prereq: final budget leaves SEARCH_OVERHEAD_PAD_S below
    the caller's cap so total play() wall stays inside the ceiling.
    """
    b = _board()
    b.player_worker.turns_left = 10  # midgame
    tm = TimeManager()
    # time_left=60s → base=(59.5)/10=5.95s, under 6s ceiling.
    # Post-pad: 5.95 − 0.3 = 5.65 s.
    budget = tm.start_turn(b, lambda: 60.0)
    usable = 60.0 - tm.safety_s
    base = usable / 10
    assert abs(budget - (base - SEARCH_OVERHEAD_PAD_S)) < 1e-6


def test_pad_does_not_starve_tiny_budgets():
    """When usable is already near zero, the pad must not drop the
    budget below _MIN_BUDGET_S — the floor protects search-always-runs.
    """
    b = _board()
    b.player_worker.turns_left = 10
    tm = TimeManager()
    # time_left=0.55 → usable=0.05 → below pad floor.
    budget = tm.start_turn(b, lambda: 0.55)
    assert budget > 0.0
    assert budget <= 0.1  # min_budget is 0.05, capped to usable


if __name__ == "__main__":
    import pytest as _p
    sys.exit(_p.main([__file__, "-v"]))
