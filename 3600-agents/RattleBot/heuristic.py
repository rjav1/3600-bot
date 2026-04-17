"""F2 linear leaf evaluator — v0.2 (9 features).

9-feature linear heuristic per BOT_STRATEGY_V02_ADDENDUM.md §2.4 / T-20c.
v0.1 shipped 7 features; v0.2 adds F8 (opponent line threat) and F13
(belief center-of-mass distance from worker) per AUDIT §3.8 + the
pre-BO-tuning prep for T-20d.

Features (all float64, sign-carried by W_INIT):

  F1  score_diff                = player.points - opponent.points
  F3  ours_prime_count          = popcount(_primed_mask)
                                  (attribution approximation — engine does
                                  not track who laid which prime; this is
                                  whole-board popcount, a perspective-
                                  invariant proxy that still self-plays
                                  cleanly per AUDIT §3.8)
  F4  ours_carpet_count         = popcount(_carpet_mask)
                                  (same attribution caveat as F3)
  F5  longest_primable_line_ours  = Carrie-style cell potential at our
                                    worker per RESEARCH_HEURISTIC §B.2
  F7  longest_primable_line_theirs= mirror of F5 from opponent perspective
  F11 belief_max                = BeliefSummary.max_mass
  F12 belief_entropy            = BeliefSummary.entropy
  F8  opp_longest_primable      = max_d reach(opp_pos, d) through primed
                                  cells — sharp opp-roll-next-turn threat
                                  signal (RESEARCH_HEURISTIC §C.2 F10)
  F13 belief_com_distance       = Manhattan(our_worker, belief_COM) —
                                  geometric signal for "am I near where
                                  the rat probably is"; sharpens sensor
                                  and cheapens a future search

Public API (module-level):

    evaluate(board, belief_summary, weights=None) -> float
    features(board, belief_summary) -> np.ndarray   # shape (9,) float64

A thin Heuristic class is kept for downstream consumers (search engine).

Hyperparams (D-011 item 5): gamma_info=0.5, gamma_reset=0.3 (used by F15
when it lands in v0.3+; not present in the v0.2 feature vector).

Owner: dev-heuristic.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from game import board as board_mod
from game.enums import BOARD_SIZE, CARPET_POINTS_TABLE

from .types import BeliefSummary

__all__ = [
    "evaluate",
    "features",
    "W_INIT",
    "N_FEATURES",
    "TERMINAL_SCALE",
    "Heuristic",
]


N_FEATURES: int = 9

# Terminal eval = (player_points - opp_points) * TERMINAL_SCALE.
# Chosen >> any realistic non-terminal eval so minimax always prefers
# a won terminal over the best heuristic continuation.
TERMINAL_SCALE: float = 1e4

# Carrie-style P(c) hyperparams (RESEARCH_HEURISTIC §B.2)
_LAMBDA: float = 0.3   # second-best-direction flexibility bonus
_ALPHA: float = 0.3    # distance decay
_BETA: float = 0.5     # opponent-first penalty

# Per BOT_STRATEGY.md §2.d / D-011 — kept here so tuning code has a
# single source of truth; v0.1 leaf does not consume these directly.
GAMMA_INFO: float = 0.5
GAMMA_RESET: float = 0.3


# ---------------------------------------------------------------------------
# Starter weights (BO tuning in v0.2 will override — see D-009)
# ---------------------------------------------------------------------------
#
#  idx  feat   w       rationale
#   0   F1     +1.0    score diff: ground-truth objective, unit weight
#   1   F3     +0.3    priming is +1 banked; extra bonus for setup value
#   2   F4     +0.2    already-banked points from CARPET rolls
#   3   F5     +1.5    Carrie's key lever — long-line future potential
#   4   F7     -1.2    mirror of F5 from opp perspective, subtracted
#   5   F11    -3.0    high max_mass => high-EV SEARCH available, NOT
#                      that sitting is good — pushes tree toward root-
#                      only SEARCH gate (see agent.py)
#   6   F12    -0.5    low entropy = belief is concentrated = good for us
#   7   F8     -0.6    opp can roll k>=5 next turn is the single biggest
#                      point swing (carpet k=5 = 10 pts). Sharper than F7
#                      but rarer, so ~0.5x F7 magnitude. Sign NEGATIVE
#                      (opponent threat should never help us).
#   8   F13    -0.05   Manhattan(our worker, belief COM). Negative — we
#                      want to be *near* the likely rat cell so future
#                      sensor draws are sharp and a potential SEARCH is
#                      cheap. Small magnitude because Manhattan in [0,14]
#                      would otherwise swamp F1. BO will retune in T-20d.
#
W_INIT: np.ndarray = np.array(
    [1.0, 0.3, 0.2, 1.5, -1.2, -3.0, -0.5, -0.6, -0.05],
    dtype=np.float64,
)
assert W_INIT.shape == (N_FEATURES,)


# ---------------------------------------------------------------------------
# Precomputed bitmask helpers (module-global, pure data; no board state)
# ---------------------------------------------------------------------------

_BOARD_CELLS: int = BOARD_SIZE * BOARD_SIZE  # 64
_FULL_MASK: int = (1 << _BOARD_CELLS) - 1

# Flat (64,) arrays of cell x- and y-coordinates; used by F13's fallback
# path when BeliefSummary.com_x / com_y are not precomputed.
# `com = float(np.dot(belief, _COM_X_COORDS))` is one BLAS call.
_COM_X_COORDS = np.tile(np.arange(BOARD_SIZE, dtype=np.float64), BOARD_SIZE)
_COM_Y_COORDS = np.repeat(np.arange(BOARD_SIZE, dtype=np.float64), BOARD_SIZE)


def _popcount(m: int) -> int:
    # Python ints have .bit_count() on 3.10+; fallback for safety.
    try:
        return m.bit_count()
    except AttributeError:  # pragma: no cover
        return bin(m).count("1")


# Carpet value table as a flat lookup: k -> value, with k=0 => 0.
# Used to map "achievable roll length" to expected points.
_CARPET_VALUE = np.zeros(8, dtype=np.float64)
for _k, _v in CARPET_POINTS_TABLE.items():
    _CARPET_VALUE[_k] = _v
# Negative k=1 is fine — the heuristic treats k=1 honestly.


# ---------------------------------------------------------------------------
# Feature computations
# ---------------------------------------------------------------------------


def _ray_reach(mask_blockers: int, x: int, y: int, dx: int, dy: int) -> int:
    """Return the maximum roll-length k (1..7) in direction (dx, dy) from
    (x, y) such that all k cells stepped onto are *primeable or primed*
    (i.e. not in mask_blockers). For the F5/F7 approximation this
    treats SPACE and PRIMED identically as "eligible cells" and walls,
    carpets, opponent-worker-cells, and own-worker-cell as blockers.

    Returns 0 if no legal step available. Capped at 7.
    """
    k = 0
    nx, ny = x + dx, y + dy
    while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
        bit = 1 << (ny * BOARD_SIZE + nx)
        if mask_blockers & bit:
            break
        k += 1
        if k == 7:
            break
        nx += dx
        ny += dy
    return k


def _cell_potential_for_worker(
    board: board_mod.Board,
    wx: int,
    wy: int,
    opp_x: int,
    opp_y: int,
) -> float:
    """Compute the Carrie-style cell potential aggregated across the
    4 cardinal directions from (wx, wy). Returns a scalar.

    Formula (deviation from RESEARCH_HEURISTIC §B.2):
      Instead of summing over every board cell, v0.1 uses the 4-ray
      best-roll-from-worker-position approximation — equivalent to
      assuming the worker stands at c. This matches what F9/F10
      (longest_primable) were designed for and is cheap; the per-cell
      sum formulation is deferred to v0.2 when we budget for it.

      P = best_roll + lambda * second_best_roll
          * (1 - beta * P_opp_first)
          / (1 + alpha * dist_to_roll_origin)

      dist_to_roll_origin == 0 here (worker IS the origin), so the
      distance term collapses to 1. P_opp_first is approximated
      directionally: if the opponent is strictly closer to the ray
      endpoint, apply beta; tied => beta/2; we strictly closer => 0.
    """
    blockers = (
        board._blocked_mask
        | board._carpet_mask
        # own-worker bit: worker is already standing, so don't block self
        | (1 << (opp_y * BOARD_SIZE + opp_x))
    )

    roll_values = []
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        k = _ray_reach(blockers, wx, wy, dx, dy)
        # endpoint cell for opp-first calc
        ex, ey = wx + dx * max(k, 1), wy + dy * max(k, 1)
        our_dist = abs(wx - ex) + abs(wy - ey)
        opp_dist = abs(opp_x - ex) + abs(opp_y - ey)
        if opp_dist < our_dist:
            p_opp_first = 1.0
        elif opp_dist == our_dist:
            p_opp_first = 0.5
        else:
            p_opp_first = 0.0
        # Roll value: for k>=2 use table; k<=1 contributes 0 (trap cell).
        base = _CARPET_VALUE[k] if k >= 2 else 0.0
        roll_values.append(base * (1.0 - _BETA * p_opp_first))

    if not roll_values:
        return 0.0
    roll_values.sort(reverse=True)
    best = roll_values[0]
    second = roll_values[1] if len(roll_values) > 1 else 0.0
    # distance from worker to cell c is 0 in this approximation, so
    # the (1 + alpha*dist) denominator is just 1.
    return best + _LAMBDA * second


def _reach_through_primed(
    primed_mask: int, blocked_mask: int, carpet_mask: int,
    workers_mask: int, x: int, y: int, dx: int, dy: int,
) -> int:
    """Count contiguous PRIMED cells starting one step away from (x, y) in
    direction (dx, dy). Stops at any non-primed cell (blocked, carpet,
    space, or worker), or at the board edge. Capped at 7.

    Used by F8: the opponent standing at (x, y) could prime-and-roll
    along these cells next turn — this is the *threat* length.
    Note: semantically we could also count k==1 as a "trap" and return 0,
    but the task spec treats the raw reach count as the signal; w_init
    sign carries the actual penalty.
    """
    # Either already-primed or free-space cells would both let the opp
    # build a run, but F8 specifically models "opp can carpet-roll NEXT
    # TURN" which requires the line to already be PRIMED. Free space
    # would still require extra priming turns.
    non_primed_blockers = (
        blocked_mask | carpet_mask | workers_mask | ~primed_mask
    ) & _FULL_MASK

    k = 0
    nx, ny = x + dx, y + dy
    while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
        bit = 1 << (ny * BOARD_SIZE + nx)
        if non_primed_blockers & bit:
            break
        k += 1
        if k == 7:
            break
        nx += dx
        ny += dy
    return k


def _opp_longest_primable(board: board_mod.Board) -> int:
    """F8 helper: longest already-primed line the opponent could roll
    starting from their worker position. Bitmask ray scan in 4 dirs.
    Returns an integer in [0, 7].
    """
    ox, oy = board.opponent_worker.position
    primed = board._primed_mask
    blocked = board._blocked_mask
    carpet = board._carpet_mask
    pw_bit = 1 << (
        board.player_worker.position[1] * BOARD_SIZE
        + board.player_worker.position[0]
    )
    ow_bit = 1 << (oy * BOARD_SIZE + ox)
    workers = pw_bit | ow_bit
    best = 0
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        k = _reach_through_primed(
            primed, blocked, carpet, workers, ox, oy, dx, dy
        )
        if k > best:
            best = k
    return best


def _belief_com_distance(
    worker_xy, belief_summary: BeliefSummary
) -> float:
    """F13 helper: Manhattan distance from worker to belief center-of-mass.

    Prefers BeliefSummary.com_x / com_y if present (O(1)); falls back to
    computing COM from `belief` (O(64)) for backwards compat with pre-v0.2
    callers that did not fill those fields.
    """
    if belief_summary.com_x is not None and belief_summary.com_y is not None:
        cx = belief_summary.com_x
        cy = belief_summary.com_y
    else:
        b = belief_summary.belief
        # dot-product path; allocates _COM_X_COORDS the first time only.
        cx = float(np.dot(b, _COM_X_COORDS))
        cy = float(np.dot(b, _COM_Y_COORDS))
    wx, wy = worker_xy
    return abs(wx - cx) + abs(wy - cy)


def features(
    board: board_mod.Board, belief_summary: BeliefSummary
) -> np.ndarray:
    """Compute the 9-feature vector (float64) from the perspective of
    `board.player_worker`. Fast path for leaf eval.

    No allocation beyond the returned array; all sub-calculations reuse
    module-level constants.
    """
    out = np.empty(N_FEATURES, dtype=np.float64)

    # F1 score_diff
    out[0] = float(
        board.player_worker.points - board.opponent_worker.points
    )

    # F3 ours_prime_count — popcount of primed mask (attribution approx)
    out[1] = float(_popcount(board._primed_mask))

    # F4 ours_carpet_count — popcount of carpet mask (attribution approx)
    out[2] = float(_popcount(board._carpet_mask))

    # F5 / F7 — Carrie cell potential from each worker's position
    wx, wy = board.player_worker.position
    ox, oy = board.opponent_worker.position
    out[3] = _cell_potential_for_worker(board, wx, wy, ox, oy)
    out[4] = _cell_potential_for_worker(board, ox, oy, wx, wy)

    # F11 / F12 — belief summary stats (O(1))
    out[5] = float(belief_summary.max_mass)
    out[6] = float(belief_summary.entropy)

    # F8 — opp_longest_primable: longest primed run the opponent could
    # roll next turn. O(4) ray scans through primed cells only.
    out[7] = float(_opp_longest_primable(board))

    # F13 — belief COM distance from our worker. O(1) if com_x/com_y are
    # precomputed in BeliefSummary, else O(64) fallback.
    out[8] = _belief_com_distance((wx, wy), belief_summary)

    return out


def evaluate(
    board: board_mod.Board,
    belief_summary: BeliefSummary,
    weights: Optional[np.ndarray] = None,
) -> float:
    """Scalar leaf evaluation from the PERSPECTIVE OF `board.player_worker`
    (negamax sign convention).

    Terminal short-circuit:
        If `board.is_game_over()`, returns
            (player_points - opp_points) * TERMINAL_SCALE
        dominating any heuristic value from non-terminal leaves.

    Non-terminal:
        return float(dot(weights or W_INIT, features(board, belief_summary)))

    Time budget: p99 <= 150 us over 10k random boards at 9 features
    (v0.2 bumped from 100 us in v0.1; see tests).
    """
    if board.is_game_over():
        return TERMINAL_SCALE * float(
            board.player_worker.points - board.opponent_worker.points
        )

    w = W_INIT if weights is None else weights
    if w.shape != (N_FEATURES,):
        raise ValueError(
            f"weights must be shape ({N_FEATURES},), got {w.shape}"
        )
    return float(np.dot(w, features(board, belief_summary)))


# ---------------------------------------------------------------------------
# Object-oriented wrapper (matches existing stub surface so downstream
# imports `Heuristic` keep working; dev-search can construct this once
# and pass it to `_alphabeta` as a callable).
# ---------------------------------------------------------------------------


class Heuristic:
    """Linear combination of handcrafted features; weights tuned via BO."""

    def __init__(self, weights: Optional[np.ndarray] = None) -> None:
        w = W_INIT.copy() if weights is None else np.asarray(
            weights, dtype=np.float64
        )
        if w.shape != (N_FEATURES,):
            raise ValueError(
                f"weights must be shape ({N_FEATURES},), got {w.shape}"
            )
        self._w: np.ndarray = w

    @property
    def weights(self) -> np.ndarray:
        return self._w

    def V_leaf(
        self, board: board_mod.Board, belief_summary: BeliefSummary
    ) -> float:
        """Leaf evaluation — negamax sign. Delegates to module evaluate()."""
        return evaluate(board, belief_summary, self._w)

    def set_weights(self, new_w: np.ndarray) -> None:
        new_w = np.asarray(new_w, dtype=np.float64)
        if new_w.shape != (N_FEATURES,):
            raise ValueError(
                f"weights must be shape ({N_FEATURES},), got {new_w.shape}"
            )
        self._w = new_w
