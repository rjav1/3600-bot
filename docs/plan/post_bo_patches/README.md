# Post-BO Patches — ready-to-apply diffs

Prepared: 2026-04-17 — while BO RUN1-v7 (PID 8868) still active.

These three unified-diff files (`patch_02_*.patch`, `patch_03_*.patch`,
`patch_04_*.patch`) are ready for `git apply` against a clean `main`
tree AFTER the live BO run completes and its weights are adopted.
They implement the post-BO fixes planned under tasks T-87, T-90, T-95,
and T-96 (plus Experiment C from the fresh-eyes architecture audit).

**`patch_01` was dropped** after confirming the C-1 / R5 k=1 CARPET
gate is already shipped in `move_gen.py` under a stricter semantics —
see §5 audit note. Patch numbering is preserved (02/03/04) so other
docs referencing those patch IDs remain valid.

All three patches have been verified with `git apply --check` against
`HEAD` at prep time and with a full sequential `git apply` sim against
a scratch repo; every target file still parses as valid Python after
the full 2 → 3 → 4 sequence.

---

## §1 Apply order and rationale (2 → 3 → 4)

Apply in numeric order. The rationale is:

1. **`patch_02_C2_early_search_lockout.patch`** — real behaviour
   change: adds a `turns_left > 30 AND max_mass <= 0.35` early-game
   SEARCH lockout to the agent.py SEARCH gate. Low risk, small diff
   (~20 LOC); apply first so the next SEARCH-heavy scrimmage gets
   the C-2 benefit.

2. **`patch_03_ExpC_R2_time_mgr_reskew.patch`** — Exp C phase
   multipliers (0.3× / 1.3× / 2.5× replacing 0.6× / 1.0× / 3.5×) +
   R2's 220 s cumulative ceiling guard + 2 new tests. This is the
   biggest change — a full rework of `start_turn`'s budget formula in
   time_mgr.py plus new tests in `tests/test_time_mgr.py`.

3. **`patch_04_version_bump.patch`** — cosmetic docstring bump
   ("RattleBot v0.2" → "RattleBot v0.4" in agent.py/move_gen.py/
   time_mgr.py/search.py, "v0.1" → "v0.4" in rat_belief.py).
   Applied last so the version label reflects the fully-patched v0.4
   state. Each hunk targets lines that patches 02/03 do NOT touch
   (line 1 of each file plus agent.py line 157 inside `commentate()`)
   so order is reversible if needed.

---

## §2 Post-apply verification

Run in this order AFTER the 4 patches are applied:

### 2.1 Syntax + import smoke
```bash
python -c "import ast; [ast.parse(open(p).read()) for p in [
    '3600-agents/RattleBot/agent.py',
    '3600-agents/RattleBot/move_gen.py',
    '3600-agents/RattleBot/time_mgr.py',
    '3600-agents/RattleBot/search.py',
    '3600-agents/RattleBot/rat_belief.py',
    '3600-agents/RattleBot/tests/test_time_mgr.py',
]]; print('syntax OK')"
```

### 2.2 RattleBot pytest suite
```bash
python -m pytest 3600-agents/RattleBot/tests/ -v
```
Expected: all existing tests pass + the 2 new patch-03 tests
(`test_multiplier_by_phase`, `test_220s_cumulative_cap`) pass. A
pre-existing test in `test_time_mgr.py` that exercises the v0.2
`_MULTIPLIER` labels may need review — the patch-03 classifier now
emits `"opening"`/`"mid"`/`"endgame"` instead of `"easy"`/`"normal"`,
so any test asserting the old labels will need updating. (The
existing `test_classify_buckets` uses the `easy`/`normal`/`critical`
labels via `classify()`, which patch-03's `classify()` no longer
returns; see §3.)

### 2.3 10-game paired smoke (RattleBot_v2 vs fresh patched RattleBot)
```bash
python engine/run_local_agents.py RattleBot RattleBot_v2
```
Repeat ~10 times (or use the paired runner if available) and check
that nothing regressed. Minimum bar: WR ≥ 45% vs current-main
RattleBot (i.e. the patches don't actively hurt play).

### 2.4 Local self-play regression check
```bash
for i in {1..20}; do python engine/run_local_agents.py RattleBot Yolanda; done
```
Expected: RattleBot WR vs Yolanda stays ≥ 90% (v0.3 baseline is
≥ 95% — a big regression indicates a patch-03 time-budget bug).

### 2.5 Real-ELO signal (preferred)
Upload the patched build via `tools/bytefight_client.py` and run
scrimmages vs George/Albert/Carrie. This is the only grade-relevant
verification.

---

## §3 Fallback / revert

Each patch is a normal `git apply` — to revert one, use:
```bash
git apply -R docs/plan/post_bo_patches/patch_03_ExpC_R2_time_mgr_reskew.patch
```

If the full sequence breaks something, the safest revert is:
```bash
git reset --hard <SHA-before-any-patch>
```
(Assumes each patch was committed as a separate commit — recommended.
If they're all one commit, the same `git reset --hard` still works.)

### Known pre-existing-test interactions

- `tests/test_time_mgr.py::test_classify_buckets` asserts the old
  `easy`/`normal`/`critical` labels. Patch 03's `classify()` no
  longer emits `easy`/`normal` (returns `opening`/`mid`/`endgame`
  instead). If this test fails post-apply, update its assertions to
  the new labels — the underlying behaviour (phase classification)
  is intentionally changed. This is a test-update item, not a
  patch-03 bug.

- `test_endgame_multiplier_extended_at_low_turns_left` is written
  against `ENDGAME_HARD_CAP_MULT = 3.5`; patch 03 lowers that to 2.5
  (the PHASE_MULT_ENDGAME value). The test will fail and needs
  updating to the new multiplier. Again, intended.

If either breakage is surprising at apply time, revert patch 03 and
re-plan — patches 02 and 04 are independent of it.

---

## §4 Expected ELO impact

Per the source audit documents:

| Patch | Source | Claimed impact |
|-------|--------|----------------|
| 01 (C-1) | COMPETITIVE_INTEL §5.C-1, LOSS_FORENSICS §4.R5 | **DROPPED** — already shipped under stricter semantics (see §5) |
| 02 (C-2) | COMPETITIVE_INTEL §5.C-2, LOSS_FORENSICS §4.R3 | +1.5 pts/match vs student agents that rat-spam early |
| 03 (Exp C + R2) | ARCH_CONTRARIAN §4 Exp C + LOSS_FORENSICS §4.R2 | +10-25 ELO (Exp C) + eliminates Match-2 "241 s" failure mode (R2) |
| 04 (version bump) | T-95 | 0 ELO (cosmetic) |

Net expected: **+10-30 ELO** improvement assuming no regression
against George/Yolanda and no interaction with the BO-adopted
weights. Patch 03 is the largest lever and also the largest risk —
the paired-test smoke in §2.3 is the load-bearing verification step.

---

## §5 C-1 / R5 audit — why `patch_01` was dropped

Grep of `3600-agents/RattleBot/move_gen.py` at prep-time HEAD shows the
k=1 CARPET gate is **already shipped** under the T-20f fix (v0.2,
`URGENT T-20f`, task #39):

```python
# move_gen.py:73-74, 92-97, 122-123
def _is_k1_carpet(m: Move) -> bool:
    return int(m.move_type) == _MT_CARPET and m.roll_length < 2

# ... inside ordered_moves() ...
has_non_k1 = False
for m in legal:
    mt = int(m.move_type)
    k1 = (mt == _MT_CARPET and m.roll_length < 2)
    if not k1:
        has_non_k1 = True
# ...
if has_non_k1:
    annotated = [entry for entry in annotated
                 if not _is_k1_carpet(entry[1])]
```

**Semantics comparison:**

- **Shipped gate (T-20f):** drop k=1 iff *any non-k=1 legal move exists*.
- **C-1 / R5 proposal:**       drop k=1 unless *all alternatives eval < −1*.

The shipped gate is strictly ≥ C-1 in expected value:

- When alternatives exist and at least one scores ≥ −1: both gates
  drop k=1. Identical behaviour.
- When alternatives exist but ALL score < −1: shipped gate still drops
  k=1 (picks a non-k=1 move scoring < −1); C-1 would *permit* k=1
  (also scoring −1). Neither move is better — shipped gate picks the
  best available non-k=1, which is ≥ k=1's −1 only if the eval bound
  is tight. In practice, this edge case is rare and a wash.
- When no non-k=1 exists: both gates allow k=1 (forced).

**Conclusion:** C-1 / R5 is already covered by T-20f. No patch
produced. A prior prep draft proposed a docstring-only no-op patch;
dropped after rattlebot-v2-fork's parallel R5 audit flagged that a
docstring "C-1 note" is just noise. The T-20f comment block in
`move_gen.py:13-21` already documents the gate.

If a future team wants to literally implement C-1 ("allow k=1 when
all alternatives eval < −1"), it would require an eval pass inside
move-gen — adding cost to every node for an edge case that doesn't
move ELO. Not recommended pre-deadline.

---

## §6 File manifest

```
docs/plan/post_bo_patches/
├── README.md                                 (this file)
├── patch_02_C2_early_search_lockout.patch    (agent.py; ~20-line diff)
├── patch_03_ExpC_R2_time_mgr_reskew.patch    (time_mgr.py + test_time_mgr.py; ~180-line diff)
└── patch_04_version_bump.patch               (5 files, line-1 only; ~20-line diff)
```

(`patch_01_C1_k1_gate.patch` dropped — see §5 audit.)

Total LOC changed across all patches (excluding patch headers, per
`git apply --stat`): roughly 200 insertions, 40 deletions, including
the 2 new test functions in patch 03.
