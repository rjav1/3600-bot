# Post-BO Patches — ready-to-apply diffs

Prepared: 2026-04-17 — while BO RUN1-v7 (PID 8868) still active.

These four unified-diff files (`patch_01_*.patch` … `patch_04_*.patch`)
are ready for `git apply` against a clean `main` tree AFTER the live
BO run completes and its weights are adopted. They implement the
post-BO fixes planned under tasks T-87, T-88, T-95, and T-96
(plus Experiment C from the fresh-eyes architecture audit).

All four patches have been verified with `git apply --check` against
`HEAD` at prep time (commit `17441ec`) and with a full sequential
`git apply` sim against a scratch repo; every target file still parses
as valid Python after the full 1 → 2 → 3 → 4 sequence.

---

## §1 Apply order and rationale (1 → 2 → 3 → 4)

Apply in numeric order. The rationale is:

1. **`patch_01_C1_k1_gate.patch`** — docstring-only note clarifying
   that R5 (k=1 CARPET gate, LOSS_FORENSICS §4.R5) is strictly
   subsumed by the existing `has_non_k1` filter. Zero behaviour
   change; lands first to establish the "we examined R5, no-op"
   record in the tree and avoid downstream patches re-raising the
   question.

2. **`patch_02_C2_early_search_lockout.patch`** — real behaviour
   change: adds a `turns_left > 30 AND max_mass <= 0.35` early-game
   SEARCH lockout to the agent.py gate. Uncorrelated with patches 01
   and 03, so order is flexible between these three, but applying
   second keeps agent.py's history linear (patch 04 edits agent.py
   too — see §3 fallback if order matters).

3. **`patch_03_ExpC_R2_time_mgr_reskew.patch`** — Exp C phase
   multipliers (0.3× / 1.3× / 2.5× replacing 0.6× / 1.0× / 3.5×) +
   R2's 220 s cumulative ceiling guard + 2 new tests. This is the
   biggest change — a full rework of `start_turn`'s budget formula in
   time_mgr.py plus new tests in `tests/test_time_mgr.py`.

4. **`patch_04_version_bump.patch`** — cosmetic docstring bump
   ("RattleBot v0.2" → "RattleBot v0.4" in agent.py/move_gen.py/
   time_mgr.py/search.py, "v0.1" → "v0.4" in rat_belief.py).
   Applied last so the version label reflects the fully-patched v0.4
   state. Each hunk targets lines that patches 01-03 do NOT touch
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
re-plan — patches 01, 02, 04 are independent of it.

---

## §4 Expected ELO impact

Per the source audit documents:

| Patch | Source | Claimed impact |
|-------|--------|----------------|
| 01 (C-1) | COMPETITIVE_INTEL §5.C-1, LOSS_FORENSICS §4.R5 | +0 ELO (no-op; matches R5 via existing filter) |
| 02 (C-2) | COMPETITIVE_INTEL §5.C-2, LOSS_FORENSICS §4.R3 | +1.5 pts/match vs student agents that rat-spam early |
| 03 (Exp C + R2) | ARCH_CONTRARIAN §4 Exp C + LOSS_FORENSICS §4.R2 | +10-25 ELO (Exp C) + eliminates Match-2 "241 s" failure mode (R2) |
| 04 (version bump) | T-95 | 0 ELO (cosmetic) |

Net expected: **+10-30 ELO** improvement assuming no regression
against George/Yolanda and no interaction with the BO-adopted
weights. Patch 03 is the largest lever and also the largest risk —
the paired-test smoke in §2.3 is the load-bearing verification step.

---

## §5 File manifest

```
docs/plan/post_bo_patches/
├── README.md                                 (this file)
├── patch_01_C1_k1_gate.patch                 (docstring only; 12-line diff)
├── patch_02_C2_early_search_lockout.patch    (agent.py; ~20-line diff)
├── patch_03_ExpC_R2_time_mgr_reskew.patch    (time_mgr.py + test_time_mgr.py; ~180-line diff)
└── patch_04_version_bump.patch               (5 files, line-1 only; ~20-line diff)
```

Total LOC changed across all patches (excluding patch headers, per
`git apply --stat`): roughly 200 insertions, 40 deletions, including
the 2 new test functions in patch 03.
