"""Ordered move generation for RattleBot v0.2.

Per BOT_STRATEGY.md v1.1 §2.f / §3.5. Wraps `Board.get_valid_moves` and
applies the ordering stack:
    1. hash-move (from TT) first if legal
    2. killer moves for this depth
    3. history heuristic (cumulative cutoff counts)
    4. type-priority: CARPET(k>=2) > PRIME > PLAIN > CARPET(k=1) > SEARCH
    5. immediate point delta
v1.1 invariant (D-011 item 2): with exclude_search=True (interior nodes),
the returned list contains NO SEARCH moves.

v0.2 T-20f (V01_LOSS_ANALYSIS bug 1): k=1 CARPET rolls are strictly
dominated (−1 point with no upside) yet were observed as 42 % of
RattleBot's carpet moves. We now drop k=1 CARPET moves from the returned
list UNLESS no non-k=1 legal move exists — in which case k=1 is kept as
the only way out (very rare; engine edge case).
"""

from __future__ import annotations
from typing import Dict, Iterable, List, Optional, Tuple

from game.enums import CARPET_POINTS_TABLE, MoveType
from game.move import Move

from .types import MoveKey
from .zobrist import move_key

__all__ = ["ordered_moves", "get_ordered_moves", "immediate_delta"]


_TYPE_PRIORITY = {
    int(MoveType.CARPET): 0,
    int(MoveType.PRIME): 1,
    int(MoveType.PLAIN): 2,
    int(MoveType.SEARCH): 3,
}


def immediate_delta(move: Move) -> int:
    mt = int(move.move_type)
    if mt == int(MoveType.CARPET):
        return CARPET_POINTS_TABLE.get(move.roll_length, 0)
    if mt == int(MoveType.PRIME):
        return 1
    return 0


def _sort_key(move: Move, history: Optional[Dict[MoveKey, int]]):
    mt = int(move.move_type)
    if mt == int(MoveType.CARPET) and move.roll_length < 2:
        type_bucket = 2
    else:
        type_bucket = _TYPE_PRIORITY[mt]
    hist = history.get(move_key(move), 0) if history is not None else 0
    return (type_bucket, -hist, -immediate_delta(move))


def _is_k1_carpet(m: Move) -> bool:
    return (
        int(m.move_type) == int(MoveType.CARPET)
        and m.roll_length < 2
    )


def ordered_moves(
    board,
    hash_move: Optional[MoveKey] = None,
    killers: Optional[List[MoveKey]] = None,
    history: Optional[Dict[MoveKey, int]] = None,
    exclude_search: bool = True,
) -> List[Move]:
    legal = board.get_valid_moves(exclude_search=exclude_search)
    if not legal:
        return legal

    # T-20f bug 1: drop strictly-dominated k=1 CARPET unless it's the only
    # option. This is a sound pruning because k=1 is worth −1 point and
    # offers no downstream advantage the other legal moves lack.
    non_k1 = [m for m in legal if not _is_k1_carpet(m)]
    if non_k1:
        legal = non_k1

    legal.sort(key=lambda m: _sort_key(m, history))

    head_keys: List[MoveKey] = []
    if hash_move is not None:
        head_keys.append(hash_move)
    if killers:
        for k in killers:
            if k is not None:
                head_keys.append(k)
    if not head_keys:
        return legal

    legal_by_key: Dict[MoveKey, Move] = {move_key(m): m for m in legal}
    out: List[Move] = []
    seen = set()
    for k in head_keys:
        if k in seen:
            continue
        cand = legal_by_key.get(k)
        if cand is not None:
            out.append(cand)
            seen.add(k)
    for m in legal:
        k = move_key(m)
        if k in seen:
            continue
        out.append(m)
    return out


def get_ordered_moves(
    board,
    is_max: bool = True,
    hash_move: Optional[Move] = None,
    killer: Optional[Tuple[Move, Move]] = None,
    history: Optional[Dict[MoveKey, int]] = None,
) -> List[Move]:
    """Legacy alias for BOT_STRATEGY §3.5 signature (Move in, Move out).

    Converts Move -> MoveKey and always filters SEARCH.
    """
    hm_key = move_key(hash_move) if hash_move is not None else None
    killer_keys: List[MoveKey] = []
    if killer is not None:
        for km in killer:
            if km is not None:
                killer_keys.append(move_key(km))
    return ordered_moves(
        board, hash_move=hm_key, killers=killer_keys,
        history=history, exclude_search=True,
    )
