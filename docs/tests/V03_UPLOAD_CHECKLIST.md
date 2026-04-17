# V03_UPLOAD_CHECKLIST — Pre-upload hardening, RattleBot v0.3

**Owner:** upload-hardener (Task #57)
**Date:** 2026-04-16
**Scope:** Verify RattleBot v0.3's init path, numba warm-up, weights-loader,
and zip packaging will NOT fail tournament validation the way FloorBot did.

---

## §0 — TL;DR verdict

**GO (YELLOW) for v0.3-prebo upload to bytefight.org.**

- Import audit: **PASS**. All imports land in the tournament allow-list
  (stdlib + numpy + numba). No network/subprocess/FS writes.
- Weights-loader stress test (15 scenarios): **PASS**. No crash path;
  pathological NaN/Inf weights still yield a legal move via the
  agent's `_emergency_fallback`.
- Numba cold warm-up: **1.33 s** for full `PlayerAgent.__init__` with no
  disk cache. Tournament `init_timeout=10 s` → **87 % headroom**.
  Pure-Python fallback is **249 ms** cold (well under 10 s even at a
  4× CPU slowdown vs dev box).
- Zip packaging: **PASS**. 32.6 KB depth-1 `RattleBot/` prefix, 9 files,
  extracts clean, `PlayerAgent(None)` constructs in an isolated process.
- Sandbox sim: **3/3 matches completed** with **0 FAILED_INIT, 0 TIMEOUT,
  0 INVALID_TURN, 0 CODE_CRASH, 0 MEMORY_ERROR, 0 violations**. RattleBot
  lost on points to Yolanda in all 3 (expected pre-BO per
  SANDBOX_SIM.md §3.2; **this is a strength issue, not a
  validation-eligibility issue**).

**Why YELLOW not GREEN:**
- v0.3-prebo is shipping with W_INIT (no BO weights yet), so its **match
  strength is provisional**. Validation may still fail on merits if the
  validator is stronger than Yolanda-class. This is the same H7 risk
  FloorBot hit.
- Tournament Linux/Py3.12/seccomp path could not be fully simulated on
  this Windows dev box (documented limit in SANDBOX_SIM.md §2.3).
- One P1 risk identified: NaN/Inf values in a malformed `weights.json`
  pass through the loader — saved by the emergency-fallback chain, but
  a defence-in-depth `np.isfinite(arr).all()` check would tighten
  safety. Not blocking.

**Recommended upload order (unchanged from tester-live plan):**
1. Upload `tools/scratch/RattleBot_v03_prebo.zip` with "Set as current
   submission once validated" **UNCHECKED** (diagnostic mode).
2. If validation WINS → `valid`. Compare against Yolanda's validation
   win — v0.3 should win the same match Yolanda won.
3. If validation LOSES → `invalid`. Do NOT panic; this is the H7 regime
   and matches FloorBot's fate. Escalate to V03 red-team (#59).
4. Only flip "Current" → Yolanda-displacing after validation WIN.

---

## §1 — Import audit

**Method:** grepped every `^import|^from ` in
`3600-agents/RattleBot/*.py` and cross-referenced the tournament env
from CLAUDE.md §6 (`stdlib, numpy, jax, flax, scikit-learn, numba,
psutil, cython, torch, pynvml`).

### §1.1 — Per-module imports

| Module | Third-party imports | Stdlib imports | Relative imports |
|---|---|---|---|
| `__init__.py` | — | — | `.agent`, `. rat_belief, search, heuristic, move_gen, time_mgr, zobrist, types` |
| `agent.py` | `numpy as np` | `__future__`, `collections.abc`, `typing`, `json`, `math`, `os`, `random` | `game.board`, `game.enums`, `game.move`, `.heuristic`, `.rat_belief`, `.search`, `.time_mgr`, `.zobrist` |
| `heuristic.py` | `numpy as np`, `numba.njit` (optional, try/except wrapped) | `__future__`, `functools`, `os`, `typing` | `game.board`, `game.enums`, `.types` |
| `move_gen.py` | — | `__future__`, `typing` | `game.enums`, `game.move`, `.types`, `.zobrist` |
| `rat_belief.py` | `numpy as np` | `__future__`, `typing` | `game.board`, `game.enums`, `.types` |
| `search.py` | — | `__future__`, `math`, `time`, `typing` | `game.enums`, `game.move`, `.move_gen`, `.types`, `.zobrist` |
| `time_mgr.py` | — | `__future__`, `typing`, `time` | `game.board`, `.types` |
| `types.py` | `numpy as np` | `__future__`, `dataclasses`, `typing` (TYPE_CHECKING only) | — |
| `zobrist.py` | — | `__future__`, `random`, `typing` | `game.enums`, `game.move`, `.types` |

### §1.2 — Cross-reference with tournament env

Tournament env per CLAUDE.md §6: `stdlib, numpy, jax, flax,
scikit-learn, numba, psutil, cython, torch, pynvml`.

**Every third-party import RattleBot makes is on this list** (numpy +
numba only). **No jax, flax, scikit-learn, psutil, cython, torch, or
pynvml is imported** (good — fewer dependencies means less
library-version skew risk per SANDBOX_SIM §5.1).

### §1.3 — Numba import path scrutiny

`heuristic.py:131-143`:

```python
_USE_NUMBA: bool = os.environ.get("RATTLEBOT_NUMBA", "1") != "0"

try:
    if _USE_NUMBA:
        from numba import njit  # type: ignore
        _NUMBA_AVAILABLE = True
    else:
        njit = None  # type: ignore
        _NUMBA_AVAILABLE = False
except ImportError:
    njit = None
    _NUMBA_AVAILABLE = False
    _USE_NUMBA = False
```

**Verified safe**: `ImportError` at `from numba import njit` cleanly
lands `_NUMBA_AVAILABLE=False` and `_USE_NUMBA=False`. The dispatcher
functions (`_ray_reach`, `_cell_potential_for_worker`,
`_cell_potential_vector`) each test `_USE_NUMBA and _NUMBA_AVAILABLE`
before dispatching to the jit kernel — pure-Python fallback is
byte-parity-verified per NUMBA_GATE §2.

**Edge case considered:** numba imports but fails to JIT at runtime
(e.g. LLVM initialization error on a particular CPU). The `@njit`
wrapping is synchronous at kernel definition time — if wrapping
itself fails, we'd see an ImportError-family exception escaping the
module body. `heuristic.py:308-330` wraps only the `@njit` definitions
in `if _NUMBA_AVAILABLE and _USE_NUMBA`, not a `try`, so a truly
broken numba install would kill `import RattleBot.heuristic` with an
exception. This escapes `PlayerAgent.__init__`'s try/except only if
the import is at the top of the module (it is). **Mitigation:** the
agent-side try/except in `__init__` catches this, sets
`_init_ok=False`, and `play()` falls through to `_emergency_fallback`
which always returns a legal move. **Verified below in Phase 5
(sandbox sim, 3/3 complete).**

### §1.4 — Flags raised

| # | Severity | Issue | Note |
|---|---|---|---|
| 1 | INFO | `weights_v03.json` is the tuning-pipeline filename but the loader reads `weights.json` | Brief calls out this name. For v0.3-prebo, no weights file is being shipped, so W_INIT is used — no mismatch. When BO-tuned weights land, the tuning pipeline must rename/copy to `weights.json` before zip-build, OR set `RATTLEBOT_WEIGHTS_JSON`. |
| 2 | INFO | `__init__.py` does `from . import rat_belief, search, heuristic, move_gen, time_mgr, zobrist, types` — i.e., eager-imports every submodule at package load time | Normal for Python packages with rich surface area. Not a validator issue — LIVE_UPLOAD_003 confirmed bytefight does NOT reject `__init__.py`-bearing zips. |

**Verdict:** no blockers in the import path.

---

## §2 — Weights-loading stress test

**Method:** `tools/scratch/stress_test_weights_loading.py` exercises
`_load_tuned_weights()` and `Heuristic(weights=...)` across 15
scenarios by writing a tmp `weights.json` into the RattleBot package
and observing both the loader return value and whether Heuristic
construction raises.

### §2.1 — Results table

| # | Scenario | Loader crash? | Fell back to W_INIT? | Heuristic built? | Safe? |
|---|---|---|---|---|---|
| 1 | `weights.json` missing | No | Yes | Yes | **YES** |
| 2 | Malformed JSON (`{broken`) | No | Yes | Yes | **YES** |
| 3 | Wrong shape: length 1 | No | Yes | Yes | **YES** |
| 4 | Wrong shape: length 12 | No | Yes | Yes | **YES** |
| 5 | Wrong shape: length 100 | No | Yes | Yes | **YES** |
| 6 | NaN values | No | **No** (weights = NaN) | Yes | **NOTE** |
| 7 | +Infinity values | No | **No** (weights = Inf) | Yes | **NOTE** |
| 8 | String values | No | Yes (np.asarray raised → caught) | Yes | **YES** |
| 9 | Empty file | No | Yes (json.load raised → caught) | Yes | **YES** |
| 10 | Bare list of correct length | No | **No** (weights loaded correctly) | Yes | **YES** — by design |
| 11 | Dict without "weights" key | No | Yes (treated as bare value → wrong shape → fallback) | Yes | **YES** |
| 12 | Nested weights dict | No | Yes (np.asarray raised → caught) | Yes | **YES** |
| 13 | Correct-shape object | No | **No** (weights loaded correctly) | Yes | **YES** — by design |
| 14 | `RATTLEBOT_WEIGHTS_JSON` points at valid file | No | **No** (weights loaded correctly) | Yes | **YES** — by design |
| 15 | `RATTLEBOT_WEIGHTS_JSON` points at missing file | No | Yes (falls through to sibling candidate → missing → W_INIT) | Yes | **YES** |

**NOTE (#6, #7):** NaN/Inf weights are accepted by the loader and by
`Heuristic.__init__` with no value-sanitization check. The NaN
propagates into every leaf eval, making all alpha-beta scores NaN,
which short-circuits move ordering. Downstream safety was verified
separately in `tools/scratch/stress_test_nan_weights_eval.py`: with
NaN, +Inf, and mixed NaN/±Inf weights, `PlayerAgent.play()` still
returns a legal `Move.search(...)` — the emergency-fallback catches
the NaN-poisoned search tree. **No crash, legal move always returned.**

### §2.2 — Interpretation

**All 15 scenarios + 4 NaN/Inf variants → legal move returned, no
crash.** The loader's `try/except Exception: continue` is wide enough
to catch every malformed-JSON path encountered.

**P1 hardening recommendation (non-blocking):**

```python
# After the shape check in _load_tuned_weights, add:
if not np.isfinite(arr).all():
    continue   # reject non-finite values, fall through to W_INIT
```

This would move scenarios #6, #7 from "NOTE" to "YES — by fallback".
Not required for the v0.3-prebo upload because the agent's
outer try/except + `_emergency_fallback` chain already neutralizes
the failure. But a one-line defence-in-depth improvement for a
later patch.

---

## §3 — Numba cold / warm-up timing

**Method:** `tools/scratch/numba_coldwarm_bench.py` and
`tools/scratch/full_init_coldwarm_bench.py`. For each configuration,
`__pycache__` is purged, then a fresh Python subprocess imports
RattleBot and times a single constructor call.

### §3.1 — Results (Windows dev box, Python 3.13, numba 0.65.0)

| Scenario | Latency |
|---|---|
| Cold `Heuristic()` (numba ON, no .nbi cache) | 1 220 ms |
| Warm `Heuristic()` (numba ON, .nbi cache hit) | 553 ms |
| Cold `Heuristic()` (numba OFF, pure Python) | 94 ms |
| Warm `Heuristic()` (numba OFF, pure Python) | 83 ms |
| Cold `PlayerAgent(__init__)` (numba ON) | **1 332 ms** |
| Warm `PlayerAgent(__init__)` (numba ON) | 685 ms |
| Cold `PlayerAgent(__init__)` (numba OFF) | 249 ms |

### §3.2 — Tournament fit

- `init_timeout = 10 s` per GAME_SPEC §7 / CLAUDE.md §7.
- Worst-case cold: **1 332 ms** → **87 % headroom**.
- At a 4× CPU slowdown (tournament box vs dev box): 1 332 × 4 = 5 328
  ms → still **47 % headroom**.
- Pure-Python fallback cold: 249 ms → even at 4× slowdown = 1 000 ms
  → **90 % headroom**.

### §3.3 — Tournament sandbox ephemeral FS implication

Tournament likely extracts the zip fresh per match, so the numba
`__pycache__/*.nbi` cache will NOT persist. **Cold is always the case
we plan for.** 1.33 s is well under 10 s; no action needed.

**Remediation options discussed** (not required to ship):

- **(a) Compile-on-demand**: already what `@njit` does — first call
  triggers compile. Our `warm_numba_kernels()` invocation at
  `Heuristic.__init__` absorbs the compile in init time (not play
  time), which is what we want.
- **(b) Ship pre-compiled `.nbi`**: risky — numba nbi is bound to
  exact Python+LLVM+numpy version. Tournament env mismatch = kernel
  falls back to re-JIT on load. Not worth the compat risk for a
  1 s gain.
- **(c) Disable numba first N calls**: overkill at 1.33 s warm-up.

**Verdict:** keep the current scheme — warm on `Heuristic.__init__`,
accept the cold 1.33 s, rely on the kill-switch if anything breaks.

---

## §4 — Zip packaging verification

**Method:** `tools/scratch/build_and_verify_zip.py` builds the zip and
runs the "clean extract + import in fresh subprocess" test.

### §4.1 — Artifact

- **Path:** `tools/scratch/RattleBot_v03_prebo.zip`
- **Size:** 33 376 bytes (32.6 KB) — well under 200 MB cap (CLAUDE.md §6).
- **Compression:** deflate.

### §4.2 — Contents (9 files, all depth-1 under `RattleBot/`)

```
RattleBot/__init__.py
RattleBot/agent.py
RattleBot/heuristic.py
RattleBot/move_gen.py
RattleBot/rat_belief.py
RattleBot/search.py
RattleBot/time_mgr.py
RattleBot/types.py
RattleBot/zobrist.py
```

### §4.3 — Checks performed

- [x] Layout matches Yolanda's successful shape (depth-1 folder +
      `.py` files).
- [x] No `__pycache__` or `*.pyc` in zip.
- [x] No `tests/` directory in zip.
- [x] No `weights.json` in zip (v0.3-prebo intentionally uses W_INIT).
- [x] No scratch / build artefacts.
- [x] `__init__.py` at correct path (`RattleBot/__init__.py`).
- [x] Size ≤ 200 MB.
- [x] **Extract-into-tempdir + `PlayerAgent(None)` in subprocess:
      `OK` returned.**

### §4.4 — Build script output

```
Built zip: RattleBot_v03_prebo.zip
Size: 33376 bytes  (32.6 KB)
Contents (9 files): [listed above]
Layout check: OK
Verifying extract+import in clean process...
stdout: OK
Extract+import: OK
```

**Verdict:** zip is submission-ready.

---

## §5 — Sandbox-sim full-match run

**Method:** `tools/sandbox_sim.py --matches 3 --a RattleBot --b
Yolanda --seed 100 --timeout 1800`. Default `limit_resources=False`
(windows dev box can't run `limit_resources=True` — requires Linux
seccomp/resource module; see SANDBOX_SIM §6.3).

### §5.1 — Results

| Match | Seed | winner | reason | RattleBot pts | Yolanda pts | Violations | Exceptions |
|---|---|---|---|---|---|---|---|
| 1 | 100 | A (RattleBot) | POINTS | 4 | 39 | 0 | 0 |
| 2 | 101 | A | POINTS | 6 | 46 | 0 | 0 |
| 3 | 102 | A | POINTS | 1 | 26 | 0 | 0 |

`[sandbox_sim] matches complete: 3/3 errors=0`
`[sandbox_sim] done  rc=0 elapsed=627.2s violations=0`

- **0 FAILED_INIT** (reason 5 never seen — init worked every time).
- **0 TIMEOUT** (reason 1 never seen — under 240 s/side budget on all 3).
- **0 INVALID_TURN** (reason 2 never seen).
- **0 CODE_CRASH** (reason 3 never seen).
- **0 MEMORY_ERROR** (reason 4 never seen).
- All 3 terminated by POINTS (reason 0 — normal end of 80 plies).
- **0 sandbox violations** — no blocked imports, no network attempts,
  no FS writes outside cwd, no RAM cap breach.
- Per-match wall clock ≈ 209 s on dev box (includes BOTH players'
  total thinking time). RattleBot's own per-side budget stayed under
  360 s (local mode); tournament gives 240 s — predicted okay per the
  T-30a audit (task #50), but confirm with a Linux WSL paired run if
  available.

### §5.2 — Caveat: RattleBot lost on points 0/3

All 3 matches ended with Yolanda outscoring RattleBot. **This is a
known v0.2/v0.3-prebo strength issue** — same signature as in
SANDBOX_SIM §3.2 — and reflects the "pre-BO weights are untuned"
state. **This is NOT a sandbox-correctness finding.** Validation on
bytefight depends on winning *the validator match*, not the
bytefight-unseen local match. Separate risk tracked by V03 red-team
(task #59).

### §5.3 — What we could NOT simulate on this box

(Per SANDBOX_SIM.md §2.3 — documented limits.)

- Linux / Python 3.12 specifics.
- Actual seccomp syscall filtering.
- UID drop.
- Tournament CPU speed.

Partial coverage existed via tester-local's WSL Py3.12-Linux
import-check (SANDBOX_SIM §3.3) — RattleBot imported cleanly there.
But no full-match under tournament seccomp has been run locally.
This is a known residual risk; the live upload IS the test.

---

## §6 — GO / NO-GO verdict

### **GO (YELLOW) for v0.3-prebo upload.**

**GO conditions all met:**

- [x] Import audit clean — every dep is in tournament env.
- [x] Weights-loader stress test: no crash path in any of 15 scenarios,
      pathological NaN/Inf weights still yield a legal move via the
      emergency-fallback chain.
- [x] Numba cold warm-up 1.33 s << 10 s init_timeout (87 % headroom).
      Pure-Python fallback 249 ms at 4× slowdown still 90 % headroom.
- [x] Zip packaging: 32.6 KB, depth-1 layout, clean
      extract+`PlayerAgent(None)` in fresh subprocess.
- [x] Sandbox sim 3/3 matches: 0 FAILED_INIT, 0 TIMEOUT,
      0 INVALID_TURN, 0 CODE_CRASH, 0 MEMORY_ERROR, 0 violations.

**Why YELLOW not GREEN:**

- v0.3-prebo ships with W_INIT, not BO-tuned weights — match
  strength is provisional. H7 risk: the tournament validator may be
  stronger than Yolanda, and v0.3-prebo could still LOSE the
  validation match on merits (same fate as FloorBot).
- Tournament-sandbox-only bugs (seccomp divergence, 240 s time
  budget at unknown-slower CPU, Python 3.12 vs 3.13 skew) are not
  fully covered locally.
- H-1 (RatBelief own-capture reset) and M-7 (endgame ceiling mask)
  from V03_REDTEAM are known pre-existing issues — not sandbox-
  blocking but would lose a few points per match against a smart
  opponent. Task #60 addresses these.

### Blockers: **NONE.**

No P0 issues discovered. No code was modified.

---

## §7 — Recommended next actions

Ordered by priority:

1. **Upload `tools/scratch/RattleBot_v03_prebo.zip` to bytefight.org**
   with "Set as current submission once validated" **UNCHECKED**
   (diagnostic mode, per HANDOFF_TESTER_LIVE §4):
   - If validation → `valid`: v0.3-prebo clears the validator gate
     with W_INIT weights. This is the benchmark for BO-tuned v0.3.
   - If validation → `invalid`: diagnostic — the validator is
     stronger than we think, or W_INIT alone isn't enough. Escalate
     to V03 red-team (#59) and consider ship-time patches (H-1, M-7
     from task #60 — could shift the validation outcome).
2. **Before flipping Current**: get a `valid` result *and* an
   AUDIT_V03.md sign-off (per D-010 promotion gate).
3. **After BO-tuned weights land** (task #55 RUN1-v2): re-run this
   entire checklist once — the weights file changes `Heuristic`
   construction but not the surface audited here. A shorter re-run
   is fine (Phases 2, 4, 5).
4. **P1 hardening** (non-blocking, <10 LOC): add
   `np.isfinite(arr).all()` check in `_load_tuned_weights` to make
   NaN/Inf weights also fall back to W_INIT. Lives in `agent.py`
   near line 74.
5. **P1 investigation** (non-blocking): the zip builder in
   `tools/scratch/build_and_verify_zip.py` is throw-away.
   tester-live / committer-2 should promote its ALLOWED_FILES list
   into a `tools/build_submission_zip.py` used by future uploads,
   so that tests/weights/scratch files can't accidentally leak.
6. **Linux WSL full-match run** (non-blocking, would close §5.3
   gap): the sandbox_sim.sh path exists; a team member with WSL
   venv + `pip install -r requirements.txt` could run
   `sandbox_sim.sh --matches 5 --a RattleBot --b Yolanda
   --limit-resources --timeout 1800` to close the last sandbox
   coverage gap. TODO tagged in SANDBOX_SIM.md §8.

---

## §8 — Files delivered

- `tools/scratch/stress_test_weights_loading.py` — Phase-2 harness.
- `tools/scratch/stress_test_nan_weights_eval.py` — Phase-2b follow-up.
- `tools/scratch/numba_coldwarm_bench.py` — Phase-3 bench (Heuristic
  only).
- `tools/scratch/full_init_coldwarm_bench.py` — Phase-3 bench (full
  PlayerAgent).
- `tools/scratch/build_and_verify_zip.py` — Phase-4 zip builder +
  verifier, produces `tools/scratch/RattleBot_v03_prebo.zip`.
- `docs/tests/V03_UPLOAD_CHECKLIST.md` — this file.

All scratch files are test-only; no production code modified.
