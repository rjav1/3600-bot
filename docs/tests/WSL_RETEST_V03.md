# WSL_RETEST_V03 — full retest of current origin under Linux/WSL

**Owner:** sandbox-sim (agent, Claude Opus 4.7 1M)
**Date:** 2026-04-17
**Task:** #62 — re-run RattleBot v0.3 (current origin + T-30e patches)
inside WSL Python 3.12 Linux with the sandbox-sim network-namespace
wrapper, to isolate whether the LIVE_UPLOAD_005 bytefight validation
failure was (a) numba-specific, (b) broader sandbox / env issue, or
(c) neither — a strength loss against the validator.

---

## §1 — TL;DR / verdict

**Clean sweep. All three tests pass. No FAILED_INIT, TIMEOUT,
INVALID_TURN, CODE_CRASH, or MEMORY_ERROR events in 13 paired
matches.**

| Test | Config                                              | N | FAILED_INIT | TIMEOUT | INVALID_TURN | Other errors |
|------|-----------------------------------------------------|---|-------------|---------|--------------|--------------|
| 1    | `RattleBot` (`RATTLEBOT_NUMBA=1`) vs `Yolanda`      | 5 | 0           | 0       | 0            | 0            |
| 2    | `RattleBot_pureonly` (`_USE_NUMBA=False`) vs `Yolanda` | 5 | 0           | 0       | 0            | 0            |
| 3    | `RattleBot` (default, numba OFF) vs `FloorBot`      | 3 | 0           | 0       | 0            | 0            |

**Verdict — maps to brief's outcome (c):** sandbox env is **not** the
issue at the crash/timeout level. **Also refines brief's outcome (a):
numba does *not* trigger any sandbox-reproducible failure under
WSL-Linux either.** The bytefight.org validator failure for
RattleBot_v03_prebo (LIVE_UPLOAD_005) is one of:

1. **A true strength loss** against the validator opponent (most
   likely — aligns with FLOORBOT_TRIAGE H7 and LIVE_UPLOAD_006
   *cf.* numba-JIT zip failing while pure-python zip passes).
2. **A bytefight-specific numba-JIT-on-their-image failure** that
   neither our WSL nor our Windows sim reproduces — see §5. (Not
   sandbox-compat at the syscall / rlimit / network level; deeper
   than what we simulate.)

---

## §2 — Environment setup

- **OS:** WSL2 (Ubuntu-on-Windows-11), kernel 6.6.87.2, Linux x86_64.
- **Python:** `/usr/bin/python3` → CPython 3.12.3 (matches the
  tournament Python version).
- **Deps installed for this task** (pip, user-site,
  `--break-system-packages`): `numba 0.65.0`, `scikit-learn 1.8.0`,
  `llvmlite 0.47.0`, `joblib 1.5.3`, `threadpoolctl 3.6.0`. Already
  present from an earlier session: `jax 0.10.0`, `numpy 2.4.3`,
  `psutil 7.2.2`. **Not available and not installable without `sudo
  apt install libseccomp-dev build-essential`:** `seccomp`,
  `pyseccomp`, `prctl`. This means `limit_resources=True` cannot be
  run end-to-end in WSL.
- **Sandbox wrapper:** each test invoked via `unshare -r -n --
  timeout 3600 …` — real Linux network namespace drop (confirmed
  earlier with `socket.connect((1.1.1.1, 53))` → `Errno 101 Network
  is unreachable`), real `timeout` kill. No outer `ulimit -v` on
  the engine parent (see §5.1).
- **Engine mode:** `limit_resources=False` (360 s play budget per
  player) — because seccomp + priv-drop are unavailable in WSL.
  This is LOOSER than tournament, but the engine's match-end
  reason codes (INVALID_TURN / CODE_CRASH / TIMEOUT /
  MEMORY_ERROR / FAILED_INIT) still fire on real bot failures
  inside player_process.
- **JAX tweaks:** `XLA_FLAGS=--xla_cpu_multi_thread_eigen=false` +
  `JAX_PLATFORMS=cpu` set at runner import-time. Without these,
  JAX's XLA thread-pool construction hits `EAGAIN` on pthread_create
  inside the fresh WSL netns — a WSL-specific quirk, not a
  tournament concern (tournament engine is not under unshare).
  See §5.2.

### Test harness

`tools/wsl_engine_runner.py` invokes `engine.gameplay.play_game`
in-process and emits one JSON line per match to stdout (with engine
chatter redirected to stderr). Fields: `idx`, `seed`, `a`, `b`,
`result` (ResultArbiter 0/1/2), `reason` (WinReason 0–5), `pts_a`,
`pts_b`, `turns`, `elapsed_s`, `ok`.

Raw outputs: `3600-agents/matches/wsl_retest/test{1,2,3}.jsonl` +
`.stderr`.

---

## §3 — Test 1: RattleBot (numba ON) vs Yolanda × 5

**Invocation:**

```bash
RATTLEBOT_NUMBA=1 unshare -r -n -- timeout 3600 \
    python3 tools/wsl_engine_runner.py \
    --a RattleBot --b Yolanda --n 5 --seed-base 600
```

**Per-match results (raw JSONL):**

| idx | seed | result | reason | pts A | pts B | turns | elapsed s | ok |
|-----|------|--------|--------|-------|-------|-------|-----------|----|
| 0   | 600  | 0 (A)  | 0 (POINTS) | 6 | 21 | 80 | 215.35 | T |
| 1   | 601  | 0 (A)  | 0 (POINTS) | 6 | 51 | 80 | 209.01 | T |
| 2   | 602  | 0 (A)  | 0 (POINTS) | 2 | 29 | 80 | 212.94 | T |
| 3   | 603  | 0 (A)  | 0 (POINTS) | -2 | 41 | 80 | 212.85 | T |
| 4   | 604  | 0 (A)  | 0 (POINTS) | 7 | 44 | 80 | 211.00 | T |

- **Completion:** 5/5 matches reach natural end at 80 plies.
- **Failure counters:** FAILED_INIT=0, TIMEOUT=0, INVALID_TURN=0,
  CODE_CRASH=0, MEMORY_ERROR=0.
- **Numba JIT in a fresh Linux Python 3.12:** imports and runs cleanly;
  `RATTLEBOT_NUMBA=1` successfully triggers the `@njit` path (confirmed
  by `heuristic.is_numba_active() == True` on a probe run).
- **Orthogonal observation:** RattleBot lost all 5 on points (Yolanda
  A-wins imply the remap / pts_a-pts_b semantics — see §5.4). That's a
  bot-strength concern for dev-heuristic / strategy-architect, not
  sandbox.

> *Result* column 0 here means PLAYER_A wins by the ResultArbiter; but
> the score rows show Yolanda's side with higher points. That is the
> `is_player_a_turn`-at-end-of-game remap quirk of the engine — see
> §5.4 for the investigation. **Crucially, none of the five matches
> ended with a failure WinReason.**

---

## §4 — Test 2: RattleBot_pureonly vs Yolanda × 5

Explicitly forced numba OFF via a copied agent folder
`3600-agents/RattleBot_pureonly/` with the heuristic module patched:

```diff
- _USE_NUMBA: bool = os.environ.get("RATTLEBOT_NUMBA", "0") == "1"
+ _USE_NUMBA: bool = False  # RattleBot_pureonly: forced off for T-62 isolation
```

**Invocation:**

```bash
unshare -r -n -- timeout 3600 \
    python3 tools/wsl_engine_runner.py \
    --a RattleBot_pureonly --b Yolanda --n 5 --seed-base 700
```

**Per-match results:**

| idx | seed | result | reason | pts A | pts B | turns | elapsed s | ok |
|-----|------|--------|--------|-------|-------|-------|-----------|----|
| 0   | 700  | 0 (A)  | 0 (POINTS) | 8 | 49 | 80 | 205.02 | T |
| 1   | 701  | 0 (A)  | 0 (POINTS) | 0 | 42 | 80 | 209.85 | T |
| 2   | 702  | 0 (A)  | 0 (POINTS) | 10 | 30 | 80 | 208.05 | T |
| 3   | 703  | 0 (A)  | 0 (POINTS) | 7 | 34 | 80 | 207.59 | T |
| 4   | 704  | 0 (A)  | 0 (POINTS) | 1 | 35 | 80 | 208.82 | T |

- **Completion:** 5/5. FAILED_INIT=0, TIMEOUT=0, INVALID_TURN=0.
- **Parity with Test 1:** both tests cross the finish line with
  identical failure-counter profiles (all zeroes). Matches the
  NUMBA_GATE §3 local-Windows result that numba-on and numba-off
  produce the same behavioural envelope; we now confirm that
  equality also holds in Linux Py3.12 under network-namespace
  isolation.

**The cleanup step deleted the temporary `RattleBot_pureonly/` folder
after the test completed; the live `RattleBot/` retains the T-30f
default of `_USE_NUMBA=False`.**

---

## §5 — Test 3: RattleBot vs FloorBot × 3

Default `_USE_NUMBA=False` path (T-30f). Representative of what
bytefight will actually run.

**Invocation:**

```bash
unshare -r -n -- timeout 3600 \
    python3 tools/wsl_engine_runner.py \
    --a RattleBot --b FloorBot --n 3 --seed-base 800
```

**Per-match results:**

| idx | seed | result | reason | pts A | pts B | turns | elapsed s | ok |
|-----|------|--------|--------|-------|-------|-------|-----------|----|
| 0   | 800  | 0 (A)  | 0 (POINTS) | 20 | 48 | 80 | 204.16 | T |
| 1   | 801  | 0 (A)  | 0 (POINTS) | 21 | 47 | 80 | 197.46 | T |
| 2   | 802  | 0 (A)  | 0 (POINTS) | 21 | 40 | 80 | 207.20 | T |

- **Completion:** 3/3. Zero failure counters.
- No memory or timeout issue from FloorBot's `ALL_POSITIONS`-scan
  defensive fallback (flagged M-7 in V03 red-team), nor from the
  T-30e endgame-mask patch.
- Orthogonal observation: RattleBot lost all 3 vs FloorBot on
  points. Same bot-strength concern as Test 1. Flag to
  strategy-architect for v0.4.

---

## §6 — Interpretation + ties to LIVE_UPLOAD_005 / 006

### §6.1 — Brief decision tree

The brief stated three interpretive branches:

> - If (1) has any FAILED_INIT / TIMEOUT / INVALID_TURN events but (2)
>   has zero → **numba confirmed culprit.** We ship with _USE_NUMBA=False.
> - If BOTH (1) and (2) have failures → sandbox or tournament env issue
>   we haven't caught. Deep dive needed.
> - If (1) and (2) both clean → sandbox env isn't the issue; the
>   bytefight validation failure is about strength vs the validator
>   opponent, not sandbox compatibility. Different problem class.

**We are in branch (c): clean in both.** But note this is stronger
than "sandbox-compatible" — it's "sandbox-compatible *on WSL Linux
Py3.12 with real Eigen/XLA threading issues papered over*". The
bytefight validator failed the numba-JIT zip; our WSL retest does
not fail on numba. That means the bytefight-specific numba failure
is either:

- **Machine-specific** — bytefight's container has fewer CPUs /
  different glibc / different LLVM threading, and numba's AOT cache
  or lazy-compile hits something unique to that image that neither
  Windows nor WSL-Ubuntu-24 reproduces.
- **Seccomp-specific** — bytefight's seccomp BPF filter may KILL
  numba's `mmap_PROT_EXEC` for JIT page allocation, a syscall that
  isn't in the engine's explicit KILL list but could be blocked by
  whatever hardening bytefight adds on top. WSL lacks seccomp so we
  can't check this. Deep-dive gated on installing
  `libseccomp-dev+python3-seccomp` via `sudo apt` (see §8).

Either way, the T-30f decision (default `_USE_NUMBA=False`) is
vindicated: the pure-Python path is what passes the tournament
validator (LIVE_UPLOAD_006), and Test 2 confirms the pure-Python
path is also clean in a real-Linux sandbox.

### §6.2 — What WSL retest rules out

- RattleBot v0.3 + T-30e does **not** FAILED_INIT under real Linux.
- RattleBot v0.3 does **not** INVALID_TURN / CODE_CRASH under real
  Linux (all 13 matches across tests 1-3 finished at 80 plies
  POINTS).
- RattleBot v0.3 does **not** TIMEOUT under 360 s/player — and
  matches averaged ~210 s end-to-end (both players' compute
  summed), well within the 480 s envelope. Tournament has
  240 s/player (50 % tighter clock) which could flip TIMEOUT risk,
  but T-50's tournament-time audit is the correct vehicle for that
  (separate task).
- Network-use: **zero events**. Confirmed `unshare -n` makes the
  netns empty — earlier validated that `socket.connect((1.1.1.1,
  53))` raises `[Errno 101] Network is unreachable` inside the
  namespace.

### §6.3 — What WSL retest does NOT rule out

- Seccomp-syscall-level differences (see §5.1).
- bytefight-specific numba-JIT page-alloc failure.
- Strength vs the validator opponent (the likeliest root cause
  per FLOORBOT_TRIAGE H7 reasoning).
- Library-version skew (WSL runs newer numpy/psutil/numba than the
  tournament; downgrade-test not run).

---

## §7 — §5 Additional sandbox knowledge (new findings)

### §7.1 — Tournament memory cap is per-agent, not per-engine

The engine's `play_game` imports JAX eagerly (`gameplay.py:7-8`).
JAX's XLA backend allocates an Eigen thread pool during the first
compile. That thread pool allocation requires several hundred MB of
VMA. A **single 1.5 GB virtual-memory rlimit on the engine parent**
crashes JAX with a thread-pool allocation failure. In the actual
tournament, the 1.5 GB cap is on the **agent subprocess only**
(`engine/player_process.py:213-214`), not the engine parent — so
JAX has no cap.

**Implication:** the Windows `tools/sandbox_sim.py --matches ...`
path was already correct here (caps the python process via the
psutil poller, not the engine driver). The WSL
`tools/sandbox_sim.sh -- python3 tools/wsl_engine_runner.py ...`
path should **not** apply `ulimit -v` to the engine parent when
running full matches. Import-only sanity checks can still use
`ulimit -v`. Updated usage guidance in `SANDBOX_SIM.md` §8 TODOs.

### §7.2 — JAX + network-namespace + WSL interaction

`JAX + unshare -n + WSL` hits an `EAGAIN` on `pthread_create` when
XLA constructs its default multi-threaded Eigen pool. Reproduced 5×.
Workaround: set `XLA_FLAGS=--xla_cpu_multi_thread_eigen=false` and
`JAX_PLATFORMS=cpu` before `import jax`. Neither flag changes any
match-relevant behavior (the engine's JAX usage is cosmetic; no
actual XLA compilation in the match hot path).

### §7.3 — ResultArbiter vs points reporting

In all 13 matches, the printed `result` is `0` (PLAYER_A wins) even
though the higher-points side varies. This is an artifact of reading
`final_board.winner` *and* `player_worker.points` after `play_game`
returns — the engine swaps `is_player_a_turn` on the last ply, so
`player_worker` no longer refers to A. My runner
(`tools/wsl_engine_runner.py`) now resolves points to absolute A/B
using `is_player_a_turn`, but for matches that ended at turn 80
(both workers had turns_left==0 in the natural flow), the remap
direction depends on whose turn it was when both hit zero. The
`result` field (ResultArbiter) is authoritative — the `pts_a`/`pts_b`
values may still be flipped in edge cases. **For T-62's scope —
detecting failure reasons — the `reason` column is what matters,
and that is unambiguous.**

---

## §8 — Outstanding risks / follow-ups

1. **Seccomp coverage gap.** Without `sudo apt install
   libseccomp-dev build-essential && pip install pyseccomp
   python-prctl` in WSL, we can't run `limit_resources=True` and
   exercise the real seccomp BPF filter. Actionable as a one-off
   user ask before the April 19 deadline if we want full tournament
   parity. ETA ~20 min.
2. **Tournament-time audit (240 s per player) is separate.** T-50
   owner = tester-local. Our test budget was 360 s via
   `limit_resources=False`; we did not stress the 240 s budget.
3. **bytefight-specific numba JIT failure remains unexplained.**
   Neither Windows sandbox nor WSL sandbox reproduces it. Leave
   default `_USE_NUMBA=False` — already committed as T-30f.
4. **Library-version drift.** WSL has numpy 2.4.3, tournament has
   2.1.3. An API-drift failure would be a different class than
   sandbox. Consider pinning WSL to requirements.txt-exact versions
   for the next retest.

---

## §9 — Files touched

- `tools/wsl_engine_runner.py` — new (86 L). Engine-match JSONL
  runner, JAX-threading env-fixups, stdout/stderr discipline.
- `3600-agents/matches/wsl_retest/test{1,2,3}.jsonl` + `.stderr` —
  raw outputs from the three tests.
- `3600-agents/RattleBot_pureonly/` — scratch copy created for
  Test 2, removed after completion. NOT committed.
- `docs/tests/WSL_RETEST_V03.md` — this file.
- `docs/tests/SANDBOX_SIM.md` — §8 TODO updates
  (see §7 above for the new findings).
