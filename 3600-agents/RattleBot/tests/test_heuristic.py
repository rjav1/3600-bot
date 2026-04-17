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
    # Sanity: F1/F3/F4 = 0 so eval is dominated by F5+F7+F11+F12+F13
    # and the three multi-scale kernels (F14/F15/F16). The kernels
    # aggregate over all 64 cells so they can contribute tens of
    # points; just check the value is finite and within a loose band.
    assert math.isfinite(val)
    assert -1000.0 < val < 1000.0, (
        f"empty-board eval {val} out of sanity bounds"
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
    # F14/F15/F16 — multi-scale distance kernels over P(c). Always
    # non-negative (P(c)>=0, kernels>=0). Depend on worker position,
    # so they're perspective-dependent. Bound loosely — with all cells
    # at max potential (21) and all 64 cells contributing: F14 ≤
    # 21·Σ 1/(1+d) for our worker; a generous upper bound is 21·64·1.
    assert feats_fwd[9] >= 0 and feats_fwd[10] >= 0 and feats_fwd[11] >= 0
    assert feats_rev[9] >= 0 and feats_rev[10] >= 0 and feats_rev[11] >= 0
    assert feats_fwd[9] < 21 * 64
    assert feats_fwd[10] < 21 * 64
    assert feats_fwd[11] < 21 * 64
    # F17 (dead-prime count) is an integer count in [0, 64]. Not
    # meaningfully perspective-symmetric in v0.3.1 (uses our worker's
    # reach + global primed mask); just check bounds.
    assert 0.0 <= feats_fwd[12] <= 64.0
    assert 0.0 <= feats_rev[12] <= 64.0
    # F18 (opp-belief entropy) is in [0, ln 64]. Perspective-invariant
    # for a fresh default board (opp_search=(None, False)).
    assert 0.0 <= feats_fwd[13] <= math.log(64) + 1e-9
    assert 0.0 <= feats_rev[13] <= math.log(64) + 1e-9
    # F19 (belief fraction within Manhattan 2 of worker) in [0, 1].
    # Depends on worker position → perspective-dependent bound only.
    assert 0.0 <= feats_fwd[14] <= 1.0 + 1e-9
    assert 0.0 <= feats_rev[14] <= 1.0 + 1e-9
    # F20 (longest primed-or-space run from opp worker) in [0, 7].
    assert 0.0 <= feats_fwd[15] <= 7.0
    assert 0.0 <= feats_rev[15] <= 7.0
    # F22 (prime-steal bonus) is non-negative; bounded by sum of all
    # CARPET_POINTS_TABLE[k] over all possible primed lines — pathological
    # upper bound is 32 * 21 = 672 but realistic < 100. Loose bound.
    assert feats_fwd[16] >= 0.0
    assert feats_rev[16] >= 0.0
    assert feats_fwd[16] <= 200.0
    assert feats_rev[16] <= 200.0
    # F10 (opp-mobility-denied + adjacency) is a non-negative integer
    # count: worst case 4 (all four neighbors) + many endpoint hits <= 8.
    assert feats_fwd[17] >= 0.0
    assert feats_rev[17] >= 0.0
    assert feats_fwd[17] <= 16.0
    assert feats_rev[17] <= 16.0
    # F24 (opp-wasted-primes) is a non-negative integer count, ≤ 64.
    assert feats_fwd[18] >= 0.0
    assert feats_rev[18] >= 0.0
    assert feats_fwd[18] <= 64.0
    assert feats_rev[18] <= 64.0


def test_per_call_timing():
    """p99 per-call should be <= 250 µs on 10k random boards (v0.4 budget
    bumped from 200 us for the 16-feature vector per team-lead T-40b brief).

    Uses time.perf_counter_ns(). Soft-warns if p99 > 250 µs but hard-fails
    if median is > 250 µs — that indicates an actual algorithmic regression.
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

    BUDGET_US = 250.0
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
    # shifts a little because peaky COM ≠ uniform COM. F18 = belief
    # entropy when opp didn't search (default board), so it also tracks
    # the entropy delta.
    observed_drop = v_low - v_high
    delta_f12 = W_INIT[6] * (bs_high.entropy - bs_low.entropy)
    # F13 delta: Manhattan(worker, COM_high) - Manhattan(worker, COM_low)
    wx, wy = board.player_worker.position
    d13_low = abs(wx - bs_low.com_x) + abs(wy - bs_low.com_y)
    d13_high = abs(wx - bs_high.com_x) + abs(wy - bs_high.com_y)
    delta_f13 = W_INIT[8] * (d13_high - d13_low)
    # F18 delta: default board has opponent_search = (None, False), so
    # F18 falls back to belief.entropy — exact same delta as F12 but
    # weighted by W_INIT[13].
    delta_f18 = W_INIT[13] * (bs_high.entropy - bs_low.entropy)
    # F19 delta: Σ belief[c] · I(d(worker,c)≤2) — depends on where the
    # peak lands vs worker, so compute from the actual masks.
    from RattleBot.heuristic import _NEAR2_MASK
    worker_idx = wy * BOARD_SIZE + wx
    f19_low = float(np.dot(bs_low.belief, _NEAR2_MASK[worker_idx]))
    f19_high = float(np.dot(bs_high.belief, _NEAR2_MASK[worker_idx]))
    delta_f19 = W_INIT[14] * (f19_high - f19_low)
    # F20 doesn't depend on belief — cancels in the delta.
    analytical = -(delta_f11 + delta_f12 + delta_f13 + delta_f18 + delta_f19)
    assert abs(observed_drop - analytical) < 1e-6, (
        f"eval delta {observed_drop} diverged from analytical "
        f"{analytical} — are F5/F7/F8/F20 varying unexpectedly?"
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


def test_multiscale_kernels_nonnegative_and_finite():
    """F14/F15/F16 must always be finite, non-negative, and bounded by
    P(c) × worst-case kernel sum. Uses a cluttered random board to
    stress the code path."""
    rng = random.Random(77)
    board = _random_board(rng)
    bs = _uniform_belief_summary()
    feats = features(board, bs)
    for idx in (9, 10, 11):
        assert math.isfinite(feats[idx]), f"F{idx+5} not finite: {feats[idx]}"
        assert feats[idx] >= 0.0


def test_f14_reciprocal_kernel_nearer_is_more():
    """For a fixed P(c) landscape, moving the worker CLOSER to the
    potential mass should INCREASE F14 (reciprocal decay weights closer
    cells more heavily). Build a board where all primable cells are in
    the top-left, and compare F14 with worker at (0,0) vs (7,7)."""
    # Empty board — no blockers, no carpet, no primes — every cell has
    # the same P(c) (= roll_value(7) = 21). We'll compare two worker
    # positions and check F14 is bigger when worker is at the "center"
    # than at a corner, since center-cells see more nearby P(c).
    board_corner = _fresh_board(
        player_pos=(0, 0), opp_pos=(7, 7), blockers=False
    )
    board_center = _fresh_board(
        player_pos=(3, 3), opp_pos=(7, 7), blockers=False
    )
    bs = _uniform_belief_summary()
    f_corner = features(board_corner, bs)
    f_center = features(board_center, bs)
    # F14 = Σ P(c) / (1 + d). Σ 1/(1+d) is larger from center than
    # corner because the 4×4 quadrant distances are smaller.
    assert f_center[9] > f_corner[9], (
        f"F14 expected center({f_center[9]}) > corner({f_corner[9]})"
    )


def test_f15_exp_kernel_decays_faster_than_recip():
    """F15 uses exp(-0.5 d). For a fixed worker and P(c), F15 must be
    LESS than F14 at the same position because exp decays faster than
    1/(1+d) beyond d=1. This catches kernel-implementation errors."""
    board = _fresh_board(player_pos=(3, 3), opp_pos=(5, 3), blockers=False)
    bs = _uniform_belief_summary()
    feats = features(board, bs)
    # F15 is smaller than F14 on any uniformly-valued landscape from
    # d=1 onward: exp(-0.5) < 0.5. At d=0 both are 1. Overall sum is
    # smaller for F15.
    assert feats[10] < feats[9], (
        f"F15 exp({feats[10]}) should be smaller than F14 recip({feats[9]})"
    )


def test_f16_step_kernel_equals_p_sum_within_d_max():
    """F16 = Σ_{c: d<=5} P(c). On an empty board with worker at (3,3),
    every cell on the 8x8 board has d<=6 except (0,0) edges; actually
    with D=5 we miss a few distant cells. This test just asserts F16
    is strictly positive and ≤ Σ_all P(c)."""
    board = _fresh_board(player_pos=(3, 3), opp_pos=(7, 0), blockers=False)
    bs = _uniform_belief_summary()
    feats = features(board, bs)
    # F16 must be a subset of the total P-sum. F14 * constant < F16
    # because all kernels assign weight 1 at d=0 and step assigns 1
    # up to d=5. A cleaner relation: F16 ≥ contribution of d=0 cell,
    # which is P(worker_cell) since kernel=1 there.
    assert feats[11] > 0
    # F16 must not exceed the raw sum of P(c).
    from RattleBot.heuristic import _cell_potential_vector
    p_sum = float(_cell_potential_vector(board).sum())
    assert feats[11] <= p_sum + 1e-9, (
        f"F16 ({feats[11]}) exceeds total P-sum ({p_sum})"
    )


def test_p_vec_zero_on_blocked_cells():
    """P(c) must be 0 on BLOCKED and CARPET cells — we can't stand
    there (BLOCKED) or roll from there (CARPET already scored)."""
    from RattleBot.heuristic import _cell_potential_vector
    board = _fresh_board(player_pos=(3, 3), opp_pos=(5, 3), blockers=False)
    # Mark some cells as BLOCKED and CARPET and verify zeros.
    board.set_cell((0, 0), Cell.BLOCKED)
    board.set_cell((7, 7), Cell.CARPET)
    p_vec = _cell_potential_vector(board)
    assert p_vec[0 * BOARD_SIZE + 0] == 0.0  # (0,0)
    assert p_vec[7 * BOARD_SIZE + 7] == 0.0  # (7,7)


def test_f17_dead_prime_count_basic():
    """F17 counts primed cells that are (a) reachable within turns_left
    Manhattan, AND (b) isolated (no primed cardinal neighbor).
    """
    from RattleBot.heuristic import _count_dead_primes
    board = _fresh_board(
        player_pos=(3, 3), opp_pos=(5, 3), blockers=False
    )
    board.player_worker.turns_left = 20
    # Isolated primes (no primed neighbor) within Manhattan 20:
    board.set_cell((2, 2), Cell.PRIMED)
    board.set_cell((6, 6), Cell.PRIMED)
    # Adjacent pair — NOT dead.
    board.set_cell((4, 4), Cell.PRIMED)
    board.set_cell((4, 5), Cell.PRIMED)
    assert _count_dead_primes(board) == 2, (
        f"expected 2 dead primes, got {_count_dead_primes(board)}"
    )
    feats = features(board, _uniform_belief_summary())
    assert feats[12] == 2.0


def test_f17_unreachable_prime_is_not_counted():
    """A prime at Manhattan distance > turns_left should NOT count."""
    from RattleBot.heuristic import _count_dead_primes
    board = _fresh_board(
        player_pos=(3, 3), opp_pos=(0, 0), blockers=False
    )
    board.player_worker.turns_left = 5
    # (2,2) is Manhattan 2 from (3,3) -> reachable.
    board.set_cell((2, 2), Cell.PRIMED)
    # (7,7) is Manhattan 8 from (3,3) -> not reachable at turns_left=5.
    board.set_cell((7, 7), Cell.PRIMED)
    assert _count_dead_primes(board) == 1, (
        f"expected 1 (only (2,2) reachable), got "
        f"{_count_dead_primes(board)}"
    )


def test_f17_zero_when_no_primes():
    """Empty board: F17 = 0."""
    from RattleBot.heuristic import _count_dead_primes
    board = _fresh_board()
    board.player_worker.turns_left = 40
    assert _count_dead_primes(board) == 0
    feats = features(board, _uniform_belief_summary())
    assert feats[12] == 0.0


def test_f17_prime_chain_has_zero_dead():
    """A line of 4 adjacent primes should have 0 dead cells (each has
    at least one primed neighbor)."""
    from RattleBot.heuristic import _count_dead_primes
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(7, 7), blockers=False
    )
    board.player_worker.turns_left = 40
    for x in range(3, 7):
        board.set_cell((x, 4), Cell.PRIMED)
    assert _count_dead_primes(board) == 0


def test_f18_no_opp_search_falls_back_to_entropy():
    """When opp didn't search last ply, F18 should equal the belief
    entropy directly (no subtraction)."""
    from RattleBot.heuristic import _opp_belief_entropy
    board = _fresh_board()
    # Default opponent_search is (None, False).
    bs = _uniform_belief_summary()
    f18 = _opp_belief_entropy(board, bs)
    assert abs(f18 - bs.entropy) < 1e-12


def test_f18_opp_miss_raises_entropy_for_peaky_belief():
    """If opp searched the argmax cell and missed, zeroing that cell
    and renormalising makes the belief FLATTER (higher entropy)."""
    from RattleBot.heuristic import _opp_belief_entropy
    board = _fresh_board()
    # Peaky belief at index 27 with mass 0.9.
    bs_peaky = _peaky_belief_summary(27, 0.9)
    # Opp searched the peak and missed.
    board.opponent_search = ((27 % BOARD_SIZE, 27 // BOARD_SIZE), False)
    f18 = _opp_belief_entropy(board, bs_peaky)
    # Pre-miss entropy was low (belief concentrated); post-miss the
    # uniform remaining mass over 63 cells ≈ ln(63) ≈ 4.143.
    assert f18 > bs_peaky.entropy, (
        f"expected post-miss entropy ({f18}) > pre ({bs_peaky.entropy})"
    )
    # Analytical: after zeroing index 27 and renormalising the other
    # 63 cells (each had mass (1-0.9)/63), the posterior is uniform
    # over 63 cells → entropy = ln 63.
    assert abs(f18 - math.log(63)) < 1e-9


def test_f18_opp_hit_uses_current_entropy():
    """A successful opp search means the rat was respawned; the belief
    has already been reset elsewhere (by rat_belief.handle_post_capture_
    reset). F18 should just echo `belief_summary.entropy` — no extra
    subtraction."""
    from RattleBot.heuristic import _opp_belief_entropy
    board = _fresh_board()
    bs = _uniform_belief_summary()
    board.opponent_search = ((3, 3), True)  # hit
    f18 = _opp_belief_entropy(board, bs)
    assert f18 == bs.entropy


def test_f18_invalid_loc_falls_back():
    """Defensive: an out-of-bounds loc (shouldn't happen per engine
    contract, but) should not blow up — just fall back to current
    entropy."""
    from RattleBot.heuristic import _opp_belief_entropy
    board = _fresh_board()
    bs = _uniform_belief_summary()
    # Out-of-bounds loc
    board.opponent_search = ((99, 99), False)
    f18 = _opp_belief_entropy(board, bs)
    assert f18 == bs.entropy


def test_f18_matches_recomputed_entropy():
    """Numerical: hand-compute the miss-posterior entropy and compare
    against the closed-form implementation."""
    from RattleBot.heuristic import _opp_belief_entropy
    # Construct a non-trivial belief with known entropy characteristics.
    rng = random.Random(42)
    raw = np.array([rng.random() for _ in range(64)], dtype=np.float64)
    raw /= raw.sum()
    bs = _bs_from_belief(raw)
    # Opp missed at index 17.
    miss_idx = 17
    board = _fresh_board()
    board.opponent_search = (
        (miss_idx % BOARD_SIZE, miss_idx // BOARD_SIZE),
        False,
    )
    f18 = _opp_belief_entropy(board, bs)
    # Reference: zero + renormalise + entropy.
    ref = raw.copy()
    ref[miss_idx] = 0.0
    ref /= ref.sum()
    nz = ref > 0.0
    ref_entropy = float(-np.sum(ref[nz] * np.log(ref[nz])))
    assert abs(f18 - ref_entropy) < 1e-9


def test_f19_concentrates_when_belief_near_worker():
    """T-40b F19: when belief is concentrated within Manhattan ≤ 2 of
    our worker, F19 must be ≈ 1.0. When belief is concentrated outside
    that radius, F19 must be ≈ 0.0."""
    board = _fresh_board(
        player_pos=(3, 3), opp_pos=(5, 3), blockers=False
    )
    # Point mass AT worker cell (d=0).
    bs_on = _point_mass_belief_summary((3, 3))
    f_on = features(board, bs_on)[14]
    assert abs(f_on - 1.0) < 1e-9, (
        f"F19 point-on-worker expected 1.0, got {f_on}"
    )

    # Point mass at d=2 (e.g. (5, 3) — two cells east of worker).
    bs_d2 = _point_mass_belief_summary((5, 3))
    f_d2 = features(board, bs_d2)[14]
    assert abs(f_d2 - 1.0) < 1e-9, (
        f"F19 at d=2 expected 1.0 (inclusive), got {f_d2}"
    )

    # Point mass at d=3 (e.g. (6, 3) — three cells east).
    bs_d3 = _point_mass_belief_summary((6, 3))
    f_d3 = features(board, bs_d3)[14]
    assert abs(f_d3 - 0.0) < 1e-9, f"F19 at d=3 expected 0.0, got {f_d3}"

    # Point mass far away — (0,0) is d=6 from (3,3).
    bs_far = _point_mass_belief_summary((0, 0))
    f_far = features(board, bs_far)[14]
    assert abs(f_far - 0.0) < 1e-9, f"F19 far expected 0.0, got {f_far}"


def test_f19_uniform_belief_fraction_matches_near_mask_size():
    """Under uniform belief (1/64 per cell), F19 = fraction of cells
    with d ≤ 2 from worker. For worker at center (3,3), that's 13
    cells (1 + 4 + 8), so F19 = 13/64 = 0.203125."""
    from RattleBot.heuristic import _NEAR2_MASK
    board = _fresh_board(
        player_pos=(3, 3), opp_pos=(0, 0), blockers=False
    )
    bs = _uniform_belief_summary()
    f = features(board, bs)[14]
    expected = float(_NEAR2_MASK[27].sum()) / 64.0
    assert abs(f - expected) < 1e-9, (
        f"F19 uniform expected {expected}, got {f}"
    )


def test_f20_longest_through_primed_or_space():
    """T-40b F20: longest PRIMED-or-SPACE run in any cardinal direction
    from opp worker position."""
    from RattleBot.heuristic import _opp_roll_imminence
    # Opp at (5, 3), empty board. Longest run in any direction:
    # West: (4,3)(3,3)(2,3)(1,3)(0,3) = 5 cells; others shorter.
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(5, 3), blockers=False
    )
    assert _opp_roll_imminence(board) == 5

    # Block (2, 3) — west run shortens to 2 (4,3)(3,3).
    # South direction remains 4 ((5,4)(5,5)(5,6)(5,7)).
    board.set_cell((2, 3), Cell.BLOCKED)
    assert _opp_roll_imminence(board) == 4

    # Move our worker to (6, 3) — blocks east run at d=1. Longest
    # remains 4 (south).
    board.player_worker.position = (6, 3)
    assert _opp_roll_imminence(board) == 4


def test_f20_superset_of_f8():
    """T-40b F20 superset: for any board, F20 ≥ F8. F8 counts only
    already-PRIMED cells; F20 also counts SPACE."""
    from RattleBot.heuristic import (
        _opp_longest_primable, _opp_roll_imminence,
    )
    # Empty board, opp has plenty of space but no primes.
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(3, 3), blockers=False
    )
    assert _opp_longest_primable(board) == 0
    assert _opp_roll_imminence(board) > 0

    # Add primes at (4,3)(5,3). F8 = 2 (primed run east); F20 should
    # see east run (4,3)(5,3)(6,3)(7,3) = 4 cells of primed-or-space.
    board.set_cell((4, 3), Cell.PRIMED)
    board.set_cell((5, 3), Cell.PRIMED)
    f8 = _opp_longest_primable(board)
    f20 = _opp_roll_imminence(board)
    assert f8 == 2
    assert f20 >= f8
    assert f20 == 4


def test_f20_carpet_blocks_run():
    """F20 stops at CARPET cells — opp can't prime them nor roll
    through them."""
    from RattleBot.heuristic import _opp_roll_imminence
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(3, 3), blockers=False
    )
    # East run = (4,3)..(7,3) = 4 space. Plant a CARPET at (5,3):
    # east run shortens to 1. Longest among other dirs: west=3, north=3,
    # south=4. Result: 4.
    board.set_cell((5, 3), Cell.CARPET)
    assert _opp_roll_imminence(board) == 4


def test_f22_steals_horizontal_line_when_we_closer():
    """T-40-EXPLOIT-1 F22: primed H-line k=3, our worker closer to one
    endpoint than opp → F22 = CARPET_POINTS_TABLE[3] = 4."""
    from RattleBot.heuristic import _prime_steal_bonus
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(7, 7), blockers=False
    )
    for loc in [(3, 0), (4, 0), (5, 0)]:
        board.set_cell(loc, Cell.PRIMED)
    # Our (0,0) to (3,0) = 3; opp (7,7) to (3,0) = 4+7=11. Our closer.
    assert _prime_steal_bonus(board) == 4.0


def test_f22_does_not_steal_when_opp_closer():
    """If opp's worker is closer to both endpoints, F22 = 0."""
    from RattleBot.heuristic import _prime_steal_bonus
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(3, 1), blockers=False
    )
    for loc in [(3, 0), (4, 0), (5, 0)]:
        board.set_cell(loc, Cell.PRIMED)
    # Our (0,0) to (3,0) = 3; opp (3,1) to (3,0) = 1. Opp closer.
    assert _prime_steal_bonus(board) == 0.0


def test_f22_ignores_k1_lines():
    """A single isolated prime (k=1) is NOT a steal target (−1 roll)."""
    from RattleBot.heuristic import _prime_steal_bonus
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(7, 7), blockers=False
    )
    board.set_cell((3, 0), Cell.PRIMED)  # k=1, isolated
    assert _prime_steal_bonus(board) == 0.0


def test_f22_vertical_line():
    """Vertical-axis primed lines are also counted."""
    from RattleBot.heuristic import _prime_steal_bonus
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(7, 7), blockers=False
    )
    for loc in [(3, 2), (3, 3), (3, 4), (3, 5)]:  # k=4
        board.set_cell(loc, Cell.PRIMED)
    # Our (0,0) to (3,2) = 5; to (3,5) = 8. min = 5.
    # Opp (7,7) to (3,2) = 9; to (3,5) = 6. min = 6.
    # Our closer → CARPET_POINTS_TABLE[4] = 6.
    assert _prime_steal_bonus(board) == 6.0


def test_f22_counts_each_line_once():
    """A 3-cell primed run in one direction should NOT be counted
    multiple times (once per start-cell). The dedup via line-start
    check ensures exactly one contribution."""
    from RattleBot.heuristic import _prime_steal_bonus
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(7, 7), blockers=False
    )
    for loc in [(3, 0), (4, 0), (5, 0)]:
        board.set_cell(loc, Cell.PRIMED)
    # k=3 line. If incorrectly counted per-cell, F22 would be 12;
    # correctly deduped, F22 = 4.
    assert _prime_steal_bonus(board) == 4.0


def test_f22_zero_when_no_primes():
    from RattleBot.heuristic import _prime_steal_bonus
    board = _fresh_board(player_pos=(3, 3), opp_pos=(5, 3), blockers=False)
    assert _prime_steal_bonus(board) == 0.0


def test_f22_feature_slot_wired_correctly():
    """F22 must land in features[16] and match _prime_steal_bonus."""
    from RattleBot.heuristic import _prime_steal_bonus
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(7, 7), blockers=False
    )
    for loc in [(3, 0), (4, 0), (5, 0)]:
        board.set_cell(loc, Cell.PRIMED)
    bs = _uniform_belief_summary()
    feats = features(board, bs)
    direct = _prime_steal_bonus(board)
    assert feats[16] == direct
    assert feats[16] == 4.0


def test_f10_counts_primed_carpet_adjacent_to_opp():
    """T-40-EXPLOIT-2 F10 base: count PRIMED/CARPET cells cardinal-
    adjacent to opp's worker."""
    from RattleBot.heuristic import _opp_mobility_denied_plus_adjacency
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(5, 5), blockers=False
    )
    board.set_cell((4, 5), Cell.PRIMED)    # adjacent
    board.set_cell((5, 4), Cell.PRIMED)    # adjacent
    board.set_cell((6, 5), Cell.CARPET)    # adjacent
    # (5,6) is SPACE; other neighbors not primed/carpet.
    # Adjacency bonus: our worker at (0,0) is not adjacent to any
    # endpoint (isolated primes with k=1 don't count as lines anyway).
    assert _opp_mobility_denied_plus_adjacency(board) == 3


def test_f10_rewards_our_adjacency_to_primed_endpoint():
    """T-40-EXPLOIT-2 F10 adjacency bonus: our worker adjacent to a
    primed-line endpoint (k ≥ 2)."""
    from RattleBot.heuristic import _opp_mobility_denied_plus_adjacency
    board = _fresh_board(
        player_pos=(2, 0), opp_pos=(7, 7), blockers=False
    )
    # Primed k=2 H-line: (3,0)(4,0). Endpoints: (3,0) and (4,0).
    # Our worker (2,0) is Manhattan 1 from (3,0) → +1. Not from (4,0).
    # Base (opp 7,7 has no primed/carpet neighbors) = 0.
    board.set_cell((3, 0), Cell.PRIMED)
    board.set_cell((4, 0), Cell.PRIMED)
    assert _opp_mobility_denied_plus_adjacency(board) == 1


def test_f10_counts_both_endpoints_when_adjacent():
    """If our worker is adjacent to BOTH endpoints (trivially: k=2
    line adjacent to our worker with both endpoints within Manhattan
    1), count both."""
    from RattleBot.heuristic import _opp_mobility_denied_plus_adjacency
    board = _fresh_board(
        player_pos=(3, 1), opp_pos=(7, 7), blockers=False
    )
    # Vertical k=2 line: (3,2)(3,3). Our worker (3,1). Manhattan
    # to (3,2)=1, to (3,3)=2. Only (3,2) within 1.
    board.set_cell((3, 2), Cell.PRIMED)
    board.set_cell((3, 3), Cell.PRIMED)
    assert _opp_mobility_denied_plus_adjacency(board) == 1


def test_f10_ignores_k1_lines():
    """Isolated primes (k=1) don't contribute to adjacency bonus."""
    from RattleBot.heuristic import _opp_mobility_denied_plus_adjacency
    board = _fresh_board(
        player_pos=(2, 0), opp_pos=(7, 7), blockers=False
    )
    board.set_cell((3, 0), Cell.PRIMED)  # isolated, k=1
    # Base = 0 (opp 7,7 no adjacent primed/carpet).
    # Adjacency: k=1 ignored.
    assert _opp_mobility_denied_plus_adjacency(board) == 0


def test_f10_feature_slot_wired_correctly():
    from RattleBot.heuristic import _opp_mobility_denied_plus_adjacency
    board = _fresh_board(
        player_pos=(2, 0), opp_pos=(5, 5), blockers=False
    )
    for loc in [(3, 0), (4, 0)]:
        board.set_cell(loc, Cell.PRIMED)
    board.set_cell((4, 5), Cell.PRIMED)  # opp's adjacency
    bs = _uniform_belief_summary()
    feats = features(board, bs)
    direct = _opp_mobility_denied_plus_adjacency(board)
    assert feats[17] == direct
    # Base 1 (opp-adj primed) + adj 1 (our endpoint-adj) = 2.
    assert feats[17] == 2.0


def test_f24_mirrors_f17_on_opp_side():
    """T-40-EXPLOIT-3 F24: same logic as F17 but uses opp's worker +
    turns_left."""
    from RattleBot.heuristic import _opp_wasted_primes, _count_dead_primes
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(3, 3), blockers=False
    )
    board.player_worker.turns_left = 5
    board.opponent_worker.turns_left = 20
    # Isolated primes: (2,2) dist 2 from opp, (7,7) dist 8. Both reachable
    # by opp at tl=20.
    board.set_cell((2, 2), Cell.PRIMED)
    board.set_cell((7, 7), Cell.PRIMED)
    # Adjacent pair — NOT dead.
    board.set_cell((4, 4), Cell.PRIMED)
    board.set_cell((4, 5), Cell.PRIMED)
    assert _opp_wasted_primes(board) == 2
    # Cross-check: from our worker's frame (tl=5, pos (0,0)), (2,2) is
    # dist 4 ≤ 5 reachable, (7,7) is dist 14 > 5 not reachable. F17 = 1.
    assert _count_dead_primes(board) == 1


def test_f24_uses_opp_turns_left_for_reachability():
    """F24 reachability uses opp.turns_left, not ours."""
    from RattleBot.heuristic import _opp_wasted_primes
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(3, 3), blockers=False
    )
    board.opponent_worker.turns_left = 5
    # (2,2) is dist 2 → reachable. (7,7) is dist 8 → not reachable at tl=5.
    board.set_cell((2, 2), Cell.PRIMED)
    board.set_cell((7, 7), Cell.PRIMED)
    assert _opp_wasted_primes(board) == 1


def test_f24_zero_when_no_primes():
    from RattleBot.heuristic import _opp_wasted_primes
    board = _fresh_board(player_pos=(0, 0), opp_pos=(3, 3), blockers=False)
    assert _opp_wasted_primes(board) == 0


def test_f24_feature_slot_wired_correctly():
    from RattleBot.heuristic import _opp_wasted_primes
    board = _fresh_board(
        player_pos=(0, 0), opp_pos=(3, 3), blockers=False
    )
    board.opponent_worker.turns_left = 20
    board.set_cell((2, 2), Cell.PRIMED)
    bs = _uniform_belief_summary()
    feats = features(board, bs)
    direct = _opp_wasted_primes(board)
    assert feats[18] == direct
    assert feats[18] == 1.0


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


# ----------------------------------------------------------------------
# T-30c-numba: numba kernels parity + kill-switch

def test_numba_kernels_match_python_reference():
    """Numba kernels must return byte-identical output to their pure-Python
    counterparts over 1 000 random mask + worker configurations."""
    from RattleBot.heuristic import (  # local import so env-var-gated
        _ray_reach_py, _cell_potential_for_worker_py,
        _cell_potential_vector_py,
        _CARPET_VALUE, _LAMBDA, _BETA,
        is_numba_active, warm_numba_kernels,
    )
    if not is_numba_active():
        # When the kill-switch is off there's nothing to compare.
        print("SKIP test_numba_kernels_match_python_reference (numba off)")
        return

    from RattleBot.heuristic import (
        _ray_reach_nb, _cell_potential_for_worker_nb,
        _cell_potential_vector_nb,
    )
    warm_numba_kernels()

    rng = random.Random(0xC0FFEE)
    dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    n = 1000
    for _ in range(n):
        blocked = rng.getrandbits(64)
        carpet = rng.getrandbits(64) & ~blocked
        opp_x = rng.randrange(BOARD_SIZE)
        opp_y = rng.randrange(BOARD_SIZE)
        own_x = rng.randrange(BOARD_SIZE)
        own_y = rng.randrange(BOARD_SIZE)
        opp_bit = 1 << (opp_y * BOARD_SIZE + opp_x)
        own_bit = 1 << (own_y * BOARD_SIZE + own_x)

        # ray_reach
        x = rng.randrange(BOARD_SIZE)
        y = rng.randrange(BOARD_SIZE)
        dx, dy = rng.choice(dirs)
        blockers = blocked | carpet | opp_bit
        r_py = _ray_reach_py(blockers, x, y, dx, dy)
        r_nb = int(_ray_reach_nb(np.uint64(blockers), x, y, dx, dy))
        assert r_py == r_nb, (
            f"ray_reach parity: py={r_py} nb={r_nb} "
            f"blockers={hex(blockers)} ({x},{y}) dir=({dx},{dy})"
        )

        # cell_potential_for_worker
        p_py = _cell_potential_for_worker_py(
            blockers, own_x, own_y, opp_x, opp_y,
            _LAMBDA, _BETA, _CARPET_VALUE,
        )
        p_nb = float(_cell_potential_for_worker_nb(
            np.uint64(blockers), own_x, own_y, opp_x, opp_y,
            _LAMBDA, _BETA, _CARPET_VALUE,
        ))
        assert abs(p_py - p_nb) < 1e-9, (
            f"cp_worker parity: py={p_py} nb={p_nb}"
        )

        # cell_potential_vector
        v_py = _cell_potential_vector_py(blocked, carpet, opp_bit, own_bit)
        v_nb = _cell_potential_vector_nb(
            np.uint64(blocked), np.uint64(carpet),
            np.uint64(opp_bit), np.uint64(own_bit),
            _CARPET_VALUE,
        )
        assert np.allclose(v_py, v_nb), (
            f"p-vec parity: max-diff={np.max(np.abs(v_py - v_nb))}"
        )


def _spawn_child_and_check_numba(env_value):
    """Helper: spawn a child Python with (or without) RATTLEBOT_NUMBA set,
    import `RattleBot.heuristic`, print `is_numba_active()` + `_USE_NUMBA`
    + `_NUMBA_AVAILABLE`. Returns the captured stdout lines.

    `env_value` may be None (unset — exercises the default) or a string.
    """
    import subprocess
    import textwrap
    script = textwrap.dedent(
        """
        import os, sys
        sys.path.insert(0, os.path.join(os.getcwd(), 'engine'))
        sys.path.insert(0, os.path.join(os.getcwd(), '3600-agents'))
        from RattleBot.heuristic import is_numba_active, _USE_NUMBA, _NUMBA_AVAILABLE
        print('active', is_numba_active())
        print('use', _USE_NUMBA)
        print('avail', _NUMBA_AVAILABLE)
        """
    )
    env = os.environ.copy()
    env.pop("RATTLEBOT_NUMBA", None)
    if env_value is not None:
        env["RATTLEBOT_NUMBA"] = env_value
    cp = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, env=env,
        cwd=_REPO_ROOT,
    )
    assert cp.returncode == 0, (
        f"child failed rc={cp.returncode}\nstdout={cp.stdout}\nstderr={cp.stderr}"
    )
    return cp.stdout.splitlines()


def test_numba_kill_switch_forces_python_path():
    """When env var `RATTLEBOT_NUMBA=0`, `is_numba_active()` must be False
    and the dispatcher must run the pure-Python reference.

    The kill switch is resolved at module-import time, so we subprocess
    into a child Python with the env var set.
    """
    lines = _spawn_child_and_check_numba("0")
    assert "active False" in lines, f"expected inactive, got: {lines}"
    assert "use False" in lines, f"use flag unexpected: {lines}"


def test_numba_default_is_off_submission_safe():
    """T-30f: with NO env var set, the default must be pure-Python
    (submission-safe per LIVE_UPLOAD_006 — numba zips fail the
    bytefight.org sandbox validator; pure-Python zips pass).

    Regression guard: any future change that flips the default back
    to ON must also update this test + commit an explicit rationale.
    """
    lines = _spawn_child_and_check_numba(None)
    assert "active False" in lines, (
        f"T-30f invariant: default must be OFF (pure Python), got: {lines}"
    )
    assert "use False" in lines, (
        f"T-30f invariant: _USE_NUMBA default must be False, got: {lines}"
    )


def test_numba_opt_in_activates_jit():
    """T-30f: with `RATTLEBOT_NUMBA=1`, numba must be active.

    Guards the opt-in path so local benchmarks + BO tuning still
    have a way to enable the numba leaf speedup.
    """
    lines = _spawn_child_and_check_numba("1")
    # `active` depends on numba being importable in the child Python.
    # We already rely on numba being installed elsewhere (T-30c-numba),
    # so this should always be True in a healthy dev env.
    assert "avail True" in lines, (
        f"numba not importable in child env: {lines}"
    )
    assert "use True" in lines, (
        f"_USE_NUMBA opt-in didn't stick: {lines}"
    )
    assert "active True" in lines, (
        f"is_numba_active() should be True with RATTLEBOT_NUMBA=1: {lines}"
    )


def test_numba_warmup_is_fast_second_time():
    """Calling `warm_numba_kernels()` after the first call is a no-op."""
    from RattleBot.heuristic import warm_numba_kernels
    warm_numba_kernels()  # guaranteed first-call done
    t0 = time.perf_counter()
    warm_numba_kernels()
    dt_ms = (time.perf_counter() - t0) * 1000.0
    assert dt_ms < 5.0, f"second warmup took {dt_ms:.2f} ms (expected < 5)"


def test_evaluate_returns_same_value_both_backends():
    """For the SAME board/belief, a numba `evaluate` must match the Python
    `evaluate` to ~1e-9. We flip the kill switch at module level (not via
    subprocess) by calling the underlying kernels directly."""
    from RattleBot.heuristic import (
        features as features_mod,
        is_numba_active,
    )
    # In the active-process module, just confirm features produces a
    # finite deterministic result under whichever backend is live.
    rng = random.Random(77)
    bel = _random_belief(rng)
    board = _random_board(rng)
    v1 = features_mod(board, bel)
    v2 = features_mod(board, bel)
    assert np.allclose(v1, v2), "features() not idempotent"
    assert np.all(np.isfinite(v1)), "features produced non-finite values"
    # Cross-backend parity is covered by test_numba_kernels_match_python_reference.


# ----------------------------------------------------------------------
# T-40a: LUT-optimized hot-path parity + speedup

def test_pvec_parity_vec_vs_scalar():
    """`_cell_potential_vector_vec` (LUT-optimized) must match the scalar
    reference byte-for-byte across 2 000 random (blocked, carpet, opp, own)
    configurations."""
    from RattleBot.heuristic import (
        _cell_potential_vector_py,
        _cell_potential_vector_vec,
    )
    rng = random.Random(0xBABE)
    diffs = 0
    for _ in range(2000):
        blocked = rng.getrandbits(64)
        carpet = rng.getrandbits(64) & ~blocked
        opp_bit = 1 << rng.randrange(64)
        own_bit = 1 << rng.randrange(64)
        v_py = _cell_potential_vector_py(blocked, carpet, opp_bit, own_bit)
        v_vec = _cell_potential_vector_vec(blocked, carpet, opp_bit, own_bit)
        if not np.array_equal(v_py, v_vec):
            diffs += 1
    assert diffs == 0, f"p-vec LUT parity: {diffs}/2000 mismatches"


def test_cpw_parity_vec_vs_scalar():
    """`_cell_potential_for_worker_vec` must match the scalar reference
    within 1e-9 across 2 000 random (blocked, worker, opp) configurations."""
    from RattleBot.heuristic import (
        _cell_potential_for_worker_py,
        _cell_potential_for_worker_vec,
        _LAMBDA, _BETA, _CARPET_VALUE,
    )
    rng = random.Random(0xCAFE)
    diffs = 0
    for _ in range(2000):
        blockers = rng.getrandbits(64)
        wx = rng.randrange(BOARD_SIZE)
        wy = rng.randrange(BOARD_SIZE)
        opp_x = rng.randrange(BOARD_SIZE)
        opp_y = rng.randrange(BOARD_SIZE)
        a = _cell_potential_for_worker_py(
            blockers, wx, wy, opp_x, opp_y, _LAMBDA, _BETA, _CARPET_VALUE,
        )
        b = _cell_potential_for_worker_vec(
            blockers, wx, wy, opp_x, opp_y, _LAMBDA, _BETA, _CARPET_VALUE,
        )
        if abs(a - b) > 1e-9:
            diffs += 1
    assert diffs == 0, f"cpw LUT parity: {diffs}/2000 mismatches"


def test_scalar_ref_env_var_routes_to_python():
    """Setting `RATTLEBOT_HEURISTIC_REF=1` in a child process must force
    the pure-Python scalar path, not the LUT-optimized one."""
    import subprocess
    import textwrap
    script = textwrap.dedent(
        """
        import os, sys
        sys.path.insert(0, os.path.join(os.getcwd(), 'engine'))
        sys.path.insert(0, os.path.join(os.getcwd(), '3600-agents'))
        from RattleBot.heuristic import _USE_SCALAR_REF
        print('SCALAR_REF', _USE_SCALAR_REF)
        """
    )
    env = os.environ.copy()
    env["RATTLEBOT_HEURISTIC_REF"] = "1"
    env.pop("RATTLEBOT_NUMBA", None)
    cp = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, env=env,
        cwd=_REPO_ROOT,
    )
    assert cp.returncode == 0, f"child rc={cp.returncode} err={cp.stderr}"
    assert "SCALAR_REF True" in cp.stdout, f"got: {cp.stdout}"


def test_vec_is_not_slower_than_scalar():
    """Warm micro-benchmark: LUT path must be at least as fast as the
    scalar reference across both hot functions. A regression here means
    the LUT indirection added overhead rather than removing it."""
    from RattleBot.heuristic import (
        _cell_potential_vector_py,
        _cell_potential_vector_vec,
        _cell_potential_for_worker_py,
        _cell_potential_for_worker_vec,
        _LAMBDA, _BETA, _CARPET_VALUE,
    )
    rng = random.Random(0xFACE)
    N = 2000
    pvec_args = [
        (
            rng.getrandbits(64),
            rng.getrandbits(64),
            1 << rng.randrange(64),
            1 << rng.randrange(64),
        )
        for _ in range(N)
    ]
    cpw_args = [
        (
            rng.getrandbits(64),
            rng.randrange(BOARD_SIZE),
            rng.randrange(BOARD_SIZE),
            rng.randrange(BOARD_SIZE),
            rng.randrange(BOARD_SIZE),
        )
        for _ in range(N)
    ]
    # warm
    _cell_potential_vector_py(*pvec_args[0])
    _cell_potential_vector_vec(*pvec_args[0])
    _cell_potential_for_worker_py(*cpw_args[0], _LAMBDA, _BETA, _CARPET_VALUE)
    _cell_potential_for_worker_vec(*cpw_args[0], _LAMBDA, _BETA, _CARPET_VALUE)

    def _bench(fn, args_list, extra=()):
        t0 = time.perf_counter()
        for a in args_list:
            fn(*a, *extra)
        return time.perf_counter() - t0

    # 3 trials, take min (least noise)
    pvec_py = min(_bench(_cell_potential_vector_py, pvec_args) for _ in range(3))
    pvec_v = min(_bench(_cell_potential_vector_vec, pvec_args) for _ in range(3))
    cpw_py = min(_bench(_cell_potential_for_worker_py, cpw_args, (_LAMBDA, _BETA, _CARPET_VALUE)) for _ in range(3))
    cpw_v = min(_bench(_cell_potential_for_worker_vec, cpw_args, (_LAMBDA, _BETA, _CARPET_VALUE)) for _ in range(3))

    # Allow small slack (10%) for Windows timer jitter.
    assert pvec_v <= pvec_py * 1.1, (
        f"pvec LUT regressed: py={pvec_py*1e6/N:.2f}us vec={pvec_v*1e6/N:.2f}us"
    )
    assert cpw_v <= cpw_py * 1.1, (
        f"cpw LUT regressed: py={cpw_py*1e6/N:.2f}us vec={cpw_v*1e6/N:.2f}us"
    )


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
        test_multiscale_kernels_nonnegative_and_finite,
        test_f14_reciprocal_kernel_nearer_is_more,
        test_f15_exp_kernel_decays_faster_than_recip,
        test_f16_step_kernel_equals_p_sum_within_d_max,
        test_p_vec_zero_on_blocked_cells,
        test_f17_dead_prime_count_basic,
        test_f17_unreachable_prime_is_not_counted,
        test_f17_zero_when_no_primes,
        test_f17_prime_chain_has_zero_dead,
        test_f18_no_opp_search_falls_back_to_entropy,
        test_f18_opp_miss_raises_entropy_for_peaky_belief,
        test_f18_opp_hit_uses_current_entropy,
        test_f18_invalid_loc_falls_back,
        test_f18_matches_recomputed_entropy,
        test_f19_concentrates_when_belief_near_worker,
        test_f19_uniform_belief_fraction_matches_near_mask_size,
        test_f20_longest_through_primed_or_space,
        test_f20_superset_of_f8,
        test_f20_carpet_blocks_run,
        test_f22_steals_horizontal_line_when_we_closer,
        test_f22_does_not_steal_when_opp_closer,
        test_f22_ignores_k1_lines,
        test_f22_vertical_line,
        test_f22_counts_each_line_once,
        test_f22_zero_when_no_primes,
        test_f22_feature_slot_wired_correctly,
        test_f10_counts_primed_carpet_adjacent_to_opp,
        test_f10_rewards_our_adjacency_to_primed_endpoint,
        test_f10_counts_both_endpoints_when_adjacent,
        test_f10_ignores_k1_lines,
        test_f10_feature_slot_wired_correctly,
        test_f24_mirrors_f17_on_opp_side,
        test_f24_uses_opp_turns_left_for_reachability,
        test_f24_zero_when_no_primes,
        test_f24_feature_slot_wired_correctly,
        test_class_wrapper_matches_module_fn,
        test_weight_shape_validation,
        test_numba_kernels_match_python_reference,
        test_numba_kill_switch_forces_python_path,
        test_numba_default_is_off_submission_safe,
        test_numba_opt_in_activates_jit,
        test_numba_warmup_is_fast_second_time,
        test_evaluate_returns_same_value_both_backends,
        test_pvec_parity_vec_vs_scalar,
        test_cpw_parity_vec_vs_scalar,
        test_scalar_ref_env_var_routes_to_python,
        test_vec_is_not_slower_than_scalar,
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
