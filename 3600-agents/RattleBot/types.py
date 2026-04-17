"""Shared dataclasses for RattleBot — the interface lock-in layer.

Per BOT_STRATEGY.md v1.1 §3.8 and D-005/D-011. These types are the contract
between `rat_belief`, `search`, `heuristic`, `move_gen`, `time_mgr`, and
`zobrist`. Treat field shapes/dtypes as load-bearing — dev-hmm/dev-search/
dev-heuristic all import from here.

v1.1 notes:
- `BeliefSummary.top8` intentionally dropped (D-011 item 3 / CON-STRAT §D-1).
  Leaves that need top-k sort 64 floats on demand (~5 µs).
- `TTEntry.flag` values: 0=EXACT, 1=LOWER, 2=UPPER (see `search.py`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    # Avoid a hard import cycle / engine dependency at module-load time.
    from game.enums import MoveType, Direction  # noqa: F401


__all__ = [
    "BeliefSummary",
    "TTEntry",
    "Undo",
    "MoveKey",
    "TT_FLAG_EXACT",
    "TT_FLAG_LOWER",
    "TT_FLAG_UPPER",
]


TT_FLAG_EXACT: int = 0
TT_FLAG_LOWER: int = 1
TT_FLAG_UPPER: int = 2


@dataclass(frozen=True)
class BeliefSummary:
    """Summary of RatBelief state passed into heuristic / leaf evaluation.

    The full posterior over the 64 rat-cells is `belief` (shape (64,),
    dtype float64, sums to 1.0 within 1e-9). Summary stats are precomputed
    so that heuristic features F11/F12 (and any future O(1) belief term)
    do not re-scan the array.

    Fields:
        belief:   shape (64,) float64, row-major flat index `y*8 + x`,
                  matches the engine bitmask layout (GAME_SPEC §1).
                  Sums to 1.0 modulo numerical slack.
        entropy:  Shannon entropy of `belief` in nats. Range [0, ln 64].
        max_mass: max(belief). Range (0, 1].
        argmax:   flat-index (0..63) of the max-mass cell. Ties broken
                  by numpy's argmax (first occurrence).
    """

    belief: np.ndarray
    entropy: float
    max_mass: float
    argmax: int


@dataclass
class TTEntry:
    """Transposition-table entry (α-β search).

    Two-slot buckets per `SearchEngine`: slot 0 = depth-preferred,
    slot 1 = always-replace. `zobrist_key` is the full 64-bit hash used
    as the collision check against the bucket index.

    Fields:
        zobrist_key: full 64-bit Zobrist key of the stored position.
        depth:       search depth used to produce `value`.
        value:       evaluation (from the perspective of the side to move
                     at storage time — sign convention is negamax).
        flag:        bound flag — TT_FLAG_EXACT / LOWER / UPPER.
        best_move:   principal-variation move from this node, or None if
                     the node was a cutoff on the first reply.
        age:         `board.turn_count` when this entry was stored;
                     used by the replacement policy to prefer current-gen.
    """

    zobrist_key: int
    depth: int
    value: float
    flag: int
    best_move: Optional["MoveKey"]
    age: int


@dataclass
class Undo:
    """Undo record for `search._make_move` / `_unmake_move` (v0.2+).

    v0.1 uses `board.forecast_move` (allocating deep copies); v0.2 flips to
    an in-place make/unmake loop using this record to reverse `apply_move`.
    Exact field set is owned by dev-search (BOT_STRATEGY.md §3.3).

    IMPORTANT (D-011 item 2 / CON-STRAT §D-2): SEARCH moves must never
    enter the in-tree move list — `search._alphabeta` asserts this on
    every node. `Undo` therefore does NOT need to model SEARCH reversal.
    """

    # dev-search fills this in (v0.2 scope). Intentional stub.
    pass


@dataclass(frozen=True)
class MoveKey:
    """Compact move identifier for TT best-move storage and history-heuristic
    keying.

    Hashable / frozen so it can be dict-keyed. Cheaper than carrying a full
    `Move` object through the TT — also decouples TT shape from engine
    Move internals.

    Fields:
        move_type:   int value of `MoveType` (PLAIN=0, PRIME=1, CARPET=2,
                     SEARCH=3).  NOTE: SEARCH must never appear for any
                     MoveKey stored by `_alphabeta` — only `get_root_moves`.
        direction:   int value of `Direction` (UP=0, RIGHT=1, DOWN=2,
                     LEFT=3) for PLAIN/PRIME/CARPET, or None for SEARCH.
        roll_length: k in [1, 7] for CARPET; 0 otherwise.
        search_loc:  (x, y) for SEARCH; None otherwise.
    """

    move_type: int
    direction: Optional[int]
    roll_length: int
    search_loc: Optional[Tuple[int, int]]
