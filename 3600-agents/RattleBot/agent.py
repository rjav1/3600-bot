"""RattleBot v0.4-arch-fixes — end-to-end wiring.

Entry-point `PlayerAgent` per CLAUDE.md §4 / BOT_STRATEGY.md v1.1 §3.1
with v0.2 updates from BOT_STRATEGY_V02_ADDENDUM and v0.4 arch-fix-ship
patches (2026-04-17) from loss-forensics-dual's audit of
`RattleBot_v03_pureonly_20260417_1022.zip`'s 26.3% bytefight WR:

- F-1: k=1 carpet rolls are forbidden by move_gen (already shipped
  via T-20f has_non_k1 gate — confirmed intact here).
- F-2: SEARCH-gate mass floor raised from 1/3 (~0.333) to 0.35, with a
  linear ramp down to 0.30 in the last 10 plies. Replaces v0.2's
  SEARCH_GATE_MASS_FLOOR constant with _search_mass_threshold(board).
- F-3: On ply 0 (turn_count == 0 / our first play() call), force a
  PRIME move when legal instead of defaulting to the search's
  unguided PLAIN. Priming on ply 0 banks +1 immediately and sets up
  contiguous prime-lines.

Pre-existing v0.2 knobs:
- T-20a: per-turn ceiling lifted 3.0 s -> 6.0 s, configurable.
- T-20b: `time_mgr` is the single owner of the 0.5 s safety reserve;
  `search.iterative_deepen(..., safety_s=0.0)` below.

Per-turn pipeline:
    1. belief.update(board, sensor_data) — canonical 4-step HMM filter.
    2. time_mgr.start_turn(board, time_left_fn, belief) -> budget_s
       (already has safety_s reserved).
    3. search.root_search_decision / iterative_deepen(..., safety_s=0.0)
       -- no double-subtract.
    4. Post-capture belief reset is applied on the next turn by
       belief.update via `board.player_search`.

Every `play()` call is wrapped in try/except that falls through to a
locally-duplicated FloorBot-style emergency fallback (D-006 — duplicate,
not import, for submission-isolation).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional, Tuple
import json
import math
import os
import random

import numpy as np

from game import board as board_mod
from game.enums import BOARD_SIZE, CARPET_POINTS_TABLE, MoveType
from game.move import Move

from .heuristic import Heuristic, N_FEATURES, W_INIT
from .rat_belief import RatBelief
from .search import Search
from .time_mgr import TimeManager
from .zobrist import Zobrist


def _load_tuned_weights() -> Optional[np.ndarray]:
    """Resolve BO-tuned weights if available.

    Resolution order (T-20d §2.5 handoff):
      1. `RATTLEBOT_WEIGHTS_JSON` env var points at a JSON file -> load it.
      2. `weights.json` sibling of this module -> load it.
      3. Otherwise return None (agent falls back to hard-coded W_INIT).

    JSON format: either a bare JSON list of N_FEATURES floats, or an
    object with key "weights" mapping to the same list.
    Any parse/shape error is swallowed (fallback to W_INIT).
    """
    candidates = []
    env_path = os.environ.get("RATTLEBOT_WEIGHTS_JSON")
    if env_path:
        candidates.append(env_path)
    candidates.append(
        os.path.join(os.path.dirname(__file__), "weights.json")
    )
    for path in candidates:
        if not path or not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            if isinstance(raw, dict) and "weights" in raw:
                arr = np.asarray(raw["weights"], dtype=np.float64)
            else:
                arr = np.asarray(raw, dtype=np.float64)
            if arr.shape == (N_FEATURES,):
                return arr
        except Exception:
            continue
    return None


# T-20f bug 2 + v0.4 F-2: SEARCH-gate saturation guards.
#
# v0.2 had mass_floor = 1/3 (~0.333) which is the raw +4/-2 break-even.
# v0.4 arch-fix-ship F-2 (loss-forensics-dual LOSS_ANALYSIS_CARRIE_APR18 +
# LOSS_ANALYSIS_MICHAEL_APR18): raise the hard floor to 0.35 so we stop
# firing speculative SEARCHes on noisily-peaked beliefs, with a linear
# ramp down to 0.30 in the last 10 plies where the opportunity cost of
# NOT searching is higher (fewer remaining ways to convert information
# into points). The ramp is linear in `turns_left` over [0, 10]:
#     turns_left >= 10 -> 0.35
#     turns_left == 5  -> 0.325
#     turns_left == 0  -> 0.30
# Entropy ceiling + consec-miss cap are unchanged from T-20f.
SEARCH_GATE_MAX_CONSEC_MISSES: int = 2
SEARCH_GATE_ENTROPY_CEIL: float = 0.75 * math.log(64.0)  # ~3.122 nats
SEARCH_GATE_MASS_FLOOR_HIGH: float = 0.35   # v0.4 F-2 baseline
SEARCH_GATE_MASS_FLOOR_LOW: float = 0.30    # v0.4 F-2 endgame floor
SEARCH_GATE_RAMP_TURNS: int = 10            # v0.4 F-2 ramp window
# Kept for backwards-compatibility imports by tests; now unused in-code.
SEARCH_GATE_MASS_FLOOR: float = SEARCH_GATE_MASS_FLOOR_HIGH


def _search_mass_threshold(turns_left: int) -> float:
    """v0.4 F-2: return the adaptive SEARCH-gate mass threshold.

    >>> _search_mass_threshold(40)
    0.35
    >>> _search_mass_threshold(10)
    0.35
    >>> abs(_search_mass_threshold(5) - 0.325) < 1e-9
    True
    >>> _search_mass_threshold(0)
    0.3
    """
    tl = max(0, int(turns_left))
    if tl >= SEARCH_GATE_RAMP_TURNS:
        return SEARCH_GATE_MASS_FLOOR_HIGH
    # Linear ramp from 0.30 at tl=0 to 0.35 at tl=10.
    span = SEARCH_GATE_MASS_FLOOR_HIGH - SEARCH_GATE_MASS_FLOOR_LOW
    return SEARCH_GATE_MASS_FLOOR_LOW + span * (tl / float(SEARCH_GATE_RAMP_TURNS))


__all__ = ["PlayerAgent"]


class PlayerAgent:
    """RattleBot primary agent.

    Alpha-beta + iterative deepening + Zobrist TT over a 7-feature
    linear heuristic (F1/F3/F4/F5/F7/F11/F12), with a forward-filter
    HMM rat belief. SEARCH is root-only, EV-gated via
    `search.root_search_decision`.
    """

    def __init__(
        self,
        board: board_mod.Board,
        transition_matrix=None,
        time_left: Callable = None,
    ):
        self._rng = random.Random(0xBA11A111)
        self._belief: Optional[RatBelief] = None
        self._search: Optional[Search] = None
        self._heuristic: Optional[Heuristic] = None
        self._time_mgr: Optional[TimeManager] = None
        self._zobrist: Optional[Zobrist] = None
        self._init_ok: bool = False
        # T-20f bug 2: count of consecutive failed SEARCHes by US (not
        # the opponent). Reset on hit or non-SEARCH move. Updated by
        # observing `board.player_search` at the top of each play().
        self._consec_search_misses: int = 0
        self._last_own_move_was_search: bool = False
        # T-40c: rolling window of recent root-value estimates. The
        # sample variance over this window feeds `time_mgr.start_turn`
        # via its `prev_eval_variance` argument so we spend more time
        # on positions whose PV value has been volatile and less on
        # positions that have been calm. Window size 5 balances
        # responsiveness with noise immunity.
        self._root_value_history: list = []
        self._ROOT_VALUE_WINDOW: int = 5

        try:
            if transition_matrix is None:
                # Degenerate graceful fallback: identity T means belief
                # stays put. Realistic path always sees a 64x64 T.
                T = np.eye(BOARD_SIZE * BOARD_SIZE, dtype=np.float64)
            else:
                T = np.asarray(transition_matrix, dtype=np.float64)
            self._belief = RatBelief(T, board)
            self._zobrist = Zobrist()
            self._search = Search(zobrist=self._zobrist)
            tuned_w = _load_tuned_weights()
            self._heuristic = Heuristic(weights=tuned_w)
            self._time_mgr = TimeManager()
            self._init_ok = True
        except Exception:
            # Never raise out of __init__; emergency fallback in play()
            # will still return legal moves.
            self._init_ok = False

    def commentate(self) -> str:
        ceiling = (
            self._time_mgr.per_turn_ceiling_s
            if self._time_mgr is not None
            else float("nan")
        )
        return (
            "RattleBot v0.4-arch-fixes — alpha-beta + ID + HMM belief "
            f"(ceiling={ceiling:.1f}s)"
        )

    # ------------------------------------------------------------------
    # Main play loop

    def play(
        self,
        board: board_mod.Board,
        sensor_data: Tuple,
        time_left: Callable,
    ) -> Move:
        if not self._init_ok:
            return self._emergency_fallback(board)
        try:
            return self._play_internal(board, sensor_data, time_left)
        except Exception:
            return self._emergency_fallback(board)

    def _play_internal(
        self,
        board: board_mod.Board,
        sensor_data: Tuple,
        time_left: Callable,
    ) -> Move:
        assert self._belief is not None
        assert self._search is not None
        assert self._heuristic is not None
        assert self._time_mgr is not None

        # T-20f bug 2: observe the outcome of OUR last move via
        # `board.player_search`. Engine guarantees this reflects our
        # previous ply (GAME_SPEC §5). Update the consec-miss counter
        # BEFORE this turn's belief.update so the gate sees fresh state.
        self._update_consec_search_misses(board)

        belief_summary = self._belief.update(board, sensor_data)
        # T-40c: variance of recent root-move values from the last few
        # completed searches. None on the first turn (no history yet)
        # so `adjust_for_context` will fall back to the entropy-only
        # term. Computed locally — no search.py change required.
        prev_var = self._prev_eval_variance()
        budget_s = self._time_mgr.start_turn(
            board, time_left, belief_summary,
            prev_eval_variance=prev_var,
        )

        # v0.4 F-3 (arch-fix-ship): force a PRIME opening on ply 0. The
        # shipped v0.3 bot often started with a PLAIN because the leaf
        # heuristic at d=1-2 hasn't yet learned that priming now gets us
        # both +1 and a starting endpoint for a future carpet roll. This
        # short-circuits the search on turn 0 only; it returns the first
        # legal PRIME move in any cardinal direction, falling back to
        # the regular search path if somehow no PRIME is legal (e.g.
        # all 4 primes blocked — essentially impossible at spawn).
        if self._is_ply_zero(board):
            opening = self._ply_zero_prime(board)
            if opening is not None:
                self._last_own_move_was_search = False
                # No TT probe needed; skip root-value history update.
                self._time_mgr.end_turn(0.0)
                return opening

        # v0.4 F-2: three-condition SEARCH gate with adaptive mass floor.
        #   (a) max_mass > threshold(turns_left) — 0.35 baseline, ramps
        #       down to 0.30 in the last 10 plies (F-2 spec).
        #   (b) entropy  < 0.75 * ln(64) ~= 3.12 nats — belief is peaked
        #   (c) consec misses <= 2 — don't death-spiral on a stale peak
        # T-20b: time_mgr owns the 0.5 s reserve; pass safety_s=0.0.
        turns_left_now = int(
            getattr(board.player_worker, "turns_left", 40) or 40
        )
        mass_threshold = _search_mass_threshold(turns_left_now)
        search_gated = (
            belief_summary.max_mass > mass_threshold
            and belief_summary.entropy < SEARCH_GATE_ENTROPY_CEIL
            and self._consec_search_misses <= SEARCH_GATE_MAX_CONSEC_MISSES
        )
        if search_gated:
            move = self._search.root_search_decision(
                board,
                belief_summary,
                self._heuristic.V_leaf,
                budget_s,
                safety_s=0.0,
            )
        else:
            move = self._search.iterative_deepen(
                board,
                belief_summary,
                self._heuristic.V_leaf,
                budget_s,
                safety_s=0.0,
            )
        if move is None or not self._looks_valid(board, move):
            move = self._emergency_fallback(board)
        # Record whether we're emitting a SEARCH so the next turn's
        # `_update_consec_search_misses` knows what to compare against.
        self._last_own_move_was_search = (
            int(move.move_type) == int(MoveType.SEARCH)
        )
        # T-40c: record root-value estimate for variance tracking next
        # turn. Best-effort TT probe — any failure is silently ignored
        # (variance just won't update, which is safe).
        try:
            root_key = self._zobrist.hash(board)
            entry = self._search._probe_tt(root_key)
            if entry is not None and entry.value is not None:
                self._root_value_history.append(float(entry.value))
                if len(self._root_value_history) > self._ROOT_VALUE_WINDOW:
                    self._root_value_history.pop(0)
        except Exception:
            pass
        self._time_mgr.end_turn(0.0)
        return move

    def _is_ply_zero(self, board: board_mod.Board) -> bool:
        """v0.4 F-3: are we on our first play() call of the game?

        Robust to both perspectives. The engine gives us the board
        from our point of view, so `player_worker.turns_left == 40`
        is the canonical marker of "no moves made yet by us". We
        also consult `board.turn_count` as a sanity check — on ply 0
        it's 0 for player A and 1 for player B.
        """
        try:
            tl = int(getattr(board.player_worker, "turns_left", 0) or 0)
        except Exception:
            tl = 0
        # turns_left decrements after each of our moves, so 40 <=> we
        # haven't moved yet.
        return tl >= 40

    def _ply_zero_prime(self, board: board_mod.Board) -> Optional[Move]:
        """v0.4 F-3: return the best legal PRIME move on ply 0, or None.

        Strategy: pick the PRIME whose destination offers the most
        cardinal-adjacent SPACE cells (maximizing future line-building
        options). Ties broken by the raw iteration order from
        `board.get_valid_moves()` for determinism. Never returns a
        non-PRIME move — callers fall through to the normal search.
        """
        try:
            legal = board.get_valid_moves(exclude_search=True)
        except Exception:
            return None
        primes = [m for m in legal if int(m.move_type) == int(MoveType.PRIME)]
        if not primes:
            return None
        if len(primes) == 1:
            return primes[0]

        # Score each prime by the number of non-blocked, non-primed,
        # non-carpeted neighbors at the landing square — a cheap proxy
        # for "how many directions can this prime extend into next".
        def _landing_score(mv: Move) -> int:
            try:
                child = board.forecast_move(mv, check_ok=False)
                if child is None:
                    return -1
                land = child.player_worker.position
                lx, ly = int(land[0]), int(land[1])
                score = 0
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = lx + dx, ly + dy
                    if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                        if not board.is_cell_blocked((nx, ny)):
                            score += 1
                return score
            except Exception:
                return 0

        best = primes[0]
        best_score = _landing_score(best)
        for mv in primes[1:]:
            s = _landing_score(mv)
            if s > best_score:
                best_score = s
                best = mv
        return best

    def _prev_eval_variance(self) -> Optional[float]:
        """T-40c: sample variance of recent root-value estimates.

        Returns None on < 2 samples (variance undefined). The variance
        is fed into `TimeManager.start_turn(prev_eval_variance=...)`
        which applies it through `adjust_for_context`.
        """
        hist = self._root_value_history
        if len(hist) < 2:
            return None
        mean = sum(hist) / len(hist)
        return sum((v - mean) ** 2 for v in hist) / len(hist)

    def _update_consec_search_misses(
        self, board: board_mod.Board
    ) -> None:
        """Reconcile `_consec_search_misses` AND belief with engine state.

        `board.player_search = (loc, result)` reflects our last ply.
        Rules:
          - If our last move was a SEARCH (we set the flag at end of
            play()):
            - hit  → reset counter to 0 AND reset belief to p_0
                     (T-30e H-1 fix: the engine respawned the rat, our
                     internal belief must follow suit).
            - miss → increment counter AND zero the searched cell in
                     belief (T-30e H-1 fix: without this, the next
                     turn's SEARCH-gate sees the same hot cell).
          - Else (we didn't search last turn): reset counter to 0.
        Belief updates use `apply_our_search(loc, hit)`; they run
        BEFORE `belief.update()`'s 4-step pipeline so the two T-step
        predicts fire on top of the post-search state (rat respawn +
        opp ply rat-move + our ply rat-move → p_0 @ T @ T).
        """
        if not self._last_own_move_was_search:
            self._consec_search_misses = 0
            return
        try:
            loc, hit = board.player_search
        except Exception:
            self._consec_search_misses = 0
            return
        if loc is None:
            # Engine lost track; reset conservatively.
            self._consec_search_misses = 0
            return
        # T-30e H-1: apply own-search outcome to belief state.
        if self._belief is not None:
            try:
                self._belief.apply_our_search(loc, bool(hit))
            except Exception:
                # Defensive: on any belief error, don't block gameplay.
                pass
        if hit:
            self._consec_search_misses = 0
        else:
            self._consec_search_misses += 1

    # ------------------------------------------------------------------
    # Emergency fallback (duplicated from FloorBot per D-006 isolation)

    def _looks_valid(self, board: board_mod.Board, move: Move) -> bool:
        try:
            return bool(board.is_valid_move(move))
        except Exception:
            return False

    def _emergency_fallback(self, board: board_mod.Board) -> Move:
        """Crash-proof move selection. Never raises."""
        try:
            move = self._floor_choose(board)
            if move is not None and self._looks_valid(board, move):
                return move
        except Exception:
            pass
        try:
            valid = board.get_valid_moves()
            if valid:
                return self._rng.choice(valid)
        except Exception:
            pass
        try:
            valid = board.get_valid_moves(exclude_search=False)
            if valid:
                return self._rng.choice(valid)
        except Exception:
            pass
        return Move.search((0, 0))

    def _floor_choose(self, board: board_mod.Board) -> Optional[Move]:
        """Lightweight FloorBot-style pick — carpet(k>=2) > prime > plain."""
        valid = board.get_valid_moves()
        if not valid:
            return None
        best_carpet = None
        best_pts = 1
        for m in valid:
            if m.move_type == MoveType.CARPET:
                pts = CARPET_POINTS_TABLE.get(m.roll_length, -999)
                if pts > best_pts:
                    best_pts = pts
                    best_carpet = m
        if best_carpet is not None:
            return best_carpet
        prime_moves = [m for m in valid if m.move_type == MoveType.PRIME]
        plain_moves = [m for m in valid if m.move_type == MoveType.PLAIN]
        if prime_moves:
            return prime_moves[0]
        if plain_moves:
            return plain_moves[0]
        return valid[0]
