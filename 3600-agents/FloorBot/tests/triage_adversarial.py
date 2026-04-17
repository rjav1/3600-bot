"""Adversarial board-state stress test for FloorBot (Task #24 Step 4).

Construct specific board states that might break each decision rule,
then feed them to FloorBot.play() and check is_valid_move on the returned
move. Anything that returns False is a bug.
"""
from __future__ import annotations

import json
import pathlib
import sys


def _bootstrap():
    top = pathlib.Path(__file__).resolve().parents[3]
    for p in (top / "engine", top / "3600-agents"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


def build_board(
    blocked=(),
    primed=(),
    carpet=(),
    player_pos=(3, 3),
    opp_pos=(5, 3),
    time_to_play=240.0,
):
    from game.board import Board
    from game.enums import Cell
    b = Board(time_to_play=time_to_play, build_history=False)
    for x, y in blocked:
        b.set_cell((x, y), Cell.BLOCKED)
    for x, y in primed:
        b.set_cell((x, y), Cell.PRIMED)
    for x, y in carpet:
        b.set_cell((x, y), Cell.CARPET)
    b.player_worker.position = player_pos
    b.opponent_worker.position = opp_pos
    return b


def probe(name, board, expect_valid=True, anomalies=None):
    import numpy as np
    from FloorBot.agent import PlayerAgent
    T = np.full((64, 64), 1.0 / 64.0, dtype=np.float32)
    agent = PlayerAgent(board, transition_matrix=T, time_left=lambda: 999.0)
    from game.enums import Noise
    move = agent.play(board, (Noise.SQUEAK, 5), lambda: 999.0)
    if move is None:
        anomalies.append({"name": name, "kind": "returned_None"})
        return

    ok = False
    try:
        ok = board.is_valid_move(move)
    except Exception as e:
        anomalies.append({
            "name": name, "kind": "is_valid_move_raised",
            "move": repr(move), "exc": f"{type(e).__name__}: {e}",
        })
        return

    if expect_valid and not ok:
        anomalies.append({
            "name": name, "kind": "INVALID_MOVE",
            "move": repr(move),
            "player_loc": board.player_worker.position,
            "opp_loc": board.opponent_worker.position,
        })
    elif not expect_valid and ok:
        anomalies.append({
            "name": name, "kind": "expected_invalid_got_valid",
            "move": repr(move),
        })
    # Always record what it returned for audit
    anomalies.append({
        "name": name, "kind": "move_chosen", "move": repr(move),
        "is_valid": ok,
    })


def main():
    _bootstrap()
    from game.enums import Cell

    anomalies = []

    # --- Scenario 1: big carpet roll blocked by opponent worker ---
    # Primed line from (2,3) toward right, but opponent on (5,3) blocks the k>=3 roll.
    # FloorBot's _best_carpet picks ONLY from valid moves, so should be safe.
    b = build_board(
        primed=[(3, 3), (4, 3)],
        player_pos=(2, 3),
        opp_pos=(5, 3),  # blocks CARPET-3 landing and CARPET-2 landing
    )
    probe("carpet_blocked_by_opp", b, anomalies=anomalies)

    # --- Scenario 2: prime-extend, 2 ahead now carpeted ---
    # FloorBot's extension_bonus checks cells 2-3 ahead for PRIMED. If the cell
    # was carpeted by opponent, bonus is 0. Should NOT think it's primed.
    b = build_board(
        carpet=[(5, 3)],  # 2 ahead of (3,3) if going RIGHT
        player_pos=(3, 3),
        opp_pos=(0, 0),  # corner
    )
    probe("extension_adjacent_carpeted", b, anomalies=anomalies)

    # --- Scenario 3: edge/corner — all 3 plain steps blocked ---
    # Worker in corner (0,0). Blocked corners around. One direction is the
    # opponent. Only some moves valid.
    b = build_board(
        blocked=[(1, 0), (2, 0), (0, 1), (0, 2)],  # 2x3 top-left
        player_pos=(2, 1),
        opp_pos=(3, 1),
    )
    probe("edge_constrained", b, anomalies=anomalies)

    # --- Scenario 4: worker standing on PRIMED or CARPET, plain-only options ---
    # FloorBot landed on CARPET; PRIME from CARPET is illegal.
    b = build_board(
        carpet=[(3, 3)],
        player_pos=(3, 3),
        opp_pos=(5, 3),
    )
    probe("standing_on_carpet", b, anomalies=anomalies)

    # --- Scenario 5: ALL 4 neighbors PRIMED (only CARPET-1 available) ---
    # FloorBot rejects CARPET-1 in _best_carpet (pts=-1 < 1). Has no prime
    # (current cell is SPACE but neighbors blocked for move) and no plain.
    # Should fall through to "valid[0]" — which is a CARPET-1 (and IS valid).
    b = build_board(
        primed=[(3, 2), (3, 4), (2, 3), (4, 3)],
        player_pos=(3, 3),
        opp_pos=(0, 0),
    )
    probe("surrounded_by_primed", b, anomalies=anomalies)

    # --- Scenario 6: opponent adjacent in all 4 dirs (impossible but sim it) ---
    # Can't actually happen (only one opponent worker), but test near-stuck.
    b = build_board(
        blocked=[(2, 3), (4, 3), (3, 2)],
        primed=[(3, 4)],
        player_pos=(3, 3),
        opp_pos=(0, 0),
    )
    probe("3_blocked_1_primed", b, anomalies=anomalies)

    # --- Scenario 7: prime-step target is CARPET — legal per GAME_SPEC §2.2 ---
    b = build_board(
        carpet=[(4, 3)],  # prime step right would land on CARPET
        player_pos=(3, 3),
        opp_pos=(0, 0),
    )
    probe("prime_to_carpet_dest", b, anomalies=anomalies)

    # --- Scenario 8: long primed line — FloorBot should pick big carpet ---
    b = build_board(
        primed=[(3, 3), (4, 3), (5, 3), (6, 3)],
        player_pos=(2, 3),
        opp_pos=(0, 0),
    )
    probe("long_prime_line", b, anomalies=anomalies)

    # --- Scenario 9: current cell IS the opponent's position (shouldn't, but
    #     test FloorBot doesn't crash/return invalid in corrupt-state). ---
    b = build_board(
        player_pos=(3, 3),
        opp_pos=(3, 3),  # corrupt: both on same cell
    )
    probe("corrupt_same_cell", b, anomalies=anomalies)

    # --- Scenario 10: get_valid_moves() returns [] (fully trapped). ---
    # Worker at corner (2,2), all 4 neighbors BLOCKED. Standing on CARPET
    # so no prime either.
    b = build_board(
        blocked=[(2, 1), (1, 2), (3, 2), (2, 3)],
        carpet=[(2, 2)],  # standing on carpet, can't prime
        player_pos=(2, 2),
        opp_pos=(0, 7),
    )
    probe("fully_trapped_workercell_carpet", b, anomalies=anomalies)

    # --- Scenario 11: edge case — player at (0,0) corner near blockers.
    b = build_board(
        blocked=[(1, 0), (0, 1), (2, 0), (0, 2), (1, 1), (2, 1)],
        player_pos=(0, 0),  # Assumed blocked corner overlap w/ spawn (rare)
        opp_pos=(7, 7),
    )
    probe("corner_00_spawn", b, anomalies=anomalies)

    # --- Scenario 12: Negative — what if CARPET_POINTS_TABLE
    #     doesn't contain roll_length (impossible from valid moves but...) ---
    # This is already guarded by _best_carpet default -999. Skip.

    # --- Output ---
    # Separate the "move_chosen" audit trail from the real anomalies.
    real = [a for a in anomalies if a["kind"] not in ("move_chosen",)]
    audit = [a for a in anomalies if a["kind"] == "move_chosen"]
    print("=== AUDIT TRAIL ===")
    for a in audit:
        print(f"  {a['name']:40s} -> {a['move']:30s} valid={a['is_valid']}")
    print()
    print(f"=== ANOMALIES: {len(real)} ===")
    for a in real:
        print(json.dumps(a, indent=2, default=str))
    if not real:
        print("No anomalies found.")


if __name__ == "__main__":
    main()
