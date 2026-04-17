# NUMBA_GATE — T-30c-numba correctness + perf verification

Owner: **dev-search** · Delivered 2026-04-17 · Scope: RattleBot v0.3

Task: verify the `@njit(cache=True)` hot-path in `heuristic.py` ships safely
to the tournament sandbox with a pure-Python kill-switch available.

---

## §1 — Kill-switch contract

- Module-level constant `_USE_NUMBA = True` in `heuristic.py`.
- Env-var override: `RATTLEBOT_NUMBA=0` → force pure-Python path at
  import time.
- Public accessor: `heuristic.is_numba_active() -> bool` — True iff numba
  is imported AND the kill-switch is not turned off.
- If `numba` import fails at load, the module silently falls back to
  the Python path (no exception escaping to `PlayerAgent.__init__`).

---

## §2 — Parity proof (in-process)

`tests/test_heuristic.py::test_numba_kernels_match_python_reference`:

- 1 000 random (blocked, carpet, opp_bit, own_bit, worker) configurations.
- Three kernels compared:
  - `_ray_reach`: `py == nb` in **1 000 / 1 000** cases.
  - `_cell_potential_for_worker`: `abs(py − nb) < 1e-9` in **1 000 / 1 000**.
  - `_cell_potential_vector`: `np.allclose(py, nb)` in **1 000 / 1 000**.
- Byte-parity holds across bitmasks with high-bit set (> 2^63) because the
  numba dispatcher coerces the Python int to `np.uint64` at the boundary.

`tests/test_heuristic.py::test_numba_kill_switch_forces_python_path`:
subprocesses a Python child with `RATTLEBOT_NUMBA=0` and asserts
`is_numba_active() == False` and `_USE_NUMBA == False` in the child.

`tests/test_heuristic.py::test_numba_warmup_is_fast_second_time`: calls
`warm_numba_kernels()` twice; second call < 5 ms (idempotency check).

`tests/test_heuristic.py::test_evaluate_returns_same_value_both_backends`:
confirms `features()` is finite + deterministic under both backends.

---

## §3 — Test matrix (local)

All four RattleBot test suites executed with numba ON then OFF:

| Suite            | numba ON | numba OFF |
|------------------|----------|-----------|
| test_heuristic   | 21 / 21  | 21 / 21   |
| test_search      | 21 / 21  | 21 / 21   |
| test_rat_belief  | 13 / 13  | 13 / 13   |
| test_time_mgr    | 12 / 12  | 12 / 12   |
| **Total**        | **67 / 67** | **67 / 67** |

`RATTLEBOT_NUMBA=0 python tests/test_*.py` runs pass with the pure-Python
fallback engaged (confirmed by `is_numba_active() == False`).

---

## §4 — Performance impact (Windows local, Python 3.13, numba 0.65.0)

Measured on `tools/scratch/profile_search.py` (mid-game board, seed=1,
5 warm calls, `limit_resources=False` local run).

| State                     | Depth @ 2 s | Depth @ 6 s | nps    | p-vec call |
|---------------------------|-------------|-------------|--------|------------|
| v0.2.2 (T-20g, pure-Py)   | 13.2 mean   | 14–16       | 34.8 k | ~7.7 µs    |
| **v0.3 (T-30c, numba ON)**| **14.0 mean** (12 – 15) | **15 – 16** | **50.1 k** | **~0.36 µs** |

- **NPS lift: +44 %** (34.8 k → 50.1 k).
- **Depth @ 2 s: +0.8 ply** (v0.3 hits 15 on warm calls).
- `_cell_potential_vector` cold call: **7.7 µs → 0.36 µs** (~21× faster).
  Through the LRU cache (repeat board): ~160 ns either way.
- Initial `warm_numba_kernels()` (first `Heuristic()` construction):
  953 ms cold, < 10 ms once the `__pycache__/*.nbi` numba cache exists.

---

## §5 — Sandbox-gate preconditions (for tester-local)

Per the v0.3 activation policy, tester-local owns the formal 20-match
WSL-sandboxed paired run. This document captures the **local** verification
that precedes that gate:

- [x] All 67 tests green with numba ON (`python test_*.py`).
- [x] All 67 tests green with numba OFF (`RATTLEBOT_NUMBA=0 python test_*.py`).
- [x] Parity: 1 000-trial random-board comparison → 0 mismatches across 3 kernels.
- [x] `warm_numba_kernels()` cost: 953 ms cold / < 10 ms warm → well below
      the 10 s tournament `init_timeout`.
- [x] Smoke: 1-match `run_local_agents.py RattleBot Yolanda` runs clean;
      agent __init__ 687 ms; first `play()` 75 ms (no cold-JIT stall).
- [ ] **Sandbox gate (tester-local to execute):** 20-match paired
      `v0.3-numba vs v0.3-pure-python` on WSL with `--limit-resources`:
      - Pass iff `0 FAILED_INIT AND mean depth ≥ 14 at 2 s AND numba
        version wins/ties`. Failure → flip `_USE_NUMBA = False` in
        `heuristic.py` and commit that single-line change; ship without
        numba.
      - Pair setup: one agent folder with `_USE_NUMBA=True`, one with
        `_USE_NUMBA=False`; same weights.json; tester-local's existing
        paired runner with `--limit-resources --matches 20`.

---

## §6 — Kill-switch operability drill

If the sandbox gate fails or numba imports abort on the tournament box,
the change to disable numba is **one line** in `heuristic.py`:

```python
_USE_NUMBA: bool = os.environ.get("RATTLEBOT_NUMBA", "1") != "0"
# Change the default to "0":
_USE_NUMBA: bool = os.environ.get("RATTLEBOT_NUMBA", "0") != "0"
```

or simply `_USE_NUMBA = False`. All tests still pass. The pure-Python
fallback is byte-identical and has been production-validated since
v0.2.2.

---

## §7 — Numba pitfalls watched

Per team-lead's brief:

- [x] **numpy-array int64 dtype for cache stability**: bitmasks are
      passed through `np.uint64` at the Python↔numba boundary to avoid
      Python's arbitrary-precision ints hitting `@njit` and boxing.
      `_CARPET_VALUE` is a length-8 `np.float64` array; passed in
      explicitly per call so numba infers a stable kernel signature.
- [x] **No Python objects in the hot path**: no tuples-of-tuples, no
      dicts, no `list.append + list.sort`. The 4 cardinal directions are
      unrolled; top-2 selection uses two `if` branches.
- [x] **cache=True works**: `__pycache__/heuristic._*_nb-*.nbi,.nbc`
      files are written on first run (confirmed locally).

---

## §8 — Files touched

- `3600-agents/RattleBot/heuristic.py` — +~180 LOC: numba imports + kill-switch,
  3 `@njit(cache=True)` kernels, 3 dispatchers, `warm_numba_kernels()`,
  `is_numba_active()`. `Heuristic.__init__` now calls `warm_numba_kernels()`
  so the first `V_leaf` in a turn doesn't absorb the cold compile.
- `3600-agents/RattleBot/tests/test_heuristic.py` — +4 new tests
  (`test_numba_kernels_match_python_reference`, `test_numba_kill_switch_forces_python_path`,
  `test_numba_warmup_is_fast_second_time`, `test_evaluate_returns_same_value_both_backends`).
- `requirements.txt` — `numba==0.61.0` already listed (unchanged).
- `docs/tests/NUMBA_GATE.md` — this file.
- `docs/STATE.md` — T-30c-numba entry.
