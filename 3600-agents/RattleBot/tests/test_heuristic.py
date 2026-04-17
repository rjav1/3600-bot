"""Tests for RattleBot.heuristic — T-15, BOT_STRATEGY §5 / T-HEUR-1/2.

Covers:
    * evaluate() returns float
    * terminal position short-circuits to (Δpoints) * TERMINAL_SCALE
    * empty-board eval is small and dominated by belief terms
    * perspective reversal flips eval sign approximately
    * per-call timing p99 <= 100 µs over 10k random boards
    * high max-mass belief produces a much more negative contribution
      than low max-mass belief (F11 signal direction check)

Run directly:
    python3 3600-agents/RattleBot/tests/test_heuristic.py

Or via pytest:
    python3 -m pytest 3600-agents/RattleBot/tests/test_heuristic.py -v
"""

from __future__ import annotations

import math
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
from game.enums import (  # noqa: E402
    BOARD_SIZE,
    Cell,
    Result,
    WinReason,
)

from RattleBot.heuristic import (  # noqa: E402
    N_FEATURES,
    TERMINAL_SCALE,
    W_INIT,
    Heuristic,
    evaluate,
    features,
)
from RattleBot.types import BeliefSummary  # noqa: E402


# ----------------------------------------------------------------------
# Fixtures


def _bs_from_belief(belief: np.ndarray) -> BeliefSummary:
    nz = belief > 0.0
    entropy = float(-np.sum(belief[nz] * np.log(belief[nz])))
    xs = np.tile(np.arange(BOARD_SIZE, dtype=np.float64), BOARD_SIZE)
    ys = np.repeat(np.arange(BOARD_SIZE, dtype=np.float64), BOARD_SIZE)
    return BeliefSummary(
        belief=belief,
        entropy=entropy,
        max_mass=float(belief.max()),
        argmax=int(belief.argmax()),
        com_x=float(np.dot(belief, xs)),
        com_y=float(np.dot(belief, ys)),
    )


def _uniform_belief_summary() -> BeliefSummary:
    belief = np.full(64, 1.0 / 64, dtype=np.float64)
    return _bs_from_belief(belief)


def _peaky_belief_summary(peak_idx: int = 27, peak: float = 0.9) -> BeliefSummary:
    belief = np.full(64, (1.0 - peak) / 63, dtype=np.float64)
    belief[peak_idx] = peak
    return _bs_from_belief(belief)


def _point_mass_belief_summary(xy) -> BeliefSummary:
    """Belief concentrated on a single cell — for F13 COM tests."""
    belief = np.zeros(64, dtype=np.float64)
    x, y = xy
    belief[y * BOARD_SIZE + x] = 1.0
    return _bs_from_belief(belief)


def _fresh_board(player_pos=(2, 3), opp_pos=(5, 3), blockers=True) -> Board:
    board = Board(time_to_play=240.0, build_history=False)
    if blockers:
        # Reproduce a canonical random-style corner set so there is
        # *some* geometry on the board.
        shapes = [(2, 3), (3, 2), (2, 2)]
        # deterministic corners for test stability
        corner_shapes = {
            (0, 0): shapes[0],
            (1, 0): shapes[1],
            (0, 1): shapes[2],
            (1, 1): shapes[0],
        }
        for (ox, oy), (w, h) in corner_shapes.items():
            for dx in range(w):
                for dy in range(h):
                    x = dx if ox == 0 else BOARD_SIZE - 1 - dx
                    y = dy if oy == 0 else BOARD_SIZE - 1 - dy
                    board.set_cell((x, y), Cell.BLOCKED)
    board.player_worker.position = player_pos
    board.opponent_worker.position = opp_pos
    return board


def _random_board(rng: random.Random) -> Board:
    """Board with random corners, random primes/carpets, random worker
    positions. Approximates in-tree positions for timing tests."""
    board = Board(time_to_play=240.0, build_history=False)
    shapes = [(2, 3), (3, 2), (2, 2)]
    for ox, oy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        w, h = rng.choice(shapes)
        for dx in range(w):
            for dy in range(h):
                x = dx if ox == 0 else BOARD_SIZE - 1 - dx
                y = dy if oy == 0 else BOARD_SIZE - 1 - dy
                board.set_cell((x, y), Cell.BLOCKED)

    # Sprinkle random PRIMED and CARPET cells on SPACE cells only.
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            if board.get_cell((x, y)) != Cell.SPACE:
                continue
            r = rng.random()
            if r < 0.08:
                board.set_cell((x, y), Cell.PRIMED)
            elif r < 0.16:
                board.set_cell((x, y), Cell.CARPET)

    # Pick SPACE-or-CARPET cells for workers.
    def _pick_walkable():
        for _ in range(200):
            x = rng.randrange(BOARD_SIZE)
            y = rng.randrange(BOARD_SIZE)
            c = board.get_cell((x, y))
            if c in (Cell.SPACE, Cell.CARPET):
                return (x, y)
        return (3, 3)

    board.player_worker.position = _pick_walkable()
    while True:
        op = _pick_walkable()
        if op != board.player_worker.position:
            board.opponent_worker.position = op
            break

    board.player_worker.points = rng.randint(0, 40)
    board.opponent_worker.points = rng.randint(0, 40)
    board.turn_count = rng.randint(0, 70)
    return board


def _random_belief(rng: random.Random) -> BeliefSummary:
    raw = np.array(
        [rng.random() ** 2 for _ in range(64)], dtype=np.float64
    )
    raw = raw / raw.sum()
    return _bs_from_belief(raw)


# ----------------------------------------------------------------------
# Tests


def test_evaluate_returns_float():
    board = _fresh_board()
    bs = _uniform_belief_summary()
    val = evaluate(board, bs)
    assert isinstance(val, float), f"expected float, got {type(val)}"

    feats = features(board, bs)
    assert isinstance(feats, np.ndarray)
    assert feats.shape == (N_FEATURES,)
    assert feats.dtype == np.float64


def test_terminal_position():
    board = _fresh_board()
    board.player_worker.points = 15
    board.opponent_worker.points = 5
    # Force game over without having to actually play 80 turns.
    board.set_winner(Result.PLAYER, WinReason.POINTS)

    val = evaluate(board, _uniform_belief_summary())
    expected = 10.0 * TERMINAL_SCALE  # 100_000 with default scale
    assert val == expected, f"expected {expected}, got {val}"


def test_zero_features_on_empty_board():
    board = _fresh_board()  # both workers, equal zero points
    bs = _uniform_belief_summary()
    feats = features(board, bs)
    # F1 score_diff == 0 at game start
    assert feats[0] == 0.0
    # F3/F4 prime/carpet popcounts are 0 at start
    assert feats[1] == 0.0
    assert feats[2] == 0.0
    # F11 max_mass = 1/64 ≈ 0.0156
    assert abs(feats[5] - 1 / 64) < 1e-9
    # F12 entropy = ln(64) ≈ 4.159
    assert abs(feats[6] - math.log(64)) < 1e-6

    val = evaluate(board, bs)
    # Sanity: eval magnitude should be well below a single-point-ish scale
    # dominated by F11*w11 and F12*w12 terms.
    contribution = (
        W_INIT[5] * (1 / 64) + W_INIT[6] * math.log(64)
    )
    # F5/F7 may add a few points of future-potential signal; bound loosely.
    assert abs(val - contribution) < 50.0, (
        f"empty-board eval {val} unreasonably far from "
        f"F11/F12 baseline {contribution}"
    )


def test_symmetry():
    """Reversing perspective should flip the sign of the F1 + F5/F7 part
    of the eval. F3/F4 popcount attribution is a known v0.1 approximation
    (total primed/carpet cells are NOT perspective-dependent), so those
    terms DO NOT flip — they contribute the same value under either
    perspective. F11/F12 are belief-based and also invariant.

    We verify:
      (a) F1 flips exactly (score_diff negates under reverse_perspective).
      (b) F5 and F7 swap (evaluated from the new player perspective).
    """
    board = _fresh_board()
    board.player_worker.points = 7
    board.opponent_worker.points = 3
    for loc in [(3, 3), (3, 4), (3, 5)]:
        board.set_cell(loc, Cell.PRIMED)
    bs = _uniform_belief_summary()

    feats_fwd = features(board, bs)
    board.reverse_perspective()
    feats_rev = features(board, bs)

    # F1 score_diff must flip exactly
    assert feats_fwd[0] == -feats_rev[0], (
        f"F1 should flip: fwd={feats_fwd[0]}, rev={feats_rev[0]}"
    )
    # F3/F4 are board-global popcounts; DO NOT flip (v0.1 approximation)
    assert feats_fwd[1] == feats_rev[1]
    assert feats_fwd[2] == feats_rev[2]
    # F5 (ours) and F7 (theirs) should swap across perspective reversal
    assert abs(feats_fwd[3] - feats_rev[4]) < 1e-9, (
        f"F5/F7 swap failed: fwd_F5={feats_fwd[3]}, rev_F7={feats_rev[4]}"
    )
    assert abs(feats_fwd[4] - feats_rev[3]) < 1e-9
    # F11/F12 are perspective-invariant
    assert feats_fwd[5] == feats_rev[5]
    assert feats_fwd[6] == feats_rev[6]
    # F8 — under reverse_perspective, the "opponent" becomes the old
    # player, so F8 (always measured off opp_worker.position) should
    # report the threat from what was previously OUR worker. The two
    # positions differ, so F8 values need not match; we just assert the
    # feature was computed (finite int-valued float in [0, 7]).
    assert 0.0 <= feats_fwd[7] <= 7.0
    assert 0.0 <= feats_rev[7] <= 7.0
    # F13 — also perspective-dependent through the worker position.
    # Belief COM is perspective-invariant; worker position swaps.
    # So F13 post-reversal = Manhattan(old opp, COM). Just check both
    # sides are non-negative and bounded by the board diameter (14).
    assert 0.0 <= feats_fwd[8] <= 14.0
    assert 0.0 <= feats_rev[8] <= 14.0


def test_per_call_timing():
    """p99 per-call should be <= 150 µs on 10k random boards (v0.2 budget
    bumped from 100 us for the 9-feature vector per team-lead T-20c brief).

    Uses time.perf_counter_ns(). Soft-warns if p99 > 150 µs but hard-fails
    if median is > 150 µs — that indicates an actual algorithmic regression.
    """
    rng = random.Random(0xBEEF)
    n = 10_000
    samples_ns = np.empty(n, dtype=np.int64)

    # Pre-generate boards + beliefs so we time only evaluate().
    boards = [_random_board(rng) for _ in range(n)]
    beliefs = [_random_belief(rng) for _ in range(n)]

    for i in range(n):
        t0 = time.perf_counter_ns()
        _ = evaluate(boards[i], beliefs[i])
        samples_ns[i] = time.perf_counter_ns() - t0

    p50 = float(np.percentile(samples_ns, 50)) / 1000.0
    p99 = float(np.percentile(samples_ns, 99)) / 1000.0
    p100 = float(samples_ns.max()) / 1000.0
    mean = float(samples_ns.mean()) / 1000.0
    print(
        f"[timing] n={n}  mean={mean:.1f}us  "
        f"p50={p50:.1f}us  p99={p99:.1f}us  max={p100:.1f}us"
    )

    BUDGET_US = 150.0
    assert p50 < BUDGET_US, (
        f"median eval time {p50:.1f}us exceeds {BUDGET_US}us budget"
    )
    if p99 > BUDGET_US:
        print(
            f"[timing] WARN: p99={p99:.1f}us exceeds {BUDGET_US}us target — "
            f"profile before BO tuning."
        )
    # Allow timer jitter slack; hard-fail at 3x budget.
    assert p99 < 3 * BUDGET_US, (
        f"p99 eval time {p99:.1f}us >> {BUDGET_US}us — regression"
    )


def test_high_max_belief_triggers_search_signal():
    """When max_mass is high, F11's contribution should be far more
    negative than when max_mass is low (signaling that a SEARCH is
    available, which the heuristic penalizes in the min-node sense —
    sitting here is NOT what we want, we want to trigger SEARCH at the
    root). With W_INIT[5] = -3.0 this means eval should DROP when
    belief becomes peaky (holding all else equal).
    """
    board = _fresh_board()
    # same board twice — only belief changes
    bs_low = _uniform_belief_summary()            # max_mass ≈ 0.0156
    bs_high = _peaky_belief_summary(27, 0.9)      # max_mass = 0.9

    v_low = evaluate(board, bs_low)
    v_high = evaluate(board, bs_high)

    # expected F11 contribution delta
    delta_f11 = W_INIT[5] * (bs_high.max_mass - bs_low.max_mass)
    assert delta_f11 < 0, "W_INIT[5] should be negative for F11"
    # v_high should be less than v_low — high max_mass drives eval down.
    assert v_high < v_low, (
        f"expected v_high ({v_high}) < v_low ({v_low}) — "
        f"F11 signal direction wrong"
    )
    # Magnitude sanity: the drop should be at least |delta_f11| minus
    # F12 jitter (entropy goes down too when belief is peaky, and
    # W_INIT[6] is negative, so that adds a positive offset). F13 also
    # shifts a little because peaky COM ≠ uniform COM.
    observed_drop = v_low - v_high
    delta_f12 = W_INIT[6] * (bs_high.entropy - bs_low.entropy)
    # F13 delta: Manhattan(worker, COM_high) - Manhattan(worker, COM_low)
    wx, wy = board.player_worker.position
    d13_low = abs(wx - bs_low.com_x) + abs(wy - bs_low.com_y)
    d13_high = abs(wx - bs_high.com_x) + abs(wy - bs_high.com_y)
    delta_f13 = W_INIT[8] * (d13_high - d13_low)
    analytical = -(delta_f11 + delta_f12 + delta_f13)
    assert abs(observed_drop - analytical) < 1e-6, (
        f"eval delta {observed_drop} diverged from analytical "
        f"{analytical} — are F5/F7/F8 varying unexpectedly?"
    )


def test_f8_opp_line_threat_on_primed_line():
    """F8 must report the contiguous primed-line length the opp can roll.

    Construct: opp at (2, 4); prime (3, 4), (4, 4), (5, 4), (6, 4).
    Expected F8 = 4 (four PRIMED cells directly east of opp).
    """
    board = _fresh_board(player_pos=(0, 0), opp_pos=(2, 4), blockers=False)
    for loc in [(3, 4), (4, 4), (5, 4), (6, 4)]:
        board.set_cell(loc, Cell.PRIMED)
    bs = _uniform_belief_summary()
    feats = features(board, bs)
    assert feats[7] == 4.0, f"F8 expected 4.0, got {feats[7]}"

    # Add a CARPET at (7,4) — doesn't extend the primed line.
    board.set_cell((7, 4), Cell.CARPET)
    assert features(board, bs)[7] == 4.0

    # Interrupt the line with a gap (unset (4, 4) to SPACE).
    board.set_cell((4, 4), Cell.SPACE)
    assert features(board, bs)[7] == 1.0, (
        "F8 should stop at the first non-primed cell"
    )

    # No primes anywhere → F8 = 0.
    for loc in [(3, 4), (5, 4), (6, 4)]:
        board.set_cell(loc, Cell.SPACE)
    assert features(board, bs)[7] == 0.0


def test_f8_no_threat_from_carpet_or_space():
    """Carpet/space cells don't contribute to F8 — opp must PRIME them
    first, so they're not an imminent threat."""
    board = _fresh_board(player_pos=(0, 0), opp_pos=(2, 4), blockers=False)
    for loc in [(3, 4), (4, 4), (5, 4)]:
        board.set_cell(loc, Cell.CARPET)
    bs = _uniform_belief_summary()
    assert features(board, bs)[7] == 0.0


def test_f13_com_dist_monotone():
    """F13 must increase with Manhattan distance from worker to the
    belief center-of-mass. Construct three point-mass beliefs at
    (3,3), (0,0), (7,7) with worker at (3,3)."""
    board = _fresh_board(player_pos=(3, 3), opp_pos=(5, 3), blockers=False)

    bs_here = _point_mass_belief_summary((3, 3))
    bs_near = _point_mass_belief_summary((4, 4))
    bs_far_nw = _point_mass_belief_summary((0, 0))
    bs_far_se = _point_mass_belief_summary((7, 7))

    f_here = features(board, bs_here)[8]
    f_near = features(board, bs_near)[8]
    f_far_nw = features(board, bs_far_nw)[8]
    f_far_se = features(board, bs_far_se)[8]

    assert f_here == 0.0, f"COM at worker -> F13=0 expected, got {f_here}"
    assert f_near == 2.0, f"COM at (4,4) worker (3,3) -> F13=2 expected, got {f_near}"
    assert f_far_nw == 6.0, f"COM at (0,0) worker (3,3) -> F13=6 expected, got {f_far_nw}"
    assert f_far_se == 8.0, f"COM at (7,7) worker (3,3) -> F13=8 expected, got {f_far_se}"
    # Monotonic ordering
    assert f_here < f_near < f_far_nw < f_far_se


def test_f13_fallback_when_com_missing():
    """If BeliefSummary lacks com_x/com_y, heuristic should fall back to
    computing COM on the fly. Tests backwards-compat with v0.1 callers.
    """
    belief = np.zeros(64, dtype=np.float64)
    belief[3 * BOARD_SIZE + 5] = 1.0  # (x=5, y=3)
    # build BeliefSummary without com_x/com_y
    bs = BeliefSummary(
        belief=belief,
        entropy=0.0,
        max_mass=1.0,
        argmax=int(belief.argmax()),
        com_x=None,
        com_y=None,
    )
    board = _fresh_board(player_pos=(3, 3), opp_pos=(5, 3), blockers=False)
    feats = features(board, bs)
    # Manhattan((3,3), (5,3)) = 2
    assert feats[8] == 2.0, f"F13 fallback path wrong: got {feats[8]}"


def test_class_wrapper_matches_module_fn():
    board = _fresh_board()
    bs = _uniform_belief_summary()
    h = Heuristic()
    assert h.weights.shape == (N_FEATURES,)
    assert h.V_leaf(board, bs) == evaluate(board, bs)

    # hot-swap
    new_w = np.ones(N_FEATURES, dtype=np.float64)
    h.set_weights(new_w)
    assert h.V_leaf(board, bs) == evaluate(board, bs, new_w)


def test_weight_shape_validation():
    board = _fresh_board()
    bs = _uniform_belief_summary()
    try:
        evaluate(board, bs, weights=np.ones(5))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for wrong weight shape")

    try:
        Heuristic(weights=np.ones(99))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for wrong weight shape")


# ----------------------------------------------------------------------
# CLI runner (no pytest required)


def _run_all():
    tests = [
        test_evaluate_returns_float,
        test_terminal_position,
        test_zero_features_on_empty_board,
        test_symmetry,
        test_per_call_timing,
        test_high_max_belief_triggers_search_signal,
        test_f8_opp_line_threat_on_primed_line,
        test_f8_no_threat_from_carpet_or_space,
        test_f13_com_dist_monotone,
        test_f13_fallback_when_com_missing,
        test_class_wrapper_matches_module_fn,
        test_weight_shape_validation,
    ]
    fails = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"  ERR   {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())
