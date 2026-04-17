"""HybridBot v0.1 — MCTS rollout + HMM-gated SEARCH.

Per ALT_ARCH_MCTS.md §6.2: the additive-edges hypothesis says HMM's
rat-capture channel and MCTS's long-horizon carpet-roll channel do not
overlap, so combining them should strictly beat either pure architecture.

Pipeline per turn:
    1. belief.update(board, sensor_data)  — canonical 4-step HMM filter
       (RattleBot module, verbatim).
    2. time_mgr.start_turn(board, time_left_fn, belief_summary)
       — adaptive per-turn budget; 0.5 s safety reserved here.
    3. SEARCH gate (3 conditions, copied from RattleBot v0.2):
           (a) max_mass > 1/3
           (b) entropy  < 0.75 * ln(64) ~= 3.122 nats
           (c) consec_search_misses <= 2
       If all hold → return Move.search(belief.argmax).
    4. Else → MCTS over MOVE-only (SEARCH excluded from the tree).
       Rollout: greedy-largest-k-carpet(>=2) → prime-toward-biggest-open
       → plain-toward-biggest-open. Depth 8.
       Determinization: rat-location samples drawn from belief.grid
       (real IS-MCTS, not MctsBot's uniform prior).

Post-own-SEARCH belief reconciliation (T-30e H-1 pattern from RattleBot):
on the turn after we searched, `board.player_search = (loc, hit)` tells
us whether the rat respawned (hit) or whether to zero that cell (miss).

All play() calls wrapped in try/except → falls through to a duplicated
FloorBot-style emergency fallback (D-006 isolation: duplicate, don't
cross-import).

D-006: the only files imported from RattleBot are rat_belief.py,
time_mgr.py, and types.py — and those were DUPLICATED into this folder,
not referenced, so that the submission zip of HybridBot is fully
self-contained.
"""

from __future__ import annotations

import math
import random
import time
from collections.abc import Callable
from typing import List, Optional, Tuple

import numpy as np

from game import board as board_mod
from game.enums import (
    BOARD_SIZE,
    Cell,
    Direction,
    MoveType,
    RAT_BONUS,
    RAT_PENALTY,
    loc_after_direction,
)
from game.move import Move

from .rat_belief import RatBelief
from .time_mgr import TimeManager
from .types import BeliefSummary


__all__ = ["PlayerAgent"]


# MCTS knobs — carried forward from MctsBot with the deliberate change
# that SEARCH is no longer in the tree so iterations-per-second should
# ~2x up.
_UCB_C: float = 1.2
_ROLLOUT_DEPTH: int = 8
_DIRECTIONS = (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT)

# SEARCH-gate constants (lifted from RattleBot v0.2 agent.py).
SEARCH_GATE_MAX_CONSEC_MISSES: int = 2
SEARCH_GATE_ENTROPY_CEIL: float = 0.75 * math.log(64.0)  # ~3.122 nats
SEARCH_GATE_MASS_FLOOR: float = 1.0 / 3.0


class _Node:
    """MCTS tree node. SEARCH moves NEVER appear in `move`/`untried`."""

    __slots__ = ("move", "parent", "children", "untried", "visits", "total_reward")

    def __init__(
        self,
        move: Optional[Move],
        parent: Optional["_Node"],
        untried: List[Move],
    ) -> None:
        self.move = move
        self.parent = parent
        self.children: List[_Node] = []
        self.untried: List[Move] = untried
        self.visits: int = 0
        self.total_reward: float = 0.0

    def ucb1(self, parent_visits: int, c: float) -> float:
        if self.visits == 0:
            return float("inf")
        exploit = self.total_reward / self.visits
        explore = c * math.sqrt(math.log(max(parent_visits, 1)) / self.visits)
        return exploit + explore

    def best_child(self, c: float) -> "_Node":
        pv = self.visits
        return max(self.children, key=lambda n: n.ucb1(pv, c))


def _reward_from_diff(diff: float) -> float:
    """Tanh-squash a point differential into [0, 1]."""
    return 0.5 + 0.5 * math.tanh(diff / 10.0)


def _filter_move_list(moves: List[Move]) -> List[Move]:
    """Drop SEARCH and k=1 CARPET from a move list."""
    out: List[Move] = []
    for m in moves:
        if m.move_type == MoveType.SEARCH:
            continue
        if m.move_type == MoveType.CARPET and m.roll_length == 1:
            continue
        out.append(m)
    return out


class PlayerAgent:
    """HybridBot primary agent — HMM belief + HMM-gated SEARCH + MCTS MOVE."""

    def __init__(
        self,
        board: board_mod.Board,
        transition_matrix=None,
        time_left: Callable = None,
    ):
        self._rng = random.Random(0xA1B0BA17)
        self._belief: Optional[RatBelief] = None
        self._time_mgr: Optional[TimeManager] = None
        self._init_ok: bool = False

        # SEARCH-gate bookkeeping (RattleBot v0.2 pattern).
        self._consec_search_misses: int = 0
        self._last_own_move_was_search: bool = False

        try:
            if transition_matrix is None:
                T = np.eye(BOARD_SIZE * BOARD_SIZE, dtype=np.float64)
            else:
                T = np.asarray(transition_matrix, dtype=np.float64)
            self._belief = RatBelief(T, board)
            self._time_mgr = TimeManager()
            self._init_ok = True
        except Exception:
            # Never raise out of __init__; emergency fallback still works.
            self._init_ok = False

    def commentate(self) -> str:
        return "HybridBot v0.1 — HMM-gated SEARCH + MCTS move rollouts."

    # ------------------------------------------------------------------
    # Top-level entry

    def play(
        self,
        board: board_mod.Board,
        sensor_data: Tuple,
        time_left: Callable,
    ) -> Move:
        if not self._init_ok:
            return self._emergency_fallback(board)
        try:
            return self._play_internal(board, sensor_data, time_left)
        except Exception:
            return self._emergency_fallback(board)

    # ------------------------------------------------------------------
    # Main pipeline

    def _play_internal(
        self,
        board: board_mod.Board,
        sensor_data: Tuple,
        time_left: Callable,
    ) -> Move:
        assert self._belief is not None
        assert self._time_mgr is not None

        # Reconcile own-search outcome with belief / consec-miss counter
        # BEFORE the canonical 4-step HMM update so the predict() steps
        # see the post-search belief.
        self._reconcile_own_search(board)

        belief_summary = self._belief.update(board, sensor_data)

        budget_s = self._time_mgr.start_turn(
            board, time_left, belief_summary,
        )

        # SEARCH gate — three conditions (copied from RattleBot v0.2).
        if self._gate_fires(belief_summary):
            move = self._gate_search_move(belief_summary)
            self._last_own_move_was_search = True
            self._time_mgr.end_turn(0.0)
            if self._looks_valid(board, move):
                return move
            # Fall through to MCTS if the gate move is somehow invalid
            # (should only happen if argmax is out of bounds — shouldn't).

        # MCTS over MOVE-only.
        move = self._mcts_choose(
            board,
            belief_summary,
            budget_s,
        )
        if move is None or not self._looks_valid(board, move):
            move = self._emergency_fallback(board)
        self._last_own_move_was_search = (
            int(move.move_type) == int(MoveType.SEARCH)
        )
        self._time_mgr.end_turn(0.0)
        return move

    # ------------------------------------------------------------------
    # SEARCH gate

    def _gate_fires(self, belief_summary: BeliefSummary) -> bool:
        if self._belief is None:
            return False
        return (
            belief_summary.max_mass > SEARCH_GATE_MASS_FLOOR
            and belief_summary.entropy < SEARCH_GATE_ENTROPY_CEIL
            and self._consec_search_misses <= SEARCH_GATE_MAX_CONSEC_MISSES
        )

    def _gate_search_move(self, belief_summary: BeliefSummary) -> Move:
        idx = int(belief_summary.argmax)
        x = idx % BOARD_SIZE
        y = idx // BOARD_SIZE
        return Move.search((x, y))

    def _reconcile_own_search(self, board: board_mod.Board) -> None:
        """Apply last-turn SEARCH outcome to belief and consec-miss counter.

        Mirrors RattleBot v0.2 `_update_consec_search_misses` (T-30e H-1).
        Runs BEFORE `belief.update()` so the canonical 4-step filter's
        predict steps see the post-search belief.
        """
        if not self._last_own_move_was_search:
            self._consec_search_misses = 0
            return
        try:
            loc, hit = board.player_search
        except Exception:
            self._consec_search_misses = 0
            return
        if loc is None:
            self._consec_search_misses = 0
            return
        if self._belief is not None:
            try:
                self._belief.apply_our_search(loc, bool(hit))
            except Exception:
                pass
        if hit:
            self._consec_search_misses = 0
        else:
            self._consec_search_misses += 1

    # ------------------------------------------------------------------
    # MCTS driver (MOVE-only; SEARCH never enters the tree)

    def _mcts_choose(
        self,
        board: board_mod.Board,
        belief_summary: BeliefSummary,
        budget_s: float,
    ) -> Optional[Move]:
        try:
            valid = board.get_valid_moves(exclude_search=True)
        except Exception:
            return None
        valid = _filter_move_list(valid)
        if not valid:
            # Only k=1-carpet or similar pathology; fall back to any
            # legal move below in the caller's emergency path.
            return None

        # Deadline: prefer time_mgr.remaining(), but also honour the
        # passed budget directly. Add a small safety inside MCTS on top
        # of time_mgr's 0.5 s reserve.
        t_start = time.perf_counter()
        deadline_rel = max(0.15, float(budget_s) - 0.1)

        # Determinization prior: current HMM belief. Pre-build cumulative
        # for fast sampling.
        prior = belief_summary.belief
        cum_prior = np.cumsum(prior)

        root = _Node(move=None, parent=None, untried=list(valid))
        iters = 0
        while (time.perf_counter() - t_start) < deadline_rel:
            # Early-stop if time_mgr thinks we're out of budget.
            try:
                if self._time_mgr is not None and self._time_mgr.should_stop():
                    break
            except Exception:
                pass

            rat_sample = self._sample_rat_cell(cum_prior)
            sim_board = board.get_copy()
            try:
                self._iteration(
                    sim_board, root, rat_sample, depth=_ROLLOUT_DEPTH
                )
            except Exception:
                pass
            iters += 1

        if not root.children:
            # No iteration completed — just take any valid move.
            return self._rng.choice(valid)
        # Robust child: most-visited, tie-break by mean reward.
        best = max(
            root.children,
            key=lambda n: (n.visits, n.total_reward / max(1, n.visits)),
        )
        return best.move

    # ------------------------------------------------------------------
    # One MCTS iteration

    def _iteration(
        self,
        sim_board,
        root: _Node,
        rat_sample: Tuple[int, int],
        depth: int,
    ) -> None:
        path: List[_Node] = [root]
        node = root
        is_us_to_move = True
        root_pts = sim_board.player_worker.get_points()
        opp_pts = sim_board.opponent_worker.get_points()

        # Selection
        while not node.untried and node.children:
            node = node.best_child(_UCB_C)
            path.append(node)
            ok = sim_board.apply_move(node.move, check_ok=False)
            if not ok or sim_board.is_game_over():
                break
            sim_board.reverse_perspective()
            is_us_to_move = not is_us_to_move

        # Expansion
        if not sim_board.is_game_over() and node.untried:
            mv = self._rng.choice(node.untried)
            node.untried.remove(mv)
            ok = sim_board.apply_move(mv, check_ok=False)
            if ok and not sim_board.is_game_over():
                sim_board.reverse_perspective()
                is_us_to_move = not is_us_to_move
                try:
                    next_moves = sim_board.get_valid_moves(exclude_search=True)
                except Exception:
                    next_moves = []
                next_moves = _filter_move_list(next_moves)
            else:
                next_moves = []
            child = _Node(move=mv, parent=node, untried=next_moves)
            node.children.append(child)
            path.append(child)
            node = child

        # Rollout
        if not sim_board.is_game_over():
            self._rollout(sim_board, depth, rat_sample)

        # Reward (root-player-POV point differential)
        cur_us = sim_board.player_worker.get_points()
        cur_them = sim_board.opponent_worker.get_points()
        if not is_us_to_move:
            cur_us, cur_them = cur_them, cur_us
        diff = (cur_us - cur_them) - (root_pts - opp_pts)
        reward = _reward_from_diff(diff)

        for n in path:
            n.visits += 1
            n.total_reward += reward

    # ------------------------------------------------------------------
    # Rollout policy (carpet-k>=2 → prime-run → plain-run)

    def _rollout(
        self,
        sim_board,
        depth: int,
        rat_sample: Tuple[int, int],
    ) -> None:
        for _ in range(depth):
            if sim_board.is_game_over():
                return
            try:
                moves = sim_board.get_valid_moves(exclude_search=True)
            except Exception:
                return
            if not moves:
                return
            mv = self._greedy_rollout_move(sim_board, moves)
            ok = sim_board.apply_move(mv, check_ok=False)
            if not ok or sim_board.is_game_over():
                return
            sim_board.reverse_perspective()

    def _greedy_rollout_move(self, sim_board, moves: List[Move]) -> Move:
        # (1) Biggest carpet roll >= 2.
        best_carpet: Optional[Move] = None
        best_k = 0
        for m in moves:
            if m.move_type == MoveType.CARPET and m.roll_length >= 2:
                if m.roll_length > best_k:
                    best_k = m.roll_length
                    best_carpet = m
        if best_carpet is not None:
            return best_carpet
        # (2) Prime toward biggest open run.
        primes = [m for m in moves if m.move_type == MoveType.PRIME]
        if primes:
            return self._toward_biggest_space(sim_board, primes)
        # (3) Plain toward biggest open run.
        plains = [m for m in moves if m.move_type == MoveType.PLAIN]
        if plains:
            return self._toward_biggest_space(sim_board, plains)
        return self._rng.choice(moves)

    def _toward_biggest_space(self, sim_board, cand: List[Move]) -> Move:
        start = sim_board.player_worker.get_location()
        best = cand[0]
        best_run = -1
        for m in cand:
            run = self._open_run_length(sim_board, start, m.direction)
            if run > best_run:
                best_run = run
                best = m
        return best

    def _open_run_length(self, sim_board, start, direction: Direction) -> int:
        cur = start
        n = 0
        for _ in range(BOARD_SIZE):
            nxt = loc_after_direction(cur, direction)
            if not sim_board.is_valid_cell(nxt):
                break
            if sim_board.is_cell_blocked(nxt):
                break
            n += 1
            cur = nxt
        return n

    # ------------------------------------------------------------------
    # Determinization sampling (real IS-MCTS via HMM posterior)

    def _sample_rat_cell(self, cum_prior: np.ndarray) -> Tuple[int, int]:
        r = self._rng.random()
        # np.searchsorted is ~O(log n); fine for n=64.
        idx = int(np.searchsorted(cum_prior, r, side="right"))
        if idx >= BOARD_SIZE * BOARD_SIZE:
            idx = BOARD_SIZE * BOARD_SIZE - 1
        return (idx % BOARD_SIZE, idx // BOARD_SIZE)

    # ------------------------------------------------------------------
    # Emergency fallback (duplicated from RattleBot / FloorBot)

    def _looks_valid(self, board: board_mod.Board, move: Move) -> bool:
        try:
            return bool(board.is_valid_move(move))
        except Exception:
            return False

    def _emergency_fallback(self, board: board_mod.Board) -> Move:
        """Crash-proof move picker. Never raises."""
        try:
            valid = board.get_valid_moves()
            if valid:
                safe = [
                    m for m in valid
                    if not (
                        m.move_type == MoveType.CARPET and m.roll_length == 1
                    )
                ]
                pick = (
                    self._rng.choice(safe) if safe
                    else self._rng.choice(valid)
                )
                if self._looks_valid(board, pick):
                    return pick
        except Exception:
            pass
        try:
            valid = board.get_valid_moves(exclude_search=False)
            if valid:
                return self._rng.choice(valid)
        except Exception:
            pass
        for d in _DIRECTIONS:
            try:
                m = Move.plain(d)
                if self._looks_valid(board, m):
                    return m
            except Exception:
                continue
        return Move.search((0, 0))
