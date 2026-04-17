"""F2 linear leaf evaluator — v0.4.2 (19 features, + F10/F24 exploits).

9-feature linear heuristic per BOT_STRATEGY_V02_ADDENDUM.md §2.4 / T-20c
expanded by 3 distance-kernel features (T-20c.1) per
CARRIE_DECONSTRUCTION §5. v0.1 shipped 7 features; v0.2 added F8
(opponent line threat) and F13 (belief COM distance); v0.2.1 adds the
multi-scale-decay superset kernel F14/F15/F16 so BO can pick Carrie's
actual decay shape without us knowing it. v0.2.2 (T-20g) caches
`_cell_potential_vector` on a 4-tuple mask key. v0.3 (T-30c-numba)
JIT-compiles the three hot functions (`_ray_reach`,
`_cell_potential_for_worker`, `_cell_potential_vector`) using
`@njit(cache=True)` with a pure-Python fallback behind the
module-level `_USE_NUMBA` kill-switch. v0.3.1 (T-30b) adds **F17**
priming-lockout (count of dead/isolated primes within our reach)
and **F18** opp-belief-proxy (post-opp-search belief entropy).
v0.4.2 (T-40-EXPLOIT-2/3) adds **F10** opp_mobility_denied + adjacency
bonus (count of PRIMED/CARPET cardinal neighbors of opp worker PLUS
primed-line endpoints cardinal-adjacent to our worker) and **F24**
opp_wasted_primes (mirror of F17 against opp's reachable primes —
rewards maneuvering opp into wasteful priming).
v0.4.1 (T-40-EXPLOIT-1) adds **F22** prime_steal_bonus (sum over
primed lines where our worker is closer to a line endpoint than the
opponent, weighted by CARPET_POINTS_TABLE[k]; rewards positions where
the engine's allow-any-player-to-carpet rule (SPEC §2.3) hands us
free rolls of opp/shared primed lines — especially effective vs
George / greedy opponents).
v0.4.0 (T-40b) adds **F19** rat_catch_threat_radius (belief mass
within Manhattan-2 of our worker) and **F20** opp_roll_imminence
(longest primed-or-space run the opp could exploit in the near
future — F8 superset).

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
  F14 cell_potential_recip      = Σ_c P(c) / (1 + d(worker, c))
                                  Carrie-decay hypothesis H1 (1/(1+d))
  F15 cell_potential_exp        = Σ_c P(c) · exp(-0.5·d(worker, c))
                                  Carrie-decay hypothesis H2 (exp(-λd),
                                  small-λ end) — λ frozen at 0.5 in
                                  v0.2.1; BO tunes the linear weight.
  F16 cell_potential_step       = Σ_{c: d≤5} P(c)
                                  Carrie-decay hypothesis H6 (step at
                                  D_max=5). No decay inside reach;
                                  zero outside.
  F17 priming_lockout           = count of primed cells that are
                                  (a) within Manhattan ≤ our_turns_left
                                      of our worker (reachable before
                                      game end); AND
                                  (b) have NO primed cardinal neighbor
                                      (i.e. can only be rolled as k=1
                                      for −1 point — strictly dominated,
                                      see CARPET_POINTS_TABLE[1] = -1).
                                  These are "dead primes" on our side.
                                  Negative weight — we paid +1 to prime
                                  them but can only extract −1 by rolling.
  F18 opp_belief_proxy          = Shannon entropy of the rat-belief
                                  distribution AFTER updating it against
                                  the opponent's last search outcome.
                                  Higher = opponent more uncertain about
                                  rat location = good for us (POSITIVE
                                  weight). If opp did not search, or
                                  searched and hit (which would have
                                  reset the belief), F18 collapses to
                                  belief_summary.entropy. (Note: the
                                  engine only exposes one-ply opp search
                                  history via `board.opponent_search`;
                                  a richer multi-ply history tracker is
                                  v0.4+.)
  F19 rat_catch_threat_radius   = Σ_c belief[c] · I(d(worker, c) ≤ 2)
                                  — prob-weighted "rat is near me" in
                                  [0, 1]. High = belief concentrated
                                  close to our worker → next SEARCH is
                                  cheap and high-EV (T-40b, V04 §c).
  F20 opp_roll_imminence        = Longest PRIMED-or-SPACE cardinal run
                                  from opp worker position, in [0, 7].
                                  Superset of F8 (F8 counts only already
                                  primed); F20 also counts SPACE so it
                                  signals looming opp threats even with
                                  no existing primes. Neg weight — big
                                  F20 = opp has room to set up a long
                                  roll (T-40b).
  F22 prime_steal_bonus         = Σ over H/V primed lines (k ≥ 2) of
                                  CARPET_POINTS_TABLE[k] · I[our_worker
                                  is strictly closer to nearer endpoint
                                  than opp_worker]. Rewards positions
                                  where we can roll opp/shared primed
                                  lines before the opp does (SPEC §2.3
                                  permits either player to roll any
                                  PRIMED run). Positive weight. Per
                                  OPPONENT_EXPLOITS §T-40-EXPLOIT-1.
                                  Attribution-agnostic — since the
                                  engine doesn't track who primed what,
                                  we treat every line as a candidate
                                  and rely on our-closer-than-opp to
                                  pick real steal targets.
  F10 opp_mobility_denied_plus_adj = count of PRIMED|CARPET cardinal
                                  neighbors of opp_worker PLUS count of
                                  primed-line endpoints (k ≥ 2) that
                                  are cardinal-adjacent to our_worker.
                                  Per OPPONENT_EXPLOITS §T-40-EXPLOIT-2.
                                  Positive weight — higher = opp is
                                  boxed AND/OR we're adjacent-to-steal.
                                  Integer in [0, 8] typical.
  F24 opp_wasted_primes         = mirror of F17 applied to opp's side:
                                  count of primed cells reachable by
                                  opp within opp.turns_left AND isolated
                                  (no primed cardinal neighbor). Per
                                  OPPONENT_EXPLOITS §T-40-EXPLOIT-3.
                                  Positive weight — their dead primes
                                  are good for us. Integer in [0, 64].

  P(c) = best-roll-value-if-worker-stood-at-c (ray scan through
         BLOCKED/CARPET/opp-worker blockers, Manhattan-extended using
         CARPET_POINTS_TABLE lookup). Cached as `_P_VEC` per eval.

Public API (module-level):

    evaluate(board, belief_summary, weights=None) -> float
    features(board, belief_summary) -> np.ndarray   # shape (19,) float64

A thin Heuristic class is kept for downstream consumers (search engine).

Hyperparams (D-011 item 5): gamma_info=0.5, gamma_reset=0.3 (used by F15
when it lands in v0.3+; not present in the v0.2 feature vector).

Owner: dev-heuristic.
"""

from __future__ import annotations

import functools
import os
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
    "clear_p_vec_cache",
    "p_vec_cache_info",
    "is_numba_active",
    "warm_numba_kernels",
]


# ---------------------------------------------------------------------------
# Numba kill-switch (T-30c-numba; default flipped OFF in T-30f)
#
# `_USE_NUMBA = True`  → compile the 3 hot functions with @njit(cache=True)
#                         and dispatch through the numba kernel. Falls back
#                         to pure-Python if numba is unavailable/broken.
# `_USE_NUMBA = False` → pure-Python path (byte-identical to v0.2.2).
#
# **Default is now OFF** (T-30f, 2026-04-17) so every zip built from this
# tree is tournament-safe by default — LIVE_UPLOAD_006 confirmed the
# bytefight.org validator rejects the numba zip. Opt in explicitly via
# env var `RATTLEBOT_NUMBA=1` for local benchmarks + BO tuning where the
# 3-4× leaf speedup matters. `RATTLEBOT_NUMBA=0` (or unset) keeps the
# safe pure-Python path.
# ---------------------------------------------------------------------------

# T-30f (2026-04-17): flipped default from ON to OFF after
# LIVE_UPLOAD_006 confirmed numba JIT breaks the bytefight.org sandbox
# validator (pure-Python zip PASSES validation, numba zip FAILS —
# byte-identical except for this one line). Default-OFF means every
# submission zip built from this tree is tournament-safe by default;
# opt in explicitly with `RATTLEBOT_NUMBA=1` for local benchmarks + BO
# tuning where the 3-4× leaf speedup matters.
_USE_NUMBA: bool = os.environ.get("RATTLEBOT_NUMBA", "0") == "1"
# T-40a: env-var escape hatch for parity debugging — forces the scalar
# Python reference to run instead of the numpy-vectorized path. Default
# False. Tests flip this to verify the scalar oracle still works.
_USE_SCALAR_REF: bool = os.environ.get("RATTLEBOT_HEURISTIC_REF", "0") == "1"

try:
    if _USE_NUMBA:
        from numba import njit  # type: ignore
        _NUMBA_AVAILABLE = True
    else:  # pragma: no cover
        njit = None  # type: ignore
        _NUMBA_AVAILABLE = False
except ImportError:  # pragma: no cover
    njit = None  # type: ignore
    _NUMBA_AVAILABLE = False
    _USE_NUMBA = False


def is_numba_active() -> bool:
    """Return True iff the numba-compiled hot path is live."""
    return bool(_USE_NUMBA and _NUMBA_AVAILABLE)


N_FEATURES: int = 19

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
#   9   F14   +0.15   Σ P(c)/(1+d): Carrie-decay H1 (reciprocal). Starter
#                     magnitude small — the three kernels are redundant
#                     at first; BO will reallocate mass to whichever
#                     shape actually correlates with Carrie's play.
#                     (CARRIE_DECONSTRUCTION §5 starter: 0.4; scaled down
#                     here because our P(c) magnitudes already saturate
#                     at carpet_value(7)=21.)
#  10   F15   +0.10   Σ P(c)·exp(-0.5 d): Carrie-decay H2 (exponential).
#  11   F16   +0.10   Σ_{d≤5} P(c): Carrie-decay H6 (step at D_max=5).
#  12   F17   -0.4    dead primes on our side. Each isolated-and-reachable
#                     prime costs +1 (paid) and earns at most -1 (roll
#                     k=1) = net -2 pts over 3 turns; -0.4 is roughly
#                     scaled to that penalty (BO will retune).
#  13   F18   +0.1    opp-belief entropy after their last search. Positive
#                     — higher entropy means opp is more uncertain, so
#                     they can't profitably SEARCH next turn. Small
#                     magnitude because entropy units are nats in
#                     [0, ln 64] ≈ [0, 4.16], similar scale to F12.
#
#  14   F19    +0.3    Σ_c belief[c] · I(Manhattan(worker, c) ≤ 2) — prob-
#                      weighted "rat is near me right now" signal. Positive:
#                      higher means we're close to the likely rat location,
#                      increasing EV of a SEARCH at the argmax or along
#                      nearby cells. Magnitude scale: feature in [0, 1]
#                      (fraction of belief within Manhattan-2 of worker).
#  15   F20    -0.6    Longest primed-or-space run (length 1..7) the opp
#                      could roll within one ply of priming/moving, from
#                      their current worker position in any cardinal dir.
#                      See `_opp_roll_imminence` — this is a SUPERSET of
#                      F8 (F8 counts only already-PRIMED cells; F20 also
#                      counts SPACE as "one prime step away from being
#                      rollable next turn"). Captures looming threats
#                      where opp has an empty corridor to set up in.
#                      Negative: big F20 = opp has space to threaten.
#  16   F22    +0.3    Prime-steal bonus. Per T-40-EXPLOIT-1 /
#                      OPPONENT_EXPLOITS.md §T-40-EXPLOIT-1: sum over
#                      primed lines (k ≥ 2, H/V) of CARPET_POINTS_TABLE[k]
#                      for lines where our worker is strictly closer to
#                      the nearer endpoint than opp's worker. Engine
#                      allows either player to CARPET any PRIMED line
#                      (SPEC §2.3), so a close primed line adjacent to
#                      us is a free steal opportunity. Especially
#                      effective vs George / greedy opponents who don't
#                      check steal-ability when priming. Positive.
#                      Attribution approximation: we don't distinguish
#                      lines we primed from lines opp primed — both
#                      are steal-candidates if we're closer. This
#                      overstates F22 for our own adjacent lines, but
#                      since rolling our own lines is the intended
#                      action anyway, the sign is still correct.
#                      Falsification per OPPONENT_EXPLOITS §T-40-EXPLOIT-1:
#                      if paired George scrimmage shows 0 actual
#                      steals in 20 matches, drop from W_INIT.
#  17   F10    +0.15   Opp-mobility-denied + adjacent-to-primed-endpoint
#                      bonus. Per T-40-EXPLOIT-2 / OPPONENT_EXPLOITS.md
#                      §T-40-EXPLOIT-2: sum of (a) count of PRIMED or
#                      CARPET cells cardinal-adjacent to opp worker
#                      (mobility-denied base); (b) count of primed-line
#                      endpoints (k ≥ 2) that are cardinal-adjacent to
#                      OUR worker (we're perfectly positioned to steal
#                      next ply). Positive — higher = we've boxed opp in
#                      AND/OR we're adjacent to a steal. Small magnitude
#                      because each sub-signal is in [0, 4].
#                      Attribution caveat: "cells we've primed/carpeted"
#                      is aspirational (engine doesn't track) — we count
#                      all PRIMED/CARPET cells since those equally
#                      restrict opp movement regardless of who laid them.
#  18   F24    +0.15   Opp-wasted-primes (mirror of F17). Per T-40-EXPLOIT-3
#                      / OPPONENT_EXPLOITS.md §T-40-EXPLOIT-3: count of
#                      primed cells that are (a) within Manhattan ≤ opp's
#                      turns_left of opp's worker (reachable) AND (b)
#                      isolated (no primed cardinal neighbor). These are
#                      "dead primes" on opp's side — opp paid +1 to prime
#                      them but can only extract −1 by rolling k=1.
#                      Albert/Carrie's simple heuristics likely miss this
#                      penalty, so the signal tells us to maneuver them
#                      into over-priming. Positive — their dead primes
#                      are good for us.
#
W_INIT: np.ndarray = np.array(
    [1.0, 0.3, 0.2, 1.5, -1.2, -3.0, -0.5, -0.6, -0.05, 0.15, 0.10, 0.10,
     -0.4, 0.1, 0.3, -0.6, 0.3, 0.15, 0.15],
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

# --------------------------------------------------------------------------
# Multi-scale distance-kernel statics (F14 / F15 / F16 — T-20c.1)
#
# Per CARRIE_DECONSTRUCTION §5, we don't know whether Carrie's decay is
# reciprocal (1/(1+d)), exponential (exp(-λd)), or step (1 if d<=D). We
# include all three with BO-tuned weights so the union dominates whichever
# one she actually uses. Each kernel maps Manhattan distance d in [0..14]
# to a scalar weight.
# --------------------------------------------------------------------------

# 64x64 Manhattan-distance matrix over flat indices i=y*8+x.
# `_MANHATTAN[i, j]` is Manhattan dist between cell i and cell j.
_MANHATTAN = (
    np.abs(_COM_X_COORDS[:, None] - _COM_X_COORDS[None, :])
    + np.abs(_COM_Y_COORDS[:, None] - _COM_Y_COORDS[None, :])
).astype(np.float64)

# Per-kernel 64x64 matrices: `_KERNEL_RECIP[i, j]` is the recip-decay
# applied to cell j when the worker is at cell i. Pre-broadcast so the
# per-eval path is a single `np.dot(P_vec, kernel_row)`.
_KERNEL_RECIP = 1.0 / (1.0 + _MANHATTAN)
# Exp kernel with λ=0.5 — matches CARRIE_DECONSTRUCTION §5.1 starter.
# λ frozen in v0.2.1 — BO tunes the *weight* not the shape; making λ
# a BO dim would promote this to a mixed search space which skopt
# handles worse than pure Real boxes (note from team-lead T-20c.1 brief).
_LAMBDA_EXP = 0.5
_KERNEL_EXP = np.exp(-_LAMBDA_EXP * _MANHATTAN)
# Step kernel with D_max = 5 — matches §5.1 starter (H6-mid).
_D_STEP = 5
_KERNEL_STEP = (_MANHATTAN <= _D_STEP).astype(np.float64)

# T-40b: mask for F19 `rat_catch_threat_radius`. `_NEAR2_MASK[i]` is a
# 64-dim float64 row where entry j == 1.0 iff Manhattan(i, j) ≤ 2,
# else 0.0. Per-eval F19 = `np.dot(belief, _NEAR2_MASK[worker_idx])`.
# "2" was chosen per V04 ADDENDUM §c — rat drift rate per ply is
# ~1 cell, so within 2 plies a cell-at-Manhattan≤2 is reachable by
# us OR by the rat meeting us.
_F19_RADIUS = 2
_NEAR2_MASK = (_MANHATTAN <= _F19_RADIUS).astype(np.float64)


# --------------------------------------------------------------------------
# T-40a: ray-step LUT + carpet-roll value LUT for the numpy-vectorized
# hot-path in `_cell_potential_vector_vec` / `_cell_potential_for_worker_vec`.
#
# `_STEP_IDX[d, c, k]` = flat-index of the cell reached by stepping (k+1)
# times in direction d starting from cell c, OR `_OFF_BOARD` (= 64) if the
# step would leave the board. d indices: 0=UP, 1=DOWN, 2=LEFT, 3=RIGHT.
# Shape (4, 64, 7), dtype int8 → 1 792 bytes. Loop-invariant — built once.
#
# `_ROLL_VALUE_BY_K = [0, 0, 2, 4, 6, 10, 15, 21]` collapses `_CARPET_VALUE`
# to the contribution per-direction for F5/F7 cell-potential (k=1 treated
# as 0 per the original per-direction loop, not −1 — matches `base = ... if
# k >= 2 else 0.0` in `_cell_potential_for_worker_py`). For F14/F15/F16 P-vec
# use the same mapping since `_cell_potential_vector_py` also guards `if
# k >= 2`.
# --------------------------------------------------------------------------

_OFF_BOARD = 64  # sentinel index appended to `blk` so off-board is a blocker
_MAX_ROLL = 7

# Cardinal direction offsets (dx, dy). Index 0..3 — order doesn't matter
# for the `max` reduction, but kept as UP/DOWN/LEFT/RIGHT for readability.
_DIR_OFFSETS = ((0, -1), (0, 1), (-1, 0), (1, 0))
_N_DIR = 4


def _build_step_lut() -> list:
    """Precompute nested-list LUT of (d, c, k) → bit mask of step cell.

    Returned as a list-of-list-of-list of Python ints:
      `_STEP_BIT[d][c]` is a length-7 tuple; entry k is `1 << idx` of
      the cell reached after stepping (k+1) times in direction d from
      cell c, or 0 if off-board. Using 0 as the off-board sentinel
      lets the hot loop terminate via `if not step_bit: break` — one
      branch instead of two.

    Nested lists (not numpy) because the hot loop is pure-Python and
    benefits more from CPython list/int indexing than from numpy
    overhead on tiny arrays (measured: ~1.3× faster than the numpy
    vectorization at N=64 × 4 × 7).
    """
    out = []
    for d, (dx, dy) in enumerate(_DIR_OFFSETS):
        per_dir = []
        for c in range(64):
            cx = c % BOARD_SIZE
            cy = c // BOARD_SIZE
            steps = []
            for k in range(_MAX_ROLL):
                nx = cx + dx * (k + 1)
                ny = cy + dy * (k + 1)
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    steps.append(1 << (ny * BOARD_SIZE + nx))
                else:
                    steps.append(0)  # off-board sentinel
            per_dir.append(tuple(steps))
        out.append(per_dir)
    return out


# Module-level step-bit LUT. Loop-invariant across all boards.
# Size: 4 × 64 × 7 = 1 792 Python ints, negligible memory.
_STEP_BIT: list = _build_step_lut()

# Roll-value-by-k as a plain list (Python int-float-mul is faster than
# numpy scalar-mul on single values). Matches `_CARPET_VALUE[k] if k >= 2
# else 0.0` exactly for both cpw and pvec.
_ROLL_VALUE_BY_K: list = [0.0, 0.0, 2.0, 4.0, 6.0, 10.0, 15.0, 21.0]


def _cell_potential_vector_vec(
    blocked: int, carpet: int, opp_bit: int, own_bit: int,
) -> np.ndarray:
    """Optimized pure-Python implementation of `_cell_potential_vector_py`.

    Despite the `_vec` suffix (retained for dispatcher compatibility),
    this uses the STEP_BIT LUT + a tight Python loop rather than numpy
    broadcasting — benchmarks on the live profile harness showed numpy
    was *slower* than optimized Python at the 64-cell problem size
    (numpy per-call overhead + dtype coercion dominates). The LUT
    eliminates the `1 << (ny*BOARD_SIZE + nx)` shift in the ray walk,
    which was the hot-loop bottleneck in the scalar reference.

    Output is byte-identical to `_cell_potential_vector_py`; exercised
    by `tests/test_heuristic.py::test_pvec_parity_vec_vs_scalar`.
    """
    blockers_base = blocked | carpet | opp_bit
    dead_mask = (blocked | carpet) & ~own_bit
    out = np.zeros(_BOARD_CELLS, dtype=np.float64)
    cv = _ROLL_VALUE_BY_K
    S = _STEP_BIT
    for idx in range(_BOARD_CELLS):
        bit = 1 << idx
        if dead_mask & bit:
            continue
        if bit == opp_bit:
            continue
        best = 0.0
        # Unroll the 4 directions; each is a 7-element ray walk.
        for d in range(4):
            steps = S[d][idx]
            k = 0
            for s in steps:
                if not s:  # off-board sentinel (= 0) terminates ray
                    break
                if blockers_base & s:
                    break
                k += 1
            if k >= 2:
                v = cv[k]
                if v > best:
                    best = v
        out[idx] = best
    return out


def _cell_potential_for_worker_vec(
    blockers: int,
    wx: int,
    wy: int,
    opp_x: int,
    opp_y: int,
    lam: float,
    beta: float,
    carpet_value: np.ndarray,
) -> float:
    """Optimized pure-Python implementation of `_cell_potential_for_worker_py`.

    Two micro-opts vs the scalar reference:
      1. Reuse `_STEP_BIT` LUT to walk each direction without rebuilding
         `1 << (ny*8 + nx)` every cell.
      2. Track top-2 roll values inline (one `if/elif` per dir) — no
         `list.append` + `list.sort` allocation per call.
    Early-exits on k<2 to skip the endpoint distance arithmetic.
    """
    c = wy * BOARD_SIZE + wx
    cv = _ROLL_VALUE_BY_K
    S = _STEP_BIT
    best = 0.0
    second = 0.0
    for d, (dx, dy) in enumerate(_DIR_OFFSETS):
        steps = S[d][c]
        k = 0
        for s in steps:
            if not s:
                break
            if blockers & s:
                break
            k += 1
        if k < 2:
            v = 0.0
        else:
            # Endpoint cell for P_opp_first comparison (k≥2 so max(k,1)=k).
            ex = wx + dx * k
            ey = wy + dy * k
            our_dist = abs(wx - ex) + abs(wy - ey)
            opp_dist = abs(opp_x - ex) + abs(opp_y - ey)
            if opp_dist < our_dist:
                p_opp_first = 1.0
            elif opp_dist == our_dist:
                p_opp_first = 0.5
            else:
                p_opp_first = 0.0
            v = cv[k] * (1.0 - beta * p_opp_first)
        # Top-2 tracker without list alloc.
        if v > best:
            second = best
            best = v
        elif v > second:
            second = v
    return best + lam * second


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


def _ray_reach_py(mask_blockers: int, x: int, y: int, dx: int, dy: int) -> int:
    """Pure-Python reference implementation of `_ray_reach`. Used when
    `_USE_NUMBA=False` and as the parity oracle for tests.

    Return the maximum roll-length k (1..7) in direction (dx, dy) from
    (x, y) such that all k cells stepped onto are *primeable or primed*
    (i.e. not in mask_blockers). Blockers = BLOCKED | CARPET | workers.
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


if _NUMBA_AVAILABLE and _USE_NUMBA:
    @njit(cache=True)
    def _ray_reach_nb(mask_blockers, x, y, dx, dy):
        """Numba-compiled equivalent of `_ray_reach_py`.

        Expects `mask_blockers` as np.uint64 (the bitmask); x, y, dx, dy
        as plain int64. Uses np.uint64 for the `1 << idx` shift to stay
        in uint64 arithmetic and avoid Python's arbitrary-precision int
        boundary (numba requires fixed-width integers).
        """
        k = 0
        nx = x + dx
        ny = y + dy
        while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
            bit = np.uint64(1) << np.uint64(ny * BOARD_SIZE + nx)
            if mask_blockers & bit:
                break
            k += 1
            if k == 7:
                break
            nx += dx
            ny += dy
        return k


def _ray_reach(mask_blockers: int, x: int, y: int, dx: int, dy: int) -> int:
    """Dispatcher — calls the numba kernel if `_USE_NUMBA` is on, else the
    pure-Python reference. Semantics identical.
    """
    if _USE_NUMBA and _NUMBA_AVAILABLE:
        return int(_ray_reach_nb(np.uint64(mask_blockers), x, y, dx, dy))
    return _ray_reach_py(mask_blockers, x, y, dx, dy)


def _cell_potential_for_worker_py(
    blockers: int,
    wx: int,
    wy: int,
    opp_x: int,
    opp_y: int,
    lam: float,
    beta: float,
    carpet_value: np.ndarray,
) -> float:
    """Pure-Python core of `_cell_potential_for_worker`. Takes the already
    assembled `blockers` mask (BLOCKED | CARPET | opp_bit) so the numba
    sibling can share the same signature. Returns the Carrie cell
    potential scalar as per `_cell_potential_for_worker`'s docstring.
    """
    roll_values = []
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        k = _ray_reach_py(blockers, wx, wy, dx, dy)
        ex, ey = wx + dx * max(k, 1), wy + dy * max(k, 1)
        our_dist = abs(wx - ex) + abs(wy - ey)
        opp_dist = abs(opp_x - ex) + abs(opp_y - ey)
        if opp_dist < our_dist:
            p_opp_first = 1.0
        elif opp_dist == our_dist:
            p_opp_first = 0.5
        else:
            p_opp_first = 0.0
        base = carpet_value[k] if k >= 2 else 0.0
        roll_values.append(base * (1.0 - beta * p_opp_first))
    roll_values.sort(reverse=True)
    best = roll_values[0]
    second = roll_values[1]
    return best + lam * second


if _NUMBA_AVAILABLE and _USE_NUMBA:
    @njit(cache=True)
    def _cell_potential_for_worker_nb(
        blockers, wx, wy, opp_x, opp_y, lam, beta, carpet_value
    ):
        """Numba-compiled equivalent. Takes the same args as
        `_cell_potential_for_worker_py`; `blockers` must be np.uint64.

        Implementation notes:
          - The 4 cardinal directions are unrolled (numba can't handle
            tuples-of-tuples on the hot path without boxing).
          - Top-2 selection uses two `if` branches rather than building
            a list + sorting — avoids list allocation inside njit.
        """
        best = -1.0
        second = -1.0

        # dir (0, -1)
        k = _ray_reach_nb(blockers, wx, wy, 0, -1)
        ex = wx
        ey = wy - max(k, 1)
        our_dist = abs(wx - ex) + abs(wy - ey)
        opp_dist = abs(opp_x - ex) + abs(opp_y - ey)
        if opp_dist < our_dist:
            p_opp = 1.0
        elif opp_dist == our_dist:
            p_opp = 0.5
        else:
            p_opp = 0.0
        base = carpet_value[k] if k >= 2 else 0.0
        v = base * (1.0 - beta * p_opp)
        if v > best:
            second = best
            best = v
        elif v > second:
            second = v

        # dir (0, 1)
        k = _ray_reach_nb(blockers, wx, wy, 0, 1)
        ex = wx
        ey = wy + max(k, 1)
        our_dist = abs(wx - ex) + abs(wy - ey)
        opp_dist = abs(opp_x - ex) + abs(opp_y - ey)
        if opp_dist < our_dist:
            p_opp = 1.0
        elif opp_dist == our_dist:
            p_opp = 0.5
        else:
            p_opp = 0.0
        base = carpet_value[k] if k >= 2 else 0.0
        v = base * (1.0 - beta * p_opp)
        if v > best:
            second = best
            best = v
        elif v > second:
            second = v

        # dir (-1, 0)
        k = _ray_reach_nb(blockers, wx, wy, -1, 0)
        ex = wx - max(k, 1)
        ey = wy
        our_dist = abs(wx - ex) + abs(wy - ey)
        opp_dist = abs(opp_x - ex) + abs(opp_y - ey)
        if opp_dist < our_dist:
            p_opp = 1.0
        elif opp_dist == our_dist:
            p_opp = 0.5
        else:
            p_opp = 0.0
        base = carpet_value[k] if k >= 2 else 0.0
        v = base * (1.0 - beta * p_opp)
        if v > best:
            second = best
            best = v
        elif v > second:
            second = v

        # dir (1, 0)
        k = _ray_reach_nb(blockers, wx, wy, 1, 0)
        ex = wx + max(k, 1)
        ey = wy
        our_dist = abs(wx - ex) + abs(wy - ey)
        opp_dist = abs(opp_x - ex) + abs(opp_y - ey)
        if opp_dist < our_dist:
            p_opp = 1.0
        elif opp_dist == our_dist:
            p_opp = 0.5
        else:
            p_opp = 0.0
        base = carpet_value[k] if k >= 2 else 0.0
        v = base * (1.0 - beta * p_opp)
        if v > best:
            second = best
            best = v
        elif v > second:
            second = v

        return best + lam * second


def _cell_potential_for_worker(
    board: board_mod.Board,
    wx: int,
    wy: int,
    opp_x: int,
    opp_y: int,
) -> float:
    """Public dispatcher — picks a backend in this preference order:

      1. numba (`@njit(cache=True)`) if `_USE_NUMBA=True` and available.
      2. numpy-vectorized (T-40a, submission-safe, pure-Python fallback).
      3. scalar Python reference (oracle; used only if env var
         `RATTLEBOT_HEURISTIC_REF=1` is set for parity debugging).

    Semantics are byte-identical across all three paths per the
    `test_numpy_vec_*_parity` + `test_numba_kernels_match_python_reference`
    tests.
    """
    blockers = (
        board._blocked_mask
        | board._carpet_mask
        | (1 << (opp_y * BOARD_SIZE + opp_x))
    )
    if _USE_NUMBA and _NUMBA_AVAILABLE:
        return float(_cell_potential_for_worker_nb(
            np.uint64(blockers), wx, wy, opp_x, opp_y,
            _LAMBDA, _BETA, _CARPET_VALUE,
        ))
    if _USE_SCALAR_REF:
        return _cell_potential_for_worker_py(
            blockers, wx, wy, opp_x, opp_y,
            _LAMBDA, _BETA, _CARPET_VALUE,
        )
    return _cell_potential_for_worker_vec(
        blockers, wx, wy, opp_x, opp_y,
        _LAMBDA, _BETA, _CARPET_VALUE,
    )


def _cell_potential_vector_py(
    blocked: int, carpet: int, opp_bit: int, own_bit: int,
) -> np.ndarray:
    """Pure-Python core of `_cell_potential_vector`. Called directly when
    `_USE_NUMBA=False`, and invoked by the numba dispatcher below. The
    returned array is NOT marked read-only here — the caller wrapper does
    that once, after picking a backend.
    """
    blockers_base = blocked | carpet | opp_bit
    dead_mask = (blocked | carpet) & ~own_bit

    out = np.zeros(_BOARD_CELLS, dtype=np.float64)
    for idx in range(_BOARD_CELLS):
        bit = 1 << idx
        if dead_mask & bit:
            continue
        if bit == opp_bit:
            continue
        x = idx % BOARD_SIZE
        y = idx // BOARD_SIZE
        blockers_c = blockers_base & ~bit
        best = 0.0
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            k = _ray_reach_py(blockers_c, x, y, dx, dy)
            if k >= 2:
                v = _CARPET_VALUE[k]
                if v > best:
                    best = v
        out[idx] = best
    return out


if _NUMBA_AVAILABLE and _USE_NUMBA:
    @njit(cache=True)
    def _cell_potential_vector_nb(blocked, carpet, opp_bit, own_bit, carpet_value):
        """Numba-compiled equivalent. Arg types: all 4 masks np.uint64,
        `carpet_value` a float64 ndarray of length 8.

        Implementation:
          - All ints kept in uint64 to avoid numba boxing Python ints.
          - Directions unrolled (numba doesn't handle tuple-of-tuples
            cleanly in hot code).
          - Writes into a fresh numpy array so the outer cache can
            retain it across calls.
        """
        blockers_base = blocked | carpet | opp_bit
        not_own = ~own_bit
        dead_mask = (blocked | carpet) & not_own

        out = np.zeros(64, dtype=np.float64)
        for idx in range(64):
            bit = np.uint64(1) << np.uint64(idx)
            if dead_mask & bit:
                continue
            if bit == opp_bit:
                continue
            x = idx % 8
            y = idx // 8
            blockers_c = blockers_base & ~bit
            best = 0.0

            k = _ray_reach_nb(blockers_c, x, y, 0, -1)
            if k >= 2:
                v = carpet_value[k]
                if v > best:
                    best = v
            k = _ray_reach_nb(blockers_c, x, y, 0, 1)
            if k >= 2:
                v = carpet_value[k]
                if v > best:
                    best = v
            k = _ray_reach_nb(blockers_c, x, y, -1, 0)
            if k >= 2:
                v = carpet_value[k]
                if v > best:
                    best = v
            k = _ray_reach_nb(blockers_c, x, y, 1, 0)
            if k >= 2:
                v = carpet_value[k]
                if v > best:
                    best = v

            out[idx] = best
        return out


@functools.lru_cache(maxsize=4096)
def _cell_potential_vector_cached(
    blocked: int, carpet: int, opp_bit: int, own_bit: int
) -> np.ndarray:
    """LRU-cached adapter over the selected backend. Returned arrays are
    read-only so the cache can safely hand out shared references.

    Cache key: the 4 integers that fully determine P(c) under the
    heuristic's blocker definition. See `_cell_potential_vector` for the
    public wrapper that extracts them from a Board.
    """
    if _USE_NUMBA and _NUMBA_AVAILABLE:
        out = _cell_potential_vector_nb(
            np.uint64(blocked), np.uint64(carpet),
            np.uint64(opp_bit), np.uint64(own_bit),
            _CARPET_VALUE,
        )
    elif _USE_SCALAR_REF:
        out = _cell_potential_vector_py(blocked, carpet, opp_bit, own_bit)
    else:
        out = _cell_potential_vector_vec(blocked, carpet, opp_bit, own_bit)
    out.setflags(write=False)
    return out


def _cell_potential_vector(
    board: board_mod.Board,
) -> np.ndarray:
    """Build P(c) over all 64 cells for the multi-scale distance kernels
    (F14/F15/F16). Returns shape (64,) float64, read-only.

    v0.2.2 (T-20g fix #2a): this function is a thin adapter over the
    LRU-cached pure implementation. Cache key is
    `(_blocked_mask, _carpet_mask, opp_bit, own_bit)` — exactly the
    inputs that affect P(c). Cache holds up to 4 096 entries (~2 MB).
    """
    blocked = board._blocked_mask
    carpet = board._carpet_mask
    ox, oy = board.opponent_worker.position
    wx, wy = board.player_worker.position
    opp_bit = 1 << (oy * BOARD_SIZE + ox)
    own_bit = 1 << (wy * BOARD_SIZE + wx)
    return _cell_potential_vector_cached(blocked, carpet, opp_bit, own_bit)


def clear_p_vec_cache() -> None:
    """Reset the P-vec LRU cache. Useful between tests / fresh matches."""
    _cell_potential_vector_cached.cache_clear()


def p_vec_cache_info():
    """Return the LRU CacheInfo (hits, misses, maxsize, currsize)."""
    return _cell_potential_vector_cached.cache_info()


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


def _opp_roll_imminence(board: board_mod.Board) -> int:
    """F20 helper: longest run of PRIMED-or-SPACE cells in a cardinal
    direction from the opponent's worker position. This extends F8's
    already-primed-only signal by counting SPACE cells as "one prime
    step away from being rollable next turn", capturing looming threats
    where the opp has an empty corridor to set up in. Returns an int
    in [0, 7].

    Spec note (T-40b): team-lead's task description says "longest
    CARPET roll length in one ply" — but one ply = one action in the
    engine (SPEC §2), so the literal one-ply-from-current is exactly
    F8. F20 intentionally uses the strict superset PRIMED-or-SPACE so
    it provides signal when F8 is zero. If this interpretation needs
    revision, flip `_F20_INCLUDE_SPACE` below to False.

    Blockers: BLOCKED | CARPET | workers. (CARPET blocks because the
    opp can't PRIME an already-CARPET cell nor roll through it.)
    """
    ox, oy = board.opponent_worker.position
    blocked = board._blocked_mask
    carpet = board._carpet_mask
    pw_bit = 1 << (
        board.player_worker.position[1] * BOARD_SIZE
        + board.player_worker.position[0]
    )
    ow_bit = 1 << (oy * BOARD_SIZE + ox)
    workers = pw_bit | ow_bit
    blockers = (blocked | carpet | workers) & _FULL_MASK

    best = 0
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        k = 0
        nx, ny = ox + dx, oy + dy
        while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
            bit = 1 << (ny * BOARD_SIZE + nx)
            if blockers & bit:
                break
            k += 1
            if k == 7:
                break
            nx += dx
            ny += dy
        if k > best:
            best = k
    return best


def _prime_steal_bonus(board: board_mod.Board) -> float:
    """F22 helper: sum of `CARPET_POINTS_TABLE[k]` over horizontal + vertical
    primed lines of length k ≥ 2, restricted to those where our worker's
    Manhattan distance to the nearer endpoint is strictly less than opp
    worker's. Engine allows either player to CARPET any PRIMED line
    (SPEC §2.3, `is_cell_carpetable`), so a reachable primed line is a
    free steal opportunity — the feature rewards positioning to cash in.

    Attribution approximation (flagged in W_INIT comment): we don't
    know who primed which cell. All primed lines are candidates; if
    we're closer we get credit. For lines we primed ourselves, this
    still behaves correctly — rolling our own line is the intended
    action, and the feature value matches the expected carpet reward.

    Implementation:
    - Scan each primed cell that starts a maximal H or V primed run
      (previous cell in that direction is NOT primed).
    - Walk forward to determine k.
    - Only count lines with k ≥ 2 (k=1 = trap, not worth stealing).
    - For each endpoint of the line, compute our and opp Manhattan
      distance; use the NEAREST endpoint for the comparison.
    - If our_dist < opp_dist, add `_CARPET_VALUE[k]` to total.

    Per OPPONENT_EXPLOITS §T-40-EXPLOIT-1. Cost: O(64) over primed mask
    with early-terminated walks. Typical mid-game ~2-5 primed cells =
    2-5 iterations × 4 neighbor checks.
    """
    primed = board._primed_mask
    if primed == 0:
        return 0.0
    wx, wy = board.player_worker.position
    ox, oy = board.opponent_worker.position

    total = 0.0
    for dx, dy in ((1, 0), (0, 1)):  # E, S only — each line counted once
        for idx in range(_BOARD_CELLS):
            bit = 1 << idx
            if not (primed & bit):
                continue
            # Is this cell a LINE-START in (dx, dy)? i.e., the preceding
            # cell in (-dx, -dy) is NOT primed (or off-board).
            x = idx % BOARD_SIZE
            y = idx // BOARD_SIZE
            px, py = x - dx, y - dy
            if 0 <= px < BOARD_SIZE and 0 <= py < BOARD_SIZE:
                prev_bit = 1 << (py * BOARD_SIZE + px)
                if primed & prev_bit:
                    continue  # not a line-start; some earlier iteration
                              # will have processed this run
            # Walk forward to count length k.
            k = 1
            nx, ny = x + dx, y + dy
            while (
                0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE
                and (primed & (1 << (ny * BOARD_SIZE + nx)))
            ):
                k += 1
                nx += dx
                ny += dy
            if k < 2:
                continue  # k=1 not worth stealing
            # Line endpoints: (x, y) is start; end = (x + (k-1)*dx, y + (k-1)*dy).
            ex, ey = x + (k - 1) * dx, y + (k - 1) * dy
            # Distance from each worker to each endpoint; use the
            # *nearer* endpoint (maximizing steal-ability).
            our_a = abs(wx - x) + abs(wy - y)
            our_b = abs(wx - ex) + abs(wy - ey)
            opp_a = abs(ox - x) + abs(oy - y)
            opp_b = abs(ox - ex) + abs(oy - ey)
            our_min = our_a if our_a < our_b else our_b
            opp_min = opp_a if opp_a < opp_b else opp_b
            if our_min < opp_min:
                total += float(_CARPET_VALUE[k])
    return total


def _opp_mobility_denied_plus_adjacency(board: board_mod.Board) -> int:
    """F10 helper (T-40-EXPLOIT-2): combined mobility-denied + adjacency
    bonus per OPPONENT_EXPLOITS §T-40-EXPLOIT-2.

    Returns an integer count:
      base = count of cardinal-adjacent cells to OPP's worker that are
             PRIMED or CARPET (these restrict opp movement regardless
             of who laid them — opp can't step onto a PRIMED cell per
             SPEC §2.1 and we can walk through the resulting CARPET
             anyway, so the mobility-denied signal is ownership-
             agnostic).
      adjacency_bonus = count of primed-line endpoints (k ≥ 2) that are
             cardinal-adjacent to OUR worker. Signals "we are one plain
             step from being perfectly positioned to start rolling a
             primed line next turn" — tight coupling with F22's steal
             signal but distinct in that F22 rewards being NEAREST to
             an endpoint while F10-adj rewards being DIRECTLY ADJACENT.

    Returns `base + adjacency_bonus`, an integer typically in [0, 8].
    """
    primed = board._primed_mask
    carpet = board._carpet_mask
    ox, oy = board.opponent_worker.position
    wx, wy = board.player_worker.position

    # Part (a): base mobility-denied. Count PRIMED/CARPET cardinal
    # neighbors of opp worker.
    base = 0
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        nx, ny = ox + dx, oy + dy
        if not (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE):
            continue
        bit = 1 << (ny * BOARD_SIZE + nx)
        if (primed | carpet) & bit:
            base += 1

    # Part (b): adjacency to primed-line endpoints. Scan H + S as in
    # _prime_steal_bonus's line-start dedup; for each maximal primed
    # run of k ≥ 2, check both endpoints against our worker's cardinal
    # neighbors (Manhattan == 1).
    adjacency_bonus = 0
    if primed != 0:
        for dx, dy in ((1, 0), (0, 1)):
            for idx in range(_BOARD_CELLS):
                bit = 1 << idx
                if not (primed & bit):
                    continue
                x = idx % BOARD_SIZE
                y = idx // BOARD_SIZE
                # Line-start dedup
                px, py = x - dx, y - dy
                if 0 <= px < BOARD_SIZE and 0 <= py < BOARD_SIZE:
                    prev_bit = 1 << (py * BOARD_SIZE + px)
                    if primed & prev_bit:
                        continue
                # Walk forward
                k = 1
                nx, ny = x + dx, y + dy
                while (
                    0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE
                    and (primed & (1 << (ny * BOARD_SIZE + nx)))
                ):
                    k += 1
                    nx += dx
                    ny += dy
                if k < 2:
                    continue
                ex, ey = x + (k - 1) * dx, y + (k - 1) * dy
                # Test each endpoint against our worker's Manhattan-1.
                if abs(wx - x) + abs(wy - y) == 1:
                    adjacency_bonus += 1
                if abs(wx - ex) + abs(wy - ey) == 1:
                    adjacency_bonus += 1

    return base + adjacency_bonus


def _opp_wasted_primes(board: board_mod.Board) -> int:
    """F24 helper (T-40-EXPLOIT-3): mirror of F17 applied to OPP's
    reachable primes. Count primed cells that are (a) reachable by opp's
    worker before the game ends (Manhattan ≤ opp.turns_left), AND (b)
    isolated (no primed cardinal neighbor). These are "dead primes" on
    opp's side — they'll only roll as k=1 for −1 point.

    Same attribution approximation as F17 / F3 / F4 (engine doesn't track
    prime ownership). The signal is: "opp has paid +1 to prime cells that
    can at best return −1 by rolling as k=1". Albert/Carrie's simple
    heuristics likely miss this penalty, so the feature rewards positions
    where we've maneuvered them into wasteful priming.

    Returns int in [0, 64]. Typical mid-game 0-3.
    """
    primed = board._primed_mask
    if primed == 0:
        return 0
    ox, oy = board.opponent_worker.position
    opp_turns_left = int(board.opponent_worker.turns_left)

    count = 0
    for idx in range(_BOARD_CELLS):
        bit = 1 << idx
        if not (primed & bit):
            continue
        px = idx % BOARD_SIZE
        py = idx // BOARD_SIZE
        # Reachability from opp's worker
        if abs(px - ox) + abs(py - oy) > opp_turns_left:
            continue
        # Isolation check: any primed cardinal neighbor?
        has_primed_neighbor = False
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx, ny = px + dx, py + dy
            if not (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE):
                continue
            nbit = 1 << (ny * BOARD_SIZE + nx)
            if primed & nbit:
                has_primed_neighbor = True
                break
        if not has_primed_neighbor:
            count += 1
    return count


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


def _count_dead_primes(board: board_mod.Board) -> int:
    """F17 helper: count primed cells that are (a) reachable by our
    worker before game end, AND (b) isolated from other primes (no
    primed cardinal neighbor).

    "Reachable" = Manhattan distance from our worker to the primed cell
    ≤ `player_worker.turns_left`. "Isolated" = no UP/DOWN/LEFT/RIGHT
    neighbor is also PRIMED (such a cell can only be rolled as k=1 for
    −1 point, so it's a strict net loss given the +1 priming cost).

    Returns an int in [0, 64]. Typical mid-game value is 0-3.
    """
    primed = board._primed_mask
    if primed == 0:
        return 0
    wx, wy = board.player_worker.position
    turns_left = int(board.player_worker.turns_left)

    count = 0
    for idx in range(_BOARD_CELLS):
        bit = 1 << idx
        if not (primed & bit):
            continue
        px = idx % BOARD_SIZE
        py = idx // BOARD_SIZE
        # Reachability filter: Manhattan dist ≤ turns_left.
        if abs(px - wx) + abs(py - wy) > turns_left:
            continue
        # Isolation check: any primed cardinal neighbor?
        has_primed_neighbor = False
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx, ny = px + dx, py + dy
            if not (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE):
                continue
            nbit = 1 << (ny * BOARD_SIZE + nx)
            if primed & nbit:
                has_primed_neighbor = True
                break
        if not has_primed_neighbor:
            count += 1
    return count


def _opp_belief_entropy(
    board: board_mod.Board, belief_summary: BeliefSummary
) -> float:
    """F18 helper: entropy of the rat belief after absorbing the
    opponent's last SEARCH outcome.

    Behaviour per GAME_SPEC §5:
      - If opp's last ply was SEARCH @ loc and MISSED, the engine already
        respawns nothing but the opp *knows* loc is empty; we model the
        opp's posterior by zeroing `belief[loc]` and renormalising.
      - If opp searched and HIT, the rat was respawned (belief already
        reset to p_0 by rat_belief.handle_post_capture_reset); opp's
        belief collapses to the same p_0. We just return the current
        entropy.
      - If opp did not search, return `belief_summary.entropy` unchanged.

    This is a *one-ply* approximation. The engine exposes only the last
    opp-search via `board.opponent_search`; multi-ply history would need
    an agent-side tracker. Flagged as v0.4+ in the module docstring.

    Returns a scalar in [0, ln 64].
    """
    opp_search = board.opponent_search
    # opp_search is (loc or None, result_bool).
    if (
        opp_search is None
        or opp_search[0] is None
        or opp_search[1]  # hit — belief was reset; no miss-subtraction
    ):
        return float(belief_summary.entropy)

    loc = opp_search[0]
    # Validate bounds defensively.
    if not (
        isinstance(loc, tuple) and len(loc) == 2
        and 0 <= loc[0] < BOARD_SIZE and 0 <= loc[1] < BOARD_SIZE
    ):
        return float(belief_summary.entropy)

    b = belief_summary.belief
    miss_idx = loc[1] * BOARD_SIZE + loc[0]
    missed = float(b[miss_idx])
    remaining = 1.0 - missed
    if remaining <= 0.0:
        # Opp's miss is inconsistent with our belief (all mass was on
        # that cell). Fall back to current entropy rather than blow up.
        return float(belief_summary.entropy)
    # Renormalised miss-posterior: zero miss_idx, divide the rest by
    # `remaining`. Entropy = -Σ p' log p' where p' = b_i / remaining
    # for i != miss_idx.
    # Expand:
    #   entropy_new = -(1/rem) Σ_{i≠m} b_i · (log b_i - log rem)
    #               = -(1/rem) [S_excl - log(rem) · remaining]
    #               = log(rem) - S_excl / rem
    # where S_excl = Σ_{i≠m, b_i>0} b_i · log b_i.
    # Relate to the cached entropy: let S = Σ_i b_i log b_i = -entropy.
    # Then S_excl = S - b_m log b_m = -entropy - b_m log b_m.
    # (b_m log b_m is negative when 0 < b_m < 1, so subtracting it
    # raises S_excl above -entropy, as expected when we remove mass.)
    if missed > 0.0:
        s_excl = -float(belief_summary.entropy) - missed * np.log(missed)
    else:
        s_excl = -float(belief_summary.entropy)
    entropy_new = np.log(remaining) - s_excl / remaining
    if entropy_new < 0.0:  # guard against fp rounding at 0 boundary
        entropy_new = 0.0
    return float(entropy_new)


def features(
    board: board_mod.Board, belief_summary: BeliefSummary
) -> np.ndarray:
    """Compute the 19-feature vector (float64) from the perspective of
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

    # F14 / F15 / F16 — multi-scale distance-kernel superset per
    # CARRIE_DECONSTRUCTION §5. Build P(c) once (~256 ray scans), then
    # three BLAS dots with the precomputed decay rows.
    p_vec = _cell_potential_vector(board)
    worker_idx = wy * BOARD_SIZE + wx
    out[9] = float(np.dot(p_vec, _KERNEL_RECIP[worker_idx]))
    out[10] = float(np.dot(p_vec, _KERNEL_EXP[worker_idx]))
    out[11] = float(np.dot(p_vec, _KERNEL_STEP[worker_idx]))

    # F17 — priming-lockout: dead primes on our side of the board.
    out[12] = float(_count_dead_primes(board))

    # F18 — opp-belief proxy: entropy of the rat belief after opp's
    # last search outcome is absorbed. Pure Python, O(1) arithmetic
    # (no full 64-element copy).
    out[13] = _opp_belief_entropy(board, belief_summary)

    # F19 — rat-catch-threat-radius: prob-weighted fraction of belief
    # mass within Manhattan ≤ 2 of our worker. One BLAS dot over the
    # precomputed _NEAR2_MASK row for `worker_idx`.
    out[14] = float(np.dot(belief_summary.belief, _NEAR2_MASK[worker_idx]))

    # F20 — opp_roll_imminence: longest PRIMED-or-SPACE cardinal run
    # from the opponent's worker position. Strict superset of F8 (F8 =
    # PRIMED-only); see `_opp_roll_imminence` docstring for the
    # spec-interpretation note.
    out[15] = float(_opp_roll_imminence(board))

    # F22 — prime-steal bonus: sum over primed lines (k ≥ 2, H/V) of
    # CARPET_POINTS_TABLE[k] for lines where our worker is strictly
    # closer to the nearer endpoint than opp's worker. O(64) over the
    # primed mask with early terminations.
    out[16] = _prime_steal_bonus(board)

    # F10 — opp mobility denied + primed-endpoint-adjacency bonus
    # (T-40-EXPLOIT-2). Integer count, typically in [0, 8].
    out[17] = float(_opp_mobility_denied_plus_adjacency(board))

    # F24 — opp wasted primes: mirror of F17 applied to opp's reachable
    # primes (T-40-EXPLOIT-3). Integer count, typically in [0, 3].
    out[18] = float(_opp_wasted_primes(board))

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

    Time budget: p99 <= 250 us over 10k random boards at 16 features
    (v0.4 bumped from 200 us in T-40b for F19/F20 tail; see tests).
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


_NUMBA_WARMED: bool = False


def warm_numba_kernels() -> None:
    """Force AOT compile of the three numba kernels on a dummy input.

    Safe to call even when `_USE_NUMBA=False` (it becomes a no-op). The
    first `@njit(cache=True)` invocation takes ~1-2 s cold; subsequent
    runs hit the disk cache (`__pycache__/*.nbi`) and warm in < 10 ms.

    `Heuristic.__init__` invokes this once; calling it from agent
    `__init__` at init time (before the tournament clock starts) keeps
    first-turn latency low.
    """
    global _NUMBA_WARMED
    if _NUMBA_WARMED or not (_USE_NUMBA and _NUMBA_AVAILABLE):
        return
    zero = np.uint64(0)
    cp = _CARPET_VALUE
    # Trigger jit compilation of each kernel with representative args.
    _ray_reach_nb(zero, 0, 0, 1, 0)
    _cell_potential_for_worker_nb(zero, 0, 0, 7, 7, _LAMBDA, _BETA, cp)
    _cell_potential_vector_nb(zero, zero, np.uint64(1), np.uint64(2), cp)
    _NUMBA_WARMED = True


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
        # Warm jit on construction so the first `V_leaf` call doesn't
        # absorb a 1-2s compile during a tournament turn.
        warm_numba_kernels()

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
