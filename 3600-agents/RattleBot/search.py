"""Alpha-beta + iterative deepening + Zobrist TT — STUB.

Backbone per D-004 / BOT_STRATEGY.md v1.1 §3.3. Belief is a leaf potential
(no in-tree chance nodes); SEARCH is root-only. Owner: dev-search.

v1.1 invariant (always-on, D-011 item 2 / CON-STRAT §D-2): inside
`_alphabeta`, assert no SEARCH move ever appears in the ordered list —
apply_move(SEARCH) is a no-op for points/belief; leaks mis-value subtrees.
"""

from __future__ import annotations
from typing import Callable, Dict, List, Optional, Tuple
import numpy as np

from game import board as board_mod
from game.move import Move

from .types import BeliefSummary, MoveKey, TTEntry

__all__ = ["SearchEngine", "MATE_SCORE", "DRAW_SCORE"]

MATE_SCORE: float = 1e9
DRAW_SCORE: float = 0.0


class SearchEngine:
    """Alpha-beta + ID + 2-slot TT + killer + history search."""

    def __init__(
        self,
        tt_size: int = 1 << 20,
        heuristic: Optional[Callable[..., float]] = None,
        zobrist: Optional[object] = None,
    ) -> None:
        """Allocate TT (~40 MB), killer, history. Time: <= 1 s.
        Raises: MemoryError if tt_size exceeds 1.5 GB RSS budget.
        """
        raise NotImplementedError("TBD by dev-search")

    def alphabeta_id(
        self,
        board: board_mod.Board,
        belief_summary: BeliefSummary,
        time_manager: object,
    ) -> Tuple[Optional[Move], float]:
        """Top-level iterative-deepening loop; catches StopIteration.
        Returns: (best_move, value). best_move None only on no-legal.
        Time: time_manager.remaining(); 2-6 s typical.
        """
        raise NotImplementedError("TBD by dev-search")

    def _alphabeta(
        self,
        board: board_mod.Board,
        depth: int,
        alpha: float,
        beta: float,
        belief_summary: BeliefSummary,
        is_maximizing: bool,
        ply_from_root: int,
    ) -> float:
        """Negamax recursion. Must assert no SEARCH in ordered_moves.
        Returns: value from side-to-move perspective.
        Raises: StopIteration on time exhaustion.
        """
        raise NotImplementedError("TBD by dev-search")

    def _order_moves(
        self,
        moves: List[Move],
        board: board_mod.Board,
        depth: int,
        tt_entry: Optional[TTEntry],
    ) -> List[Move]:
        """Order: hash -> killer -> history -> type -> delta.
        Time: <= 200 us per node.
        """
        raise NotImplementedError("TBD by dev-search")

    def _probe_tt(self, hash_key: int) -> Optional[TTEntry]:
        """Full-key match in 2-slot bucket. Time: <= 1 us."""
        raise NotImplementedError("TBD by dev-search")

    def _store_tt(
        self,
        hash_key: int,
        depth: int,
        value: float,
        flag: int,
        best_move: Optional[Move],
    ) -> None:
        """Depth-preferred + always-replace. Time: <= 1 us."""
        raise NotImplementedError("TBD by dev-search")
