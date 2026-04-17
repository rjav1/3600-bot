"""Alpha-beta + iterative deepening + Zobrist TT for RattleBot v0.1.

Per BOT_STRATEGY.md v1.1 §2.a / §2.d / §2.f / §2.g / §3.3.
Belief is a leaf potential (D-004); SEARCH is root-only (D-011 item 2).
v0.1 uses `board.forecast_move(...)` + `reverse_perspective()` for child
generation. Time safety margin: 0.5 s (D-011 item 4).
"""

from __future__ import annotations

import math
import time as _time
from typing import Callable, Dict, List, Optional, Tuple

from game.enums import MoveType
from game.move import Move

from .move_gen import ordered_moves
from .types import (
    BeliefSummary, MoveKey, TTEntry,
    TT_FLAG_EXACT, TT_FLAG_LOWER, TT_FLAG_UPPER,
)
from .zobrist import Zobrist, move_key

__all__ = ["Search", "SearchEngine", "MATE_SCORE", "DRAW_SCORE", "MAX_DEPTH"]


MATE_SCORE: float = 1e9
DRAW_SCORE: float = 0.0
MAX_DEPTH: int = 32
_TIME_CHECK_EVERY = 1024


class _TimeUp(Exception):
    """Internal signal -- caught by `iterative_deepen`."""


class Search:
    """Alpha-beta + iterative deepening + two-slot Zobrist TT.

    TT: slot 0 depth-preferred, slot 1 always-replace. Both probed on hit.
    """

    def __init__(
        self,
        zobrist: Optional[Zobrist] = None,
        tt_size: int = 1 << 20,
        gamma_info: float = 0.5,
        gamma_reset: float = 0.3,
        eps_tiebreak: float = 0.25,
    ) -> None:
        self.zobrist = zobrist if zobrist is not None else Zobrist()
        if tt_size <= 0 or (tt_size & (tt_size - 1)) != 0:
            p = 1
            while p < max(1, tt_size):
                p <<= 1
            tt_size = p
        self.tt_size = tt_size
        self.tt_mask = tt_size - 1
        self.tt: List[List[Optional[TTEntry]]] = [
            [None, None] for _ in range(tt_size)
        ]
        self.tt_probes = 0
        self.tt_hits = 0
        self.tt_cutoffs = 0
        self.nodes = 0
        self.leaves = 0

        self.gamma_info = float(gamma_info)
        self.gamma_reset = float(gamma_reset)
        self.eps_tiebreak = float(eps_tiebreak)

        self.killers: List[List[Optional[MoveKey]]] = [
            [None, None] for _ in range(MAX_DEPTH + 1)
        ]
        self.history: Dict[MoveKey, int] = {}

        self._deadline: float = float("inf")
        self._eval_fn: Optional[Callable[..., float]] = None
        self._root_belief: Optional[BeliefSummary] = None

    # -- TT ------------------------------------------------------------

    def reset_tt(self) -> None:
        for bucket in self.tt:
            bucket[0] = None
            bucket[1] = None
        self.tt_probes = self.tt_hits = self.tt_cutoffs = 0

    def _probe_tt(self, key: int) -> Optional[TTEntry]:
        self.tt_probes += 1
        bucket = self.tt[key & self.tt_mask]
        for slot in bucket:
            if slot is not None and slot.zobrist_key == key:
                self.tt_hits += 1
                return slot
        return None

    def _store_tt(self, key, depth, value, flag, best_move, age):
        entry = TTEntry(
            zobrist_key=key, depth=depth, value=float(value),
            flag=flag, best_move=best_move, age=age,
        )
        bucket = self.tt[key & self.tt_mask]
        slot0 = bucket[0]
        if slot0 is None or depth >= slot0.depth:
            bucket[0] = entry
        bucket[1] = entry

    # -- time ----------------------------------------------------------

    def _time_check(self) -> None:
        if _time.perf_counter() >= self._deadline:
            raise _TimeUp()

    # -- iterative deepening ------------------------------------------

    def iterative_deepen(
        self,
        board,
        belief: BeliefSummary,
        eval_fn: Callable[..., float],
        time_left_s: float,
        safety_s: float = 0.5,
    ) -> Move:
        """Iteratively deepen until time runs out; return the best non-SEARCH
        move from the deepest completed iteration.
        """
        self._root_belief = belief
        self._eval_fn = eval_fn
        start = _time.perf_counter()
        budget = max(0.0, float(time_left_s) - float(safety_s))
        self._deadline = start + budget

        legal = ordered_moves(board, exclude_search=True)
        if not legal:
            legal = board.get_valid_moves(exclude_search=False)
            if not legal:
                return Move.search((0, 0))
            return legal[0]

        best_move: Move = legal[0]
        self.nodes = 0
        self.leaves = 0

        for depth in range(1, MAX_DEPTH + 1):
            try:
                _, move = self._root_search(board, depth, legal, best_move)
                best_move = move
                legal = self._reorder_pv_first(legal, move)
            except _TimeUp:
                break
            if _time.perf_counter() >= self._deadline:
                break
        return best_move

    def _reorder_pv_first(self, legal: List[Move], pv: Move) -> List[Move]:
        pv_k = move_key(pv)
        out = [m for m in legal if move_key(m) == pv_k]
        out.extend(m for m in legal if move_key(m) != pv_k)
        return out

    def _root_search(self, board, depth, legal, prev_best):
        alpha = -MATE_SCORE
        beta = MATE_SCORE
        best_val = -MATE_SCORE
        best_move: Move = prev_best

        root_key = self.zobrist.hash(board)
        tt_entry = self._probe_tt(root_key)
        hash_mk = tt_entry.best_move if tt_entry else None
        ordered = ordered_moves(
            board, hash_move=hash_mk, killers=self.killers[depth],
            history=self.history, exclude_search=True,
        )
        if not ordered:
            ordered = legal

        age = board.turn_count
        for mv in ordered:
            child = board.forecast_move(mv, check_ok=False)
            if child is None:
                continue
            child.reverse_perspective()
            v = -self._alphabeta(child, depth - 1, -beta, -alpha, 1)
            if v > best_val:
                best_val = v
                best_move = mv
                if v > alpha:
                    alpha = v

        self._store_tt(root_key, depth, best_val, TT_FLAG_EXACT,
                       move_key(best_move), age)
        return best_val, best_move

    # -- alpha-beta (negamax) -----------------------------------------

    def _alphabeta(self, board, depth, alpha, beta, ply_from_root):
        self.nodes += 1
        if (self.nodes & (_TIME_CHECK_EVERY - 1)) == 0:
            self._time_check()

        if board.is_game_over():
            return self._terminal_value(board)
        if depth <= 0:
            self.leaves += 1
            return self._eval_leaf(board)

        alpha0 = alpha
        key = self.zobrist.hash(board)
        tt_entry = self._probe_tt(key)
        hash_mk: Optional[MoveKey] = None
        if tt_entry is not None:
            hash_mk = tt_entry.best_move
            if tt_entry.depth >= depth:
                v = tt_entry.value
                f = tt_entry.flag
                if f == TT_FLAG_EXACT:
                    return v
                if f == TT_FLAG_LOWER and v > alpha:
                    alpha = v
                elif f == TT_FLAG_UPPER and v < beta:
                    beta = v
                if alpha >= beta:
                    self.tt_cutoffs += 1
                    return v

        killers_here = (
            self.killers[depth] if 0 <= depth < len(self.killers) else None
        )
        ordered = ordered_moves(
            board, hash_move=hash_mk, killers=killers_here,
            history=self.history, exclude_search=True,
        )
        assert all(
            m.move_type != MoveType.SEARCH for m in ordered
        ), "SEARCH must never enter the in-tree move list"

        if not ordered:
            self.leaves += 1
            return self._eval_leaf(board)

        best_val = -MATE_SCORE
        best_mk: Optional[MoveKey] = None
        for mv in ordered:
            child = board.forecast_move(mv, check_ok=False)
            if child is None:
                continue
            child.reverse_perspective()
            v = -self._alphabeta(child, depth - 1, -beta, -alpha, ply_from_root + 1)
            if v > best_val:
                best_val = v
                best_mk = move_key(mv)
            if v > alpha:
                alpha = v
            if alpha >= beta:
                mk = move_key(mv)
                if killers_here is not None and killers_here[0] != mk:
                    killers_here[1] = killers_here[0]
                    killers_here[0] = mk
                self.history[mk] = self.history.get(mk, 0) + depth * depth
                break

        if best_val <= alpha0:
            flag = TT_FLAG_UPPER
        elif best_val >= beta:
            flag = TT_FLAG_LOWER
        else:
            flag = TT_FLAG_EXACT
        self._store_tt(key, depth, best_val, flag, best_mk, board.turn_count)
        return best_val

    # -- leaf / terminal ----------------------------------------------

    def _eval_leaf(self, board) -> float:
        fn = self._eval_fn
        bs = self._root_belief
        if fn is None:
            return _point_diff(board)
        try:
            return float(fn(board, bs))
        except TypeError:
            return float(fn(board))

    def _terminal_value(self, board) -> float:
        return _point_diff(board)

    # -- root SEARCH-vs-non-SEARCH gate -------------------------------

    def root_search_decision(
        self,
        board,
        belief: BeliefSummary,
        eval_fn: Callable[..., float],
        time_budget_s: float,
        safety_s: float = 0.5,
    ) -> Move:
        """Compare (best non-SEARCH move value) vs (best SEARCH EV).

        EV_search = 6p - 2 + gamma_info * dH - gamma_reset * p * H(p_0)
        """
        best_move = self.iterative_deepen(
            board, belief, eval_fn, time_budget_s, safety_s
        )
        root_key = self.zobrist.hash(board)
        entry = self._probe_tt(root_key)
        best_value = entry.value if entry is not None else 0.0

        loc, ev = self._best_search_ev(board, belief)
        if loc is None:
            return best_move
        if ev > best_value + self.eps_tiebreak:
            return Move.search(loc)
        return best_move

    def _best_search_ev(self, board, belief: BeliefSummary):
        b = belief.belief
        if b is None or len(b) != 64:
            return None, -math.inf
        idx = int(belief.argmax)
        p = float(belief.max_mass)
        H_before = float(belief.entropy)
        s = 1.0 - p
        if s <= 1e-12:
            H_miss = 0.0
        else:
            H_miss = 0.0
            for i in range(64):
                if i == idx:
                    continue
                v = float(b[i])
                if v <= 0.0:
                    continue
                q = v / s
                H_miss -= q * math.log(q + 1e-18)
        dH = max(0.0, H_before - ((1.0 - p) * H_miss))
        H_p0 = math.log(64.0)
        ev = 6.0 * p - 2.0 + self.gamma_info * dH - self.gamma_reset * p * H_p0
        x = idx % 8
        y = idx // 8
        return (x, y), ev


SearchEngine = Search


def _point_diff(board) -> float:
    try:
        return float(
            board.player_worker.get_points() - board.opponent_worker.get_points()
        )
    except Exception:
        return 0.0
