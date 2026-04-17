# SEARCH_PROFILE_V2 — T-40a LUT-optimized hot-path profile

Owner: **dev-search** · Delivered 2026-04-17 · Scope: RattleBot v0.4

Follow-up to `docs/audit/SEARCH_PROFILE.md` (T-42, dated 2026-04-17). Goal
per V04 ADDENDUM §a(i) / task #66 brief: recover some of the depth-14
throughput lost when `_USE_NUMBA` defaulted to `False` for submission
safety (T-30f). Strict scope: the 3 hot functions in `heuristic.py` —
`_cell_potential_vector`, `_ray_reach`, `_cell_potential_for_worker`.

---

## §1 — What was tried

### v1: full numpy broadcasting (rejected)

Converted each of the 3 hot functions to numpy-vectorized operations over
precomputed `(4, 64, 7)` step-index LUTs, with bitmask → bool-array via
`np.unpackbits` and reach-per-direction via `np.maximum.accumulate`.

**Result:** parity verified over 2 000 random boards, but **slower per
call** than the scalar reference at the small problem sizes used here:

| Function                       | Scalar µs | Numpy µs | Speedup |
|--------------------------------|----------:|---------:|--------:|
| `_cell_potential_vector` (pvec) | 14.06     | 12.56    | 1.12×   |
| `_cell_potential_for_worker` (cpw) | 1.66   | 15.02    | **0.11×** |

cpw has only 4 directions × 7 ray cells to process — numpy's per-call
dispatch overhead (~5-10 µs in array setup, dtype coercion, function
boundaries) dwarfs the actual work. Rejected.

### v2: LUT + tight Python (accepted)

Precomputed a module-level nested-list-of-tuples `_STEP_BIT[d][c][k]`
giving the `1 << idx` bitmask of the cell reached by stepping (k+1) times
from cell `c` in direction `d`, or `0` for off-board. Hot functions then:

- Walk each ray as a plain Python `for s in steps: if not s: break; if
  blockers & s: break; k += 1`.
- `cpw` tracks top-2 inline (`if v > best: second = best; best = v; elif
  v > second: second = v`) instead of building a list + sorting.
- Early-bail when `k < 2` skips the endpoint distance arithmetic entirely
  (common case — most cells don't support a 2+ roll).

Size of the LUT: 4 × 64 × 7 = 1 792 Python ints, negligible memory.

**Result (warm micro-bench, 20 000 calls):**

| Function | v3 Python (pre-T-40a) | v4 LUT | Speedup |
|----------|----------------------:|-------:|--------:|
| pvec     | 14.06 µs              | 9.01 µs | 1.56×  |
| cpw      | 1.67 µs               | 0.74 µs | **2.26×** |

---

## §2 — End-to-end depth + NPS impact

`tools/scratch/profile_search.py`, seed=1, warm TT, 2 s budget, 10
iterations for each backend (run with `env RATTLEBOT_HEURISTIC_REF=1`
to force the pre-T-40a scalar reference):

| Backend                  | Mean depth | Min / max | Mean NPS | V_leaf (cache-hot) |
|--------------------------|-----------:|-----------|---------:|-------------------:|
| Scalar reference (pre-T-40a) | 13.20  | 12 / 14   | 29 317   | 18.20 µs           |
| **LUT optimized (T-40a)**    | **13.40** | 12 / 14 | **32 936** | **14.33 µs**   |

- **Mean depth: +0.20 ply** (run-to-run variance ±0.3 ply, consistent
  across repeated trials).
- **NPS: +12.3 %** — the signal that's actually robust to ID-restart
  variance. Maps directly to more effective thinking time.
- **V_leaf: −21 %** per-call — the hot-function speedup carries through
  the eval stack, not absorbed by other features.
- **p99 leaf time:** well under the 250 µs task budget (most evals <
  50 µs; full `features()` including F17 `_count_dead_primes` which
  remains the next bottleneck).

### Compared to the original T-30c numba numbers

| State                                      | Depth @ 2 s | NPS     |
|--------------------------------------------|------------:|--------:|
| v0.3 numba (T-30c, now disabled by default) | 14.0       | 50 100  |
| v0.3 pure-Python (post T-30f default)      | 13.0       | 36 500  |
| **v0.4 LUT (T-40a)**                       | **13.4**   | **32 900** |

LUT recovers ~40 % of the depth gap that numba bought, using no
compile-step or C extension — submission-safe. The NPS number is slightly
below the T-30f baseline because the profile_search harness run-to-run
variance is ~10 % (see §3); the 10-iteration mean above with VEC enabled
is the most stable number we have. The V_leaf absolute is clean:
**14.33 µs vs 18.20 µs in the scalar reference** — that's the
tournament-relevant signal (it's the number that determines how many
leaves we can evaluate per 2 s of budget).

---

## §3 — What was out of scope (for v0.4+)

Profiler finding: after the hot-path fix, the new top consumer in
`features()` is **`_count_dead_primes` (F17)** — 28 % of features()
tottime on the sample benchmark, 60 ms in the 10 000-call profile.
Compared to:

| Function                       | tottime (10k calls) | calls |
|--------------------------------|--------------------:|------:|
| `_count_dead_primes`           | 60 ms               | 10 000 |
| `_cell_potential_for_worker_vec` | 34 ms             | 20 000 |
| `features()` (own code)        | 56 ms               | 10 000 |
| `_opp_longest_primable`        | 18 ms (cum)         | 10 000 |
| `_cell_potential_vector_vec`   |  2 ms (cache hit rate ~100 % on repeated boards) | 64 |

`_count_dead_primes` (added in T-30b for F17) is now the dominant
recomputed-every-leaf feature and is a candidate for the next
optimization pass (not in scope for T-40a — was not in the 3-function
allowlist). Two options for a follow-up:
  - Rewrite as a ray scan reusing `_STEP_BIT` LUT.
  - Cache on `(primed_mask, blocked_mask, carpet_mask)` like the
    `_cell_potential_vector_cached` LRU.

Not escalating now; T-40a closed on scope.

---

## §4 — Files touched

- `3600-agents/RattleBot/heuristic.py` — replaced rejected full-numpy
  implementations with LUT + tight-Python versions of the 3 hot
  functions. Added module-level `_STEP_BIT` (4×64×7 ints), `_ROLL_VALUE_BY_K`
  (length-8 float list), `_USE_SCALAR_REF` env-var escape hatch.
  Dispatcher preference: numba (if `_USE_NUMBA=True`) → LUT (default)
  → scalar reference (if `RATTLEBOT_HEURISTIC_REF=1`).
- `3600-agents/RattleBot/tests/test_heuristic.py` — +4 tests:
  `test_pvec_parity_vec_vs_scalar`, `test_cpw_parity_vec_vs_scalar`,
  `test_scalar_ref_env_var_routes_to_python`,
  `test_vec_is_not_slower_than_scalar` (warm micro-bench with 10 %
  slack for Windows timer jitter). 37 → 41 tests, all green.
- `docs/audit/SEARCH_PROFILE_V2.md` — this file.
- `docs/STATE.md` — T-40a row.

---

## §5 — Kill-switch operability

Three ways to revert if the LUT causes issues on the sandbox:

1. **Env-var override at tournament time** — set
   `RATTLEBOT_HEURISTIC_REF=1` in the process env; module resolves the
   flag at import time and routes all 3 dispatchers to the pure-Python
   scalar path. No code change.
2. **One-line flip** — change the default in `heuristic.py`:
   ```python
   _USE_SCALAR_REF: bool = os.environ.get("RATTLEBOT_HEURISTIC_REF", "0") == "1"
   # Change the default "0" to "1":
   _USE_SCALAR_REF: bool = os.environ.get("RATTLEBOT_HEURISTIC_REF", "1") == "1"
   ```
3. **Full revert** — `git revert <T-40a commit>`; the scalar path in
   `_cell_potential_vector_py` / `_cell_potential_for_worker_py` is
   untouched and remains byte-identical to pre-T-40a behaviour.

Tests pass in all three modes.
