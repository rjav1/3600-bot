"""Zobrist hashing for RattleBot v0.1.

Per BOT_STRATEGY.md v1.1 §2.g / §3.7. 64-bit keys XORed over:
  - 4 x 64 cell-state keys (space/primed/carpet/blocked)
  - 2 x 64 worker-position keys (player + opponent)
  - 2 side-to-move keys
  - 41 turn-count buckets (turn_count // 2)
Search-tuple XORs and incremental PLAIN/PRIME/CARPET/SEARCH XORs are v0.2
(BOT_STRATEGY §3.7 v0.2 scope). v0.1 uses `hash()` (full rehash) since
children come from `forecast_move` which already returns a fresh Board.
"""

from __future__ import annotations

import random
from typing import Optional

from game.enums import Cell, MoveType, BOARD_SIZE
from game.move import Move

from .types import MoveKey

__all__ = ["Zobrist", "ZobristTable", "move_key", "MASK64"]


MASK64 = (1 << 64) - 1


def _rand_u64(rng: random.Random) -> int:
    return rng.getrandbits(64)


class Zobrist:
    """Precomputed random tables + full-board hash.

    Tables (all uint64):
        cell[ct][idx]   ct in 0..3, idx in 0..63
        player_pos[idx], opp_pos[idx]  idx in 0..63
        side[2]         0 = A to move, 1 = B to move
        turn[41]        turn_count // 2 bucket in 0..40
    """

    __slots__ = ("cell", "player_pos", "opp_pos", "side", "turn")

    def __init__(self, seed: int = 0xBADDCAFE) -> None:
        rng = random.Random(seed)
        self.cell = tuple(
            tuple(_rand_u64(rng) for _ in range(64)) for _ in range(4)
        )
        self.player_pos = tuple(_rand_u64(rng) for _ in range(64))
        self.opp_pos = tuple(_rand_u64(rng) for _ in range(64))
        self.side = (_rand_u64(rng), _rand_u64(rng))
        self.turn = tuple(_rand_u64(rng) for _ in range(41))

    def hash(self, board) -> int:
        h = 0
        primed = board._primed_mask
        carpet = board._carpet_mask
        blocked = board._blocked_mask
        for idx in range(64):
            bit = 1 << idx
            if primed & bit:
                h ^= self.cell[Cell.PRIMED][idx]
            elif carpet & bit:
                h ^= self.cell[Cell.CARPET][idx]
            elif blocked & bit:
                h ^= self.cell[Cell.BLOCKED][idx]
            else:
                h ^= self.cell[Cell.SPACE][idx]

        px, py = board.player_worker.position
        ox, oy = board.opponent_worker.position
        if 0 <= px < BOARD_SIZE and 0 <= py < BOARD_SIZE:
            h ^= self.player_pos[py * BOARD_SIZE + px]
        if 0 <= ox < BOARD_SIZE and 0 <= oy < BOARD_SIZE:
            h ^= self.opp_pos[oy * BOARD_SIZE + ox]

        h ^= self.side[0 if board.is_player_a_turn else 1]
        tbucket = min(max(board.turn_count // 2, 0), 40)
        h ^= self.turn[tbucket]
        return h & MASK64

    def incremental_update(self, h: int, old_ct: int, new_ct: int, idx: int) -> int:
        """One cell at `idx` changed from old_ct to new_ct. v0.2 convenience."""
        return (h ^ self.cell[old_ct][idx] ^ self.cell[new_ct][idx]) & MASK64


ZobristTable = Zobrist


def move_key(move: Move) -> MoveKey:
    """Immutable, hashable identifier for a Move (dict-friendly)."""
    mt = int(move.move_type)
    if mt == int(MoveType.SEARCH):
        return MoveKey(mt, None, 0, move.search_loc)
    direction = int(move.direction) if move.direction is not None else None
    roll = move.roll_length if mt == int(MoveType.CARPET) else 0
    return MoveKey(mt, direction, roll, None)
