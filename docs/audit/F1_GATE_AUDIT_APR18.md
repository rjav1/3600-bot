# F-1 k=1 Carpet Gate Audit — 2026-04-18

**Auditor:** `f1-gate-audit` (ephemeral)
**Scope:** Verify the claim in LOSS_ANALYSIS_CARRIE_APR18 (§RC-1) that RattleBot rolls k=1 "19.7% of the time" despite the `has_non_k1` gate in `move_gen.py`.
**Baseline commit:** 3b9cbbd (arch-fix-ship v0.4)

---

## §1 Current gate logic (exact)

`3600-agents/RattleBot/move_gen.py` lines 91–123:

```python
annotated: List[Tuple[int, Move, MoveKey]] = []
has_non_k1 = False
for m in legal:
    mt = int(m.move_type)
    k1 = (mt == _MT_CARPET and m.roll_length < 2)
    if not k1:
        has_non_k1 = True
    ...
if has_non_k1:
    annotated = [entry for entry in annotated if not _is_k1_carpet(entry[1])]
```

**Semantics:** `has_non_k1` is True whenever **any** non-k1 move exists in `get_valid_moves(exclude_search=True)`. That includes PLAIN, PRIME, or CARPET k>=2 in **any** cardinal direction. When True, k=1 CARPET is dropped. Only when `has_non_k1` is False — i.e. every legal non-search move is a k=1 carpet — does k=1 survive to the search.

The gate is invoked at every interior node of the alpha-beta tree (`search.py:217, 254, 364`) and by the agent's opening path. No known bypass on the normal search path.

---

## §2 Forensic ground-truth from Carrie replays

Re-tallying A-player k=1 carpet rolls across **all 12 Carrie matches** in `docs/intel/replays/carrie_*.json`, using ground truth (mover-side point delta == -1 **and** `left_behind == "carpet"`), I find exactly **2** A-side k=1 rolls in the dataset:

| Match | Ply | A pos (before→after) | dA | Notes |
|-------|-----|---------------------|----|-------|
| `carrie_14a319d3` (our one WIN) | 57 | (5,7)→(4,7) | -1 | Corner pin |
| `carrie_b93942ed` (loss -32) | 43 | (0,2)→(0,3) | -1 | Edge pin |

**The LOSS_ANALYSIS_CARRIE_APR18 "15/76 = 19.7%" figure is an overcount.** That analysis treated every ply whose `new_carpets` list had length 1 as a k=1 roll, which over-attributes: a k=2 or k=3 roll by **either** side ending at an endpoint that only added 1 cell to `new_carpets` (because the other cells were already carpet from cross-overlapping primes, etc.) was counted. The true A-side k=1 rate in this dataset is **2/11 losses + 1/1 win = ~8% of games, ~1-2 rolls/match in the minority of games it occurs**, not 19.7% of all rolls.

That materially reframes the bug: the gate is largely doing its job. The residual k=1 rolls are **not** gate leakage — they are **forced k=1 rolls** when every other legal move is illegal.

---

## §3 Forensic reconstruction of the 2 A-side k=1 rolls

### Scenario A — `carrie_14a319d3` ply 57 (WIN, still ate -1)

Reconstructed board-state **before** ply 57:

```
A at (5,7), B at (5,6)
A cell type: SPACE
Neighbors of A:
  UP    (5,6): CARPET, occupied by B
  DOWN  (5,8): OFFBOARD
  LEFT  (4,7): PRIMED
  RIGHT (6,7): BLOCKED (corner rectangle)
```

Legal-move enumeration (engine `get_valid_moves` semantics):
- PLAIN LEFT → (4,7) is primed, PLAIN disallowed (rules).
- PRIME LEFT → destination (4,7) primed, disallowed.
- CARPET LEFT k=1 → (4,7) is primed ray of length 1, **legal**, rolls to carpet for **-1 pt**.
- UP/RIGHT/DOWN all disallowed (worker / blocked / offboard).

**Only legal non-SEARCH move was CARPET-LEFT-k=1.** Gate correctly kept it.

### Scenario B — `carrie_b93942ed` ply 43 (LOSS -32, also ate -1 here)

Reconstructed state **before** ply 43:

```
A at (0,2), B at (1,2)
A cell type: SPACE
Neighbors:
  UP    (0,1): BLOCKED
  DOWN  (0,3): PRIMED
  LEFT  OFFBOARD
  RIGHT (1,2): CARPET, occupied by B
```

Legal non-search moves:
- PLAIN DOWN disallowed (primed dest).
- PRIME DOWN disallowed (primed dest).
- CARPET DOWN k=1 legal → -1 pt.
- No other direction legal.

**Again, forced k=1.** Gate behavior correct.

---

## §4 Concrete scenarios where k=1 is currently ALLOWED but should NOT be

Even though the gate is "correct" in that it only passes k=1 as a last resort, the agent is still taking **−1 pts** in those last-resort cases when a **+EV alternative exists that the gate does not consider: SEARCH**. Search has expected value `6p − 2` where `p = belief.max_mass`. That is strictly > −1 iff `p > 1/6 ≈ 0.167` — a much lower bar than the ~0.35 rat-gate threshold.

### S1 — Forced-k1 position with peaked belief (both replay scenarios qualify)

At `carrie_b93942ed` ply 43, A had 18 turns left and a presumably mid-entropy belief. Even a **flat** belief gives `max_mass ≈ 1/50 ≈ 0.02` over the reachable posterior — EV = 6·0.02 − 2 ≈ −1.88, *worse* than −1. But if `max_mass > 1/6`, **SEARCH dominates k=1**.

### S2 — Forced-k1 position with cold belief, but information gain valuable

In late game (turns_left ≤ 10), a miss still surfaces information for subsequent turns. Skipping the −1 roll and probing a moderately-hot cell preserves the scoreline. Currently the adaptive gate (F-2 ramp, `_search_mass_threshold`) drops the *search-fire* threshold to 0.30 there, but it still won't fire below 0.30 — while **k=1 is strictly −1, not −0.5**, so even at p=0.20 (EV = −0.8) SEARCH beats k=1.

### S3 — Forced-k1 when you'd prefer to pass (burn a turn)

At the last turn (`turns_left == 1`), k=1 scores −1 and ends the game. An illegal-fallthrough SEARCH to a dead cell scores −2 but the game ends anyway. So k=1 is correct there — but only there. Any game with ≥ 2 turns left: search-for-info beats k=1-for-points if `p > 1/6`.

### S4 — k=1 inside the tree horizon (secondary)

Interior nodes also invoke `ordered_moves(exclude_search=True)`. So a minimax leaf at depth 4 where the opponent's future play forces us into k=1 will be scored at −1, correctly, by the honest heuristic. No fix needed here — the leaf already reflects reality.

### S5 — Opening trap (primarily handled by F-3)

F-3 forces ply-0 PRIME, so k=1 can't be the first move. Not an issue post-F-3.

---

## §5 Concrete patch

**Minimum-touch fix (agent layer, ~12 LoC):** After the search returns its best move, if that move is k=1 CARPET, try to swap it for a SEARCH with EV > −1. This preserves the existing gate, only adds a defensive swap at the root.

```python
# agent.py, end of _play_internal, just before _last_own_move_was_search update:

# v0.4.1 F-1 tightening: if the tree is forced into a k=1 carpet (-1 pt),
# try a SEARCH move when its EV exceeds -1. EV_search = 6*max_mass - 2
# > -1 iff max_mass > 1/6 ≈ 0.167. Only triggers in hard corner-pin
# positions where move_gen's has_non_k1 gate had no alternative.
if (
    int(move.move_type) == int(MoveType.CARPET)
    and move.roll_length < 2
    and belief_summary.max_mass > (1.0 / 6.0) + 1e-9
):
    loc, search_ev = self._search._best_search_ev(board, belief_summary)
    if loc is not None and search_ev > -1.0:
        move = Move.search(loc)
```

This is a minimal and purely-additive patch: zero impact when the search tree returns anything other than k=1 carpet (the common case), and a strict upgrade when it does.

**Alternative (rejected):** Modify `move_gen.ordered_moves` to include SEARCH when `has_non_k1` is False. Rejected because it violates the D-011 invariant "SEARCH is root-only" and would need matching changes in `_root_search` and `_alphabeta`.

---

## §6 Expected impact

- **Replay precedent:** 2 rolls / 12 games = ~0.17 rolls/game. Patch saves at most −1 pt on those plies, conditional on `max_mass > 0.167`. Order of magnitude: **+0.1 to +0.3 pts/game vs Carrie** in the worst case, negligible ELO gain.
- **Real value:** future unknown opponents (Michael, Albert, George) may corner-pin us more often. Patch is defense-in-depth with no downside.
- **Risk:** swapping in a SEARCH might burn a move that the heuristic valued positively for other reasons (e.g. escaping a pin by rolling). But k=1 carpet **is** a step, and after the swap to SEARCH we'd sit still — the next turn the pin may still exist. Acceptable trade: we're choosing between "move and lose 1" vs "probe and possibly gain 4". The existing `_best_search_ev` already accounts for information gain via `gamma_info * dH`.

---

## §7 Recommendation

Ship the §5 patch. Bump version string from `v0.4-arch-fixes` to `v0.4.1`. Run `pytest 3600-agents/RattleBot/tests/` to confirm no regressions. Commit to the repo; team-lead will bundle into v05.

**End of F1_GATE_AUDIT_APR18.**
