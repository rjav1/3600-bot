"""Tests for T-20f (V01_LOSS_ANALYSIS fixes):
  - Bug 1: move_gen excludes k=1 CARPET when a non-k=1 move exists.
  - Bug 2: SEARCH-gate saturation guards (consec-miss + entropy ceilings).

Run via pytest:
    python3 -m pytest 3600-agents/RattleBot/tests/test_t20f.py -v
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

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
from game.enums import Cell, Direction, MoveType
from game.move import Move

from RattleBot.agent import (
    PlayerAgent,
    SEARCH_GATE_ENTROPY_CEIL,
    SEARCH_GATE_MASS_FLOOR,
    SEARCH_GATE_MAX_CONSEC_MISSES,
)
from RattleBot.move_gen import ordered_moves


# --- Bug 1: k=1 CARPET pruning -----------------------------------------


def test_move_gen_excludes_k1_when_alternative():
    """When a k=2 CARPET (or any non-k=1 move) is available, k=1 must
    not appear in the returned list."""
    fake_moves = [
        Move.carpet(Direction.RIGHT, 1),
        Move.carpet(Direction.RIGHT, 2),
        Move.plain(Direction.UP),
        Move.prime(Direction.DOWN),
    ]

    class _StubBoard:
        def get_valid_moves(self, exclude_search=True):
            return list(fake_moves)

    out = ordered_moves(_StubBoard())
    assert len(out) == 3
    assert all(
        not (m.move_type == MoveType.CARPET and m.roll_length < 2)
        for m in out
    ), f"k=1 CARPET leaked: {out}"


def test_move_gen_permits_k1_fallback():
    """If k=1 CARPET is the ONLY legal move, keep it — the engine may
    have produced an edge case where nothing else is viable."""
    k1 = Move.carpet(Direction.LEFT, 1)

    class _StubBoard:
        def get_valid_moves(self, exclude_search=True):
            return [k1]

    out = ordered_moves(_StubBoard())
    assert len(out) == 1
    assert out[0].move_type == MoveType.CARPET
    assert out[0].roll_length == 1


# --- Bug 2: SEARCH-gate saturation guards ------------------------------


def _board_with_T() -> Board:
    # Full-rank T so RatBelief(T, board) init doesn't choke.
    return Board(time_to_play=240)


def _identity_T() -> np.ndarray:
    return np.eye(64, dtype=np.float64)


def test_search_gate_consecutive_miss_guard():
    """After SEARCH_GATE_MAX_CONSEC_MISSES consecutive misses, the gate
    should stop firing SEARCH even if max_mass > 1/3 and entropy is low.
    """
    b = _board_with_T()
    agent = PlayerAgent(b, transition_matrix=_identity_T())
    assert agent._init_ok

    # Simulate miss counter already at the cap.
    agent._consec_search_misses = SEARCH_GATE_MAX_CONSEC_MISSES + 1
    # Peaked belief that would otherwise pass the mass + entropy gates.
    peaked = np.zeros(64, dtype=np.float64)
    peaked[0] = 0.9
    peaked[1:] = 0.1 / 63.0
    from RattleBot.types import BeliefSummary
    bs = BeliefSummary(
        belief=peaked, entropy=0.5, max_mass=0.9, argmax=0
    )

    # Mass floor and entropy ceiling pass individually...
    assert bs.max_mass > SEARCH_GATE_MASS_FLOOR
    assert bs.entropy < SEARCH_GATE_ENTROPY_CEIL
    # ...but the consec-miss guard should veto.
    gate = (
        bs.max_mass > SEARCH_GATE_MASS_FLOOR
        and bs.entropy < SEARCH_GATE_ENTROPY_CEIL
        and agent._consec_search_misses <= SEARCH_GATE_MAX_CONSEC_MISSES
    )
    assert gate is False, "gate should refuse SEARCH after cap"


def test_search_gate_entropy_guard():
    """A flat belief (near max-entropy) must fail the gate even if one
    cell barely clears the mass floor."""
    # Construct a belief where max_mass is just above the floor but
    # entropy is near max (ln 64 ≈ 4.159).
    flat = np.full(64, (1.0 - 0.34) / 63.0, dtype=np.float64)
    flat[0] = 0.34  # barely over 1/3
    # entropy of this distribution
    nz = flat[flat > 0]
    ent = float(-(nz * np.log(nz)).sum())
    assert ent > SEARCH_GATE_ENTROPY_CEIL, (
        f"test precondition broken: ent={ent}"
    )

    gate = bool(
        flat[0] > SEARCH_GATE_MASS_FLOOR
        and ent < SEARCH_GATE_ENTROPY_CEIL
        and 0 <= SEARCH_GATE_MAX_CONSEC_MISSES
    )
    assert gate is False, "flat-belief gate should veto SEARCH"


# --- Extra: consec-miss counter reconciles with board.player_search ----


def test_consec_miss_counter_increments_on_miss():
    b = _board_with_T()
    agent = PlayerAgent(b, transition_matrix=_identity_T())
    agent._last_own_move_was_search = True
    b.player_search = ((3, 3), False)
    agent._update_consec_search_misses(b)
    assert agent._consec_search_misses == 1
    # Another miss keeps climbing.
    agent._update_consec_search_misses(b)
    assert agent._consec_search_misses == 2


def test_consec_miss_counter_resets_on_hit():
    b = _board_with_T()
    agent = PlayerAgent(b, transition_matrix=_identity_T())
    agent._consec_search_misses = 5
    agent._last_own_move_was_search = True
    b.player_search = ((3, 3), True)
    agent._update_consec_search_misses(b)
    assert agent._consec_search_misses == 0


def test_consec_miss_counter_resets_on_non_search():
    b = _board_with_T()
    agent = PlayerAgent(b, transition_matrix=_identity_T())
    agent._consec_search_misses = 5
    agent._last_own_move_was_search = False
    agent._update_consec_search_misses(b)
    assert agent._consec_search_misses == 0


if __name__ == "__main__":
    import pytest as _p
    sys.exit(_p.main([__file__, "-v"]))
