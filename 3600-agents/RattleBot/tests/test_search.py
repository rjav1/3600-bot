"""Tests for RattleBot.search / .zobrist / .move_gen -- T-14 (T-SRCH-1).

Run directly:
    python3 3600-agents/RattleBot/tests/test_search.py

Or via pytest:
    python3 -m pytest 3600-agents/RattleBot/tests/test_search.py -v
"""

from __future__ import annotations

import os
import random
import sys
import time

import numpy as np

_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
for p in (
    os.path.join(_REPO_ROOT, "engine"),
    os.path.join(_REPO_ROOT, "3600-agents"),
):
    if p not in sys.path:
        sys.path.insert(0, p)

from game.board import Board
from game.enums import Cell, MoveType, Direction
from game.move import Move

from RattleBot.move_gen import ordered_moves, immediate_delta
from RattleBot.search import Search, MATE_SCORE
from RattleBot.types import BeliefSummary
from RattleBot.zobrist import Zobrist, move_key


def _make_board(seed: int = 0) -> Board:
    rng = random.Random(seed)
    b = Board(time_to_play=240)
    # Place corners blocked per engine convention
    shapes = [(2, 3), (3, 2), (2, 2)]
    for ox, oy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        w, h = rng.choice(shapes)
        for dx in range(w):
            for dy in range(h):
                x = dx if ox == 0 else 7 - dx
                y = dy if oy == 0 else 7 - dy
                b.set_cell((x, y), Cell.BLOCKED)
    # Spawn workers in inner box
    b.player_worker.position = (2, 4)
    b.opponent_worker.position = (5, 4)
    return b


def _uniform_belief() -> BeliefSummary:
    arr = np.ones(64, dtype=np.float64) / 64.0
    return BeliefSummary(
        belief=arr,
        entropy=float(np.log(64)),
        max_mass=1.0 / 64.0,
        argmax=0,
    )


def _point_eval(board, belief=None) -> float:
    return float(
        board.player_worker.get_points() - board.opponent_worker.get_points()
    )


# ---------------------------------------------------------------------------
# Zobrist tests

def test_zobrist_determinism():
    z1 = Zobrist(seed=12345)
    z2 = Zobrist(seed=12345)
    for seed in range(5):
        b = _make_board(seed=seed)
        assert z1.hash(b) == z2.hash(b), "same seed -> same keys -> same hash"

    # Different seeds => different table => different hash (almost always)
    z3 = Zobrist(seed=99999)
    b = _make_board(seed=0)
    assert z1.hash(b) != z3.hash(b)
    print("PASS test_zobrist_determinism")


def test_zobrist_hash_sensitivity():
    z = Zobrist(seed=7)
    b1 = _make_board(seed=0)
    h1 = z.hash(b1)
    b2 = b1.get_copy()
    b2.set_cell((3, 3), Cell.PRIMED)
    h2 = z.hash(b2)
    assert h1 != h2, "cell-state change must flip hash"

    # Worker position change
    b3 = b1.get_copy()
    b3.player_worker.position = (3, 5)
    assert z.hash(b3) != h1, "worker-pos change must flip hash"

    # Side-to-move change
    b4 = b1.get_copy()
    b4.is_player_a_turn = not b4.is_player_a_turn
    assert z.hash(b4) != h1, "side flip must flip hash"
    print("PASS test_zobrist_hash_sensitivity")


def test_zobrist_collision():
    z = Zobrist(seed=0xBADDCAFE)
    rng = random.Random(5)
    seen = {}
    collisions = 0
    trials = 10000
    for _ in range(trials):
        b = Board(time_to_play=240)
        # Randomize cell states (primed/carpet/blocked bits)
        b._primed_mask = rng.getrandbits(64)
        b._carpet_mask = rng.getrandbits(64) & ~b._primed_mask
        b._blocked_mask = rng.getrandbits(64) & ~(b._primed_mask | b._carpet_mask)
        b.player_worker.position = (rng.randrange(8), rng.randrange(8))
        b.opponent_worker.position = (rng.randrange(8), rng.randrange(8))
        b.is_player_a_turn = bool(rng.getrandbits(1))
        b.turn_count = rng.randrange(80)
        h = z.hash(b)
        if h in seen:
            collisions += 1
        else:
            seen[h] = True
    rate = collisions / trials
    assert rate < 0.01, f"collision rate {rate:.4%} >= 1% over {trials} boards"
    print(f"PASS test_zobrist_collision  (rate {rate:.4%} over {trials})")


def test_move_key_uniqueness():
    # Each move-variant should map to a distinct MoveKey
    m1 = Move.plain(Direction.UP)
    m2 = Move.prime(Direction.UP)
    m3 = Move.carpet(Direction.UP, 3)
    m4 = Move.carpet(Direction.UP, 4)
    m5 = Move.search((2, 3))
    keys = {move_key(m) for m in (m1, m2, m3, m4, m5)}
    assert len(keys) == 5
    print("PASS test_move_key_uniqueness")


# ---------------------------------------------------------------------------
# move_gen tests

def test_ordered_moves_excludes_search_by_default():
    b = _make_board(seed=2)
    om = ordered_moves(b)
    assert all(m.move_type != MoveType.SEARCH for m in om)
    print("PASS test_ordered_moves_excludes_search_by_default")


def test_ordered_moves_carpet_first():
    # Construct a board where a CARPET k=3 is legal, verify it sorts ahead
    # of PRIME moves.
    b = Board(time_to_play=240)
    b.player_worker.position = (3, 3)
    b.opponent_worker.position = (7, 7)
    # Prime a 3-cell line to the right of player
    for dx in range(1, 4):
        b.set_cell((3 + dx, 3), Cell.PRIMED)
    om = ordered_moves(b)
    # First move should be a CARPET (largest k available)
    assert om, "expected legal moves"
    assert om[0].move_type == MoveType.CARPET
    print("PASS test_ordered_moves_carpet_first")


def test_ordered_moves_hash_move_promoted():
    b = _make_board(seed=4)
    legal = b.get_valid_moves()
    assert legal
    # Pick a non-first move and promote it via hash_move
    target = legal[-1]
    key = move_key(target)
    om = ordered_moves(b, hash_move=key)
    assert move_key(om[0]) == key, "hash-move should sit at index 0"
    print("PASS test_ordered_moves_hash_move_promoted")


# ---------------------------------------------------------------------------
# Minimax reference used to validate alpha-beta correctness

def _plain_minimax(board, depth, eval_fn, max_nodes=[0]):
    max_nodes[0] += 1
    if depth <= 0 or board.is_game_over():
        return eval_fn(board, None)
    moves = board.get_valid_moves(exclude_search=True)
    if not moves:
        return eval_fn(board, None)
    best = -MATE_SCORE
    for mv in moves:
        child = board.forecast_move(mv, check_ok=False)
        if child is None:
            continue
        child.reverse_perspective()
        v = -_plain_minimax(child, depth - 1, eval_fn, max_nodes)
        if v > best:
            best = v
    return best


def test_alphabeta_matches_minimax():
    b = _make_board(seed=7)
    # Small depth: 2 plies
    depth = 2
    mm_nodes = [0]
    mm_val = _plain_minimax(b, depth, _point_eval, mm_nodes)

    s = Search(zobrist=Zobrist(seed=7), tt_size=1024)
    s._eval_fn = _point_eval
    s._root_belief = _uniform_belief()
    s._deadline = time.perf_counter() + 10.0
    # Root value = max over moves of -alphabeta(child, depth-1, ...)
    legal = ordered_moves(b, exclude_search=True)
    root_val = -MATE_SCORE
    for mv in legal:
        child = b.forecast_move(mv, check_ok=False)
        if child is None:
            continue
        child.reverse_perspective()
        v = -s._alphabeta(child, depth - 1, -MATE_SCORE, MATE_SCORE, 1)
        if v > root_val:
            root_val = v
    assert abs(root_val - mm_val) < 1e-6, (
        f"alphabeta value {root_val} != minimax value {mm_val}"
    )
    assert s.nodes <= mm_nodes[0], (
        f"alphabeta visited {s.nodes} nodes, minimax {mm_nodes[0]}"
    )
    print(
        f"PASS test_alphabeta_matches_minimax  "
        f"(mm_nodes={mm_nodes[0]}, ab_nodes={s.nodes}, value={root_val})"
    )


# ---------------------------------------------------------------------------
# TT hit-rate test

def test_tt_reduces_nodes():
    b = _make_board(seed=11)
    belief = _uniform_belief()
    z = Zobrist(seed=11)

    s1 = Search(zobrist=z, tt_size=1 << 14)
    s1.iterative_deepen(b, belief, _point_eval, time_left_s=0.8, safety_s=0.05)
    first_nodes = s1.nodes
    first_hits = s1.tt_hits
    first_probes = s1.tt_probes

    # Second run reuses the SAME search engine (TT warm). It should reach
    # at least the same depth with fewer nodes OR exhibit >0 cutoffs from TT.
    s1.nodes = 0
    before_cutoffs = s1.tt_cutoffs
    s1.iterative_deepen(b, belief, _point_eval, time_left_s=0.8, safety_s=0.05)
    second_nodes = s1.nodes

    assert first_nodes > 0
    assert s1.tt_hits > first_hits, "TT hits should grow on second run"
    # Second run should benefit: either fewer nodes or non-zero cutoffs added.
    cutoffs_gained = s1.tt_cutoffs - before_cutoffs
    assert second_nodes < first_nodes or cutoffs_gained > 0, (
        f"TT did not help: first_nodes={first_nodes} second_nodes={second_nodes} "
        f"cutoffs_gained={cutoffs_gained}"
    )
    print(
        f"PASS test_tt_reduces_nodes  "
        f"(first_nodes={first_nodes}, second_nodes={second_nodes}, "
        f"tt_hits={s1.tt_hits}, tt_cutoffs={s1.tt_cutoffs})"
    )


# ---------------------------------------------------------------------------
# SEARCH-not-in-tree invariant

def test_search_not_in_tree_invariant():
    """If a SEARCH move leaks into the child list of _alphabeta, it must
    trigger an AssertionError. We simulate this by monkey-patching the
    ordered_moves import inside search.py."""
    b = _make_board(seed=13)
    belief = _uniform_belief()
    s = Search(zobrist=Zobrist(seed=13), tt_size=1024)

    import RattleBot.search as search_mod
    original = search_mod.ordered_moves

    def sneak(board, **kwargs):
        base = original(board, **kwargs)
        # Inject a SEARCH move: assertion should fire.
        return list(base) + [Move.search((0, 0))]

    search_mod.ordered_moves = sneak
    try:
        s._eval_fn = _point_eval
        s._root_belief = belief
        s._deadline = time.perf_counter() + 1.0
        triggered = False
        try:
            s._alphabeta(b, depth=1, alpha=-MATE_SCORE, beta=MATE_SCORE, ply_from_root=0)
        except AssertionError:
            triggered = True
        assert triggered, "Expected AssertionError when SEARCH leaks into move list"
    finally:
        search_mod.ordered_moves = original
    print("PASS test_search_not_in_tree_invariant")


# ---------------------------------------------------------------------------
# Iterative deepening budget compliance

def test_iterative_deepening_respects_budget():
    b = _make_board(seed=17)
    belief = _uniform_belief()
    s = Search(zobrist=Zobrist(seed=17), tt_size=1 << 14)

    start = time.perf_counter()
    mv = s.iterative_deepen(
        b, belief, _point_eval, time_left_s=1.0, safety_s=0.2
    )
    elapsed = time.perf_counter() - start

    assert mv is not None
    assert elapsed < 1.1, f"ID overran budget: {elapsed:.3f}s > 1.1s"
    assert mv.move_type != MoveType.SEARCH, "non-SEARCH expected from ID"
    print(
        f"PASS test_iterative_deepening_respects_budget  "
        f"(elapsed={elapsed*1000:.0f}ms, move={mv!r})"
    )


# ---------------------------------------------------------------------------
# Root decision returns a legal move

def test_root_decision_returns_valid_move():
    b = _make_board(seed=19)
    belief = _uniform_belief()
    s = Search(zobrist=Zobrist(seed=19), tt_size=1 << 14)

    mv = s.root_search_decision(
        b, belief, _point_eval, time_budget_s=0.5, safety_s=0.05
    )
    assert mv is not None
    legal_all = b.get_valid_moves(exclude_search=False)
    keys = {move_key(m) for m in legal_all}
    assert move_key(mv) in keys, f"move {mv!r} not in legal set"
    print(f"PASS test_root_decision_returns_valid_move  (move={mv!r})")


def test_root_decision_triggers_search_when_mass_high():
    b = _make_board(seed=23)
    # Concentrated belief: 0.9 mass on cell (3, 3) -> idx = 3*8+3 = 27
    arr = np.full(64, 0.1 / 63.0, dtype=np.float64)
    arr[27] = 0.9
    arr /= arr.sum()
    # Entropy
    entropy = float(-(arr * np.log(arr + 1e-18)).sum())
    belief = BeliefSummary(belief=arr, entropy=entropy, max_mass=0.9, argmax=27)

    # Heuristic returns ~0 so SEARCH ev ~= 6*0.9 - 2 + bonuses = 3.4+ wins
    def zero_eval(board, b=None):
        return 0.0

    s = Search(
        zobrist=Zobrist(seed=23),
        tt_size=1 << 12,
        gamma_info=0.5,
        gamma_reset=0.3,
        eps_tiebreak=0.25,
    )
    mv = s.root_search_decision(
        b, belief, zero_eval, time_budget_s=0.3, safety_s=0.05
    )
    assert mv.move_type == MoveType.SEARCH, (
        f"Expected SEARCH when p=0.9, got {mv!r}"
    )
    assert mv.search_loc == (3, 3), f"Expected (3,3), got {mv.search_loc}"
    print(f"PASS test_root_decision_triggers_search_when_mass_high  ({mv!r})")


# ---------------------------------------------------------------------------
# Runner

def _run_all():
    tests = [
        test_zobrist_determinism,
        test_zobrist_hash_sensitivity,
        test_zobrist_collision,
        test_move_key_uniqueness,
        test_ordered_moves_excludes_search_by_default,
        test_ordered_moves_carpet_first,
        test_ordered_moves_hash_move_promoted,
        test_alphabeta_matches_minimax,
        test_tt_reduces_nodes,
        test_search_not_in_tree_invariant,
        test_iterative_deepening_respects_budget,
        test_root_decision_returns_valid_move,
        test_root_decision_triggers_search_when_mass_high,
    ]
    failures = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            failures += 1
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return failures


if __name__ == "__main__":
    rc = _run_all()
    sys.exit(0 if rc == 0 else 1)
