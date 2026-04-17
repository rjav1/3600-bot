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
    """With a warm TT, second call should either hit more depth, have
    TT-based cutoffs, or reach the same move with fewer nodes."""
    b = _make_board(seed=11)
    belief = _uniform_belief()
    z = Zobrist(seed=11)

    s1 = Search(zobrist=z, tt_size=1 << 14)
    s1.iterative_deepen(b, belief, _point_eval, time_left_s=0.8, safety_s=0.05)
    first_stats = s1.get_stats()
    first_nodes = first_stats["nodes"]
    first_depth = first_stats["last_depth_reached"]

    # Second run reuses the SAME engine (warm TT).
    s1.iterative_deepen(b, belief, _point_eval, time_left_s=0.8, safety_s=0.05)
    second_stats = s1.get_stats()
    second_nodes = second_stats["nodes"]
    second_depth = second_stats["last_depth_reached"]
    tt_cutoffs = second_stats["tt_cutoffs"]

    assert first_nodes > 0
    # Warm TT must produce real work-savings signal: either deeper, or
    # fewer nodes at the same depth, or TT-flag cutoffs fired.
    saved = (
        second_depth > first_depth
        or (second_depth == first_depth and second_nodes < first_nodes)
        or tt_cutoffs > 0
    )
    assert saved, (
        f"TT did not help: first_nodes={first_nodes}@d{first_depth} "
        f"second_nodes={second_nodes}@d{second_depth} tt_cutoffs={tt_cutoffs}"
    )
    print(
        f"PASS test_tt_reduces_nodes  "
        f"(d1={first_depth} n1={first_nodes}  d2={second_depth} n2={second_nodes} "
        f"tt_cutoffs={tt_cutoffs})"
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
# T-20e: move-ordering instrumentation + audit tests

def test_get_stats_schema():
    """`get_stats()` returns all T-20e telemetry fields."""
    b = _make_board(seed=29)
    belief = _uniform_belief()
    s = Search(zobrist=Zobrist(seed=29), tt_size=1 << 14)
    s.iterative_deepen(b, belief, _point_eval, time_left_s=0.3, safety_s=0.05)
    stats = s.get_stats()
    required = [
        "nodes", "leaves", "last_depth_reached",
        "tt_probes", "tt_hits", "tt_hit_rate", "tt_cutoffs",
        "tt_stores", "tt_replacements",
        "hash_move_attempts", "hash_move_legal", "hash_move_first",
        "killer_slot_0_hits", "killer_slot_1_hits",
        "history_reorder_count",
        "cutoffs_total", "cutoff_on_first_move",
        "cutoff_on_first_rate", "cutoff_on_nth_move",
    ]
    missing = [k for k in required if k not in stats]
    assert not missing, f"stats missing keys: {missing}"
    assert isinstance(stats["cutoff_on_nth_move"], list)
    assert len(stats["cutoff_on_nth_move"]) == 8
    print(f"PASS test_get_stats_schema  ({len(required)} fields present)")


def test_ordering_stack_fires():
    """Hash-move, killer, and history tiers all must produce > 0 hits in a
    non-trivial search."""
    b = _make_board(seed=31)
    belief = _uniform_belief()
    s = Search(zobrist=Zobrist(seed=31), tt_size=1 << 14)
    # Deep enough budget to warm the TT + history + killers.
    s.iterative_deepen(b, belief, _point_eval, time_left_s=1.5, safety_s=0.1)
    stats = s.get_stats()

    assert stats["hash_move_attempts"] > 0, "TT never offered a hash move"
    assert stats["hash_move_legal"] > 0, "hash moves never matched a legal move"
    assert stats["hash_move_first"] > 0, "hash move never sat at ordered[0]"
    # Cutoffs must happen
    assert stats["cutoffs_total"] > 0, "no beta-cutoffs in tree"
    # Killer table must get populated and lead to at least some slot-0 hits
    killer_hits = stats["killer_slot_0_hits"] + stats["killer_slot_1_hits"]
    assert killer_hits > 0, "killer slots never led ordered[0]"
    # History must influence ordering at least once
    assert stats["history_reorder_count"] > 0, "history never influenced ordering"
    print(
        f"PASS test_ordering_stack_fires  "
        f"(hash_first={stats['hash_move_first']}, "
        f"killer_hits={killer_hits}, "
        f"history_reorder={stats['history_reorder_count']}, "
        f"cutoff_first_rate={stats['cutoff_on_first_rate']:.2f})"
    )


def _apply_any_move(board):
    """Advance board by one legal (non-SEARCH) move in each perspective.

    Mutates by applying the move, reversing perspective, and returning the
    mutated board so the caller can use it as the next 'current' state.
    """
    legal = board.get_valid_moves(exclude_search=True)
    if not legal:
        return board
    # Prefer CARPET/PRIME to change the cell masks (more TT churn = more
    # realistic evolving-board scenario).
    legal.sort(key=lambda m: (m.move_type, -(m.roll_length or 0)))
    for mv in legal:
        ok = board.apply_move(mv, check_ok=False)
        if ok:
            break
    board.reverse_perspective()
    return board


def test_tt_hit_rate_20_calls():
    """Run 20 consecutive searches on an evolving board.

    T-20e gate (relative to BOT_STRATEGY addendum §2.3): confirms the
    ordering/TT pipeline keeps firing across real game turns. We check:
      - TT hit-rate across calls 10-19 remains > 40 % (the T-SRCH-3 gate
        is > 15 %; iterative-deepening naturally re-probes positions as
        early-depth iterations warm the TT for deeper ones, so 40 % is
        the correct realistic ceiling on an evolving board at depth 5-9);
      - cutoff_on_first_rate > 0.60 (§2.3 hard gate — measures that move
        ordering is actually producing best-move-first cutoffs);
      - TT cutoffs happen on most calls (proves the TT is consulted).
    """
    b = _make_board(seed=37)
    belief = _uniform_belief()
    s = Search(zobrist=Zobrist(seed=37), tt_size=1 << 16)

    per_call_probes = []
    per_call_hits = []
    per_call_depth = []
    per_call_first_rate = []
    per_call_tt_cutoffs = []
    for _ in range(20):
        s.iterative_deepen(b, belief, _point_eval, time_left_s=0.25, safety_s=0.05)
        stats = s.get_stats()
        per_call_probes.append(stats["tt_probes"])
        per_call_hits.append(stats["tt_hits"])
        per_call_depth.append(stats["last_depth_reached"])
        per_call_first_rate.append(stats["cutoff_on_first_rate"])
        per_call_tt_cutoffs.append(stats["tt_cutoffs"])
        b = _apply_any_move(b)

    late_probes = sum(per_call_probes[10:])
    late_hits = sum(per_call_hits[10:])
    late_rate = late_hits / late_probes if late_probes else 0.0

    assert late_probes > 0, "no probes in late-half calls"
    # Hit-rate on calls 10-19 must clear the realistic >40% bar.
    assert late_rate > 0.40, (
        f"TT hit-rate calls 10-19 = {late_rate:.3f}; gate is >0.40. "
        f"per-call probes={per_call_probes} hits={per_call_hits}"
    )
    # First-move-cutoff rate must be > 0.60 averaged over late calls.
    late_first_rate = (
        sum(per_call_first_rate[10:]) / len(per_call_first_rate[10:])
    )
    assert late_first_rate > 0.60, (
        f"cutoff_on_first_rate calls 10-19 = {late_first_rate:.3f}; gate >0.60"
    )
    # At least 80 % of late calls must see >= 1 TT cutoff.
    late_with_cutoff = sum(1 for c in per_call_tt_cutoffs[10:] if c > 0)
    assert late_with_cutoff >= 8, (
        f"only {late_with_cutoff}/10 late calls had TT cutoffs"
    )
    avg_depth = sum(per_call_depth) / len(per_call_depth)
    print(
        f"PASS test_tt_hit_rate_20_calls  "
        f"(late_rate={late_rate:.3f}, late_first_cutoff={late_first_rate:.3f}, "
        f"avg_depth={avg_depth:.1f}, late_calls_with_tt_cutoff={late_with_cutoff}/10)"
    )


def test_killer_move_promoted():
    """When a killer slot holds a MoveKey that matches a legal move, the
    returned `ordered_moves` list places that killer at or near the front
    (ahead of type-priority tier)."""
    from RattleBot.move_gen import ordered_moves as om
    b = _make_board(seed=41)
    legal = b.get_valid_moves(exclude_search=True)
    assert legal
    # Pick a PLAIN move that would normally sort LAST by type-priority.
    target = None
    for m in legal:
        if m.move_type == MoveType.PLAIN:
            target = m
            break
    assert target is not None, "fixture expects at least one PLAIN legal"
    target_key = move_key(target)

    # With no killer, the PLAIN move should NOT lead.
    baseline = om(b, history=None, killers=None)
    assert move_key(baseline[0]) != target_key or len(baseline) == 1, (
        "fixture assumption: PLAIN shouldn't be ordered[0] by default"
    )

    # With killer slot 0 set to the PLAIN move, it must lead.
    promoted = om(b, killers=[target_key, None])
    assert move_key(promoted[0]) == target_key, (
        f"killer slot 0 failed to promote; got {promoted[0]!r}"
    )
    # Killer slot 1 should also promote when slot 0 is None or non-matching
    promoted2 = om(b, killers=[None, target_key])
    assert move_key(promoted2[0]) == target_key
    print("PASS test_killer_move_promoted")


def test_history_reorder_monotone():
    """Repeated cutoffs on a MoveKey must increase its history priority so
    that, all else equal, ordered_moves promotes it."""
    from RattleBot.move_gen import ordered_moves as om
    b = _make_board(seed=43)
    legal = b.get_valid_moves(exclude_search=True)
    assert legal
    # Pick a PLAIN move (lowest default priority tier among non-k=1 moves).
    target = next((m for m in legal if m.move_type == MoveType.PLAIN), None)
    assert target is not None
    tkey = move_key(target)

    # With no history, target is typically not first.
    base = om(b)
    base_idx = next(
        (i for i, m in enumerate(base) if move_key(m) == tkey), None
    )
    assert base_idx is not None

    # Incrementally increase history; find the point where target sits
    # ahead of the type-0 (CARPET-k>=2) block or at least moves forward.
    history: Dict[MoveKey, int] = {}
    for _ in range(50):
        history[tkey] = history.get(tkey, 0) + 1
    out = om(b, history=history)
    new_idx = next(i for i, m in enumerate(out) if move_key(m) == tkey)

    # Higher-priority CARPET moves (same type bucket) still come first, but
    # among same-type bucket, the target should tie/precede other PLAIN
    # moves. The clearest assertion: position does not get WORSE, and any
    # PLAIN that lacks history cannot outrank our target.
    assert new_idx <= base_idx, (
        f"history did not help; base_idx={base_idx} new_idx={new_idx}"
    )
    # Among same-bucket PLAIN moves, target comes first.
    plain_order = [m for m in out if m.move_type == MoveType.PLAIN]
    assert plain_order and move_key(plain_order[0]) == tkey, (
        "history did not reorder within PLAIN bucket"
    )
    print(
        f"PASS test_history_reorder_monotone  (base_idx={base_idx}, new_idx={new_idx})"
    )


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
        test_get_stats_schema,
        test_ordering_stack_fires,
        test_tt_hit_rate_20_calls,
        test_killer_move_promoted,
        test_history_reorder_monotone,
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
