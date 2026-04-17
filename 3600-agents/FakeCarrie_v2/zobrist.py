"""Zobrist hashing for FakeCarrie_v2's alpha-beta transposition table."""

from __future__ import annotations

import random
from typing import NamedTuple, Optional, Tuple

from game.enums import BOARD_SIZE, Cell, MoveType
from game.move import Move


_MASK64 = (1 << 64) - 1


class MoveKey(NamedTuple):
    move_type: int
    direction: Optional[int]
    roll_length: int
    search_loc: Optional[Tuple[int, int]]


def move_key(move: Move) -> MoveKey:
    mt = int(move.move_type)
    if mt == int(MoveType.SEARCH):
        return MoveKey(mt, None, 0, move.search_loc)
    direction = int(move.direction) if move.direction is not None else None
    roll = move.roll_length if mt == int(MoveType.CARPET) else 0
    return MoveKey(mt, direction, roll, None)


class Zobrist:
    """Precomputed u64 tables + full-board hash (deterministic seed)."""

    __slots__ = ("cell", "player_pos", "opp_pos", "side")

    def __init__(self, seed: int = 0xCA881E2) -> None:
        rng = random.Random(seed)
        self.cell = tuple(
            tuple(rng.getrandbits(64) for _ in range(64)) for _ in range(4)
        )
        self.player_pos = tuple(rng.getrandbits(64) for _ in range(64))
        self.opp_pos = tuple(rng.getrandbits(64) for _ in range(64))
        self.side = (rng.getrandbits(64), rng.getrandbits(64))

    def hash(self, board) -> int:
        h = 0
        primed = board._primed_mask
        carpet = board._carpet_mask
        blocked = board._blocked_mask
        for idx in range(64):
            bit = 1 << idx
            if primed & bit:
                h ^= self.cell[int(Cell.PRIMED)][idx]
            elif carpet & bit:
                h ^= self.cell[int(Cell.CARPET)][idx]
            elif blocked & bit:
                h ^= self.cell[int(Cell.BLOCKED)][idx]
            else:
                h ^= self.cell[int(Cell.SPACE)][idx]
        px, py = board.player_worker.position
        ox, oy = board.opponent_worker.position
        if 0 <= px < BOARD_SIZE and 0 <= py < BOARD_SIZE:
            h ^= self.player_pos[py * BOARD_SIZE + px]
        if 0 <= ox < BOARD_SIZE and 0 <= oy < BOARD_SIZE:
            h ^= self.opp_pos[oy * BOARD_SIZE + ox]
        h ^= self.side[0 if board.is_player_a_turn else 1]
        return h & _MASK64
