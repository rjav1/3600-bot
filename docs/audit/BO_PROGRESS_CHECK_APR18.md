# BO_PROGRESS_CHECK_APR18 — RUN1-v7 + RUN1-v8 progress audit

**Audit time:** 2026-04-18 14:17 UTC / 10:17 local
**Auditor:** post-bo-patch-prep
**Scope:** READ-ONLY check. No process kills. No BO/RattleBot edits.

---

## §1 Headline

**Both BO runs are DEAD. No weights produced.** The tournament-blocker
assumption that BO RUN1-v7 is producing candidates throughout the night
is wrong.

| Run | PID | Launched (local) | PID alive? | Last artifact | Trials done | Output weights |
|---|---|---|---|---|---|---|
| v7 | 8868 | 2026-04-17 21:48 | **NO** | `cand_trial002_50du6joq.json` @ 21:48:08 | **0** (see §2) | **none** |
| v8 | 23708 | 2026-04-17 23:11 | **NO** | `cand_trial002_wipmu_fb.json` @ 00:13:06 | **0** (see §2) | **none** |

Neither `3600-agents/RattleBot/weights_v03.json` nor any trial-result
`.json` beyond the single `trialXXX` filename-only artifact exists.

---

## §2 Trial count interpretation

Each run directory contains exactly **one** `cand_trial00*_*.json`
file. The filename says `trial002`, but this is misleading — the
number in the filename is the `skopt` ask() call index, which includes
the initial random-sampled points BO asks for before building its
Gaussian-process surrogate. With `skopt` default
`n_initial_points=10`, the filename `trialNNN` does NOT equal the
number of completed fitness evaluations.

The content of both candidate files is **identical** (same 19-weight
vector, same bytes). This is the `W_INIT`-adjacent weight vector that
skopt generates deterministically from seed=0 as its first ask. It was
written at launch time (21:48 for v7, 23:11→00:13 for v8 — note v8's
file is stamped 00:13, ~1 h after launch, which is the one and only
sign v8 made any progress past launch).

**Interpretation:** both runs produced zero completed fitness
evaluations (no `result_trial*` file, no `weights_v03.json`). The
`cand_trial*` file is BO's *proposal*, written before the paired match
runs start. If no corresponding result file exists, the worker
subprocess either never ran a game or crashed before writing.

---

## §3 PID status verification

```
tasklist //FI "PID eq 8868"  → "No tasks are running"
tasklist //FI "PID eq 23708" → "No tasks are running"
```

Neither python.exe process exists. The repo-root `bo_pid.txt` sentinel
file is also gone (it is listed in `bo_v03_run1_v7/bo_pid.txt` per-run
but the root-level sentinel used by the PING-FIRST protocol is
missing).

`docs/audit/BO_RUN_LOG.md` has no v8 entry, so the v8 relaunch was
undocumented at the time of logging.

---

## §4 Log content

Both `bo_stdout.log` files contain ONLY the launch banner (8-9 lines):
cwd, argv, warning about `--limit-resources` on Windows, followed by
the `[bo_tune] opponent=... log_dir=...` line. **Zero** `[trial N
complete]`/`[trial N result]` output. This is consistent with the
worker never completing a game, or with stdout buffering being cut off
when the parent process died (less likely — `-u` unbuffered flag is
set in argv).

---

## §5 Revised ETA

**ETA to completion: N/A.** Both runs are stopped. There is nothing
to wait for.

If a new BO run (v9+) is launched now (2026-04-18 10:17 local):

- **v7 config** (40 trials × 20 pairs × ~30-45 s/pair sequential) ≈
  **6.7-10 h** to full completion under the original ETA. Deadline is
  2026-04-19 23:59 = ~37 h 42 min away. Fits.
- **v8 config** (20 trials × 5 pairs) ≈ **0.8-1.3 h**. Would finish
  tonight.

BUT: given both earlier launches died silently with no progress past
trial 0, the v9 launch needs a diagnostic pre-flight (run one trial
synchronously and verify `result_trial*.json` is produced) before
committing to a background run.

---

## §6 Anomalies

1. **Root `bo_pid.txt` deleted** — the PING-FIRST sentinel used by
   other agents to detect live BO is gone. Teammates that cache its
   presence may think BO is still protecting `RattleBot/*.py`, but it
   isn't.
2. **v8 undocumented** — `docs/audit/BO_RUN_LOG.md` has no row for v8.
   Whoever launched v8 didn't log it.
3. **Filename numbering** — `cand_trial002` on the very first ask is
   surprising. If `skopt.gp_minimize` internal counter is at 2 on the
   first emitted file, two earlier candidates may have been generated
   in memory but not persisted. This is consistent with silent-early-
   death (process dies after skopt.ask() #2 but before the first
   trial result write).
4. **T-104 "BO v7 pace crisis" is marked completed** in the task
   system. v04-v09 RattleBot zips have shipped (tasks #115, #117,
   #120, #123, #127) — team moved on from BO-tuned weights and
   proceeded with hand-tuned heuristic fixes (F-1/F-2/F-3) instead.
   This audit confirms that pivot was correct: there were no BO
   weights to wait for.

---

## §7 Recommendation

1. **Do NOT relaunch BO.** v04/v05/v06/v07/v09 shipped using hand-
   tuned weights; BO-adopted weights are no longer on the critical
   path per the ship log.
2. **Update `BO_RUN_LOG.md`** to reflect both v7 and v8 as DEAD with
   the timestamps above. Mark task #116 ("Relaunch BO v9 with
   F-1/F-2/F-3 baked in (post-ship)") as blocked-on-investigation —
   the silent-exit bug hasn't been diagnosed, and relaunching without
   fixing it just consumes another ~24 h of process table.
3. **If BO is still desired** for a v10+ ship candidate: before
   relaunch, run
   `python tools/bo_tune.py --opponent FloorBot --n-per-trial 2
    --max-trials 1 --parallel 1 --out /tmp/test.json
    --log-dir /tmp/bo_test/` in the foreground. If that produces
   `/tmp/test.json` with updated weights, detached launch is safe.
   If it silently exits before writing, that's the bug to fix.
4. **Task #126** ("Diagnose WHY v06 F-2 revert went 0W/22") is done
   and #123 ("Ship v06") is done, so the team has already pivoted
   past the BO-adoption flow. Treat BO as a v10+ stretch goal, not a
   ship-blocker.

---

## §8 Artifact inventory

```
3600-agents/matches/bo_v03_run1_v7/
  bo_pid.txt                 — contains "8868"
  bo_stdout.log              — 9 lines, launch banner only
  cand_trial002_50du6joq.json — skopt ask() output at launch, 19 weights

3600-agents/matches/bo_v03_run1_v8/
  bo_pid.txt                 — contains "23708"
  bo_stdout.log              — 9 lines, launch banner only
  cand_trial002_wipmu_fb.json — skopt ask() output at launch, 19 weights
                                (same vector as v7 — seed=0 reproducible)

3600-agents/RattleBot/       — no weights_v03.json
(repo root)                  — no bo_pid.txt
```

Total BO artifacts: ~3 KB across both runs. Nothing salvageable for a
weight-adoption step.
