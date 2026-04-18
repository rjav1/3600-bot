"""Tests for RattleBot.rat_belief — T-13, BOT_STRATEGY §5 / T-HMM-1, T-HMM-2.

Run directly (no pytest required):
    python3 3600-agents/RattleBot/tests/test_rat_belief.py

Or via pytest:
    python3 -m pytest 3600-agents/RattleBot/tests/test_rat_belief.py -v

The test file bootstraps `sys.path` so it works from the repo root without
installing the package.
"""

from __future__ import annotations

import os
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
from game.enums import Noise, BOARD_SIZE  # noqa: E402

from RattleBot.rat_belief import RatBelief, _compute_p0  # noqa: E402


# ----------------------------------------------------------------------
# Fixtures

def _make_T(seed: int = 0) -> np.ndarray:
    """Deterministic row-stochastic 64x64 with lazy random-walk structure.

    Mirrors the engine's rat-transition pattern: self-loop + up-to-4 neighbors.
    Good enough for the HMM math -- we don't need a specific mixing rate.
    """
    rng = np.random.default_rng(seed)
    n = BOARD_SIZE * BOARD_SIZE
    T = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        x, y = i % BOARD_SIZE, i // BOARD_SIZE
        neighbors = [i]  # self-loop
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                neighbors.append(ny * BOARD_SIZE + nx)
        weights = rng.uniform(0.1, 1.0, size=len(neighbors))
        weights = weights / weights.sum()
        for j, w in zip(neighbors, weights):
            T[i, j] = w
    # paranoid renorm
    T = T / T.sum(axis=1, keepdims=True)
    return T


def _make_board() -> Board:
    """Minimal Board with a worker positioned at (3, 3) (inner 4x4).
    Does not run a real game -- we only need `get_cell`, `player_worker`,
    `opponent_search`, `is_player_a_turn`, `turn_count`.
    """
    board = Board(build_history=False)
    board.player_worker.position = (3, 3)
    board.opponent_worker.position = (4, 4)
    board.turn_count = 0
    board.is_player_a_turn = True
    board.opponent_search = (None, False)
    board.player_search = (None, False)
    return board


# ----------------------------------------------------------------------
# Tests

def test_p0_valid_distribution():
    T = _make_T()
    rb = RatBelief(T, _make_board())
    b = rb.p_0
    assert b.shape == (64,), f"shape {b.shape}"
    assert abs(b.sum() - 1.0) < 1e-9, f"sum={b.sum()}"
    assert (b >= 0).all(), f"neg entries: {b.min()}"
    # Should be close to stationary and not a delta at (0,0).
    assert b.max() < 0.2, (
        "p_0 max too high -- looks like under-mixed or still delta-like"
    )


def test_belief_init_matches_p0():
    T = _make_T()
    rb = RatBelief(T, _make_board())
    assert np.array_equal(rb.belief, rb.p_0)
    assert rb._first_call is True


def test_update_preserves_normalization():
    T = _make_T()
    board = _make_board()
    rb = RatBelief(T, board)
    rng = np.random.default_rng(123)
    for turn in range(40):
        noise = Noise(int(rng.integers(0, 3)))
        # Reported distance in a realistic range, worker is at (3,3).
        dist = int(rng.integers(0, 12))
        board.turn_count = turn
        board.is_player_a_turn = bool(turn % 2 == 0)
        summary = rb.update(board, (noise, dist))
        b = rb.belief
        assert abs(b.sum() - 1.0) < 1e-9, f"turn {turn}: sum={b.sum()}"
        assert (b >= 0).all(), f"turn {turn}: neg entry"
        assert abs(summary.belief.sum() - 1.0) < 1e-9
        assert summary.max_mass == b.max()
        assert summary.argmax == int(b.argmax())
        # Entropy in nats: [0, ln 64]
        assert 0.0 <= summary.entropy <= np.log(64) + 1e-6


def test_post_hit_resets_to_p0_via_helper():
    T = _make_T()
    board = _make_board()
    rb = RatBelief(T, board)
    # Walk a few turns so belief diverges from p_0.
    for _ in range(5):
        board.turn_count += 1
        rb.update(board, (Noise.SCRATCH, 4))
    assert not np.allclose(rb.belief, rb.p_0), "belief should have diverged"
    rb.handle_post_capture_reset(captured_by_us=True)
    assert np.allclose(rb.belief, rb.p_0)


def test_apply_our_search_hit_resets_to_p0():
    T = _make_T()
    board = _make_board()
    rb = RatBelief(T, board)
    for _ in range(3):
        board.turn_count += 1
        rb.update(board, (Noise.SQUEAL, 2))
    rb.apply_our_search((5, 5), hit=True)
    assert np.allclose(rb.belief, rb.p_0)


def test_apply_our_search_miss_zeros_cell():
    T = _make_T()
    board = _make_board()
    rb = RatBelief(T, board)
    # One update so we're not right at p_0 (any cell has mass).
    board.turn_count = 1
    rb.update(board, (Noise.SQUEAK, 3))
    # Pick a cell with nonzero mass.
    cell_idx = int(rb.belief.argmax())
    cell = (cell_idx % BOARD_SIZE, cell_idx // BOARD_SIZE)
    before_mass = rb.belief[cell_idx]
    assert before_mass > 0.0
    rb.apply_our_search(cell, hit=False)
    assert rb.belief[cell_idx] == 0.0
    assert abs(rb.belief.sum() - 1.0) < 1e-9
    # Other cells should sum to 1 (renormalized up).
    assert (rb.belief >= 0).all()


def test_first_turn_guard_no_double_predict():
    """On player A turn_count=0, update() must be equivalent to
    'one predict + one sensor update', not 'two predicts + opp-search +
    sensor update'. We compare to a hand-computed reference.
    """
    T = _make_T()
    board = _make_board()  # is_player_a_turn=True, turn_count=0
    board.opponent_search = (None, False)

    rb = RatBelief(T, board)
    # Reference: one predict from p_0, then sensor update.
    ref = rb.p_0 @ T

    # Simulate sensor update inline using the same likelihoods.
    from RattleBot.rat_belief import _NOISE_LIK, _DIST_LIK, _MAX_TRUE_DIST
    cell_types = np.array(
        [int(board.get_cell((i % 8, i // 8))) for i in range(64)]
    )
    noise_factor = _NOISE_LIK[int(Noise.SCRATCH), cell_types]
    worker_loc = board.player_worker.get_location()
    worker_idx = worker_loc[1] * 8 + worker_loc[0]
    from RattleBot.rat_belief import _MANHATTAN
    td = np.minimum(_MANHATTAN[worker_idx], _MAX_TRUE_DIST)
    dist_factor = _DIST_LIK[td, 4]
    ref = ref * noise_factor * dist_factor
    ref = ref / ref.sum()

    rb.update(board, (Noise.SCRATCH, 4))
    assert np.allclose(rb.belief, ref, atol=1e-12), (
        f"first-turn belief != expected 'one-predict + sensor'; "
        f"max abs diff = {np.max(np.abs(rb.belief - ref))}"
    )
    assert rb._first_call is False


def test_snapshot_restore_roundtrip():
    T = _make_T()
    board = _make_board()
    rb = RatBelief(T, board)
    for _ in range(4):
        board.turn_count += 1
        rb.update(board, (Noise.SCRATCH, 3))
    snap = rb.snapshot()
    # Mutate.
    rb.apply_our_search((2, 2), hit=True)
    assert np.allclose(rb.belief, rb.p_0)
    # Restore.
    rb.restore(snap)
    assert np.array_equal(rb.belief, snap)


def test_opp_search_miss_zeros_cell():
    T = _make_T()
    board = _make_board()
    rb = RatBelief(T, board)
    # Bump past the first-turn guard so the opp-phase runs.
    board.turn_count = 2
    board.is_player_a_turn = True
    board.opponent_search = ((6, 6), False)
    rb.update(board, (Noise.SQUEAK, 3))
    idx = 6 * 8 + 6
    # After opp-miss at (6,6), then one more predict, then sensor update,
    # cell (6,6) may have received mass back from neighbors via the second
    # predict. That's correct behavior -- we only strictly assert that the
    # miss *temporarily* zeroed the cell by checking on a separate path.
    # Here we use apply_opp_search directly for the strict invariant.
    rb2 = RatBelief(T, _make_board())
    rb2.apply_opp_search((6, 6), hit=False)
    assert rb2.belief[idx] == 0.0
    assert abs(rb2.belief.sum() - 1.0) < 1e-9


def test_opp_search_hit_resets_to_p0():
    T = _make_T()
    board = _make_board()
    rb = RatBelief(T, board)
    for _ in range(3):
        board.turn_count += 1
        rb.update(board, (Noise.SCRATCH, 4))
    rb.apply_opp_search((2, 5), hit=True)
    assert np.allclose(rb.belief, rb.p_0)


def test_timing_update_budget():
    """Average per-call update time must be <= 2 ms (target ~ 0.5 ms)."""
    T = _make_T()
    board = _make_board()
    rb = RatBelief(T, board)
    # Warm-up.
    for _ in range(10):
        rb.update(board, (Noise.SQUEAK, 3))
        board.turn_count += 1

    N = 1000
    t0 = time.perf_counter()
    for i in range(N):
        board.turn_count = (i % 40) + 1
        rb.update(board, (Noise(i % 3), i % 10))
    elapsed = time.perf_counter() - t0
    per_call_ms = 1000.0 * elapsed / N
    # Strategy §3.2 budget: <= 2 ms (target 0.5 ms).
    assert per_call_ms <= 2.0, (
        f"update avg {per_call_ms:.3f} ms/call exceeds 2 ms budget"
    )


def test_p0_compute_independent_of_board():
    """`_compute_p0` should depend only on T, not on board state."""
    T = _make_T(seed=42)
    p0a = _compute_p0(T, steps=1000)
    p0b = _compute_p0(T, steps=1000)
    assert np.array_equal(p0a, p0b)
    # Stationary check: p_0 @ T should approximately equal p_0.
    drift = np.abs(p0a @ T - p0a).max()
    assert drift < 1e-4, f"p_0 not near-stationary, drift={drift}"


def test_summary_fields():
    T = _make_T()
    board = _make_board()
    rb = RatBelief(T, board)
    s = rb.summary()
    assert s.belief.shape == (64,)
    assert s.belief.dtype == np.float64
    assert abs(s.belief.sum() - 1.0) < 1e-9
    assert 0.0 < s.max_mass <= 1.0
    assert 0 <= s.argmax < 64
    assert 0.0 <= s.entropy <= float(np.log(64)) + 1e-6


# ----------------------------------------------------------------------
# Tiny test runner so we don't hard-depend on pytest being on PATH.


def _run_all():
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    timings = {}
    import traceback
    for f in funcs:
        t0 = time.perf_counter()
        try:
            f()
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {f.__name__}: {e}")
            traceback.print_exc()
            continue
        except Exception as e:
            failed += 1
            print(f"[ERROR] {f.__name__}: {type(e).__name__}: {e}")
            traceback.print_exc()
            continue
        dt = time.perf_counter() - t0
        timings[f.__name__] = dt
        passed += 1
        print(f"[PASS] {f.__name__}  ({1000 * dt:.1f} ms)")
    print(f"\n{passed} passed, {failed} failed out of {passed + failed}")
    return failed


if __name__ == "__main__":
    sys.exit(0 if _run_all() == 0 else 1)
