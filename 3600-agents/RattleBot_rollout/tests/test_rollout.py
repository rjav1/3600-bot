"""Tests for RattleBot_rollout — prototype sanity tests.

Run directly:
    python3 3600-agents/RattleBot_rollout/tests/test_rollout.py

Or via pytest:
    python3 -m pytest 3600-agents/RattleBot_rollout/tests/test_rollout.py -v
"""

from __future__ import annotations

import os
import random
import sys
import time

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

from game.board import Board  # noqa: E402
from game.enums import Cell, MoveType, Noise, BOARD_SIZE  # noqa: E402
from game.move import Move  # noqa: E402

from RattleBot_rollout.agent import PlayerAgent  # noqa: E402
from RattleBot_rollout.rollout import (  # noqa: E402
    RolloutPlanner,
    plan_move,
)


# ---------------------------------------------------------------------------
# Fixtures


def _make_T(seed: int = 0) -> np.ndarray:
    """Row-stochastic 64x64 lazy random-walk matrix (mirrors engine pattern)."""
    rng = np.random.default_rng(seed)
    n = BOARD_SIZE * BOARD_SIZE
    T = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        x, y = i % BOARD_SIZE, i // BOARD_SIZE
        neighbors = [i]
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                neighbors.append(ny * BOARD_SIZE + nx)
        weights = rng.uniform(0.1, 1.0, size=len(neighbors))
        weights = weights / weights.sum()
        for j, w in zip(neighbors, weights):
            T[i, j] = w
    # renorm
    T = T / T.sum(axis=1, keepdims=True)
    return T


def _make_board(seed: int = 0) -> Board:
    rng = random.Random(seed)
    b = Board(time_to_play=240)
    shapes = [(2, 3), (3, 2), (2, 2)]
    for ox, oy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        w, h = rng.choice(shapes)
        for dx in range(w):
            for dy in range(h):
                x = dx if ox == 0 else 7 - dx
                y = dy if oy == 0 else 7 - dy
                b.set_cell((x, y), Cell.BLOCKED)
    # Spawn workers in inner 4x4.
    b.player_worker.position = (3, 3)
    b.opponent_worker.position = (5, 4)
    return b


def _fake_time_left(seconds: float):
    """Factory — returns a callable that claims N seconds remain."""
    def _fn():
        return seconds
    return _fn


# ---------------------------------------------------------------------------
# Tests


def test_planner_returns_legal_move_on_spawn_board():
    T = _make_T(seed=0)
    board = _make_board(seed=1)
    belief = np.ones(64, dtype=np.float64) / 64.0
    planner = RolloutPlanner(rng=random.Random(0))
    # Give it 1.5 s of budget — should complete promptly on an empty-ish
    # board.
    t0 = time.monotonic()
    mv = planner.plan(
        board=board,
        belief_vec=belief,
        T=T,
        time_left=_fake_time_left(1.5),
        budget_s=1.5,
    )
    elapsed = time.monotonic() - t0
    assert mv is not None, "planner should return a move"
    assert board.is_valid_move(mv), f"planner returned invalid move: {mv}"
    assert elapsed < 6.0, f"planner overshot: {elapsed:.2f}s"


def test_planner_handles_zero_budget_gracefully():
    T = _make_T(seed=0)
    board = _make_board(seed=2)
    belief = np.ones(64, dtype=np.float64) / 64.0
    mv = plan_move(
        board=board,
        belief_vec=belief,
        T=T,
        time_left=_fake_time_left(0.05),   # essentially none
        budget_s=0.05,
    )
    assert mv is not None
    assert board.is_valid_move(mv)


def test_agent_play_returns_legal_move():
    T = _make_T(seed=0)
    board = _make_board(seed=3)
    agent = PlayerAgent(board, transition_matrix=T)
    assert agent._init_ok
    # Sensor: squeak, dist 3 — arbitrary.
    sensor = (Noise.SQUEAK, 3)
    mv = agent.play(board, sensor, _fake_time_left(4.0))
    assert mv is not None
    assert board.is_valid_move(mv), f"agent returned invalid move: {mv}"


def test_agent_crash_proof_on_bad_init():
    """If init fails (e.g. bad T), play must still return a legal move."""
    board = _make_board(seed=4)
    # Force init to fail by passing a malformed T.
    try:
        agent = PlayerAgent(board, transition_matrix=np.zeros((3, 3)))
    except Exception:
        agent = None
    assert agent is not None, "PlayerAgent.__init__ must not raise"
    assert agent._init_ok is False
    mv = agent.play(board, (Noise.SQUEAK, 2), _fake_time_left(4.0))
    assert mv is not None
    # Emergency fallback should yield a legal move or a SEARCH at (0,0).
    # Either is acceptable for crash-proofing.


def test_agent_plays_multiple_turns_without_crashing():
    T = _make_T(seed=0)
    board = _make_board(seed=5)
    agent = PlayerAgent(board, transition_matrix=T)
    for turn in range(4):
        mv = agent.play(board, (Noise.SQUEAK, 2), _fake_time_left(3.0))
        assert mv is not None and board.is_valid_move(mv), (
            f"turn {turn} returned invalid move {mv}"
        )
        # Apply to mutate — this is how the engine advances state.
        ok = board.apply_move(mv, check_ok=True)
        assert ok, f"apply_move rejected move {mv} at turn {turn}"
        if board.is_game_over():
            break
        # Simulate a fake opp response: pick the first legal move.
        valid = board.get_valid_moves(exclude_search=True)
        if valid:
            # Need to reverse perspective so opp_worker becomes
            # player_worker, apply, then reverse back.
            board.reverse_perspective()
            opp_valid = board.get_valid_moves(exclude_search=True)
            if opp_valid:
                board.apply_move(opp_valid[0], check_ok=True)
            board.reverse_perspective()


if __name__ == "__main__":
    import sys as _sys

    tests = [
        test_planner_returns_legal_move_on_spawn_board,
        test_planner_handles_zero_budget_gracefully,
        test_agent_play_returns_legal_move,
        test_agent_crash_proof_on_bad_init,
        test_agent_plays_multiple_turns_without_crashing,
    ]
    failures = 0
    for t in tests:
        name = t.__name__
        try:
            t()
            print(f"PASS  {name}")
        except Exception as e:
            failures += 1
            print(f"FAIL  {name}: {e!r}")
    _sys.exit(1 if failures else 0)
