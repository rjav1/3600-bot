"""Zobrist hashing + move packing — STUB.

Precomputed u64 tables per BOT_STRATEGY.md v1.1 §3.7.
Owner: dev-integrator.
"""

from __future__ import annotations

from game.move import Move

__all__ = ["ZobristTable", "pack_move", "unpack_move"]


class ZobristTable:
    """Deterministic u64 key tables (~3.1 KB total)."""

    def __init__(self, seed: int = 0xBEEF1234) -> None:
        """Fill all u64 tables. Time: <= 5 ms."""
        raise NotImplementedError("TBD by dev-integrator")

    def hash_from_scratch(self, board) -> int:
        """Full recompute from board state. Time: <= 50 us."""
        raise NotImplementedError("TBD by dev-integrator")

    def xor_plain(
        self, old_hash: int, from_cell: int, to_cell: int, is_player_a: bool
    ) -> int:
        """PLAIN incremental XOR. Time: <= 1 us."""
        raise NotImplementedError("TBD by dev-integrator")

    def xor_prime(
        self, old_hash: int, from_cell: int, to_cell: int, is_player_a: bool
    ) -> int:
        """PRIME incremental XOR (curr -> PRIMED). Time: <= 1 us."""
        raise NotImplementedError("TBD by dev-integrator")

    def xor_carpet(
        self,
        old_hash: int,
        direction: int,
        k: int,
        from_cell: int,
        is_player_a: bool,
    ) -> int:
        """CARPET incremental XOR over k cells. Time: <= 5 us."""
        raise NotImplementedError("TBD by dev-integrator")

    def xor_search_update(
        self, old_hash: int, new_loc, new_result: bool, acting_is_a: bool
    ) -> int:
        """Search-tuple XOR (v0.2). Time: <= 1 us."""
        raise NotImplementedError("TBD by dev-integrator")

    def xor_parity(self, old_hash: int) -> int:
        """Flip side-to-move bit. Time: <= 1 us."""
        raise NotImplementedError("TBD by dev-integrator")


def pack_move(m: Move) -> int:
    """Pack Move into u16. Layout: [type:2|dir:2|roll:3|loc:6|_:3].
    Time: <= 1 us.
    """
    raise NotImplementedError("TBD by dev-integrator")


def unpack_move(packed: int) -> Move:
    """Inverse of pack_move. Raises: ValueError on bad encoding."""
    raise NotImplementedError("TBD by dev-integrator")
