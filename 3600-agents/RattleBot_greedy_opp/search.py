"""Alpha-beta + iterative deepening + Zobrist TT for RattleBot.

Per BOT_STRATEGY.md v1.1 §2.a / §2.d / §2.f / §2.g / §3.3 and v0.2 addendum
§2.3 T-20e (move-ordering instrumentation).

Belief is a leaf potential (D-004); SEARCH is root-only (D-011 item 2).
Time safety margin: 0.5 s (D-011 item 4). v0.2 adds `get_stats()` telemetry
covering the full ordering stack (hash-move, killer, history, TT, cutoffs).

v0.7 (RattleBot_greedy_opp fork, 2026-04-18, phase2-shipper): BS-2 per
docs/audit/CONTRARIAN_APR18.md. Stock α-β treats the opponent as a pure
minimax-against-our-heuristic demon, but replay data (Carrie err_b≈12-14,
Rusty ~120s of 240s used, top-teams 100s unused) shows real opponents
play fixed-heuristic greedy — they don't minimax us. Our 97.9%
cutoff-on-first-move rate confirms we're paying for depth we don't
exploit. With `SEARCH_ASSUME_GREEDY_OPP=True`, at opp-to-move nodes
(odd `ply_from_root`) we skip the negamax enumeration and descend into
a single greedy-opp reply chosen by `(immediate_delta + opp-perspective
cell_potential)`. Branch factor at opp plies drops from ~7 to 1, so the
same compute buys ~7× more depth along the realistic game line.
`SEARCH_ASSUME_GREEDY_OPP=False` restores prior v0.4.2 negamax behavior
(tested: tree is identical).
"""

from __future__ import annotations

import math
import time as _time
from typing import Callable, Dict, List, Optional, Tuple

from game.enums import MoveType
from game.move import Move

from .move_gen import ordered_moves, immediate_delta
from .types import (
    BeliefSummary, MoveKey, TTEntry,
    TT_FLAG_EXACT, TT_FLAG_LOWER, TT_FLAG_UPPER,
)
from .zobrist import Zobrist, move_key

__all__ = [
    "Search", "SearchEngine", "MATE_SCORE", "DRAW_SCORE", "MAX_DEPTH",
    "SEARCH_ASSUME_GREEDY_OPP", "GREEDY_OPP_CP_WEIGHT",
]


# ---------------------------------------------------------------------------
# BS-2 gate (docs/audit/CONTRARIAN_APR18.md §1 BS-2).
#
# When True: at opp-to-move nodes (odd `ply_from_root` in the negamax
# recursion, i.e. the `board` argument was reverse_perspective'd so that
# `board.player_worker` is the real opponent), replace the negamax
# enumeration of all opp moves with a 1-ply greedy opp model and
# continue down the single greedy child. Yields ~7× effective depth at
# the same compute.
#
# When False: strict negamax (prior v0.4.2 behavior). Used by
# `tests/test_greedy_opp.py` to verify tree identity under the gate.
SEARCH_ASSUME_GREEDY_OPP: bool = True

# Greedy-opp scoring: `immediate_delta + w * cell_potential(opp)`.
# The cell_potential term lets opp prefer moves that reach/extend
# prime-lines even when the immediate +1 / k-roll is tied — closer to
# the fixed-heuristic greedy that real student bots + Carrie use.
# Weight 0.25 chosen to match F5/F7's BO-tuned leaf weight magnitude
# (cell_potential is typically a few points; we want it to tie-break,
# not dominate `immediate_delta` when a k=3 (+4) is available vs a
# k=2 (+2) w/ slightly higher cp).
GREEDY_OPP_CP_WEIGHT: float = 0.25


MATE_SCORE: float = 1e9
DRAW_SCORE: float = 0.0
MAX_DEPTH: int = 32

# v0.4.2 BS-3 light: opp-reach carpet penalty coefficient.
# Per CONTRARIAN_APR18.md §1 BS-3 and Phase 1 §1: rolling carpets inside
# the opp's 2-step reach gifts them free mobility on primes we paid for.
# The linear heuristic has no feature encoding this asymmetry (F4 is
# perspective-invariant; it zeros out in self-play). We subtract a flat
# 0.5 * opp_reach_factor * new_carpet_count at the root, where
# opp_reach_factor = popcount(new_carpets ∩ opp_manhattan_2_mask) /
# max(1, popcount(new_carpets)). This pushes big rolls away from the
# opponent's immediate sphere of influence without disturbing the
# leaf-eval BO surface.
BS3_CARPET_OPP_REACH_COEF: float = 0.5
_TIME_CHECK_EVERY = 1024
# T-40c-prereq: at depths >= 6 where leaf eval dominates runtime, use
# a tighter 256-node cadence. Bounds worst-case post-check overshoot
# to ~15 ms (256 leaves × ~60 µs/leaf) vs ~60 ms at 1024.
_TIME_CHECK_DEEP = 256
_CUTOFF_HIST_BUCKETS = 8  # index i = cutoff on i-th move (i>=7 clamps to 7)


class _TimeUp(Exception):
    """Internal signal -- caught by `iterative_deepen`."""


class Search:
    """Alpha-beta + iterative deepening + two-slot Zobrist TT.

    TT: slot 0 depth-preferred, slot 1 always-replace. Both probed on hit.

    v0.2 telemetry (per `get_stats()`):
        nodes, leaves           -- counters reset at every iterative_deepen
        tt_probes, tt_hits, tt_cutoffs, tt_stores, tt_replacements
        hash_move_attempts      -- nodes where a TT best_move was offered
        hash_move_legal         -- subset where the hash-move was legal
        hash_move_first         -- subset where the hash-move sat at slot 0
        killer_slot_0_hits      -- nodes where ordered[0] == killers_here[0]
        killer_slot_1_hits      -- nodes where ordered[0] == killers_here[1]
        history_reorder_count   -- nodes where a non-empty history dict had
                                    at least one legal-move match (i.e.
                                    history actually influenced ordering)
        cutoffs_total           -- sum of beta-cutoffs
        cutoff_on_first_move    -- beta-cutoffs on ordered[0]
        cutoff_on_nth_move[i]   -- beta-cutoffs on ordered[i] (0..7 clamp)
    """

    def __init__(
        self,
        zobrist: Optional[Zobrist] = None,
        tt_size: int = 1 << 20,
        gamma_info: float = 0.5,
        gamma_reset: float = 0.3,
        eps_tiebreak: float = 0.25,
    ) -> None:
        self.zobrist = zobrist if zobrist is not None else Zobrist()
        if tt_size <= 0 or (tt_size & (tt_size - 1)) != 0:
            p = 1
            while p < max(1, tt_size):
                p <<= 1
            tt_size = p
        self.tt_size = tt_size
        self.tt_mask = tt_size - 1
        self.tt: List[List[Optional[TTEntry]]] = [
            [None, None] for _ in range(tt_size)
        ]

        self.gamma_info = float(gamma_info)
        self.gamma_reset = float(gamma_reset)
        self.eps_tiebreak = float(eps_tiebreak)

        self.killers: List[List[Optional[MoveKey]]] = [
            [None, None] for _ in range(MAX_DEPTH + 1)
        ]
        self.history: Dict[MoveKey, int] = {}

        self._deadline: float = float("inf")
        self._eval_fn: Optional[Callable[..., float]] = None
        self._root_belief: Optional[BeliefSummary] = None

        self._init_counters()

    def _init_counters(self) -> None:
        self.nodes = 0
        self.leaves = 0
        self.tt_probes = 0
        self.tt_hits = 0
        self.tt_cutoffs = 0
        self.tt_stores = 0
        self.tt_replacements = 0

        self.hash_move_attempts = 0
        self.hash_move_legal = 0
        self.hash_move_first = 0
        self.killer_slot_0_hits = 0
        self.killer_slot_1_hits = 0
        self.history_reorder_count = 0

        self.cutoffs_total = 0
        self.cutoff_on_first_move = 0
        self.cutoff_on_nth_move = [0] * _CUTOFF_HIST_BUCKETS

        self.last_depth_reached = 0

    def get_stats(self) -> Dict[str, object]:
        """Snapshot telemetry from the most recent `iterative_deepen`."""
        tt_hit_rate = (
            self.tt_hits / self.tt_probes if self.tt_probes else 0.0
        )
        first_cutoff_rate = (
            self.cutoff_on_first_move / self.cutoffs_total
            if self.cutoffs_total else 0.0
        )
        return {
            "nodes": self.nodes,
            "leaves": self.leaves,
            "last_depth_reached": self.last_depth_reached,
            "tt_probes": self.tt_probes,
            "tt_hits": self.tt_hits,
            "tt_hit_rate": tt_hit_rate,
            "tt_cutoffs": self.tt_cutoffs,
            "tt_stores": self.tt_stores,
            "tt_replacements": self.tt_replacements,
            "hash_move_attempts": self.hash_move_attempts,
            "hash_move_legal": self.hash_move_legal,
            "hash_move_first": self.hash_move_first,
            "killer_slot_0_hits": self.killer_slot_0_hits,
            "killer_slot_1_hits": self.killer_slot_1_hits,
            "history_reorder_count": self.history_reorder_count,
            "cutoffs_total": self.cutoffs_total,
            "cutoff_on_first_move": self.cutoff_on_first_move,
            "cutoff_on_first_rate": first_cutoff_rate,
            "cutoff_on_nth_move": list(self.cutoff_on_nth_move),
        }

    # -- TT ------------------------------------------------------------

    def reset_tt(self) -> None:
        for bucket in self.tt:
            bucket[0] = None
            bucket[1] = None
        self._init_counters()

    def _probe_tt(self, key: int) -> Optional[TTEntry]:
        self.tt_probes += 1
        bucket = self.tt[key & self.tt_mask]
        for slot in bucket:
            if slot is not None and slot.zobrist_key == key:
                self.tt_hits += 1
                return slot
        return None

    def _store_tt(self, key, depth, value, flag, best_move, age):
        entry = TTEntry(
            zobrist_key=key, depth=depth, value=float(value),
            flag=flag, best_move=best_move, age=age,
        )
        bucket = self.tt[key & self.tt_mask]
        slot0 = bucket[0]
        if slot0 is None:
            bucket[0] = entry
        elif depth >= slot0.depth:
            if slot0.zobrist_key != key:
                self.tt_replacements += 1
            bucket[0] = entry
        if bucket[1] is not None and bucket[1].zobrist_key != key:
            self.tt_replacements += 1
        bucket[1] = entry
        self.tt_stores += 1

    # -- time ----------------------------------------------------------

    def _time_check(self) -> None:
        if _time.perf_counter() >= self._deadline:
            raise _TimeUp()

    # -- iterative deepening ------------------------------------------

    def iterative_deepen(
        self,
        board,
        belief: BeliefSummary,
        eval_fn: Callable[..., float],
        time_left_s: float,
        safety_s: float = 0.5,
    ) -> Move:
        """Iteratively deepen until time runs out; return the best non-SEARCH
        move from the deepest completed iteration. Per-call telemetry is
        reset at entry and available via `get_stats()` after return.
        """
        self._root_belief = belief
        self._eval_fn = eval_fn
        start = _time.perf_counter()
        budget = max(0.0, float(time_left_s) - float(safety_s))
        self._deadline = start + budget

        self._init_counters()

        legal = ordered_moves(board, exclude_search=True)
        if not legal:
            legal = board.get_valid_moves(exclude_search=False)
            if not legal:
                return Move.search((0, 0))
            return legal[0]

        best_move: Move = legal[0]

        for depth in range(1, MAX_DEPTH + 1):
            try:
                _, move = self._root_search(board, depth, legal, best_move)
                best_move = move
                self.last_depth_reached = depth
                legal = self._reorder_pv_first(legal, move)
            except _TimeUp:
                break
            if _time.perf_counter() >= self._deadline:
                break
        return best_move

    def _reorder_pv_first(self, legal: List[Move], pv: Move) -> List[Move]:
        pv_k = move_key(pv)
        out = [m for m in legal if move_key(m) == pv_k]
        out.extend(m for m in legal if move_key(m) != pv_k)
        return out

    def _root_search(self, board, depth, legal, prev_best):
        alpha = -MATE_SCORE
        beta = MATE_SCORE
        best_val = -MATE_SCORE
        best_move: Move = prev_best

        root_key = self.zobrist.hash(board)
        tt_entry = self._probe_tt(root_key)
        hash_mk = tt_entry.best_move if tt_entry else None
        killers_here = self.killers[depth]
        ordered = ordered_moves(
            board, hash_move=hash_mk, killers=killers_here,
            history=self.history, exclude_search=True,
        )
        if not ordered:
            ordered = legal

        self._record_ordering_stats(ordered, hash_mk, killers_here)

        age = board.turn_count
        parent_carpet_mask = int(getattr(board, "_carpet_mask", 0))
        for mv in ordered:
            # T-40c-prereq: per-child deadline check at the root so a
            # single deep child subtree can't carry us past the budget.
            # Raises `_TimeUp` which iterative_deepen catches.
            self._time_check()
            child = board.forecast_move(mv, check_ok=False)
            if child is None:
                continue
            # v0.4.2 BS-3 light: compute opp-reach carpet penalty for
            # this root edge BEFORE reverse_perspective (so child's
            # `opponent_worker` is still the real opponent, the one
            # who can walk on the carpet we just laid).
            carpet_penalty = 0.0
            if int(mv.move_type) == int(MoveType.CARPET):
                carpet_penalty = _bs3_carpet_opp_reach_penalty(
                    parent_carpet_mask,
                    int(getattr(child, "_carpet_mask", 0)),
                    child.opponent_worker.position,
                )
            child.reverse_perspective()
            v = -self._alphabeta(child, depth - 1, -beta, -alpha, 1)
            v -= carpet_penalty
            if v > best_val:
                best_val = v
                best_move = mv
                if v > alpha:
                    alpha = v

        self._store_tt(root_key, depth, best_val, TT_FLAG_EXACT,
                       move_key(best_move), age)
        return best_val, best_move

    # -- ordering telemetry -------------------------------------------

    def _record_ordering_stats(
        self,
        ordered: List[Move],
        hash_mk: Optional[MoveKey],
        killers_here: Optional[List[Optional[MoveKey]]],
    ) -> None:
        if not ordered:
            return
        first_key = move_key(ordered[0])

        hash_matched = False
        if hash_mk is not None:
            self.hash_move_attempts += 1
            for m in ordered:
                if move_key(m) == hash_mk:
                    self.hash_move_legal += 1
                    break
            if first_key == hash_mk:
                self.hash_move_first += 1
                hash_matched = True

        if not hash_matched and killers_here is not None:
            k0 = killers_here[0]
            k1 = killers_here[1]
            if k0 is not None and first_key == k0:
                self.killer_slot_0_hits += 1
            elif k1 is not None and first_key == k1:
                self.killer_slot_1_hits += 1

        if self.history:
            for m in ordered:
                if self.history.get(move_key(m), 0) > 0:
                    self.history_reorder_count += 1
                    break

    # -- alpha-beta (negamax) -----------------------------------------

    def _alphabeta(self, board, depth, alpha, beta, ply_from_root):
        self.nodes += 1
        # T-40c-prereq: tighten cadence at deep iterations. Leaves at
        # d≥6 are dominant in runtime, so the 1024-node stride could
        # overshoot a per-move budget by hundreds of ms. At d<6 the
        # 1024 stride keeps check overhead amortized.
        if depth >= 6:
            check_mask = _TIME_CHECK_DEEP - 1
        else:
            check_mask = _TIME_CHECK_EVERY - 1
        if (self.nodes & check_mask) == 0:
            self._time_check()

        if board.is_game_over():
            return self._terminal_value(board)
        if depth <= 0:
            self.leaves += 1
            return self._eval_leaf(board)

        # --- BS-2 greedy-opp branch (docs/audit/CONTRARIAN_APR18.md) ---
        # At odd `ply_from_root` the board has been reverse_perspective'd
        # by the caller, so `board.player_worker` is the real opponent.
        # Instead of enumerating all of opp's moves and picking the
        # one that minimizes our value (the pure-negamax straw-man
        # model), we descend into a SINGLE greedy opp-move and keep
        # alpha-beta only along our own plies. Branch factor at opp
        # plies drops from ~7 to 1.
        #
        # Gate check goes BEFORE TT / ordered_moves so the TT never
        # stores a value computed under the minimax branch at an
        # opp-ply key under the greedy-opp branch (avoids a TT
        # poisoning bug when toggling the gate at runtime).
        if SEARCH_ASSUME_GREEDY_OPP and (ply_from_root & 1) == 1:
            return self._alphabeta_greedy_opp(
                board, depth, alpha, beta, ply_from_root,
            )

        alpha0 = alpha
        key = self.zobrist.hash(board)
        tt_entry = self._probe_tt(key)
        hash_mk: Optional[MoveKey] = None
        if tt_entry is not None:
            hash_mk = tt_entry.best_move
            if tt_entry.depth >= depth:
                v = tt_entry.value
                f = tt_entry.flag
                if f == TT_FLAG_EXACT:
                    return v
                if f == TT_FLAG_LOWER and v > alpha:
                    alpha = v
                elif f == TT_FLAG_UPPER and v < beta:
                    beta = v
                if alpha >= beta:
                    self.tt_cutoffs += 1
                    return v

        killers_here = (
            self.killers[depth] if 0 <= depth < len(self.killers) else None
        )
        ordered = ordered_moves(
            board, hash_move=hash_mk, killers=killers_here,
            history=self.history, exclude_search=True,
        )
        assert all(
            m.move_type != MoveType.SEARCH for m in ordered
        ), "SEARCH must never enter the in-tree move list"

        if not ordered:
            self.leaves += 1
            return self._eval_leaf(board)

        self._record_ordering_stats(ordered, hash_mk, killers_here)

        best_val = -MATE_SCORE
        best_mk: Optional[MoveKey] = None
        move_idx = -1
        for mv in ordered:
            move_idx += 1
            child = board.forecast_move(mv, check_ok=False)
            if child is None:
                continue
            child.reverse_perspective()
            v = -self._alphabeta(child, depth - 1, -beta, -alpha, ply_from_root + 1)
            if v > best_val:
                best_val = v
                best_mk = move_key(mv)
            if v > alpha:
                alpha = v
            if alpha >= beta:
                self.cutoffs_total += 1
                bucket = move_idx if move_idx < _CUTOFF_HIST_BUCKETS else (
                    _CUTOFF_HIST_BUCKETS - 1
                )
                self.cutoff_on_nth_move[bucket] += 1
                if move_idx == 0:
                    self.cutoff_on_first_move += 1
                mk = move_key(mv)
                if killers_here is not None and killers_here[0] != mk:
                    killers_here[1] = killers_here[0]
                    killers_here[0] = mk
                self.history[mk] = self.history.get(mk, 0) + depth * depth
                break

        if best_val <= alpha0:
            flag = TT_FLAG_UPPER
        elif best_val >= beta:
            flag = TT_FLAG_LOWER
        else:
            flag = TT_FLAG_EXACT
        self._store_tt(key, depth, best_val, flag, best_mk, board.turn_count)
        return best_val

    # -- BS-2 greedy-opp branch ---------------------------------------

    def _alphabeta_greedy_opp(self, board, depth, alpha, beta, ply_from_root):
        """Single-child negamax step at an opp-to-move node.

        Pick ONE opp move via `_greedy_opp_move` (scored as
        `immediate_delta + GREEDY_OPP_CP_WEIGHT * cp_opp`), forecast,
        reverse_perspective, and recurse into `_alphabeta` for the
        next (our-to-move) ply. No move enumeration, no TT store at
        this node (the value is derivative of downstream work and TT
        semantics differ between gate modes — storing it would cause
        gate-toggle TT aliasing).
        """
        mv = self._greedy_opp_move(board)
        if mv is None:
            self.leaves += 1
            return self._eval_leaf(board)
        child = board.forecast_move(mv, check_ok=False)
        if child is None:
            self.leaves += 1
            return self._eval_leaf(board)
        child.reverse_perspective()
        v = -self._alphabeta(child, depth - 1, -beta, -alpha, ply_from_root + 1)
        return v

    def _greedy_opp_move(self, board) -> Optional[Move]:
        """Return opp's single greedy reply at the current board.

        `board` is expected to have been `reverse_perspective()`'d by
        the caller, so `board.player_worker` IS the real opponent.
        Score each legal non-SEARCH move by:
            score = immediate_delta(m) + GREEDY_OPP_CP_WEIGHT * cp_opp
        where `cp_opp` is `_cell_potential_for_worker` evaluated from
        opp's worker position (opp is the one making this move, so we
        pass `board.player_worker` as the subject).

        On tie, the earliest move in the `ordered_moves` list wins
        (matches the move-ordering type-priority that real greedy
        bots implicitly follow: CARPET(k≥2) > PRIME > PLAIN).
        Returns None if no legal non-SEARCH move exists.
        """
        # Pass no hash_move / killers / history so the ordering reflects
        # raw type-priority (what a fixed-heuristic greedy bot would
        # see). Our-ply history-heuristic state is irrelevant to opp's
        # move choice; and using hash-move here would cause the greedy
        # child to depend on TT contents, breaking determinism tests.
        ordered = ordered_moves(board, exclude_search=True)
        if not ordered:
            return None

        # Lazy import: heuristic.py is large; import at call time to
        # avoid any test-time circular-import risk.
        from .heuristic import _cell_potential_for_worker

        best_move: Optional[Move] = None
        best_score = -math.inf

        # Score each legal non-SEARCH move by its POST-FORECAST state
        # from opp's own perspective:
        #     score = immediate_delta(m)
        #           + GREEDY_OPP_CP_WEIGHT * cp(child_opp, child_us)
        # where child.player_worker is still opp (we did NOT call
        # reverse_perspective after forecast_move). This mirrors how a
        # fixed-heuristic greedy bot scores moves: the +Δ it banks
        # (immediate_delta) plus the positional value it gains
        # (cell_potential) in the state that results.
        for m in ordered:
            child = board.forecast_move(m, check_ok=False)
            if child is None:
                continue
            try:
                ox, oy = child.player_worker.position
                wx, wy = child.opponent_worker.position
                cp = float(_cell_potential_for_worker(child, ox, oy, wx, wy))
            except Exception:
                cp = 0.0
            s = float(immediate_delta(m)) + GREEDY_OPP_CP_WEIGHT * cp
            if s > best_score:
                best_score = s
                best_move = m

        # If every forecast failed (degenerate), fall back to the
        # first ordered move so we always return something legal.
        if best_move is None:
            return ordered[0]
        return best_move

    # -- leaf / terminal ----------------------------------------------

    def _eval_leaf(self, board) -> float:
        fn = self._eval_fn
        bs = self._root_belief
        if fn is None:
            return _point_diff(board)
        try:
            return float(fn(board, bs))
        except TypeError:
            return float(fn(board))

    def _terminal_value(self, board) -> float:
        return _point_diff(board)

    # -- root SEARCH-vs-non-SEARCH gate -------------------------------

    def root_search_decision(
        self,
        board,
        belief: BeliefSummary,
        eval_fn: Callable[..., float],
        time_budget_s: float,
        safety_s: float = 0.5,
    ) -> Move:
        """Compare (best non-SEARCH move value) vs (best SEARCH EV).

        EV_search = 6p - 2 + gamma_info * dH - gamma_reset * p * H(p_0)
        """
        best_move = self.iterative_deepen(
            board, belief, eval_fn, time_budget_s, safety_s
        )
        root_key = self.zobrist.hash(board)
        entry = self._probe_tt(root_key)
        best_value = entry.value if entry is not None else 0.0

        loc, ev = self._best_search_ev(board, belief)
        if loc is None:
            return best_move
        if ev > best_value + self.eps_tiebreak:
            return Move.search(loc)
        return best_move

    def _best_search_ev(self, board, belief: BeliefSummary):
        b = belief.belief
        if b is None or len(b) != 64:
            return None, -math.inf
        idx = int(belief.argmax)
        p = float(belief.max_mass)
        H_before = float(belief.entropy)
        s = 1.0 - p
        if s <= 1e-12:
            H_miss = 0.0
        else:
            H_miss = 0.0
            for i in range(64):
                if i == idx:
                    continue
                v = float(b[i])
                if v <= 0.0:
                    continue
                q = v / s
                H_miss -= q * math.log(q + 1e-18)
        dH = max(0.0, H_before - ((1.0 - p) * H_miss))
        H_p0 = math.log(64.0)
        ev = 6.0 * p - 2.0 + self.gamma_info * dH - self.gamma_reset * p * H_p0
        x = idx % 8
        y = idx // 8
        return (x, y), ev


SearchEngine = Search


def _point_diff(board) -> float:
    try:
        return float(
            board.player_worker.get_points() - board.opponent_worker.get_points()
        )
    except Exception:
        return 0.0


def _manhattan_2_mask(x: int, y: int) -> int:
    """64-bit mask of cells whose Manhattan distance from (x,y) is ≤ 2.

    Used by BS-3 to measure how much of a new carpet lies within the
    opponent's 2-step reach. ≤ 13 cells on the interior; edges/corners
    clip naturally via the 0..7 bounds check.
    """
    m = 0
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            if abs(dx) + abs(dy) > 2:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                m |= (1 << (ny * 8 + nx))
    return m


def _bs3_carpet_opp_reach_penalty(
    parent_carpet_mask: int,
    child_carpet_mask: int,
    opp_position,
) -> float:
    """v0.4.2 BS-3 light: penalize carpets rolled into the opp's reach.

    penalty = coef * opp_reach_factor * new_carpet_count
    where
        new_carpet_count = popcount(child_mask & ~parent_mask)
        opp_reach_factor = popcount(new_carpets ∩ opp_M2_mask)
                           / max(1, new_carpet_count)

    Returns 0.0 for non-carpet moves or when `new_carpet_count == 0`
    (degenerate but can happen with forced k=1 already carpeted overlap).
    """
    new_carpets = child_carpet_mask & ~parent_carpet_mask
    if new_carpets == 0:
        return 0.0
    try:
        ox, oy = int(opp_position[0]), int(opp_position[1])
    except Exception:
        return 0.0
    reach_mask = _manhattan_2_mask(ox, oy)
    new_count = new_carpets.bit_count() if hasattr(new_carpets, "bit_count") else bin(new_carpets).count("1")
    reach_hit = (new_carpets & reach_mask)
    reach_count = reach_hit.bit_count() if hasattr(reach_hit, "bit_count") else bin(reach_hit).count("1")
    if new_count <= 0:
        return 0.0
    opp_reach_factor = reach_count / float(new_count)
    return BS3_CARPET_OPP_REACH_COEF * opp_reach_factor * float(new_count)
