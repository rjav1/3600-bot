"""Rollout-based planner — 2-ply lookahead + biased Monte Carlo playouts.

Per CONTRARIAN_APR18 §3 "Bold Swing":
  - At root: enumerate our legal moves (filtered by move_gen — k=1 carpet
    dropped unless forced).
  - For each root move, forecast; then enumerate opp's top-N greedy moves
    (N=3). Forecast again for each (our, opp) pair.
  - From the resulting state, run K biased rollouts of depth D plies.
    Each rollout plays both sides greedy-with-noise, advances belief via
    T each ply, and accumulates per-side point deltas.
  - Value(our_move) = min over opp_moves of mean(rollout_score_diff).
  - Pick argmax(value).

Budget:
  - Target 200-400 rollouts/turn, 2-4s wall. time_left() is consulted
    between rollouts so we can cut short safely.

Perspective convention:
  - The engine hands us a board where `player_worker` is us. We maintain
    "ours vs opp" scoring ourselves (diff = our_points - opp_points).
  - Inside a rollout we alternately play us/opp; `reverse_perspective()`
    is called between plies so the side-to-move is always the
    `player_worker` of the local board.

Fallback:
  - Any exception in planning → greedy immediate_delta pick. Never crash.
"""

from __future__ import annotations

import math
import random
import time
from typing import Callable, List, Optional, Tuple

import numpy as np

from game import board as board_mod
from game.enums import (
    BOARD_SIZE,
    CARPET_POINTS_TABLE,
    Cell,
    MoveType,
    Noise,
)
from game.move import Move

from .move_gen import ordered_moves, immediate_delta

__all__ = ["RolloutPlanner", "plan_move"]


_N_CELLS = BOARD_SIZE * BOARD_SIZE
_MT_CARPET = int(MoveType.CARPET)
_MT_PRIME = int(MoveType.PRIME)
_MT_PLAIN = int(MoveType.PLAIN)
_MT_SEARCH = int(MoveType.SEARCH)

# Tunable knobs — conservative defaults, can be overridden per-call.
DEFAULT_TOP_N_OPP: int = 3
DEFAULT_ROLLOUT_DEPTH: int = 10         # plies total within a rollout
DEFAULT_MAX_ROLLOUTS_PER_PAIR: int = 15
DEFAULT_MIN_ROLLOUTS_PER_PAIR: int = 3
DEFAULT_TIME_FRAC_FOR_ROLLOUTS: float = 0.85   # leave 15% headroom
DEFAULT_SAFETY_S: float = 0.3


def _is_k1_carpet(m: Move) -> bool:
    return int(m.move_type) == _MT_CARPET and m.roll_length < 2


def _opp_candidate_moves(
    board: board_mod.Board, top_n: int
) -> List[Move]:
    """Return up to top_n of the opponent's best greedy moves from
    `board` (post-our-move, opponent now to move after reverse).

    NOTE: caller must have already called `board.reverse_perspective()`
    so that `board.player_worker` is now the opponent. This lets us
    reuse `board.get_valid_moves()` without re-implementing the 'enemy'
    path.
    """
    try:
        legal = board.get_valid_moves(exclude_search=True)
    except Exception:
        return []
    if not legal:
        return []
    # Drop k=1 carpets unless forced (mirror move_gen.py).
    has_non_k1 = any(not _is_k1_carpet(m) for m in legal)
    if has_non_k1:
        legal = [m for m in legal if not _is_k1_carpet(m)]
    # Sort by immediate_delta desc (greedy). Tie-break stable.
    scored = sorted(legal, key=lambda m: -immediate_delta(m))
    return scored[: max(1, top_n)]


def _choose_greedy_with_noise(
    board: board_mod.Board,
    rng: random.Random,
    temperature: float = 0.7,
) -> Optional[Move]:
    """Pick a legal move weighted by immediate point delta + noise.

    Returns None if no legal move. SEARCH is excluded inside rollouts —
    rollouts don't sample the true rat position, so SEARCH in-rollout
    can't be scored meaningfully without much more plumbing.
    """
    try:
        legal = board.get_valid_moves(exclude_search=True)
    except Exception:
        return None
    if not legal:
        return None
    has_non_k1 = any(not _is_k1_carpet(m) for m in legal)
    if has_non_k1:
        legal = [m for m in legal if not _is_k1_carpet(m)]
    # Softmax on immediate_delta with small noise. Temperature 0.7:
    # 4-point move is ~exp(4/0.7)=~313x more likely than 0-point one, so
    # effectively greedy but with nonzero exploration.
    deltas = [immediate_delta(m) for m in legal]
    mx = max(deltas)
    weights = [math.exp((d - mx) / max(temperature, 1e-3)) for d in deltas]
    tot = sum(weights)
    if tot <= 0:
        return rng.choice(legal)
    r = rng.random() * tot
    acc = 0.0
    for m, w in zip(legal, weights):
        acc += w
        if r <= acc:
            return m
    return legal[-1]


def _apply_move_safe(
    board: board_mod.Board, move: Move
) -> Optional[board_mod.Board]:
    """Return board after move applied (on a copy), or None on failure."""
    try:
        nxt = board.forecast_move(move, check_ok=False)
    except Exception:
        return None
    return nxt


def _points_of_move(move: Move) -> int:
    """Immediate point delta for the side that played it."""
    mt = int(move.move_type)
    if mt == _MT_CARPET:
        return CARPET_POINTS_TABLE.get(move.roll_length, 0)
    if mt == _MT_PRIME:
        return 1
    return 0


class RolloutPlanner:
    """2-ply lookahead + Monte Carlo rollouts."""

    def __init__(
        self,
        rng: Optional[random.Random] = None,
        top_n_opp: int = DEFAULT_TOP_N_OPP,
        rollout_depth: int = DEFAULT_ROLLOUT_DEPTH,
        min_rollouts_per_pair: int = DEFAULT_MIN_ROLLOUTS_PER_PAIR,
        max_rollouts_per_pair: int = DEFAULT_MAX_ROLLOUTS_PER_PAIR,
        time_frac: float = DEFAULT_TIME_FRAC_FOR_ROLLOUTS,
        safety_s: float = DEFAULT_SAFETY_S,
    ) -> None:
        self._rng = rng or random.Random(0xC0FFEE)
        self._top_n_opp = top_n_opp
        self._rollout_depth = rollout_depth
        self._min_rollouts = min_rollouts_per_pair
        self._max_rollouts = max_rollouts_per_pair
        self._time_frac = time_frac
        self._safety_s = safety_s

    # ------------------------------------------------------------------
    # Public entry

    def plan(
        self,
        board: board_mod.Board,
        belief_vec: np.ndarray,
        T: np.ndarray,
        time_left: Callable[[], float],
        budget_s: Optional[float] = None,
    ) -> Optional[Move]:
        """Return the best root move, or None if planning failed.

        Parameters:
            board: our-perspective Board.
            belief_vec: (64,) float64 rat posterior at root.
            T: (64, 64) rat transition matrix.
            time_left: callable returning seconds remaining this turn.
            budget_s: optional explicit budget. If None, consume
                `time_frac * time_left()` when rollouts start.
        """
        t_start = time.monotonic()

        # Root legal moves — use move_gen so k=1 is auto-filtered.
        try:
            root_moves = ordered_moves(board, exclude_search=True)
        except Exception:
            return None
        if not root_moves:
            return None

        # Determine available wall budget.
        try:
            tl = float(time_left()) if time_left is not None else 4.0
        except Exception:
            tl = 4.0
        total_budget = max(0.1, tl - self._safety_s)
        if budget_s is not None:
            total_budget = min(total_budget, max(0.1, float(budget_s)))

        # First pass: score each root move via rollouts against top-N opp.
        # Budget is split roughly evenly per root move, per opp reply.
        if len(root_moves) == 0:
            return None

        per_root_budget = total_budget / float(len(root_moves))
        best_move = root_moves[0]
        best_value = -math.inf

        for rm in root_moves:
            # Check for hard cutoff — never starve the final turn.
            if time_left is not None:
                try:
                    if float(time_left()) <= self._safety_s:
                        break
                except Exception:
                    pass

            val = self._score_root_move(
                board=board,
                root_move=rm,
                belief_vec=belief_vec,
                T=T,
                time_left=time_left,
                per_move_budget=per_root_budget,
            )
            if val is None:
                continue
            if val > best_value:
                best_value = val
                best_move = rm

        return best_move

    # ------------------------------------------------------------------
    # Internals

    def _score_root_move(
        self,
        board: board_mod.Board,
        root_move: Move,
        belief_vec: np.ndarray,
        T: np.ndarray,
        time_left: Callable[[], float],
        per_move_budget: float,
    ) -> Optional[float]:
        """Return min_{opp_reply} mean_rollout_score_diff.

        Returns None if the root move is somehow illegal or the forecast
        fails.
        """
        our_pts_before = int(board.player_worker.get_points())
        opp_pts_before = int(board.opponent_worker.get_points())

        # Apply our root move. If it's SEARCH, we can't resolve the
        # rat-caught outcome inside forecast (engine-side). Give SEARCH a
        # cheap proxy value and fall through to normal rollout flow.
        after_our = _apply_move_safe(board, root_move)
        if after_our is None:
            return None

        # Our immediate delta (recorded directly — points update inside
        # apply_move for PRIME/CARPET via worker.increment_points).
        our_immediate = (
            int(after_our.player_worker.get_points()) - our_pts_before
        )
        # SEARCH EV approximation against frozen root belief: +4 * p(cell)
        # − 2 * (1 − p(cell)).
        search_ev_bonus = 0.0
        if int(root_move.move_type) == _MT_SEARCH:
            loc = root_move.search_loc
            if loc is not None:
                idx = loc[1] * BOARD_SIZE + loc[0]
                if 0 <= idx < _N_CELLS:
                    p_here = float(belief_vec[idx])
                    search_ev_bonus = 4.0 * p_here - 2.0 * (1.0 - p_here)

        # Advance belief by one T-step (rat moved during our ply).
        post_our_belief = belief_vec @ T
        s = post_our_belief.sum()
        if s > 1e-18:
            post_our_belief = post_our_belief / s

        # Now perspective-swap: opponent is to move.
        after_our.reverse_perspective()
        opp_candidates = _opp_candidate_moves(after_our, self._top_n_opp)
        if not opp_candidates:
            # Opp has no legal moves — this is effectively a win (or
            # close). Run a single rollout from `after_our` reverted to
            # our perspective after one T-step.
            after_our.reverse_perspective()
            return float(
                our_immediate + search_ev_bonus + self._rollout_value(
                    after_our,
                    post_our_belief,
                    T,
                    side_to_move_is_us=False,
                    depth=self._rollout_depth,
                    rng=self._rng,
                )
            )

        # Split the per-move budget across opp candidates.
        per_opp_budget = per_move_budget / float(len(opp_candidates))
        worst_mean = math.inf  # min over opp replies

        for opp_m in opp_candidates:
            if time_left is not None:
                try:
                    if float(time_left()) <= self._safety_s:
                        break
                except Exception:
                    pass

            # Apply opp move, then advance belief one T-step (rat moves
            # during opp's ply too), then swap back to our perspective.
            after_opp = _apply_move_safe(after_our, opp_m)
            if after_opp is None:
                continue

            opp_immediate = (
                int(after_opp.player_worker.get_points())
                - int(after_our.player_worker.get_points())
            )  # note: after reverse, player_worker == opp

            post_opp_belief = post_our_belief @ T
            s2 = post_opp_belief.sum()
            if s2 > 1e-18:
                post_opp_belief = post_opp_belief / s2

            # Perspective back to us — after_opp.player_worker currently
            # is opp; we want it to be us for the rollout body.
            after_opp.reverse_perspective()

            # Budget the rollouts for this (our, opp) pair.
            n_rollouts, mean_val = self._rollout_loop(
                board=after_opp,
                belief_vec=post_opp_belief,
                T=T,
                time_left=time_left,
                budget_s=per_opp_budget,
                side_to_move_is_us=True,
                depth=self._rollout_depth,
            )
            if n_rollouts == 0:
                # No budget; fall back to immediate delta only.
                mean_val = 0.0

            # score diff so far = our_immediate + search_ev - opp_immediate
            # + mean(rollout tail)
            total = (
                float(our_immediate)
                + float(search_ev_bonus)
                - float(opp_immediate)
                + float(mean_val)
            )
            if total < worst_mean:
                worst_mean = total

        if worst_mean == math.inf:
            # Every opp forecast failed — fall back to just root immediate.
            return float(our_immediate + search_ev_bonus)
        return float(worst_mean)

    def _rollout_loop(
        self,
        board: board_mod.Board,
        belief_vec: np.ndarray,
        T: np.ndarray,
        time_left: Callable[[], float],
        budget_s: float,
        side_to_move_is_us: bool,
        depth: int,
    ) -> Tuple[int, float]:
        """Run multiple rollouts from `board`, returning (n, mean_diff)."""
        t_start = time.monotonic()
        total = 0.0
        n = 0
        # Always do at least `_min_rollouts` (cheap) unless we run out of
        # time very hard.
        while n < self._max_rollouts:
            if n >= self._min_rollouts:
                # Budget check after min batch.
                if (time.monotonic() - t_start) >= budget_s:
                    break
                if time_left is not None:
                    try:
                        if float(time_left()) <= self._safety_s:
                            break
                    except Exception:
                        pass
            v = self._rollout_value(
                board=board,
                belief_vec=belief_vec,
                T=T,
                side_to_move_is_us=side_to_move_is_us,
                depth=depth,
                rng=self._rng,
            )
            total += v
            n += 1
        if n == 0:
            return 0, 0.0
        return n, total / float(n)

    def _rollout_value(
        self,
        board: board_mod.Board,
        belief_vec: np.ndarray,
        T: np.ndarray,
        side_to_move_is_us: bool,
        depth: int,
        rng: random.Random,
    ) -> float:
        """One biased-greedy playout. Returns our_points - opp_points
        accumulated across the rollout plies (NOT absolute scores — we
        only measure the delta produced by the rollout body).
        """
        # Work on a local copy so we don't mutate caller state.
        sim = board.get_copy()
        our_gain = 0.0
        opp_gain = 0.0
        # Track perspective: initially `sim.player_worker` is "us" if
        # side_to_move_is_us is False (we flipped back after opp move).
        # Actually — when `side_to_move_is_us=True`, the side to move IS
        # us. The planner sets this up via reverse_perspective().
        is_us_turn = side_to_move_is_us
        belief = belief_vec

        for _ in range(depth):
            if sim.is_game_over():
                break
            # Side-to-move is `sim.player_worker` because the engine's
            # perspective convention. Pick a move.
            mv = _choose_greedy_with_noise(sim, rng)
            if mv is None:
                # No legal non-search move — fall back to any valid
                # (including SEARCH); if still nothing, stop rollout.
                try:
                    any_legal = sim.get_valid_moves(exclude_search=False)
                except Exception:
                    any_legal = []
                if not any_legal:
                    break
                mv = any_legal[0]

            # Apply move.
            mv_pts = _points_of_move(mv)
            nxt = _apply_move_safe(sim, mv)
            if nxt is None:
                # Illegal somehow — bail.
                break
            # Credit the gain to the right side.
            if is_us_turn:
                our_gain += float(mv_pts)
            else:
                opp_gain += float(mv_pts)

            # Swap perspective and advance belief (rat moves between
            # plies).
            nxt.reverse_perspective()
            belief = belief @ T
            s = belief.sum()
            if s > 1e-18:
                belief = belief / s

            sim = nxt
            is_us_turn = not is_us_turn

        return our_gain - opp_gain


def plan_move(
    board: board_mod.Board,
    belief_vec: np.ndarray,
    T: np.ndarray,
    time_left: Callable[[], float],
    rng: Optional[random.Random] = None,
    budget_s: Optional[float] = None,
) -> Optional[Move]:
    """Convenience wrapper — build a default planner and invoke it."""
    planner = RolloutPlanner(rng=rng)
    return planner.plan(
        board=board,
        belief_vec=belief_vec,
        T=T,
        time_left=time_left,
        budget_s=budget_s,
    )
