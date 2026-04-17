"""Tests for T-40c context-adaptive time budget.

Run via pytest:
    python3 -m pytest 3600-agents/RattleBot/tests/test_t40c.py -v
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np

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
    CONTEXT_ENTROPY_COEF,
    CONTEXT_VARIANCE_COEF,
    CONTEXT_VARIANCE_HIGH_THRESHOLD,
    ENDGAME_HARD_CAP_MULT,
    ENDGAME_HARD_CEILING_S,
)
from RattleBot.types import BeliefSummary


def _board() -> Board:
    return Board(time_to_play=240)


def _flat_belief() -> BeliefSummary:
    # Uniform belief: entropy ≈ ln(64) ≈ 4.159.
    arr = np.full(64, 1.0 / 64.0, dtype=np.float64)
    return BeliefSummary(
        belief=arr, entropy=math.log(64.0), max_mass=1.0 / 64.0, argmax=0
    )


def _peaked_belief() -> BeliefSummary:
    # Near-delta belief: entropy ≈ 0.
    arr = np.zeros(64, dtype=np.float64)
    arr[0] = 0.99
    arr[1:] = 0.01 / 63.0
    nz = arr[arr > 0]
    ent = float(-(nz * np.log(nz)).sum())
    return BeliefSummary(
        belief=arr, entropy=ent, max_mass=0.99, argmax=0
    )


# --- adjust_for_context unit ------------------------------------------


def test_adjust_for_context_high_entropy_gives_multiplier_above_one():
    tm = TimeManager()
    m = tm.adjust_for_context(_flat_belief(), prev_eval_variance=None)
    # Uniform belief → entropy fraction ≈ 1.0 → 1.0 + 0.3 = 1.3.
    assert m > 1.0
    assert abs(m - (1.0 + CONTEXT_ENTROPY_COEF)) < 1e-6


def test_adjust_for_context_low_entropy_stays_near_one():
    tm = TimeManager()
    m = tm.adjust_for_context(_peaked_belief(), prev_eval_variance=None)
    # Peaked belief → entropy ≈ 0 → multiplier ≈ 1.0.
    assert 0.95 < m < 1.05


def test_adjust_for_context_high_variance_adds_positive():
    tm = TimeManager()
    v_high = CONTEXT_VARIANCE_HIGH_THRESHOLD + 1.0
    m_hi = tm.adjust_for_context(_flat_belief(), prev_eval_variance=v_high)
    m_base = tm.adjust_for_context(_flat_belief(), prev_eval_variance=None)
    assert m_hi > m_base
    assert abs(m_hi - m_base - CONTEXT_VARIANCE_COEF) < 1e-6


def test_adjust_for_context_low_variance_drops_below_base():
    tm = TimeManager()
    # Variance below half the threshold triggers the negative term.
    v_low = 0.25 * CONTEXT_VARIANCE_HIGH_THRESHOLD
    m_lo = tm.adjust_for_context(_peaked_belief(), prev_eval_variance=v_low)
    # Peaked belief contributes near-zero entropy (~0.007 nats ≈
    # 0.0005 in the 0.3× term); low variance subtracts 0.2 cleanly.
    # So m_lo ≈ 0.8005 — comfortably below 1.0 but not exactly 1.0-0.2.
    assert m_lo < 0.9
    assert abs(m_lo - (1.0 - CONTEXT_VARIANCE_COEF)) < 0.02


def test_adjust_for_context_clamps_to_bounds():
    """Even with extreme inputs, multiplier stays in [0.5, 1.5]."""
    tm = TimeManager()
    # All terms maxed: flat belief + high variance = 1 + 0.3 + 0.2 = 1.5
    m = tm.adjust_for_context(
        _flat_belief(),
        prev_eval_variance=CONTEXT_VARIANCE_HIGH_THRESHOLD * 100,
    )
    assert 0.5 <= m <= 1.5


# --- composition with start_turn --------------------------------------


def test_start_turn_applies_context_multiplier():
    """Context multiplier actually changes the budget returned by
    `start_turn`. To isolate the effect from `classify()` (which uses
    belief max_mass too), we fix the classification label by passing
    belief_summary=None in both calls and use only the variance signal.
    """
    b = _board()
    b.player_worker.turns_left = 20  # midgame: normal class via None
    tm = TimeManager(per_turn_ceiling_s=1e6)  # ceiling out of the way
    # baseline: no context signal (variance=None, belief=None).
    budget_base = tm.start_turn(b, lambda: 60.0, None, prev_eval_variance=None)
    # ctx: high variance → +0.2 multiplier.
    budget_ctx = tm.start_turn(
        b, lambda: 60.0, None,
        prev_eval_variance=CONTEXT_VARIANCE_HIGH_THRESHOLD * 2,
    )
    assert budget_ctx > budget_base + 0.1, (
        f"ctx {budget_ctx:.3f} not > base {budget_base:.3f} + 0.1"
    )
    # Sanity: ratio should be ~1.2 (variance coefficient).
    assert abs(budget_ctx / budget_base - 1.2) < 0.05


def test_context_composes_with_endgame_not_override():
    """Endgame multiplier (3.5x) should still kick in, and context
    multiplier compounds on top of it without lifting past the usable
    cap."""
    b = _board()
    b.player_worker.turns_left = 3  # endgame
    tm = TimeManager()
    # Flat belief + no variance → entropy term 0.3 → context mult 1.3.
    budget = tm.start_turn(
        b, lambda: 30.0, _flat_belief(), prev_eval_variance=None,
    )
    # Non-endgame equivalent would be: turns_left=20
    b2 = _board()
    b2.player_worker.turns_left = 20
    budget_mid = tm.start_turn(
        b2, lambda: 30.0, _flat_belief(), prev_eval_variance=None,
    )
    # Endgame turn should reserve MORE time than midgame even with
    # identical context inputs (the 3.5x cap lift dominates).
    assert budget > budget_mid, (
        f"endgame {budget:.3f} not > midgame {budget_mid:.3f}"
    )


def test_context_never_violates_safety_reserve():
    """Even with max context multiplier, budget stays ≤ usable."""
    b = _board()
    b.player_worker.turns_left = 20
    tm = TimeManager(per_turn_ceiling_s=1e6)
    # usable = 1.0 - 0.5 = 0.5
    budget = tm.start_turn(
        b, lambda: 1.0, _flat_belief(),
        prev_eval_variance=CONTEXT_VARIANCE_HIGH_THRESHOLD * 100,
    )
    assert budget <= 0.5 + 1e-6


def test_context_with_none_variance_only_entropy_applies():
    tm = TimeManager()
    m = tm.adjust_for_context(_flat_belief(), None)
    # Entropy-only: 1 + 0.3 * 1.0 = 1.3.
    assert abs(m - 1.3) < 1e-6


def test_context_with_none_belief_only_variance_applies():
    tm = TimeManager()
    m = tm.adjust_for_context(
        None, prev_eval_variance=CONTEXT_VARIANCE_HIGH_THRESHOLD + 1.0
    )
    # Variance-only high: 1 + 0 + 0.2 = 1.2.
    assert abs(m - 1.2) < 1e-6


def test_context_with_both_none_is_identity():
    tm = TimeManager()
    assert tm.adjust_for_context(None, None) == 1.0


if __name__ == "__main__":
    import pytest as _p
    sys.exit(_p.main([__file__, "-v"]))
