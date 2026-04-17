# FLOORBOT_TRIAGE — Task #24

**Owner:** floorbot-triage (agent, Claude Opus 4.7 1M)
**Date:** 2026-04-17 (on the 2026-04-16 triage cycle — carrying the late-night session)
**Scope:** Reproduce FloorBot's bytefight.org validation-LOST failure locally.
**Status:** **COULD NOT REPRODUCE.** 381+ local matches, 0 INVALID_TURN / 0 CODE_CRASH / 0 TIMEOUT / 0 MEMORY_ERROR. The adversarial-board hand-crafted suite (11 scenarios including fully-trapped, corrupt-state, standing-on-carpet, all-neighbors-primed) also produced 0 invalid moves. A direct consistency test between `get_valid_moves()` and `is_valid_move()` across 138,547 random moves found 0 mismatches.

---

## §1 — Executive summary

**Finding:** No reproducible bug. FloorBot is locally sound. I ran every test I could construct in the time available and could not trigger an `INVALID_TURN`, a `CODE_CRASH`, a `MEMORY_ERROR`, a `TIMEOUT`, or even an unexpected exception in `play()`. FloorBot's defensive programming (try/except wrapping `_choose`, `is_valid_move` re-check before return, multi-tier `_safe_fallback`) appears to be working exactly as designed in every scenario I could simulate.

**Implication:** The bytefight.org validation loss is **most likely a true match loss on merits** against a non-trivial validator opponent (LIVE-003 H7), OR a non-deterministic stochastic loss against a close-level opponent. **NOT** an INVALID_MOVE bug in FloorBot's Move-generation pipeline.

**Priority:** LOW. Fixing FloorBot's local code can't solve a bug that doesn't reproduce locally. The real fix is upstream: either upload a stronger bot (RattleBot), OR reduce FloorBot's variance by adding opportunistic SEARCH (small chance of +4) to pick up a stochastic point bonus against a borderline-wins-validator opponent.

**Implication for RattleBot:** RattleBot's defense-in-depth (try/except fallback ending at `Move.search((0,0))`) covers the same failure surface as FloorBot's. If FloorBot doesn't invalid-move locally, RattleBot — which is strictly more complex but has the same fallback — is also unlikely to invalid-move. That said, RattleBot's additional failure surfaces (MEMORY, TIMEOUT) are real risks worth independent stress-testing. See §5 below.

---

## §2 — Reproduction recipe

**No reproducible bug found.** This section documents what I tried and DID NOT find, so future triagers know this ground has been covered.

### §2.1 — What I ran

| Test | N | Result |
|---|---|---|
| In-process sim FloorBot vs Yolanda (`triage_instrumented.py --sim --n 200`) | 200 | 0 invalid moves, 0 exceptions |
| Real engine FloorBot vs Yolanda (`triage_instrumented.py --n 100 --opponent Yolanda`) | 100 | 99 FloorBot wins, 1 tie, 0 invalid / 0 crash / 0 timeout / 0 mem / 0 init-fail |
| Real engine FloorBot vs FloorBot (self-play, 50 each side) | 50 | 29-20-1, 0 invalid / 0 crash / 0 timeout |
| Real engine FloorBot vs FloorBot (self-play, 10 each side — Step 3 seed 0) | 20 | 8-10-2, 0 invalid / 0 crash |
| Real engine FloorBot vs RattleBot (preliminary, floor-side A seed 0) | 2 | 0 invalid / 0 crash / 0 timeout (FloorBot lost 2/2 on points — expected) |
| Adversarial hand-crafted board states (11 scenarios, `triage_adversarial.py`) | 11 | 0 invalid; all scenarios returned valid move (see §2.2) |
| `get_valid_moves()` vs `is_valid_move()` consistency (`triage_consistency.py`) | 138,547 moves across 2,000 random boards | 0 mismatches |

**Total: 381+ simulated matches, 0 invalid-move events on FloorBot's side.**

### §2.2 — Adversarial board scenarios tested

See `3600-agents/FloorBot/tests/triage_adversarial.py:22-219`. All 11 scenarios return a move that passes `board.is_valid_move(move)`:

| Scenario | Move chosen | Valid? |
|---|---|---|
| carpet_blocked_by_opp (primed line, opponent on far end) | `CARPET(RIGHT, roll=2)` | yes |
| extension_adjacent_carpeted (cell 2 ahead is CARPET, not PRIMED) | `PRIME(DOWN)` | yes |
| edge_constrained (near top-left corner with blockers) | `PRIME(DOWN)` | yes |
| standing_on_carpet (worker on CARPET, PRIME illegal) | `PLAIN(DOWN)` | yes |
| surrounded_by_primed (all 4 neighbors PRIMED, only CARPET-1 available) | `CARPET(UP, roll=1)` | yes |
| 3_blocked_1_primed (3 blocked neighbors + 1 primed) | `CARPET(DOWN, roll=1)` | yes |
| prime_to_carpet_dest (prime-target is CARPET, legal) | `PRIME(DOWN)` | yes |
| long_prime_line (4-cell primed line available) | `CARPET(RIGHT, roll=4)` | yes |
| corrupt_same_cell (both workers on same square) | `PRIME(RIGHT)` | yes |
| fully_trapped_workercell_carpet (4 blocked neighbors, on carpet) | `SEARCH(loc=(4, 3))` | yes |
| corner_00_spawn (hypothetical corner overlap spawn) | `SEARCH(loc=(4, 3))` | yes |

In the fully-trapped cases, `_choose` returns `None` (because `get_valid_moves()` returns `[]`), `play` falls through to `_safe_fallback`, `_safe_fallback` tries `get_valid_moves(exclude_search=False)` which returns the 64 SEARCH candidates, and picks one via `self._rng.choice` — a SEARCH on any in-bounds cell is always valid per `is_valid_move`.

### §2.3 — What I did NOT reproduce

- **No INVALID_TURN** on FloorBot's side in any match.
- **No CODE_CRASH** — no exception ever reached the outer `try/except` in `play()`.
- **No TIMEOUT** — FloorBot's max per-move wall time remains <1 ms, consistent with the prior microbench.
- **No MEMORY_ERROR** — FloorBot uses trivial memory (<5 MB RSS).
- **No `_safe_fallback` activation** in normal games — the primary path always produced a valid move.

---

## §3 — Root cause analysis (speculative, since no local repro)

Because I cannot reproduce the bug locally, this section is necessarily speculative. Ranked by prior:

### §3.1 — **MOST LIKELY: non-deterministic validator match, FloorBot lost on merits**

Per LIVE-003, Yolanda passed validation 1/1 on a purely random policy. The most plausible story: the validator opponent is at or near Yolanda's level (a very weak bot, perhaps a "pass-always" or "always-search-(0,0)" bot), AND the match outcome depends on the random `T` matrix, random spawns, and random rat walk. Yolanda got lucky; FloorBot's deterministic policy occasionally gets "unlucky" against this validator. The validator's specific board state may exploit FloorBot's greedy carpet-extension in a way that lets the opponent outscore.

**Evidence supporting this:**
- FloorBot's local win-rate vs Yolanda is 99/100 (per my 100-match run), not 100/100. There IS a ~1% loss-to-random-mover base rate, consistent with stochastic board variance.
- LIVE-003 computed that two consecutive losses (FloorBot 0/2) against a 50/50 opponent has P = 0.25 — not small enough to be dispositive.
- No invalid-move behavior locally suggests no deterministic bug.

**Fix:** Upload RattleBot v0.1+ (task #22 tracks paired eval). RattleBot's alpha-beta search should beat the validator reliably. FloorBot is a weak insurance bot and always was — its inability to pass validation is a strength problem, not a correctness problem.

### §3.2 — **MEDIUM LIKELIHOOD: tournament-sandbox timing skew**

Tournament mode runs with `limit_resources=True`: 240 s play budget (vs 360 s local), tighter clock. Also runs under seccomp + SIGSTOP/SIGCONT freeze between plies (`engine/player_process.py:532-627`). On Windows local (`limit_resources=False`) we never exercise the SIGSTOP freeze path.

**Failure surface I could not test:** after the engine does `SIGSTOP` between plies, does the agent process cleanly resume? FloorBot has no background threads or timers, so *in principle* SIGSTOP/SIGCONT should be a no-op. But I cannot verify this without a Linux environment.

**Evidence against:**
- FloorBot's observed per-move wall time is 0.06 ms max (microbench in `bench_play.py`). Even a 100× sandbox slowdown leaves 3+ orders of magnitude of headroom vs the 240 s budget.
- LIVE-003's reading of the validation-match duration ("1m ago"/"17m ago" were relative timestamps, not match durations) suggests matches ended in seconds, not minutes — which WOULD indicate an early crash. But that also matches an early-game point-merits loss.

**Fix if triggered:** none needed for FloorBot — the fallback is already safe. If RattleBot hits this, enable `limit_resources=True` in a Linux VM/WSL and retest (task #37 tracks this).

### §3.3 — **LOW LIKELIHOOD: seccomp syscall rejection at a specific code path**

Per LIVE-003, Yolanda passed validation — and Yolanda's imports are a strict subset of FloorBot's (Yolanda imports `random`, `collections.abc`, `typing`, and `game.*`; FloorBot adds nothing). So any seccomp-blocked import/syscall reachable by FloorBot is also reachable by Yolanda and would have killed Yolanda. This hypothesis is effectively ruled out.

### §3.4 — **VERY LOW: `random.Random(seed)` or `_rng.choice` behavior divergence**

FloorBot's `__init__` does `self._rng = random.Random(0xF1008070)`. On Python 3.12, `random.Random(seed)` is pure-Python + C hash; no syscalls. Unlikely to differ. Even if it raised, FloorBot's `__init__` has a try/except fallback to `self._rng = random`. No failure mode I can construct.

### §3.5 — **RULED OUT: get_valid_moves / is_valid_move mismatch**

Across 138,547 randomized moves, every move returned by `board.get_valid_moves(exclude_search=False)` passed `board.is_valid_move(move)`. So FloorBot trusting `get_valid_moves()` is safe.

### §3.6 — **RULED OUT: FloorBot's fallback path returns an invalid move**

`_safe_fallback` ultimately returns `Move.search((0, 0))`. (0, 0) is in bounds. `is_valid_move` on a SEARCH only checks `is_valid_cell(search_loc)` — which returns True for (0, 0). So the ultimate fallback is always valid.

---

## §4 — Proposed fix

**No code fix proposed — no reproducible bug to fix.**

However, two defensive hardening options could reduce FloorBot's **variance** against the validator (potentially pushing it from 50% to 60%+ against a borderline opponent):

### §4.1 — Option A: opportunistic CARPET-1 endgame fallback (reduce variance)

**Rationale:** `_best_carpet` currently rejects CARPET-1 because k=1 is −1 pt. But at turn 38+ with nothing else to do, a −1 CARPET-1 is **strictly better** than a 0-point PLAIN step (because it also opens up a new SPACE cell for next-turn priming). This is a negligible change but might swing a close endgame.

**Change:** in `_best_carpet`, replace `best_pts = 1  # require > 1 point` with a turn-adaptive threshold: at turn ≥ 36, accept CARPET-1. **But do NOT apply this — it's a strength tweak, not a correctness fix, and we have no evidence it would change validator outcomes.**

### §4.2 — Option B: double-check the fallback's move before returning (cosmetic)

**Rationale:** `_safe_fallback` currently returns `self._rng.choice(valid)` without re-validating the chosen move. If `get_valid_moves()` were to return an inconsistent list (ruled out by §3.5, but just-in-case), the fallback could return an invalid move. Adding `if board.is_valid_move(move): return move` before returning is free.

**Change to `agent.py:204-218`:**
```python
def _safe_fallback(self, board):
    for exclude in (True, False):
        try:
            valid = board.get_valid_moves(exclude_search=exclude)
            if valid:
                pick = self._rng.choice(valid)
                if board.is_valid_move(pick):
                    return pick
        except Exception:
            pass
    return Move.search((0, 0))
```

**But again — do not apply.** The existing code is defensively correct under the engine invariants we've verified. Adding the re-check is belt-and-suspenders, not a fix for an observed bug. If we wanted to *ship* a patch to FloorBot before the deadline, this is the only thing I'd consider changing, and only as low-risk hardening.

### §4.3 — The real action item

**Submit RattleBot, not a patched FloorBot.** The triage clears FloorBot of correctness suspicions, which means the team's engineering time is better spent hardening RattleBot (tasks #25-29) than modifying FloorBot.

If RattleBot slips and we need a fallback submission, the most valuable change to FloorBot would be **adding at least one SEARCH per game** with a hand-tuned probability threshold — this would pick up the +4 rat bonus occasionally and dramatically improve the mean score against a close-level validator. That's a strategy change, not a bug fix, and is out of scope for Task #24.

---

## §5 — Implications for RattleBot

AUDIT_V01.md notes RattleBot has a try/except fallback ending at `Move.search((0,0))` via the `emergency_fallback` at `agent.py` bottom. Does that cover ALL invalid-move paths, or just exceptions?

Looking at `RattleBot/agent.py` (per AUDIT_V01.md §3.3): the outer `play()` wraps the whole pipeline in try/except and on any exception falls through to a FloorBot-style fallback that calls `get_valid_moves(exclude_search=False)` and ultimately `Move.search((0, 0))`. This matches FloorBot's pattern and is sound — any exception-raising path is covered.

**However**, RattleBot has failure surfaces FloorBot lacks:

1. **Alpha-beta returning a non-valid move.** The search code (`search.py`) returns the best move from its move-ordering + tree walk. If the move-ordering logic or a TT cache poisoning ever returns a move not in the current legal set, RattleBot would return it directly (bypassing any `is_valid_move` check). **Audit action:** verify that `search.py` *never* returns a move unless it came from `ordered_moves(board)`, which calls `board.get_valid_moves(exclude_search=True)`. Per AUDIT_V01 §3.1 this invariant is asserted in `search.py:235-237` — good.

2. **SEARCH-as-root move.** RattleBot's `root_search_decision` CAN pick a SEARCH. If the SEARCH was EV-positive per HMM belief, RattleBot returns `Move.search(best_cell)`. This is always valid (in-bounds guaranteed). OK.

3. **Timeout on the sandbox's tighter clock.** RattleBot's alpha-beta with `_PER_TURN_CEILING_S = 3.0 s` (now 6.0 s post-T-20a per tasks) targets 6 s/turn. Total budget is 240 s (tournament) / 40 turns = 6 s/turn average. Under sandbox CPU contention this could spike into timeout territory. M-01 in AUDIT_V01 flags this. **Not a FloorBot-triage issue**, but a real risk for RattleBot.

4. **Memory pressure from HMM belief + TT.** RattleBot allocates a 64-length belief vector per turn + a zobrist TT. With `MAX_TT_SIZE` or similar, total RSS should stay well under 1536 MB. Not tested here.

**Bottom line for RattleBot:** same invalid-move immunity as FloorBot (both use `get_valid_moves()` + emergency fallback). The distinct risks are TIMEOUT and MEMORY_ERROR, neither of which showed up in local FloorBot testing because FloorBot is trivially small.

---

## §6 — Files added during triage

- `3600-agents/FloorBot/tests/triage_instrumented.py` — wraps play() and runs N matches via sim (fast, in-process, no subprocess) OR via the real `play_game` engine (high-fidelity). Instruments every move against `board.is_valid_move(move)`; writes a JSON summary of anomalies. Callable as: `python -X utf8 3600-agents/FloorBot/tests/triage_instrumented.py --n 100 --opponent Yolanda --outfile /tmp/out.json`.
- `3600-agents/FloorBot/tests/triage_adversarial.py` — 11 hand-crafted worst-case board states fed to FloorBot.play(); checks each returned move against `is_valid_move`.
- `3600-agents/FloorBot/tests/triage_consistency.py` — random-board generator that enumerates `get_valid_moves()` and checks each against `is_valid_move()` for consistency (138,547 moves tested, 0 mismatches).

All three files are **test-only**, per the task's constraint not to modify production code (`3600-agents/FloorBot/agent.py`).

---

## §7 — Recommendations

1. **Mark task #24 completed with verdict "COULD NOT REPRODUCE".** Don't patch FloorBot.
2. **Ship RattleBot.** FloorBot was the insurance bot and is now strength-limited (too weak for the validator), but RattleBot's alpha-beta should beat the validator comfortably.
3. **Before RattleBot's first bytefight upload**, run the same triage suite against RattleBot — `triage_instrumented.py` works with `--opponent` pointing at any agent and an `--agent` flag could be added to instrument any agent. The TIMEOUT risk (M-01 in AUDIT_V01) is the main unknown.
4. **If FloorBot must pass validation** (e.g., for a last-ditch submission 1 hour before deadline): consider adding one deterministic SEARCH per game (e.g., at turn 20 search (3,3) or wherever belief mass is highest) to pick up the +4 bonus occasionally. This is a 5-line change in `_choose` and can flip close games. But apply this only if the team lead decides FloorBot needs to ship — otherwise the audit verdict stands: FloorBot is correct but not strong enough.
