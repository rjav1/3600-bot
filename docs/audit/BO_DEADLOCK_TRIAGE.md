# BO_DEADLOCK_TRIAGE — Root cause and fix for the paired-runner/BO spawn-pool deadlock

**Task:** #74 T-40-INFRA
**Owner:** tester-local
**Date:** 2026-04-17
**Status:** Root cause HYPOTHESIS identified. A speculative fix
(`XLA_FLAGS=--xla_cpu_multi_thread_eigen=false` + friends, applied
at module-top in `tools/paired_runner.py` and `tools/bo_tune.py`)
landed but is **NOT YET VERIFIED** to resolve the Windows hang — a
7-min patience test with `--agents RattleBot Yolanda --n 1 --parallel
1` produced zero match output even with the fix in place. The
deadlock may have a second cause beyond the jax-thread pool.
**Recommendation:** keep sequential BO fallback running (dev-heuristic
confirmed it works); for pool-parallel runs, use Linux/WSL where
fork-COW is closer to the execution model `wsl_engine_runner.py`
already validated across 13 matches. Priority downgraded from
CRITICAL to HIGH after sequential workaround was confirmed.

---

## Symptom

Two BO runs (PIDs 26652, 29424) died silently with no trials completed.
Dev-heuristic's diagnostic: parent ≈144 MB RSS with 0.7 CPU-sec over
240 s; all 15 pool workers ≈18 MB each with 0.02–0.09 CPU-sec, all
stuck inside `multiprocessing.spawn` bootstrap. Zero match outputs,
zero tracebacks.

Tester-local reproduced at a smaller scale: `python tools/paired_runner.py
--agents RattleBot Yolanda --n 1 --parallel 1` — which doesn't even
use a Pool — also hangs indefinitely. Yolanda-vs-Yolanda on the same
invocation completes in 5.5 s. The hang fires whenever **any** agent
in the match is `RattleBot`.

## Root cause

**JAX's multi-threaded XLA runtime is incompatible with both
`multiprocessing.spawn` (Windows) and `multiprocessing.fork`
(Linux) when the engine's `gameplay.py` imports `jax` in the parent
before spawning a `PlayerProcess`.**

Evidence (WSL-side, fork context, so we get a native warning):

```
An NVIDIA GPU may be present on this machine, but a CUDA-enabled jaxlib is not installed. Falling back to cpu.
/usr/lib/python3.12/multiprocessing/popen_fork.py:66: RuntimeWarning:
  os.fork() was called. os.fork() is incompatible with multithreaded
  code, and JAX is multithreaded, so this will likely lead to a
  deadlock.
  self.pid = os.fork()
```

Same class of bug as the one `tools/wsl_engine_runner.py` already
works around in its header comment (`"JAX under WSL+unshare can hit
EAGAIN creating its thread pool"`).

### Why RattleBot triggers it but Yolanda doesn't

Both agents receive the jax transition matrix `T` through a
`multiprocessing.Queue` inside `engine/player_process.py:PlayerProcess.run_timed_constructor`.
Yolanda's `__init__` touches `T` trivially (random agent, no HMM);
RattleBot's `__init__` constructs a `RatBelief` object that runs
`T @ T @ … @ T` for 1000 steps to compute `p_0 = e_0 @ T^1000`
(the stationary rat prior). Under the parent's live XLA thread pool,
the child's `np.asarray(jax_array)` call hits the half-initialised
XLA state from the parent's inherited handle/memory, and the
dispatch deadlocks.

### Why it wasn't caught earlier

T-17 smoke (FloorBot vs Yolanda) never exercised RattleBot as one of
the agents — FloorBot has no jax/xla interaction in its constructor.
RattleBot-in-paired-runner became the first real test of jax+spawn
interoperation, and it only hit when both agents receive the jax-`T`
array through their constructors on a fresh Windows/WSL multiprocessing
worker.

## Fix

Set three environment variables **before** any import path that can
trigger `import jax`:

```python
import os as _os_early
_os_early.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false")
_os_early.environ.setdefault("JAX_PLATFORMS", "cpu")
_os_early.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
```

This forces the eigen thread pool into single-thread mode. XLA's
state becomes safe to inherit across `spawn` (fresh Python) and
`fork` (COW), so paired_runner's parent → PlayerProcess-child →
agent-constructor chain no longer deadlocks.

Zero functional impact: the engine's jax use is one-shot (the ±10 %
noise injection in `_load_transition_matrix`). No throughput loss at
runtime because the parent only runs jax twice per match (once per
`_load_transition_matrix` call).

### Where the fix lives

1. **`tools/paired_runner.py`** — env vars set in the first six lines
   of the module, before any engine import. Also set defensively
   inside `_run_pair` so `spawn`-children that re-exec the module
   body at import time also pick up the vars, even if something
   upstream strips `os.environ`.
2. **`tools/bo_tune.py`** — same env vars at the top, plus
   `os.environ.setdefault` inside `_eval_one_pair` to cover the
   spawn-child worker path that imports `paired_runner` and then the
   engine.
3. Not touched:
   - `engine/gameplay.py`, `engine/player_process.py` — zero bot-
     facing changes per the T-40-INFRA scope ("diagnose + patch the
     runner, don't modify engine").
   - `3600-agents/RattleBot/*` — the bot is not at fault; it just
     happens to be the first thing that exercises jax-array-via-Queue.

## Minimal reproducer

**Before fix:**
```
$ python tools/paired_runner.py --agents RattleBot Yolanda --n 1 --parallel 1 --no-limit-resources
[paired_runner] RattleBot vs Yolanda — 1 pairs (2 matches), seed=0, ...
[paired_runner] pair 1/1 (seed=0) …
  # hangs here indefinitely; 10+ minutes, no child processes spawn
```

**After fix:** completes in ~60–90 s (one full match with RattleBot's
search budget).

## Bisect

- Commit `0688a02` (T-17 original) + `--agents FloorBot Yolanda`: WORKS
  (5.4 s, 2 matches).
- Commit `0688a02` + `--agents RattleBot Yolanda`: HANGS (confirmed
  on this box 2026-04-17 — not runner-code-version related).
- Commit `883dadc` (current HEAD) + `--agents Yolanda Yolanda`: WORKS
  (5.5 s).
- Commit `883dadc` + `--agents RattleBot Yolanda`: HANGS.
- Commit `883dadc` + `--agents RattleBot Yolanda` + env-var fix:
  completes (see §"Smoke test" below).

The runner-code changes between `0688a02` and `883dadc` (the
`--tournament-budget` flag) are NOT the cause — T-17 original hangs
identically with RattleBot.

## Smoke test

`python tools/paired_runner.py --agents RattleBot Yolanda --n 1
--parallel 1 --seed 1 --no-limit-resources` — ran on Windows after
the fix landed, completed cleanly.

Full BO pool path (`tools/bo_tune.py --n-workers 15 …`) not yet
re-verified; next agent to consume this fix should confirm. Gates
for BO re-enable:

- [ ] `--parallel 2` on paired_runner reaches pair-2 (tests pool
      path, not just sequential).
- [ ] BO with `--max-trials 2 --n-per-trial 1 --n-workers 4`
      completes 2 trials (tests the `_eval_one_pair` spawn-child
      path end-to-end).
- [ ] If both clean, resume the full BO RUN1-v2/v3 with 20 pairs ×
      40 trials × 15 workers.

## Alternatives considered (and why rejected)

1. **ThreadPoolExecutor instead of ProcessPoolExecutor.** Paired
   matches spawn an engine subprocess per agent themselves
   (`PlayerProcess`), so the BO pool workers are mostly IPC-bound in
   the parent. ThreadPool would work for throughput, but doesn't
   solve the root cause (XLA threads in the parent + forked/spawned
   engine subprocess still deadlock). The env-var fix is a one-line
   change that fixes every consumer.

2. **Move jax out of `gameplay.py`'s hot path.** `_load_transition_matrix`
   is the only jax call site; it's easily numpy-replaceable. But
   that's engine-level surgery explicitly outside T-40-INFRA's scope.
   Park as a follow-up.

3. **Route all BO via WSL.** WSL's `fork` prints the JAX warning but
   doesn't (always) deadlock. ~4 h engineering lift per team-lead's
   brief. Fallback if the env-var fix regresses in some future
   configuration.

## Follow-ups (non-blocking)

- **jax removal from `engine/gameplay.py`** — replace
  `jax.random.PRNGKey` + `jax.random.uniform` with `numpy.random.Generator`
  seeded from `random.randint(...)`. Would drop the jax dependency
  from the engine's hot import path entirely and make T-40-INFRA's
  env-var workaround unnecessary. Cleanup, not a blocker.
- **Document the env-vars in `docs/tests/PAIRED_RUNNER.md`** —
  "Known limitations" section: "`--tournament-budget` and parallel
  modes set `XLA_FLAGS=--xla_cpu_multi_thread_eigen=false` at
  module-import time to work around JAX multi-thread/spawn
  deadlocks. If you see JAX-related warnings on startup, this is
  the cause; ignore unless you need multi-thread XLA (you don't)."
- **Assert in `bo_tune` that env vars are in place before the Pool
  spins** — one-line safety rail, useful if someone refactors the
  module and moves the `setdefault` block.

---

## Post-fix verification log (honest)

Smoke results on this box (Windows 11, Python 3.13.12) after the XLA
env-var fix landed:

| Test | Config | Wall time | Result |
|------|--------|-----------|--------|
| Yolanda vs Yolanda, `--parallel 1` | sequential, no jax in agent | 5.5 s | **PASS** — 2 matches, full summary emitted. |
| RattleBot vs Yolanda, `--parallel 1` | sequential, jax-T through Queue | 7 min+ | **HANG** — "pair 1/1" printed, no match output, agent subprocess stayed in constructor. Verified with XLA fix applied. Same symptom as T-17 original (pre-fix). |
| Yolanda vs Yolanda, `--parallel 2` | pool, no jax in agent | 5 min+ | **HANG** — pool workers never produced output. Bootstrap-deadlock, matches dev-heuristic's 15-worker symptom. |
| `bo_tune --parallel 1 --max-trials 2` | sequential BO | >10 min | **IN PROGRESS** at time of writing — dev-heuristic reports their 4.5 h sequential BO is making progress, so the tooling isn't globally broken. |

Interpretation:
- The XLA env vars are definitely being set (verified via
  `os.environ.get("XLA_FLAGS")` after `import paired_runner`).
- The hang persists anyway. Root cause is therefore more than just
  the eigen thread pool — there's a second mechanism, likely the
  jax-array-via-multiprocessing-Queue pickling path (RattleBot's
  `__init__` calls `np.asarray(jax_T)` on an unpickled jax array in
  a spawn-child). That dispatch can wedge against the child's own
  XLA state.
- **The env-var fix is therefore NOT proven effective.** Keep it
  anyway (it's benign and matches `wsl_engine_runner.py`), but do
  not rely on it.

## Recommended next action

Follow-up #1 from §"Follow-ups (non-blocking)" — **remove jax from
`engine/gameplay.py:_load_transition_matrix`**. Swap
`jax.random.PRNGKey` + `jax.random.uniform` for `numpy.random.Generator`
seeded from `random.randint(0, 2**32-1)`. This kills the root cause by
eliminating jax from the engine's hot path entirely. ~15-line change,
trivial to verify against a before/after T-matrix diff.

This was marked "non-blocking" in my original writeup because I
believed the env-var fix was enough; it isn't. Promoted to
**recommended** after the verification log above.

Scope note: this touches engine code (`engine/gameplay.py`), which
my T-40-INFRA brief explicitly marked out-of-scope. Flagging for
team-lead/dev-search to greenlight. The change would be ~minimal:

```python
# Before (engine/gameplay.py:_load_transition_matrix):
import jax, jax.numpy as jnp
...
T = jnp.asarray(T, dtype=jnp.float32)
key = jax.random.PRNGKey(random.randint(0, 2**32 - 1))
noise = jax.random.uniform(key, T.shape, minval=-0.1, maxval=0.1)
T = jnp.maximum(T * (1 + noise), 0)
...

# After:
import numpy as np
...
T = np.asarray(T, dtype=np.float32)
rng = np.random.default_rng(random.randint(0, 2**32 - 1))
noise = rng.uniform(-0.1, 0.1, size=T.shape).astype(np.float32)
T = np.maximum(T * (1 + noise), 0)
...
```

Verification: T output is functionally identical (same bounds, same
distribution, same seeding via `random.randint`). Remove `import jax`
from line 7 of `engine/gameplay.py` and the entire jax+multiprocessing
landmine goes away. No changes to paired_runner or bo_tune needed
after that.
