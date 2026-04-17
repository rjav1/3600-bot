"""Alpha-beta + iterative deepening + 2-slot Zobrist TT for FakeCarrie_v2.

Negamax alpha-beta with PV-first reordering between iterations, hash-move +
type-priority ordering (no killers / history / numba). SEARCH is
excluded from the in-tree move list; root-only SEARCH is handled by
the caller (see `agent.py`).

Leaf evaluator: `eval_fn(board, belief_max) -> float`.
"""

from __future__ import annotations

import time as _time
from typing import Callable, List, Optional, Tuple

from game.enums import CARPET_POINTS_TABLE, MoveType
from game.move import Move

from .zobrist import MoveKey, Zobrist, move_key


MATE_SCORE: float = 1e9
MAX_DEPTH: int = 24
_TT_FLAG_EXACT = 0
_TT_FLAG_LOWER = 1
_TT_FLAG_UPPER = 2


class _TimeUp(Exception):
    pass


class _TTEntry:
    __slots__ = ("key", "depth", "value", "flag", "best_move")

    def __init__(self, key, depth, value, flag, best_move):
        self.key = key
        self.depth = depth
        self.value = value
        self.flag = flag
        self.best_move = best_move


class Search:
    def __init__(
        self,
        zobrist: Optional[Zobrist] = None,
        tt_size: int = 1 << 18,
    ) -> None:
        self.zobrist = zobrist if zobrist is not None else Zobrist()
        p = 1
        while p < max(1, tt_size):
            p <<= 1
        self.tt_size = p
        self.tt_mask = p - 1
        self.tt: List[List[Optional[_TTEntry]]] = [
            [None, None] for _ in range(p)
        ]
        self._deadline: float = float("inf")
        self._eval_fn: Optional[Callable[..., float]] = None
        self._belief_max: float = 0.0
        self.last_depth = 0

    def iterative_deepen(
        self,
        board,
        eval_fn: Callable[..., float],
        belief_max: float,
        budget_s: float,
    ) -> Optional[Move]:
        self._eval_fn = eval_fn
        self._belief_max = float(belief_max)
        self._deadline = _time.perf_counter() + max(0.0, float(budget_s))

        legal = _order_moves(board, hash_move=None, exclude_search=True)
        if not legal:
            legal = board.get_valid_moves(exclude_search=False)
            if not legal:
                return None
            return legal[0]

        best_move: Move = legal[0]
        for depth in range(1, MAX_DEPTH + 1):
            try:
                _, mv = self._root_search(board, depth, legal, best_move)
                if mv is not None:
                    best_move = mv
                    self.last_depth = depth
                    legal = _reorder_pv_first(legal, mv)
            except _TimeUp:
                break
            if _time.perf_counter() >= self._deadline:
                break
        return best_move

    def _root_search(self, board, depth, legal, prev_best):
        alpha = -MATE_SCORE
        beta = MATE_SCORE
        best_val = -MATE_SCORE
        best_move: Move = prev_best

        root_key = self.zobrist.hash(board)
        tt_entry = self._probe_tt(root_key)
        hash_mk = tt_entry.best_move if tt_entry else None
        ordered = _order_moves(board, hash_move=hash_mk, exclude_search=True)
        if not ordered:
            ordered = legal

        for mv in ordered:
            if _time.perf_counter() >= self._deadline:
                raise _TimeUp()
            child = board.forecast_move(mv, check_ok=False)
            if child is None:
                continue
            child.reverse_perspective()
            v = -self._alphabeta(child, depth - 1, -beta, -alpha)
            if v > best_val:
                best_val = v
                best_move = mv
                if v > alpha:
                    alpha = v

        self._store_tt(
            root_key, depth, best_val, _TT_FLAG_EXACT, move_key(best_move)
        )
        return best_val, best_move

    def _alphabeta(self, board, depth, alpha, beta):
        if (depth & 3) == 0 and _time.perf_counter() >= self._deadline:
            raise _TimeUp()
        if board.is_game_over():
            return self._terminal_value(board)
        if depth <= 0:
            return self._leaf(board)

        alpha0 = alpha
        key = self.zobrist.hash(board)
        tt_entry = self._probe_tt(key)
        hash_mk: Optional[MoveKey] = None
        if tt_entry is not None:
            hash_mk = tt_entry.best_move
            if tt_entry.depth >= depth:
                v = tt_entry.value
                f = tt_entry.flag
                if f == _TT_FLAG_EXACT:
                    return v
                if f == _TT_FLAG_LOWER and v > alpha:
                    alpha = v
                elif f == _TT_FLAG_UPPER and v < beta:
                    beta = v
                if alpha >= beta:
                    return v

        ordered = _order_moves(board, hash_move=hash_mk, exclude_search=True)
        if not ordered:
            return self._leaf(board)

        best_val = -MATE_SCORE
        best_mk: Optional[MoveKey] = None
        for mv in ordered:
            child = board.forecast_move(mv, check_ok=False)
            if child is None:
                continue
            child.reverse_perspective()
            v = -self._alphabeta(child, depth - 1, -beta, -alpha)
            if v > best_val:
                best_val = v
                best_mk = move_key(mv)
            if v > alpha:
                alpha = v
            if alpha >= beta:
                break

        if best_val <= alpha0:
            flag = _TT_FLAG_UPPER
        elif best_val >= beta:
            flag = _TT_FLAG_LOWER
        else:
            flag = _TT_FLAG_EXACT
        self._store_tt(key, depth, best_val, flag, best_mk)
        return best_val

    def _leaf(self, board) -> float:
        fn = self._eval_fn
        if fn is None:
            return _point_diff(board)
        try:
            return float(fn(board, self._belief_max))
        except TypeError:
            return float(fn(board))

    def _terminal_value(self, board) -> float:
        return _point_diff(board) * 10_000.0

    def _probe_tt(self, key: int) -> Optional[_TTEntry]:
        bucket = self.tt[key & self.tt_mask]
        for slot in bucket:
            if slot is not None and slot.key == key:
                return slot
        return None

    def _store_tt(self, key, depth, value, flag, best_move):
        entry = _TTEntry(key, depth, float(value), flag, best_move)
        bucket = self.tt[key & self.tt_mask]
        slot0 = bucket[0]
        if slot0 is None or depth >= slot0.depth:
            bucket[0] = entry
        bucket[1] = entry


def _reorder_pv_first(legal: List[Move], pv: Move) -> List[Move]:
    pv_k = move_key(pv)
    out = [m for m in legal if move_key(m) == pv_k]
    out.extend(m for m in legal if move_key(m) != pv_k)
    return out


_MT_CARPET = int(MoveType.CARPET)
_MT_PRIME = int(MoveType.PRIME)
_MT_PLAIN = int(MoveType.PLAIN)


def _is_k1_carpet(m: Move) -> bool:
    return int(m.move_type) == _MT_CARPET and m.roll_length < 2


def _order_moves(
    board,
    hash_move: Optional[MoveKey] = None,
    exclude_search: bool = True,
) -> List[Move]:
    legal = board.get_valid_moves(exclude_search=exclude_search)
    if not legal:
        return legal

    has_non_k1 = any(not _is_k1_carpet(m) for m in legal)
    filtered = [m for m in legal if (not has_non_k1) or not _is_k1_carpet(m)]
    if not filtered:
        filtered = legal

    def sort_key(m: Move):
        mt = int(m.move_type)
        if mt == _MT_CARPET:
            bucket = 0 if m.roll_length >= 2 else 2
            delta = CARPET_POINTS_TABLE.get(m.roll_length, 0)
        elif mt == _MT_PRIME:
            bucket, delta = 1, 1
        elif mt == _MT_PLAIN:
            bucket, delta = 2, 0
        else:
            bucket, delta = 3, 0
        return (bucket, -delta)

    filtered.sort(key=sort_key)

    if hash_move is not None:
        head = [m for m in filtered if move_key(m) == hash_move]
        if head:
            rest = [m for m in filtered if move_key(m) != hash_move]
            return head + rest
    return filtered


def _point_diff(board) -> float:
    try:
        return float(
            board.player_worker.get_points() - board.opponent_worker.get_points()
        )
    except Exception:
        return 0.0
