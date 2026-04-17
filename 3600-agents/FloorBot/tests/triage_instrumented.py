"""FloorBot triage instrumentation — Task #24.

Wraps FloorBot.play() and logs every Move it returns + whether
board.is_valid_move(move) returns True on the board BEFORE apply_move.
Any False is the bug we're hunting (an INVALID_TURN on bytefight.org
is an instant loss per GAME_SPEC §5).

Usage:
    python 3600-agents/FloorBot/tests/triage_instrumented.py <n> [opponent]

Writes a line per anomaly to stderr and a JSON summary to stdout.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
import traceback
from typing import Optional


def _bootstrap():
    top = pathlib.Path(__file__).resolve().parents[3]
    engine_dir = str(top / "engine")
    agents_dir = str(top / "3600-agents")
    for p in (engine_dir, agents_dir):
        if p not in sys.path:
            sys.path.insert(0, p)
    return top, engine_dir, agents_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20, help="Number of matches")
    parser.add_argument("--opponent", default="Yolanda", help="Opponent agent name")
    parser.add_argument("--floor_side", default="both", choices=["A", "B", "both"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sim", action="store_true",
                        help="Run in-process simulation (skip subprocess engine) — better "
                             "for catching errors since tournament sandbox isn't available.")
    parser.add_argument("--outfile", default=None,
                        help="Write JSON results to this file (instead of stdout).")
    args = parser.parse_args()

    top, engine_dir, agents_dir = _bootstrap()

    if args.sim:
        return run_sim(args, top)
    return run_engine(args, top)


def _emit(stats, args):
    payload = json.dumps(stats, indent=2, default=str)
    if args.outfile:
        pathlib.Path(args.outfile).write_text(payload, encoding="utf-8")
    else:
        print(payload)


def run_sim(args, top):
    """In-process sim: play FloorBot vs opponent using Board directly,
    skipping the subprocess engine entirely. This lets us intercept every
    move BEFORE apply_move and check is_valid_move.
    """
    from game.board import Board
    from game.enums import (
        BOARD_SIZE, Cell, Direction, MoveType, Noise, ResultArbiter, WinReason,
        MAX_TURNS_PER_PLAYER,
    )
    from game.rat import Rat
    from board_utils import generate_spawns

    # Load agent classes
    from FloorBot.agent import PlayerAgent as FloorAgent
    if args.opponent == "Yolanda":
        from Yolanda.agent import PlayerAgent as OppAgent
    elif args.opponent == "FloorBot":
        from FloorBot.agent import PlayerAgent as OppAgent
    elif args.opponent == "RattleBot":
        from RattleBot.agent import PlayerAgent as OppAgent
    else:
        raise SystemExit(f"Unknown opponent: {args.opponent}")

    # Fake transition matrix (identity-like). Real engine passes a 64x64 but
    # RatBelief only reads it in __init__ — doesn't affect FloorBot.
    import numpy as np
    # A simple uniform-ish T (not used for move validity, just so agents init).
    T = np.full((64, 64), 1.0 / 64.0, dtype=np.float32)

    stats = {
        "n_matches": 0,
        "floor_wins": 0, "floor_losses": 0, "ties": 0,
        "invalid_moves": 0, "exceptions": 0, "timeouts": 0,
        "anomalies": [],
    }

    rng = random.Random(args.seed)

    sides = []
    if args.floor_side in ("A", "both"):
        sides.append("A")
    if args.floor_side in ("B", "both"):
        sides.append("B")

    per_side = args.n // max(1, len(sides))
    for side in sides:
        for match_i in range(per_side):
            match_seed = args.seed + 1000 * (0 if side == "A" else 1) + match_i
            rng_match = random.Random(match_seed)
            random.seed(match_seed)  # for generate_spawns etc.

            board = Board(time_to_play=240.0, build_history=False)

            # Blocked corners
            shapes = [(2, 3), (3, 2), (2, 2)]
            for ox, oy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                w, h = rng_match.choice(shapes)
                for dx in range(w):
                    for dy in range(h):
                        x = dx if ox == 0 else BOARD_SIZE - 1 - dx
                        y = dy if oy == 0 else BOARD_SIZE - 1 - dy
                        board.set_cell((x, y), Cell.BLOCKED)

            spawn_a, spawn_b = generate_spawns(board)
            board.player_worker.position = spawn_a
            board.opponent_worker.position = spawn_b

            # Init agents — FloorBot is either player_worker (A) or opponent_worker (B).
            try:
                floor_agent = FloorAgent(board, transition_matrix=T, time_left=lambda: 999.0)
                opp_agent = OppAgent(board, transition_matrix=T, time_left=lambda: 999.0)
            except Exception as e:
                stats["anomalies"].append({
                    "kind": "init_exception",
                    "match": match_i, "side": side,
                    "exc": f"{type(e).__name__}: {e}",
                })
                stats["exceptions"] += 1
                continue

            # Game loop
            floor_is_a = (side == "A")
            rat = Rat(T)
            rat.spawn()

            try:
                invalid_hit = False
                for ply in range(2 * MAX_TURNS_PER_PLAYER):
                    if board.is_game_over():
                        break
                    # Rat moves before each turn
                    rat.move()
                    # Build sensor_data (noise + dist) from the acting player's POV.
                    noise, dist = rat.sample(board)
                    sensor = (noise, dist)

                    # Whose turn (absolute A/B)?
                    is_a_turn = board.is_player_a_turn
                    acting_is_floor = (is_a_turn == floor_is_a)

                    # board.player_worker must be the acting worker. After
                    # initialization, player_worker == A. is_player_a_turn
                    # flips in end_turn(). So we need player_worker = acting.
                    # We'll enforce this invariant explicitly: if the board's
                    # player_worker is NOT the acting side, reverse_perspective.
                    # After init: player_worker is A, is_player_a_turn=True.
                    # After A's move + end_turn: is_player_a_turn=False, but
                    # player_worker still points at A. So before B moves we
                    # must reverse_perspective.
                    # Simpler: we track this via a flag.
                    agent = floor_agent if acting_is_floor else opp_agent

                    try:
                        move = agent.play(board, sensor, lambda: 999.0)
                    except Exception as e:
                        if acting_is_floor:
                            stats["anomalies"].append({
                                "kind": "play_exception",
                                "match": match_i, "side": side, "ply": ply,
                                "exc": f"{type(e).__name__}: {e}",
                                "tb": traceback.format_exc(),
                            })
                            stats["exceptions"] += 1
                        invalid_hit = True
                        break

                    # CRITICAL CHECK: is_valid_move BEFORE apply_move.
                    ok = False
                    try:
                        ok = board.is_valid_move(move)
                    except Exception as e:
                        stats["anomalies"].append({
                            "kind": "is_valid_move_raised",
                            "match": match_i, "side": side, "ply": ply,
                            "acting_is_floor": acting_is_floor,
                            "move": repr(move),
                            "exc": f"{type(e).__name__}: {e}",
                        })

                    if not ok:
                        if acting_is_floor:
                            stats["invalid_moves"] += 1
                            stats["anomalies"].append({
                                "kind": "FLOORBOT_INVALID_MOVE",
                                "match": match_i, "side": side, "ply": ply,
                                "move": repr(move),
                                "player_loc": board.player_worker.position,
                                "opp_loc": board.opponent_worker.position,
                                "primed_popcount": bin(board._primed_mask).count("1"),
                                "carpet_popcount": bin(board._carpet_mask).count("1"),
                                "blocked_popcount": bin(board._blocked_mask).count("1"),
                                "turn_count": board.turn_count,
                            })
                        invalid_hit = True
                        break

                    applied = board.apply_move(move, timer=0.001, check_ok=True)
                    if not applied:
                        # Only reachable if is_valid_move passed but apply_move
                        # still failed — a real engine inconsistency.
                        stats["anomalies"].append({
                            "kind": "apply_move_failed_after_valid",
                            "match": match_i, "side": side, "ply": ply,
                            "acting_is_floor": acting_is_floor,
                            "move": repr(move),
                        })
                        invalid_hit = True
                        break

                    # SEARCH point handling (engine side)
                    if move.move_type == MoveType.SEARCH:
                        if move.search_loc == rat.get_position():
                            board.player_worker.increment_points(4)
                            rat.spawn()
                        else:
                            board.player_worker.decrement_points(2)

                    if not board.is_game_over():
                        board.reverse_perspective()
                        # Note: we do NOT update opponent_search/player_search
                        # in this sim — not needed for FloorBot.

                stats["n_matches"] += 1
                if not invalid_hit:
                    w = board.get_winner()
                    # Who is "FloorBot" in absolute frame?
                    # Map PLAYER_A = floor_is_a; PLAYER_B = not floor_is_a.
                    if w == ResultArbiter.TIE or w is None:
                        stats["ties"] += 1
                    elif (w == ResultArbiter.PLAYER_A and floor_is_a) or \
                         (w == ResultArbiter.PLAYER_B and not floor_is_a):
                        stats["floor_wins"] += 1
                    else:
                        stats["floor_losses"] += 1
            except Exception as e:
                stats["anomalies"].append({
                    "kind": "loop_exception",
                    "match": match_i, "side": side,
                    "exc": f"{type(e).__name__}: {e}",
                    "tb": traceback.format_exc(),
                })
                stats["exceptions"] += 1

    _emit(stats, args)


def run_engine(args, top):
    """Subprocess-engine path: replays the real gameplay loop per match.
    Slower but higher-fidelity. We post-process the history for anomalies."""
    from gameplay import play_game
    from game.enums import ResultArbiter, WinReason

    agents_dir = str(top / "3600-agents")
    stats = {
        "n_matches": 0,
        "floor_wins": 0, "floor_losses": 0, "ties": 0,
        "invalid": 0, "crash": 0, "timeout": 0, "mem": 0, "init_fail": 0,
        "anomalies": [],
    }

    sides = []
    if args.floor_side in ("A", "both"):
        sides.append("A")
    if args.floor_side in ("B", "both"):
        sides.append("B")

    per_side = args.n // max(1, len(sides))
    for side in sides:
        for i in range(per_side):
            try:
                board, *_ = play_game(
                    agents_dir, agents_dir,
                    "FloorBot" if side == "A" else args.opponent,
                    args.opponent if side == "A" else "FloorBot",
                    display_game=False, delay=0.0, clear_screen=False,
                    record=False, limit_resources=False,
                )
            except Exception as e:
                stats["anomalies"].append({
                    "kind": "play_game_exception", "side": side, "match": i,
                    "exc": f"{type(e).__name__}: {e}",
                })
                continue

            stats["n_matches"] += 1
            w = board.get_winner()
            r = getattr(board, "win_reason", None)

            floor_is_a = (side == "A")
            if w == ResultArbiter.TIE:
                stats["ties"] += 1
            elif (w == ResultArbiter.PLAYER_A and floor_is_a) or \
                 (w == ResultArbiter.PLAYER_B and not floor_is_a):
                stats["floor_wins"] += 1
            else:
                stats["floor_losses"] += 1

            if r == WinReason.INVALID_TURN:
                stats["invalid"] += 1
                # If the LOSER was FloorBot, that's our bug!
                floor_lost = (w == ResultArbiter.PLAYER_B) if floor_is_a else (w == ResultArbiter.PLAYER_A)
                if floor_lost:
                    stats["anomalies"].append({
                        "kind": "FLOORBOT_LOST_INVALID_TURN",
                        "match": i, "side": side,
                        "winner": w.name, "reason": r.name,
                    })
            elif r == WinReason.CODE_CRASH:
                stats["crash"] += 1
            elif r == WinReason.TIMEOUT:
                stats["timeout"] += 1
            elif r == WinReason.MEMORY_ERROR:
                stats["mem"] += 1
            elif r == WinReason.FAILED_INIT:
                stats["init_fail"] += 1

    _emit(stats, args)


if __name__ == "__main__":
    main()
