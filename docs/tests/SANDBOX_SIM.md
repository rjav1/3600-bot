# SANDBOX_SIM — Tournament-sandbox simulator

**Owner:** sandbox-sim (agent, Claude Opus 4.7 1M)
**Date:** 2026-04-16
**Task:** #37 — reproduce bytefight.org's tournament execution environment locally,
so we catch sandbox-incompatible code BEFORE uploading.

**TL;DR.** We ship **two** complementary simulator paths and used **both**.
RattleBot v0.2 and FloorBot both run to completion with **0 sandbox violations**,
**0 exceptions**, **0 memory cap breaches**. RattleBot's pytest suite runs
**51/52 passing** under the sandbox, identical to the baseline (the one
failing test is an in-progress T-20c.1 heuristic test, unrelated to sandbox).
The simulator is not a proof, but it rules out a large class of pre-flight
failure modes and narrows the residual risk envelope sharply.

---

## §1 — Environment chosen

We implement **both** paths the brief allows:

1. **`tools/sandbox_sim.py`** — pure-Python in-process sandbox (primary).
   Runs on Windows + WSL + Linux. Installs hooks into the running Python
   interpreter and propagates them to `multiprocessing` child processes
   via a generated `sitecustomize.py`.
2. **`tools/sandbox_sim.sh`** — shell wrapper using WSL's `ulimit` +
   `unshare -n` + `timeout` (secondary, for Linux import-checks only).

### Why both

- The tournament Python (3.12, Linux x86_64) is available inside WSL —
  that's a match on version + OS that Windows Python 3.13 can't give.
  **Use case:** prove our agents import cleanly under the actual
  tournament Python.
- WSL's Python 3.12, however, **lacks the engine's dependencies**
  (`jax`, `psutil`, `scikit-learn`) because those aren't present on the
  WSL rootfs, and the constraint is "don't install new OS packages."
  So the WSL path can only run **bot-import sanity checks**, not full
  engine matches.
- Windows Python 3.13 has every engine dep. **Use case:** run full
  engine matches + pytest under the pure-Python sandbox.

This hybrid covers complementary failure surfaces: WSL proves Linux-Py3.12
compatibility at import time; Windows sandbox proves the bots don't touch
blocked resources during actual gameplay.

---

## §2 — What the simulator simulates (and doesn't)

### §2.1 — What `sandbox_sim.py` enforces

| Rule (from GAME_SPEC §7 / CLAUDE.md §6)          | How enforced                                                                                                                  |
|---------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| No network                                        | `sys.meta_path` hook rejects third-party net libs (`requests`, `httpx`, `aiohttp`, etc.). `socket.socket.__init__` and `socket.create_connection` / `getaddrinfo` raise `PermissionError`. Mirrors seccomp, which blocks the *syscall*, not the module import. |
| No filesystem writes outside cwd                  | `builtins.open` is wrapped. Any `open(path, 'w'/'a'/'x'/'+')` where the resolved path is outside `os.getcwd()` raises `PermissionError`. Device paths (`NUL`, `/dev/null`, `\\.\\nul`) are whitelisted so stdlib/pytest logging still works. |
| 1.5 GB RAM cap (matches `limit_resources=True`)   | On Linux: `resource.setrlimit(RLIMIT_AS, 1.5 GB)`. On all platforms: psutil background poller (250 ms) sums RSS of self + children, `os._exit(137)` if exceeded. |
| 4 min play budget + 10 s init                     | Enforced by the engine itself when the sandbox passes `limit_resources=True`. We pass a 5 min outer wall-clock timeout via `--timeout`. |
| Child-process isolation                           | `multiprocessing` children (spawned by `engine/player_process.py`) re-install the sandbox automatically via `tools/_sandbox_site/sitecustomize.py`, prepended to `PYTHONPATH` by the parent. |

### §2.2 — What `sandbox_sim.sh` enforces (WSL path)

| Rule                              | How enforced                                                                         |
|-----------------------------------|---------------------------------------------------------------------------------------|
| No network                        | `unshare -r -n` — child runs in a fresh network namespace with no interfaces.         |
| 1.5 GB virtual memory             | `ulimit -v 1572864`                                                                   |
| 512 MB max single-file size       | `ulimit -f 524288`                                                                    |
| No core dumps                     | `ulimit -c 0`                                                                         |
| 5 min wall-clock                  | `timeout --signal=TERM --kill-after=5s 300s`                                          |

### §2.3 — What we canNOT simulate

Be honest about the limits:

1. **Seccomp syscall filter.** `limit_resources=True` in `engine/player_process.py:apply_seccomp` installs a seccomp BPF filter that KILLs the process on restricted syscalls (`chmod`, `prctl`, `execve`, `setrlimit`, `adjtimex`, etc.). Our Python-level patches do not intercept direct syscalls made by C extensions. A C extension in a bot could still issue a raw `socket()` syscall we would miss — but we'd catch its Python-visible effects (a bot can only *use* the socket from Python, which is patched).
2. **UID drop.** Tournament drops to an unprivileged UID. We don't — Windows has no equivalent, and WSL-path commands run as user (root-in-userns when unshare is active).
3. **Exact Python version.** Windows sandbox runs Python 3.13; tournament is 3.12. WSL sandbox runs Python 3.12 (match) but can only import-check, not full-play. **So no single run covers both "3.12 Linux" AND "full engine match" at once.**
4. **Library-version skew.** Our local numpy/psutil/etc. versions may differ from the tournament machine. Not something the sandbox can fix.
5. **Clock-speed skew.** The tournament machine's CPU is slower than a modern Windows dev box by some amount. `limit_resources=False` gives 360 s instead of 240 s specifically to paper over this. Our sandbox does not simulate slower CPU.
6. **Memory-pressure edge cases.** `RLIMIT_AS` (virtual) is not the same as `RLIMIT_RSS` (physical). On Linux they mostly coincide; on Windows we only have the psutil poller which has ~250 ms lag.
7. **Sandbox propagation via `multiprocessing.spawn`.** Windows and macOS use `spawn` by default; our sitecustomize hack works, but the re-install happens *after* the target module has already started importing, so if the very first import in the child is a blocked module we'd miss it. The engine's child entry point (`run_player_process`) doesn't import net libs, so this is academic.

---

## §3 — RattleBot v0.2 results under sandbox

### §3.1 — Pytest suite

```
cd 3600-bot
PYTHONPATH="engine;3600-agents" python tools/sandbox_sim.py \
    --pytest 3600-agents/RattleBot/tests/
```

**Result: 51/52 passed.** Elapsed 11.8 s.

| Group                   | Passed | Failed                                  |
|-------------------------|--------|-----------------------------------------|
| test_heuristic.py       | N-1    | `test_zero_features_on_empty_board` *†* |
| test_rat_belief.py      | all    | —                                       |
| test_search.py          | all    | —                                       |
| test_time_mgr.py        | all    | —                                       |

*†* This test ALSO fails in the baseline (no sandbox) run, confirmed by
a side-by-side comparison. The failure is caused by T-20c.1's
multi-scale distance kernel landing new features the test wasn't
updated for. **Not a sandbox-induced failure.**

**Net sandbox impact on tests: 0 new failures, 0 spurious passes.**

### §3.2 — Engine matches (5× RattleBot vs Yolanda)

```
PYTHONIOENCODING=utf-8 python tools/sandbox_sim.py \
    --matches 5 --a RattleBot --b Yolanda --seed 400 --timeout 2400
```

| Match | Seed | Exit reason | RattleBot pts | Yolanda pts | Violations | Exceptions |
|-------|------|-------------|---------------|-------------|------------|------------|
| 1     | 400  | POINTS      | 0             | 30          | 0          | 0          |
| 2     | 401  | POINTS      | 4             | 44          | 0          | 0          |
| 3     | 402  | POINTS      | −5            | 25          | 0          | 0          |
| 4     | 403  | POINTS      | −2            | 17          | 0          | 0          |
| 5     | 404  | POINTS      | −1            | 53          | 0          | 0          |

All 5 matches completed cleanly through all 80 plies (`reason=0 = POINTS`).
**0 INVALID_TURN, 0 CODE_CRASH, 0 MEMORY_ERROR, 0 TIMEOUT, 0 FAILED_INIT.**
Total elapsed: 1069 s (this run was under heavy CPU contention from
teammates running BO tuning in parallel; throughput is not a data
point here, completion is).

> **Aside — not a sandbox finding:** RattleBot v0.2 underperforms
> Yolanda on points in this run. That's **bot quality**, not sandbox
> correctness. Flag to tester-local / v02-planner.

### §3.3 — WSL Py3.12 Linux import sanity (path B)

```
wsl -- tools/sandbox_sim.sh -- python3 -c \
    'import sys; sys.path[0:0]=["engine","3600-agents"]; import RattleBot'
```

**Result:** `RattleBot imported OK in Py3.12 Linux under sandbox` with
exit 0, `unshare -r -n` active (network dropped — confirmed by a
side-test that `socket.connect((\"1.1.1.1\", 53))` raises
`[Errno 101] Network is unreachable`).

Also verified `import Yolanda` and `import FloorBot` succeed.

**This is the single strongest piece of evidence we have that RattleBot's
code is Linux-Py3.12-compatible at import time.** None of its
submodules (`rat_belief`, `search`, `heuristic`, `move_gen`,
`time_mgr`, `zobrist`, `types`, `agent`) throw in Python 3.12 / Linux.

---

## §4 — FloorBot sanity-check result

```
PYTHONIOENCODING=utf-8 python tools/sandbox_sim.py \
    --matches 5 --a FloorBot --b Yolanda --seed 500 --timeout 600
```

| Match | Seed | Exit reason | FloorBot pts | Yolanda pts | Violations | Exceptions |
|-------|------|-------------|--------------|-------------|------------|------------|
| 1     | 500  | POINTS      | 9            | 32          | 0          | 0          |
| 2     | 501  | POINTS      | 4            | 38          | 0          | 0          |
| 3     | 502  | POINTS      | 3            | 26          | 0          | 0          |
| 4     | 503  | POINTS      | −1           | 24          | 0          | 0          |
| 5     | 504  | POINTS      | −2           | 27          | 0          | 0          |

**5/5 complete, 0 errors, 0 violations, elapsed 14.4 s.**

### Does this indicate an incomplete sandbox?

The brief says: *"FloorBot passes 100/100 locally. If it STILL passes
under our sandbox simulator AND we know the real tournament kills it —
then our sandbox simulator is incomplete."*

**Reading the full triage:** `docs/audit/FLOORBOT_TRIAGE.md` (Task #24,
completed 2026-04-17) concluded that FloorBot's bytefight failure
**was not a local code bug** — 381+ local matches, 0 INVALID_TURN, 0
CODE_CRASH, 0 TIMEOUT, 0 MEMORY_ERROR, 0 FAILED_INIT. The failure
diagnosis was H7: *"validator is winning gate, FloorBot lost on
merits"*.

Given FloorBot does not fail locally under any test we've run, our
sandbox showing FloorBot passing is **expected and consistent**, not a
sandbox-simulator gap. This is a negative confirmation, not negative
evidence against the simulator.

The brief's hypothetical ("if FloorBot still passes here") was based
on an earlier interpretation where the bytefight failure might have
been a sandbox-specific kill. The newer triage ruled that out.

---

## §5 — Outstanding risks (things the simulator can't catch)

1. **Library-version skew.** Tournament runs
   `numpy==2.1.3`, `numba==0.61.0`, `psutil==6.0.0`, `torch==2.9.0`,
   `jax` (unpinned). Our Windows has whatever pip installed last. An
   API that exists in our version and not theirs would only show up
   on upload.
   *Mitigation:* pin `requirements.txt` versions locally and diff
   against the tournament list.
2. **Slower-CPU timeouts.** `limit_resources=True` gives 240 s play.
   If the tournament CPU is 1.5× slower than our dev box, a
   9-ply search that fits in 4 s locally may time out at 6 s remote.
   *Mitigation:* `time_mgr.py` has a 6 s hard ceiling; stay well
   under. Consider running
   `sandbox_sim.py --matches N --limit-resources` (tournament's
   240 s budget) as an artificial tightening; on Windows this won't
   actually drop UID / apply seccomp (psutil/seccomp missing in
   WSL), but it *will* halve the play budget, which is the
   clock-skew worst-case.
3. **C-extension direct syscalls.** A C extension linked into numpy
   or torch could issue a raw `socket()` syscall we'd never see from
   Python. Practically, nobody in the numerical-stack does this;
   `socket.socket()` is the only audit path we check.
4. **Seccomp divergence.** The actual seccomp rules
   (`engine/player_process.py:apply_seccomp`) kill on `chdir`,
   `chmod`, `mount`, etc. We do not patch most of those. A bot that
   calls `os.chdir` would not fail locally but would fail on
   tournament. *Mitigation:* code-review forbids `os.chdir` in bot
   code.
5. **Memory-cap lag.** 250 ms psutil poll means a bot that allocates
   2 GB in a single 100 ms spike may OOM the process before our
   poller reports. `RLIMIT_AS` on Linux kicks in synchronously; on
   Windows we are stuck with the poller.
6. **WSL path can't run full matches.** WSL Py3.12 is missing `jax`,
   `psutil`, etc. The brief said "don't install new OS packages,"
   so we did not `apt install python3-jax` or `pip install`. To
   close this gap, a future-dev TODO is to create a WSL venv and
   `pip install -r requirements.txt` into it. That would let us
   run full matches in the actual tournament Python version. Out of
   scope for this task.
7. **Validator opponent unknown.** Our simulator can't model how
   the bytefight validator decides to promote a submission. Live
   scrimmages (see `docs/tests/LIVE_UPLOAD_*.md`) are the only
   ground truth there.

---

## §6 — Usage — how to invoke before upload

### §6.1 — Quick pre-flight (≤ 1 min)

```bash
# 1. Sandbox self-test — 5 probes, confirms install works.
python tools/sandbox_sim.py --self-test

# 2. WSL Py3.12 Linux import check — cheapest possible "will this
#    even import on the tournament Python?" test.
wsl -- /mnt/c/Users/rahil/downloads/3600-bot/tools/sandbox_sim.sh -- \
    python3 -c 'import sys; sys.path[0:0]=["engine","3600-agents"]; import RattleBot'
```

Both should exit 0.

### §6.2 — Full pre-flight (≥ 5 min)

```bash
# 3. Pytest under sandbox — confirms no new failures vs baseline.
PYTHONPATH="engine;3600-agents" python tools/sandbox_sim.py \
    --pytest 3600-agents/RattleBot/tests/

# 4. Five matches against Yolanda — confirms no crash/timeout/mem/net
#    under sandbox.
PYTHONIOENCODING=utf-8 python tools/sandbox_sim.py \
    --matches 5 --a RattleBot --b Yolanda --seed 42 --timeout 1800
```

Both should exit 0 with `violations=0` and `errors=0` in the summary
line printed to stderr.

### §6.3 — Optional tighter pre-flight (slow)

```bash
# 5. Use tournament's 240 s budget (not local 360 s).
python tools/sandbox_sim.py \
    --matches 5 --a RattleBot --b Yolanda --seed 42 \
    --limit-resources --timeout 2000
```

If this passes, our tournament-clock-budget margin is real.
Note: on Windows/WSL without `seccomp`/`prctl` Python bindings, the
engine path `limit_resources=True` will raise at
`apply_seccomp()` import. Skip this on Windows — use it only on a
Linux box with the full tournament deps installed.

### §6.4 — Reporting

Look for these lines in stderr (one per run):

```
[sandbox_sim] installed — cwd='...' cap=1536 MB blocked_imports=6 socket_patched=yes
[sandbox_sim] match N/M seed=S winner=W reason=R A=P_A B=P_B
[sandbox_sim] matches complete: M/M errors=0
[sandbox_sim] done — rc=0 elapsed=Xs violations=0
```

Any `VIOLATION` lines indicate the bot touched a blocked resource.
Investigate before uploading.

---

## §7 — Files delivered

- `tools/sandbox_sim.py` — pure-Python simulator + CLI.
- `tools/sandbox_sim.sh` — WSL/Linux shell wrapper.
- `tools/_sandbox_site/sitecustomize.py` — auto-generated, propagates
  the sandbox to multiprocessing child processes. Do NOT hand-edit;
  `install_sandbox()` regenerates it.
- `docs/tests/SANDBOX_SIM.md` — this file.

---

## §8 — TODOs / follow-ups

- **~~TODO (non-blocking):~~ RESOLVED 2026-04-17 (T-62).** WSL now has
  `jax numpy psutil numba scikit-learn` installed to user-site (not a
  venv, `pip install --user --break-system-packages`). Full engine
  matches run in WSL Py3.12 Linux via the new
  `tools/wsl_engine_runner.py`. See `docs/tests/WSL_RETEST_V03.md` for
  13 clean matches across RattleBot (numba ON + OFF) × Yolanda/FloorBot.
- **New finding (T-62) — memory cap scope.** The 1.5 GB cap is a
  **per-agent** cap in tournament (`engine/player_process.py:213-214`),
  not a per-engine cap. JAX imported in `engine/gameplay.py:7-8`
  needs hundreds of MB of VMA for its Eigen thread pool; capping the
  engine parent with `ulimit -v 1572864` crashes JAX during init.
  **Do NOT pass `--mem-kb 1572864` to `sandbox_sim.sh` when running
  full engine matches.** For import-only sanity checks, the tight cap
  is fine.
- **New finding (T-62) — JAX + unshare.** Under `unshare -r -n` in
  WSL, JAX hits `EAGAIN` on `pthread_create` building its Eigen pool.
  Workaround (set as defaults in `tools/wsl_engine_runner.py`):
  `XLA_FLAGS=--xla_cpu_multi_thread_eigen=false` + `JAX_PLATFORMS=cpu`.
  Not a tournament concern — the tournament engine isn't under unshare.
- **TODO (non-blocking):** `libseccomp-dev + python3-seccomp + prctl`
  not installed in WSL. Blocks running `limit_resources=True` end-to-end
  in WSL (to exercise the real seccomp BPF filter). Requires `sudo apt
  install libseccomp-dev build-essential && pip install --user
  --break-system-packages pyseccomp python-prctl`. Estimated ~20 min of
  user action.
- **TODO (non-blocking):** Wire `sandbox_sim.py --pytest` into a
  pre-commit hook so any RattleBot push runs the sandbox suite first.
- **TODO (non-blocking):** Add a `--strict-seccomp` flag that also
  intercepts `os.chdir`, `os.chmod`, `os.execve*` — would tighten
  tournament-divergence item §5.4.
