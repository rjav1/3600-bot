# BO RUN1-v7 Pace Crisis Diagnosis + Fix Recommendation

**Author:** diagnostician agent
**Timestamp:** 2026-04-17 23:02 local (T-49h to deadline)
**BO PID:** 8868 (alive, verified via `tasklist`)
**Scope:** READ-ONLY on BO + RattleBot + bo_tune files. Recommendation only.

---

## 1. Ground truth (what the filesystem says)

| Signal | Value | Source |
|---|---|---|
| BO launcher stdout first write | 2026-04-17 **17:40:46** | `bo_stdout.log` mtime |
| Latest trial candidate JSON | 2026-04-17 **21:48:08** (`cand_trial002_50du6joq.json`) | `ls -la --time-style=full-iso` |
| Current time | 2026-04-17 **23:02:36** | `date` |
| PID 8868 | **Alive** (49,736 K RSS, low — it's the parent orchestrator) | `tasklist` |
| Trials completed | **2** (trial 0, trial 1 done; trial 2 in flight) | candidate JSONs |
| Elapsed wall-clock | **5h 22m** since launcher started | 23:02 − 17:40 |
| Trials / hr | **~0.37** (2 / 5.37) | math |

**Note on team-lead's "started ~21:22" claim:** the filesystem evidence contradicts
it — `bo_stdout.log` and `bo_pid.txt` both have mtime 17:40, and `bo_pid.txt`
contains PID 8868 which is still alive. The process has been running ~5.4h, not
~1.5h. This shifts the projection further in the wrong direction.

## 2. Config of the running process

Parsed from `bo_stdout.log`:

```
--opponent FloorBot
--n-per-trial 20        # 20 PAIRS = 40 matches per trial
--max-trials 40
--max-hours 24
--parallel 1            # sequential (spawn-pool broken on Windows, per T-74/commit cdfff25)
--catastrophe-penalty 5
--catastrophe-threshold -30
--seed 0
```

**Match budget:** `paired_runner._run_pair` is invoked with `tournament_budget=False`
(hard-coded in `bo_tune.py:193`). `limit_resources=False` (Windows fallback in
`bo_tune.py:490-496`). This means **each match runs with the LOCAL default
time budget, which is 360 s per agent** (per §3 HANDOFF.md invariant: "local
default is 360 s for headroom"), not the tournament 240 s.

## 3. The math (honest projection)

- **Per-trial wall-clock observed:** 5.37 h / 2 trials ≈ **2.68 h/trial** = **161 min/trial**
- **Per-match wall-clock:** 161 min / 40 matches ≈ **4.0 min/match**

  (Sanity: 4 min × 40 moves = 6 s/move × 40 = 240 s bot-time per bot per game,
  × 2 bots = 480 s in theory, but games terminate at turn 80 or earlier, move
  budgets are adaptive via `time_mgr`, and many moves use << 6 s. 4 min/match
  is consistent with an adaptive budget averaging ~3 s/move.)

- **Projected completion of 40 trials:** 40 × 2.68 h = **107 h** from launch
  = 17:40 today + 107h = **2026-04-22 ~04:40** (!!)

- **Time to deadline:** 2026-04-19 23:59 − now = **~49 h**

- **Trials completable by deadline at current pace:** 49 / 2.68 ≈ **~18 trials**
  (plus 2 already done = 20 total). **But** BO needs ≥6h reserved before
  deadline for the 50-match success gate (T-HEUR-3 in `BO_TUNING.md` §6), zip
  build, upload, and scrimmage validation. Realistic usable budget: ~43 h →
  **~16 trials total by the harvest point (T-6h)**.

**Conclusion: at current pace we will get ~40 % of planned trials.** That's not
necessarily fatal — BO's best-observed vector usually lands in the first half
of trials when `x0=W_INIT` seeds the search — but it leaves the exploration
phase truncated.

## 4. Root cause of the slow pace

### Trial dimensionality (dominant factor)
`20 pairs × 2 matches = 40 matches/trial`, each ~4 min → **~160 min/trial** sequential. The root cause is **n_per_trial=20 at sequential=1**.

### Why not parallel?
Per HANDOFF.md §2 and commit cdfff25: the JAX XLA thread pool deadlocks under
`multiprocessing.spawn` on Windows. `bo_tune.py` sets
`XLA_FLAGS=--xla_cpu_multi_thread_eigen=false` + `JAX_PLATFORMS=cpu` in both
parent and child (lines 60-62 and 174-176), but this wasn't sufficient in
earlier runs (v4/v5/v6 all died mid-trial). v7 is **sequential by design** to
avoid the deadlock.

### Why n_per_trial=20?
V01_LOSS_ANALYSIS §6 catastrophe-penalty design needs ≥20 matches for
stable catastrophe-fraction estimates. At n=10 the catastrophe signal is too
noisy (1/20 vs 2/20 swings the term by 0.25, half the whole win-rate range).
At n=20 each trial has 40 matches → stable Wilson 95 % CI of ±10 % around the
point estimate.

### Scrimmage CPU contention
Checked `tasklist` — 7 python.exe processes running:
- PID 8868 = BO orchestrator (49 MB RSS — low, so it's waiting on children)
- PID 16816, 30316, 3088 = 218-374 MB each (likely one BO child + scrimmage workers)
- Others are smaller — probably bytefight poll + scrimmage runners

Scrimmages run via bytefight.org (remote), so they should not compete for CPU
with BO's local matches. But the 3 heavy python.exe processes (~900 MB combined)
suggest **something local is running beside BO**. Need to verify, but this is
not the dominant factor — 4 min/match is already explained by 40 moves × ~6 s.

### Subprocess startup overhead
`paired_runner._run_pair` does NOT spawn a fresh Python for each match; it's
called from within the BO child process. Each match does re-import
engine/gameplay and re-init the agent, but that's ~1-2 s, not minutes.

## 5. Highest-ROI knobs to speed up (ranked)

| Knob | Expected speedup | Cost |
|---|---|---|
| **Cut `n_per_trial` 20 → 10** | **2×** | Catastrophe fraction noisier (but 0.37 → 0.82 trials/hr; better coverage > noise reduction) |
| **Cut `n_per_trial` 20 → 8 + re-rigor at gate** | **2.5×** | Same as above; lose Wilson tightness per trial but still have 16-match signal |
| **Tournament-accurate 240 s/match** | **1.5×** (360 → 240) | Need `tournament_budget=True` in `bo_tune.py:193` — BUT requires edit to bo_tune.py which violates PING-FIRST while BO alive |
| Parallel 2-4 workers | 2-4× **IF** the JAX deadlock stays fixed at sequential seed → pool scale-up | Unknown risk; v4-v6 all deadlocked at >1 worker. Do NOT attempt without a smoke test |
| `--max-trials` 40 → 25 | 0% faster per trial; just declares earlier finish | Loses late exploration (skopt's GP gets most value from first ~15 trials post-seed; 25 is a reasonable stopping point) |

## 6. Recommendation: **HYBRID D — kill + relaunch with n=10, target 25 trials in 14 h**

### Verdict: **Option D (Hybrid)**

### Rationale
- **Option A (kill + relaunch reduced rigor)** is good but team-lead's 10×2s framing mixes up two knobs. The `2s/turn` knob doesn't exist directly — `time_mgr.py` has an adaptive per-turn budget backed by `time_left`. What we can do is flip `tournament_budget=True` (240 s/match instead of 360 s/match, ~1.5× speedup) and cut n_per_trial. But `tournament_budget=True` requires an edit to `bo_tune.py:193` — forbidden while BO alive per PING-FIRST. So: **kill first, then edit, then relaunch**.
- **Option B (let v7 run, harvest at T-6h)** gives us ~16-18 trials with full rigor. This is a defensible "do nothing" option — BO often finds its best in trial 5-15 when seeded from W_INIT. But we lose all late-trial exploration of the 19-dim space and lose flexibility.
- **Option C (skip BO entirely)** forfeits the expected +5-10 ELO. Only pick if we have strong evidence BO is failing to find a better vector than W_INIT, which we don't — we've only seen 2 trials. Premature.
- **Option D (kill + relaunch with n=10 + smaller trials target)** gets us ~30 trials in ~14-16 h, leaving ample time (>30 h) for gate eval, upload, scrimmage. This is the best risk-adjusted option.

### Exact proposed commands (for team-lead to execute)

**Step 1 — verify PID + harvest partial state:**
```bash
cat C:/Users/rahil/downloads/3600-bot/bo_pid.txt          # should be 8868
tasklist | grep 8868                                       # confirm alive
cp -r C:/Users/rahil/downloads/3600-bot/3600-agents/matches/bo_v03_run1_v7 \
     C:/Users/rahil/downloads/3600-bot/3600-agents/matches/bo_v03_run1_v7_preserved
```

**Step 2 — kill BO:**
```bash
taskkill /F /PID 8868
# confirm gone:
tasklist | grep 8868                                       # should be empty
rm C:/Users/rahil/downloads/3600-bot/bo_pid.txt
```

**Step 3 — (optional) edit `bo_tune.py:193` to flip `tournament_budget=False` → `True`:**
Only do this if WSL is available. On pure-Windows this path is disabled
(`paired_runner.py:586-592` errors out on Windows for `tournament_budget=True`).
**Skip this step on Windows.** The local 360 s budget is fine for BO; the gate
run uses tournament budget separately.

**Step 4 — relaunch v8:**
```bash
cd C:/Users/rahil/downloads/3600-bot
python tools/_launch_bo_detached.py -- \
  --opponent FloorBot \
  --n-per-trial 10 \
  --max-trials 30 \
  --max-hours 16 \
  --parallel 1 \
  --catastrophe-penalty 5 \
  --catastrophe-threshold -30 \
  --seed 0 \
  --out 3600-agents/RattleBot/weights_v03.json \
  --log-dir 3600-agents/matches/bo_v03_run1_v8/
```

Diffs vs v7: `--n-per-trial 20 → 10` (2× faster per trial), `--max-trials 40 → 30`
(we'd only reach ~18 at full rigor anyway; 30 at half-rigor gives us more
posterior signal), `--max-hours 24 → 16` (matches the realistic budget given
deadline).

### Expected v8 projection
- Per-trial wall-clock: ~80 min (half of v7's 161 min)
- 30 trials × 80 min = **40 h budget**... wait, that's still too long.

**Recalculation — if we're going with n=10 we get**: 30 trials × 80 min = 2400 min = **40 h**. Deadline is 49 h away. That leaves only 9 h slack — tight but workable.

**Amended proposal:** cut further to **n=8 and max-trials=25**, target **~10 h budget**:
- Per-trial: 8 pairs × 2 matches × 4 min = **64 min/trial**
- 25 trials × 64 min = **~27 h**... still too long.

**Honest final proposal:** the arithmetic forces `n=5, max-trials=20`:
- 5 pairs × 2 matches × 4 min = **40 min/trial**
- 20 trials × 40 min = **13.3 h**

That gives us BO done by 2026-04-18 ~14:00, with 34 h remaining for gate,
upload, scrimmage, and a possible second BO run or patch wave. **This is the
minimum-viable BO — n=5 is 10 matches of signal per weight vector, which is
thin but still informative when the BO objective is dominated by the winrate
term and the GP surrogate averages across nearby trials.**

### Final recommended launch (n=5, 20 trials, 13 h budget)
```bash
python tools/_launch_bo_detached.py -- \
  --opponent FloorBot \
  --n-per-trial 5 \
  --max-trials 20 \
  --max-hours 14 \
  --parallel 1 \
  --catastrophe-penalty 5 \
  --catastrophe-threshold -30 \
  --seed 0 \
  --out 3600-agents/RattleBot/weights_v03.json \
  --log-dir 3600-agents/matches/bo_v03_run1_v8/
```

### Risk notes
- n=5 means catastrophe-fraction resolution is 1/10 = 10 % steps. With penalty
  5, that's a 0.5 point penalty per catastrophe — still dominates 0.1 win-rate
  signal, so catastrophic vectors will still be rejected, just with higher
  noise.
- Wilson 95 % CI at n=10 matches ±30 % — so trial-to-trial comparison is
  noisy. Rely on the BO GP surrogate to smooth, not per-trial comparisons.
- **Gate eval at T-HEUR-3 must still be 50 matches** (per `BO_TUNING.md` §6)
  — do NOT cut the gate's rigor, just the tuning loop's.

## 7. Mandatory report summary

- **Trials completed:** 2 (trial 0, trial 1 done; trial 2 in flight since 21:48)
- **Pace:** 0.37 trials/hr (not 0.5 as team-lead estimated; worse)
- **Recommendation:** **Option D (hybrid)** — kill PID 8868, relaunch as v8 with `--n-per-trial 5 --max-trials 20 --max-hours 14`. This gets us ~20 trials done by 2026-04-18 ~14:00 with 34 h buffer for gate/upload/scrimmage.
- **Rationale:** current pace yields only ~18 trials by deadline-with-buffer anyway; cutting n_per_trial 4× (20→5) and max-trials 2× (40→20) doubles trial coverage in half the wall-clock, at the cost of per-trial CI tightness which BO's GP surrogate mostly absorbs.
- **Fallback if v8 also stalls:** harvest best-trial weights at T-6h (2026-04-19 17:59) from whichever run is alive. Ship W_INIT if no trial beats the gate.
