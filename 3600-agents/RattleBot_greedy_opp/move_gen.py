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
dominated (−1 point with no upside). We drop k=1 CARPET moves from the
returned list UNLESS no non-k=1 legal move exists.

v0.2 T-20g (SEARCH_PROFILE §3 #4): the sort key is now a plain int, the
k=1 filter + type-priority + immediate-delta + history lookup is computed
in a single pre-pass that also builds a `{MoveKey: Move}` map — so each
Move's `move_key` is derived exactly once per `ordered_moves` call rather
than 3-4× as in v0.2.0. Drops ~6 % wall time.
"""

from __future__ import annotations
from typing import Dict, Iterable, List, Optional, Tuple

from game.enums import CARPET_POINTS_TABLE, MoveType
from game.move import Move

from .types import MoveKey
from .zobrist import move_key

__all__ = ["ordered_moves", "get_ordered_moves", "immediate_delta"]


_MT_CARPET = int(MoveType.CARPET)
_MT_PRIME = int(MoveType.PRIME)
_MT_PLAIN = int(MoveType.PLAIN)
_MT_SEARCH = int(MoveType.SEARCH)

_TYPE_PRIORITY = {
    _MT_CARPET: 0,
    _MT_PRIME: 1,
    _MT_PLAIN: 2,
    _MT_SEARCH: 3,
}


def immediate_delta(move: Move) -> int:
    mt = int(move.move_type)
    if mt == _MT_CARPET:
        return CARPET_POINTS_TABLE.get(move.roll_length, 0)
    if mt == _MT_PRIME:
        return 1
    return 0


def _sort_key(move: Move, history: Optional[Dict[MoveKey, int]]):
    """Legacy helper kept for callers / tests that invoke it directly.

    The hot path in `ordered_moves` no longer calls this — it inlines an
    integer sort-key computation to avoid per-move tuple allocation.
    """
    mt = int(move.move_type)
    if mt == _MT_CARPET and move.roll_length < 2:
        type_bucket = 2
    else:
        type_bucket = _TYPE_PRIORITY[mt]
    hist = history.get(move_key(move), 0) if history is not None else 0
    return (type_bucket, -hist, -immediate_delta(move))


def _is_k1_carpet(m: Move) -> bool:
    return int(m.move_type) == _MT_CARPET and m.roll_length < 2


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

    # Single pre-pass: drop k=1 CARPET (unless it's the only option), cache
    # each move's MoveKey, compute the integer sort-key, and build the
    # head-promotion lookup dict in one sweep. O(N) with N ~ 12.
    annotated: List[Tuple[int, Move, MoveKey]] = []
    has_non_k1 = False
    for m in legal:
        mt = int(m.move_type)
        k1 = (mt == _MT_CARPET and m.roll_length < 2)
        if not k1:
            has_non_k1 = True
        # compute move_key once and reuse
        mk = move_key(m)
        # integer sort key: (type_bucket * 10_000_000)
        #   + (-history_score * 100) clamped to 6 decimals
        #   + (-immediate_delta)
        if mt == _MT_CARPET:
            type_bucket = 2 if m.roll_length < 2 else 0
            delta = CARPET_POINTS_TABLE.get(m.roll_length, 0)
        elif mt == _MT_PRIME:
            type_bucket = 1
            delta = 1
        elif mt == _MT_PLAIN:
            type_bucket = 2
            delta = 0
        else:  # SEARCH
            type_bucket = 3
            delta = 0
        hist_score = history.get(mk, 0) if history is not None else 0
        # Pack into a single int so Python's sort doesn't allocate tuples:
        #   key = type_bucket * 10^10 - hist_score * 10^4 - delta
        # type_bucket in [0..3], hist_score up to ~10^6, delta in [-1..21].
        sort_key = type_bucket * 10_000_000_000 - hist_score * 10_000 - delta
        annotated.append((sort_key, m, mk))

    if has_non_k1:
        annotated = [entry for entry in annotated if not _is_k1_carpet(entry[1])]

    # Sort by the integer key (stable, no tuple overhead).
    annotated.sort(key=lambda e: e[0])

    # Assemble head-keys (hash-move first, then killers).
    head_keys: List[MoveKey] = []
    if hash_move is not None:
        head_keys.append(hash_move)
    if killers:
        for kk in killers:
            if kk is not None:
                head_keys.append(kk)

    if not head_keys:
        # Fast path: no head promotion needed. Allocate only the final list.
        return [m for _, m, _ in annotated]

    # Build the key -> Move map from the already-computed MoveKeys (no
    # second pass of move_key).
    by_key: Dict[MoveKey, Move] = {mk: m for _, m, mk in annotated}
    out: List[Move] = []
    seen = set()
    for k in head_keys:
        if k in seen:
            continue
        cand = by_key.get(k)
        if cand is not None:
            out.append(cand)
            seen.add(k)
    for _, m, mk in annotated:
        if mk in seen:
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
