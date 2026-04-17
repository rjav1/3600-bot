"""Tests for T-30e (V03_REDTEAM H-1 + M-7 fixes).

Run via pytest:
    python3 -m pytest 3600-agents/RattleBot/tests/test_t30e.py -v
"""

from __future__ import annotations

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
from game.enums import Cell, MoveType, Noise
from game.move import Move

from RattleBot.agent import PlayerAgent
from RattleBot.time_mgr import (
    TimeManager,
    ENDGAME_HARD_CEILING_S,
    ENDGAME_HARD_CAP_MULT,
    ENDGAME_TURNS_THRESHOLD,
    DEFAULT_PER_TURN_CEILING_S,
)


def _identity_T() -> np.ndarray:
    return np.eye(64, dtype=np.float64)


def _board() -> Board:
    return Board(time_to_play=240)


# --- H-1: own-capture resets belief ------------------------------------


def test_h1_our_capture_resets_belief():
    """When `board.player_search = (loc, True)` at the top of play(), the
    agent must reset its belief to p_0 before the subsequent
    `belief.update()` runs. Verified via
    `_update_consec_search_misses`, which owns the reconciliation.
    """
    b = _board()
    agent = PlayerAgent(b, transition_matrix=_identity_T())
    assert agent._init_ok

    # Poison belief so we can detect the reset.
    agent._belief.belief = np.zeros(64, dtype=np.float64)
    agent._belief.belief[17] = 1.0  # delta at a non-(0,0) cell
    # Simulate: our last move was SEARCH that HIT at cell (3, 3).
    agent._last_own_move_was_search = True
    b.player_search = ((3, 3), True)
    agent._update_consec_search_misses(b)

    # belief must be back to p_0 (identity T → p_0 = e_0).
    expected_p0 = agent._belief.p_0
    assert np.allclose(agent._belief.belief, expected_p0), (
        "belief did not reset to p_0 after our capture"
    )
    assert agent._consec_search_misses == 0


def test_h1_our_miss_zeroes_cell():
    """On miss, the searched cell's probability must be zeroed and the
    belief renormalized — otherwise the SEARCH-gate sees a stale peak.
    """
    b = _board()
    agent = PlayerAgent(b, transition_matrix=_identity_T())
    # Seed a peaked belief at the cell we're about to search.
    hot_cell_flat = 3 * 8 + 3  # (3, 3) → flat index 27
    belief = np.full(64, 0.01 / 63, dtype=np.float64)
    belief[hot_cell_flat] = 0.99
    belief /= belief.sum()
    agent._belief.belief = belief.copy()

    agent._last_own_move_was_search = True
    b.player_search = ((3, 3), False)
    agent._update_consec_search_misses(b)

    assert agent._belief.belief[hot_cell_flat] == 0.0, (
        "searched cell not zeroed after miss"
    )
    assert abs(agent._belief.belief.sum() - 1.0) < 1e-9
    assert agent._consec_search_misses == 1


def test_h1_non_search_leaves_belief_untouched():
    """If our last move was NOT a SEARCH, the reconcile path must not
    alter belief (we only apply to SEARCH outcomes)."""
    b = _board()
    agent = PlayerAgent(b, transition_matrix=_identity_T())
    seed = np.full(64, 1.0 / 64, dtype=np.float64)
    agent._belief.belief = seed.copy()

    agent._last_own_move_was_search = False
    agent._update_consec_search_misses(b)

    assert np.array_equal(agent._belief.belief, seed)
    assert agent._consec_search_misses == 0


# --- M-7: endgame ceiling bypass ---------------------------------------


def test_m7_endgame_budget_bypasses_ceiling():
    """With turns_left=3 and time_left=60s, base≈19.8s. The default 6s
    ceiling should NOT clamp in endgame; budget should land at
    `ENDGAME_HARD_CEILING_S` (20s) or the cap × base, whichever is lower.
    """
    b = _board()
    b.player_worker.turns_left = 3
    tm = TimeManager()  # default 6 s per_turn_ceiling_s
    budget = tm.start_turn(b, lambda: 60.0)

    # Sanity: we're clearly past the default 6 s clamp.
    assert budget > DEFAULT_PER_TURN_CEILING_S + 1e-6, (
        f"endgame still clamped at 6 s: budget={budget:.3f}s"
    )
    # Exact bound: min(cap_mult × base, ENDGAME_HARD_CEILING_S, usable).
    usable = 60.0 - tm.safety_s
    base = usable / 3
    cap_bound = base * ENDGAME_HARD_CAP_MULT
    expected = min(cap_bound, ENDGAME_HARD_CEILING_S, usable)
    assert abs(budget - expected) < 1e-6, (
        f"expected ≈{expected:.3f}s, got {budget:.3f}s"
    )


def test_m7_endgame_with_moderate_time_hits_ceiling():
    """With enough time, the endgame budget lands exactly at the
    dedicated 20 s endgame ceiling (bigger than default 6 s)."""
    b = _board()
    b.player_worker.turns_left = 3
    tm = TimeManager()
    # time_left=120 s, base=(119.5)/3≈39.83 s, cap_bound≈139.4 s
    # → clamped to ENDGAME_HARD_CEILING_S=20 s.
    budget = tm.start_turn(b, lambda: 120.0)
    assert abs(budget - ENDGAME_HARD_CEILING_S) < 1e-6, (
        f"expected {ENDGAME_HARD_CEILING_S}s, got {budget:.3f}s"
    )


def test_m7_non_endgame_still_clamps_at_default_ceiling():
    """Midgame turns MUST still clamp at per_turn_ceiling_s (default 6s)
    — the M-7 fix only lifts the endgame ceiling."""
    b = _board()
    b.player_worker.turns_left = 20  # well above ENDGAME_TURNS_THRESHOLD
    tm = TimeManager()
    budget = tm.start_turn(b, lambda: 240.0)
    assert budget <= DEFAULT_PER_TURN_CEILING_S + 1e-6, (
        f"midgame leaked past default ceiling: {budget:.3f}s"
    )


def test_m7_endgame_safety_s_still_reserved():
    """Even with the bigger endgame ceiling, the 0.5 s safety reserve
    must hold: budget ≤ usable = time_left − safety_s."""
    b = _board()
    b.player_worker.turns_left = 3
    tm = TimeManager()
    # time_left tiny → usable≈0 → budget collapses to min-budget.
    budget = tm.start_turn(b, lambda: 0.4)
    assert budget <= 0.1
    # Slightly larger case: time_left=1.0 → usable=0.5 → budget ≤ usable.
    budget = tm.start_turn(b, lambda: 1.0)
    assert budget <= 0.5 + 1e-6


if __name__ == "__main__":
    import pytest as _p
    sys.exit(_p.main([__file__, "-v"]))
