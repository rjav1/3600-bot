"""Ordered move generation — STUB.

Per BOT_STRATEGY.md v1.1 §3.5. Owner: dev-integrator.

v1.1 contract: get_ordered_moves must NEVER return a SEARCH move — the
tree-invariant in search._alphabeta will assert on it (D-011 item 2).
SEARCH is root-only via get_root_moves_with_search.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from game import board as board_mod
from game.move import Move

from .types import BeliefSummary, MoveKey

__all__ = ["get_ordered_moves", "get_root_moves_with_search"]


def get_ordered_moves(
    board: board_mod.Board,
    is_max: bool,
    hash_move: Optional[Move] = None,
    killer: Optional[Tuple[Move, Move]] = None,
    history: Optional[Dict[MoveKey, int]] = None,
) -> List[Move]:
    """Legal non-SEARCH moves, ordered. Every element has
    move_type != MoveType.SEARCH. Time: <= 200 us per internal node.
    """
    raise NotImplementedError("TBD by dev-integrator")


def get_root_moves_with_search(
    board: board_mod.Board,
    belief_summary: BeliefSummary,
) -> Tuple[List[Move], Optional[Move]]:
    """Root-only: ordered non-SEARCH moves plus EV-gated SEARCH candidate.
    Returns: (non_search_moves, search_candidate_or_None).
    Time: <= 300 us (once/turn at root).
    """
    raise NotImplementedError("TBD by dev-integrator")
