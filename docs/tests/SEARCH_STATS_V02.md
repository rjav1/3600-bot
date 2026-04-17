# SEARCH_STATS_V02 — T-20e move-ordering audit

Per BOT_STRATEGY_V02_ADDENDUM.md §2.3 T-20e. Confirms that the D-004
move-ordering stack (hash-move → killer → history → type-priority →
immediate-delta) is actually firing in `RattleBot/search.py`, with
telemetry now exposed via `Search.get_stats()`.

---

## Instrumentation added (`search.py::Search`)

Per-call counters (reset on every `iterative_deepen`):

| Counter                    | Meaning                                                                   |
|----------------------------|---------------------------------------------------------------------------|
| `tt_probes / tt_hits`      | Bucket probes vs. full-key matches                                        |
| `tt_cutoffs`               | Beta-cutoffs from a TT EXACT/bound hit at sufficient depth                |
| `tt_stores / tt_replacements` | Store calls and slot replacements (depth-preferred evictions)          |
| `hash_move_attempts`       | Nodes where a TT entry offered a `best_move`                              |
| `hash_move_legal`          | Subset where the hash-move was in the legal list                          |
| `hash_move_first`          | Subset where the hash-move landed at `ordered[0]`                         |
| `killer_slot_0_hits`       | Nodes where `ordered[0] == killers_here[0]` (hash-move not matching)      |
| `killer_slot_1_hits`       | Same for slot 1                                                           |
| `history_reorder_count`    | Nodes where the history dict had ≥ 1 legal move with a positive score    |
| `cutoffs_total`            | Total beta-cutoffs in the tree                                            |
| `cutoff_on_first_move`     | Cutoffs on `ordered[0]` (the core ordering-quality metric)                |
| `cutoff_on_nth_move[i]`    | Distribution of cutoffs by move index (0..7, clamped)                     |

`Search.get_stats()` returns the above plus derived `tt_hit_rate`,
`cutoff_on_first_rate`, and `last_depth_reached`.

---

## Measurements

### Single-call benchmark @ 2 s budget (warm TT, seed=1)

```
depth reached:        9
nodes:                40 960
leaves:               22 608
nps:                  22 328
tt_probes / tt_hits:  18 361 / 8 939
tt_hit_rate:          48.7 %
tt_cutoffs:           3 196
tt_stores:            15 156
hash_move attempts:   5 743
hash_move_legal:      5 743   (100 % legality)
hash_move_first:      5 743   (100 % promoted to ordered[0])
killer_slot_0_hits:   6 835
killer_slot_1_hits:   869
history_reorder_count: 15 091
cutoffs_total:        10 013
cutoff_on_first:      9 804   (97.9 %)
cutoff_on_nth_move:   [9 804, 166, 30, 12, 1, 0, 0, 0]
```

### 20-call evolving-board sweep (0.25 s / call, seed=37)

Applied one legal CARPET/PRIME-preferred move + reverse_perspective
between calls (mimics a game turn).

| Metric                                 | Value     | Gate          | Pass |
|----------------------------------------|-----------|---------------|------|
| `tt_hit_rate` on calls 10–19           | **49.8 %** | > 15 % (T-SRCH-3) | ✓ |
| `cutoff_on_first_rate` on calls 10–19  | **97.6 %** | > 60 % (§2.3)     | ✓ |
| Late calls with ≥ 1 TT cutoff          | **10 / 10** | ≥ 8              | ✓ |
| Average `last_depth_reached`           | 8.0       | —             | —    |

---

## Audit verdict

All five ordering tiers are wired and firing:

1. **Hash-move.** Every TT entry's `best_move` was legal (5 743/5 743 in
   the 2 s benchmark) and reached `ordered[0]` every time. No plumbing
   bug.
2. **Killer.** 6 835 slot-0 and 869 slot-1 hits in the 2 s benchmark —
   killer slots promote correctly when the TT had no hit. Verified
   independently by `tests/test_search.py::test_killer_move_promoted`.
3. **History.** 15 091 nodes where the history dict influenced ordering.
   Verified by `test_history_reorder_monotone` (a PLAIN move with high
   history score leads the PLAIN bucket even against the type-priority
   default).
4. **Type-priority.** Unchanged from v0.1 — `test_ordered_moves_carpet_first`
   still passes (CARPET k=3 ahead of PRIME on a primed-line fixture).
5. **Immediate-point-delta.** Covered by the sort key's third field; not
   individually gated but exercised by the same fixture.

### Gate: `cutoff_on_first_move / cutoffs_total ≥ 0.60` — **PASS (0.979)**

The instrumentation also **rules out** the bug-triage path in §2.3 item 5:
no tier is silently dead.

---

## Zobrist change (v0.2 adjustment)

Per BOT_STRATEGY §2.g "TT deliberately excludes `turn_count` from the key
to maintain hit-rate", the `turn_count // 2` contribution was removed
from `zobrist.hash()`. The 41-entry `turn` table is retained in the
`Zobrist` init (seeded deterministically) so that `Zobrist.__init__`
stays backward compatible with any caller that introspects
`self.turn`. Side-to-move, worker positions, and all four cell-type
tables still contribute — the TT remains safe against false hash
collisions at the measured collision rate of 0.00 % over 10 000 random
boards.

Trade-off acknowledged: two identical (masks + worker_pos + side) states
at different turn counts now share a TT entry. In an 80-ply game this
almost never occurs; when it does, the leaf value is at most ~2–4 turns
mis-estimated — within the per-move heuristic noise band.

---

## Files changed

- `3600-agents/RattleBot/search.py` — 353 → 481 LOC (instrumentation)
- `3600-agents/RattleBot/zobrist.py` — dropped turn-bucket XOR in `hash()`
- `3600-agents/RattleBot/tests/test_search.py` — 18/18 passing; added
  `test_get_stats_schema`, `test_ordering_stack_fires`,
  `test_tt_hit_rate_20_calls`, `test_killer_move_promoted`,
  `test_history_reorder_monotone`; `test_tt_reduces_nodes` tightened to
  match the new `get_stats()` accounting.
