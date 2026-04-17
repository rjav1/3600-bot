"""MctsBot — MCTS-based agent (contrarian probe vs RattleBot alpha-beta+HMM).

Design:
- UCB1 selection with tunable c.
- Expansion: one untried child per iteration (classic UCT).
- Rollout: greedy carpet-if-possible (k>=2), else prime toward biggest open
  space, else plain step. Depth-limited.
- Partial information: no HMM belief tracker. Rat location is sampled from
  a prior (uniform by default; short power-iteration of T if supplied) at
  the root of every iteration — poor-man's IS-MCTS. Rat belief emerges
  from tree visit statistics aggregated over many rat samples.
- Time: ~5 s per move hard cap, with a 0.3 s safety margin, subject to
  remaining total budget / turns_left.
- All play() calls wrapped in try/except; on any failure, returns a random
  valid move.
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


__all__ = ["PlayerAgent"]


_PER_MOVE_CAP_S = 5.0
_SAFETY_S = 0.3
_UCB_C = 1.2
_ROLLOUT_DEPTH = 8
_DIRECTIONS = (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT)


class _Node:
    __slots__ = ("move", "parent", "children", "untried", "visits", "total_reward")

    def __init__(self, move: Optional[Move], parent: Optional["_Node"], untried: List[Move]):
        self.move = move
        self.parent = parent
        self.children: List["_Node"] = []
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
    """Map a point differential into a [0,1] reward for MCTS backup."""
    # Tanh squash: 0.5 = even, >0.5 = winning. 10-pt lead → ~0.88.
    return 0.5 + 0.5 * math.tanh(diff / 10.0)


class PlayerAgent:
    def __init__(self, board, transition_matrix=None, time_left: Callable = None):
        self._rng = random.Random(0xCAFE1234)
        # Default uniform prior. If T is supplied, compute a short
        # power-iteration from (0,0) as a weak "approximate stationary"
        # prior. This is strictly weaker than a real HMM filter — no
        # per-turn Bayesian updating.
        self._prior = np.full(BOARD_SIZE * BOARD_SIZE, 1.0 / (BOARD_SIZE * BOARD_SIZE))
        if transition_matrix is not None:
            try:
                T = np.asarray(transition_matrix, dtype=np.float64)
                v = np.zeros(BOARD_SIZE * BOARD_SIZE)
                v[0] = 1.0
                for _ in range(64):
                    v = v @ T
                s = float(v.sum())
                if s > 0:
                    self._prior = v / s
            except Exception:
                pass

    def commentate(self):
        return "MctsBot: sampled the rat, rolled the carpet."

    # ------------------------------------------------------------------

    def play(self, board: board_mod.Board, sensor_data: Tuple, time_left: Callable):
        try:
            mv = self._mcts_choose(board, time_left)
            if mv is not None and board.is_valid_move(mv):
                return mv
        except Exception:
            pass
        return self._safe_fallback(board)

    # ------------------------------------------------------------------
    # MCTS driver

    def _mcts_choose(self, board: board_mod.Board, time_left: Callable) -> Optional[Move]:
        valid = board.get_valid_moves(exclude_search=False)
        if not valid:
            return None

        root_candidates = self._root_move_filter(valid)
        if not root_candidates:
            root_candidates = [
                m for m in valid
                if not (m.move_type == MoveType.CARPET and m.roll_length == 1)
            ] or valid

        # Budget: min(per-move cap, remaining_total / remaining_turns) - safety
        deadline_rel = _PER_MOVE_CAP_S
        try:
            remaining = float(time_left())
            turns_left = max(1, int(board.player_worker.turns_left))
            deadline_rel = min(_PER_MOVE_CAP_S, remaining / max(1, turns_left))
        except Exception:
            pass
        deadline_rel = max(0.15, deadline_rel - _SAFETY_S)
        t_start = time.perf_counter()

        root = _Node(move=None, parent=None, untried=list(root_candidates))

        iters = 0
        while (time.perf_counter() - t_start) < deadline_rel:
            rat_sample = self._sample_rat_cell()
            sim_board = board.get_copy()
            try:
                self._iteration(sim_board, root, rat_sample, depth=_ROLLOUT_DEPTH)
            except Exception:
                pass
            iters += 1

        if not root.children:
            return self._rng.choice(root_candidates)
        # Robust child: most-visited, break ties by mean reward.
        best = max(
            root.children,
            key=lambda n: (n.visits, n.total_reward / max(1, n.visits)),
        )
        return best.move

    # ------------------------------------------------------------------
    # One MCTS iteration (select -> expand -> rollout -> backprop)

    def _iteration(self, sim_board, root: _Node, rat_sample: Tuple[int, int], depth: int):
        path: List[_Node] = [root]
        node = root
        is_us_to_move = True  # the root player is "us"
        root_pts = sim_board.player_worker.get_points()
        opp_pts = sim_board.opponent_worker.get_points()

        # Selection
        while not node.untried and node.children:
            node = node.best_child(_UCB_C)
            path.append(node)
            ok = self._apply_move_with_search_reward(sim_board, node.move, rat_sample)
            if not ok or sim_board.is_game_over():
                break
            sim_board.reverse_perspective()
            is_us_to_move = not is_us_to_move

        # Expansion
        if not sim_board.is_game_over() and node.untried:
            mv = self._rng.choice(node.untried)
            node.untried.remove(mv)
            ok = self._apply_move_with_search_reward(sim_board, mv, rat_sample)
            if ok and not sim_board.is_game_over():
                sim_board.reverse_perspective()
                is_us_to_move = not is_us_to_move
                try:
                    next_moves = sim_board.get_valid_moves(exclude_search=False)
                except Exception:
                    next_moves = []
                next_moves = self._rollout_filter_moves(next_moves)
            else:
                next_moves = []
            child = _Node(move=mv, parent=node, untried=next_moves)
            node.children.append(child)
            path.append(child)
            node = child

        # Rollout
        if not sim_board.is_game_over():
            self._rollout(sim_board, depth, rat_sample)

        # Reward from root-player's POV
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
    # Rollout policy

    def _rollout(self, sim_board, depth: int, rat_sample: Tuple[int, int]):
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
            ok = self._apply_move_with_search_reward(sim_board, mv, rat_sample)
            if not ok or sim_board.is_game_over():
                return
            sim_board.reverse_perspective()

    def _greedy_rollout_move(self, sim_board, moves: List[Move]) -> Move:
        # (1) carpet with k>=2: take the largest
        best_k = 0
        best_carpet: Optional[Move] = None
        for m in moves:
            if m.move_type == MoveType.CARPET and m.roll_length >= 2:
                if m.roll_length > best_k:
                    best_k = m.roll_length
                    best_carpet = m
        if best_carpet is not None:
            return best_carpet

        # (2) prime toward biggest open space
        primes = [m for m in moves if m.move_type == MoveType.PRIME]
        if primes:
            return self._toward_biggest_space(sim_board, primes)

        # (3) plain step
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
    # Move application — apply_move does NOT award SEARCH points; do it here.

    def _apply_move_with_search_reward(
        self, sim_board, mv: Move, rat_sample: Tuple[int, int]
    ) -> bool:
        if mv.move_type == MoveType.SEARCH:
            hit = mv.search_loc == rat_sample
            ok = sim_board.apply_move(mv, check_ok=False)
            if not ok:
                return False
            # sim_board.player_worker is still the searcher (apply_move
            # doesn't reverse perspective). Credit points now.
            if hit:
                sim_board.player_worker.increment_points(RAT_BONUS)
            else:
                sim_board.player_worker.decrement_points(RAT_PENALTY)
            return True
        return sim_board.apply_move(mv, check_ok=False)

    # ------------------------------------------------------------------
    # Candidate pruning

    def _root_move_filter(self, valid: List[Move]) -> List[Move]:
        # Drop k=1 rolls (-1 pt) and all but top-2 SEARCH cells by prior.
        top_cells = set(
            sorted(
                range(BOARD_SIZE * BOARD_SIZE),
                key=lambda i: -float(self._prior[i]),
            )[:2]
        )
        out: List[Move] = []
        for m in valid:
            if m.move_type == MoveType.CARPET and m.roll_length == 1:
                continue
            if m.move_type == MoveType.SEARCH:
                ix = m.search_loc[1] * BOARD_SIZE + m.search_loc[0]
                if ix not in top_cells:
                    continue
                # Under uniform prior, P=1/64 — expected value deeply
                # negative. Only let SEARCH enter the tree if prior mass
                # on that cell > 1/8 (eightfold concentration).
                if float(self._prior[ix]) < 1.0 / 8.0:
                    continue
            out.append(m)
        return out

    def _rollout_filter_moves(self, valid: List[Move]) -> List[Move]:
        top_cells = set(
            sorted(
                range(BOARD_SIZE * BOARD_SIZE),
                key=lambda i: -float(self._prior[i]),
            )[:2]
        )
        out: List[Move] = []
        for m in valid:
            if m.move_type == MoveType.CARPET and m.roll_length == 1:
                continue
            if m.move_type == MoveType.SEARCH:
                ix = m.search_loc[1] * BOARD_SIZE + m.search_loc[0]
                if ix not in top_cells:
                    continue
                if float(self._prior[ix]) < 1.0 / 8.0:
                    continue
            out.append(m)
        return out

    # ------------------------------------------------------------------
    # Rat sampling (poor-man's IS-MCTS)

    def _sample_rat_cell(self) -> Tuple[int, int]:
        r = self._rng.random()
        cum = 0.0
        prior = self._prior
        n = len(prior)
        for i in range(n):
            cum += float(prior[i])
            if r < cum:
                return (i % BOARD_SIZE, i // BOARD_SIZE)
        return (0, 0)

    # ------------------------------------------------------------------
    # Emergency fallback

    def _safe_fallback(self, board: board_mod.Board) -> Move:
        try:
            valid = board.get_valid_moves(exclude_search=False)
            if valid:
                safe = [
                    m for m in valid
                    if not (m.move_type == MoveType.CARPET and m.roll_length == 1)
                    and m.move_type != MoveType.SEARCH
                ]
                pick = self._rng.choice(safe) if safe else self._rng.choice(valid)
                if board.is_valid_move(pick):
                    return pick
        except Exception:
            pass
        for d in _DIRECTIONS:
            try:
                m = Move.plain(d)
                if board.is_valid_move(m):
                    return m
            except Exception:
                continue
        return Move.search((0, 0))
