# DEPENDENCY_SURFACE_AUDIT — Tournament Import Safety

**Auditor:** auditor (post-compact brief)
**Date:** 2026-04-17
**Scope:** Every import in `3600-agents/RattleBot/*.py` cross-referenced against `requirements.txt` and tournament env (CLAUDE.md §6: x86_64 Linux, Python 3.12, libs in requirements.txt, no network, no FS writes outside cwd).
**Method:** Static grep + cross-reference + sandbox_sim claim review. READ-ONLY on all RattleBot source (BO RUN1-v6 live, PID 8868 in `bo_pid.txt`).

---

## §1 — Imports per file (RattleBot package, tests excluded)

| File | Stdlib | 3rd-party | Engine (`game.*`) | Package-internal (`.*`) |
|---|---|---|---|---|
| `__init__.py` | — | — | — | `.agent`, `.rat_belief`, `.search`, `.heuristic`, `.move_gen`, `.time_mgr`, `.zobrist`, `.types` |
| `agent.py` | `__future__`, `collections.abc.Callable`, `typing.{Optional,Tuple}`, `json`, `math`, `os`, `random` | `numpy as np` | `game.board as board_mod`, `game.enums.{BOARD_SIZE, CARPET_POINTS_TABLE, MoveType}`, `game.move.Move` | `.heuristic.{Heuristic, N_FEATURES, W_INIT}`, `.rat_belief.RatBelief`, `.search.Search`, `.time_mgr.TimeManager`, `.zobrist.Zobrist` |
| `heuristic.py` | `__future__`, `functools`, `os`, `typing.Optional` | `numpy as np`, **`numba.njit` (conditional, see §2.2)** | `game.board as board_mod`, `game.enums.{BOARD_SIZE, CARPET_POINTS_TABLE}` | `.types.BeliefSummary` |
| `move_gen.py` | `__future__`, `typing.{Dict,Iterable,List,Optional,Tuple}` | — | `game.enums.{CARPET_POINTS_TABLE, MoveType}`, `game.move.Move` | `.types.MoveKey`, `.zobrist.move_key` |
| `rat_belief.py` | `__future__`, `typing.Tuple` | `numpy as np` | `game.board as board_mod`, `game.enums.{Cell, Noise, BOARD_SIZE}` | `.types.BeliefSummary` |
| `search.py` | `__future__`, `math`, `time as _time`, `typing.{Callable,Dict,List,Optional,Tuple}` | — | `game.enums.MoveType`, `game.move.Move` | `.move_gen.ordered_moves`, `.types.{BeliefSummary, MoveKey, TTEntry, TT_FLAG_EXACT/LOWER/UPPER}`, `.zobrist.{Zobrist, move_key}` |
| `time_mgr.py` | `__future__`, `math as _math`, `typing.{Callable,List,Optional}`, `time as _time` | — | `game.board as board_mod` | `.types.BeliefSummary` |
| `types.py` | `__future__`, `dataclasses.dataclass`, `typing.{Optional,Tuple,TYPE_CHECKING}` | `numpy as np` | `game.enums.{MoveType, Direction}` (TYPE_CHECKING-only) | — |
| `zobrist.py` | `__future__`, `random`, `typing.Optional` | — | `game.enums.{Cell, MoveType, BOARD_SIZE}`, `game.move.Move` | `.types.MoveKey` |

**Total distinct non-stdlib, non-engine, non-internal imports: 2** — `numpy` and (optional) `numba`.

---

## §2 — Stdlib vs 3rd-party classification

### §2.1 Stdlib imports (all guaranteed on any Python 3.12)

`__future__`, `collections.abc`, `dataclasses`, `functools`, `json`, `math`, `os`, `random`, `time`, `typing`.

**Verdict:** all load on Python 3.12 with no extra installs. No risk.

### §2.2 Third-party imports

| Module | Where imported | Requirements.txt? | Tournament env guaranteed? | Load path |
|---|---|---|---|---|
| `numpy` | `agent.py:32`, `heuristic.py:160`, `rat_belief.py:31`, `types.py:19` | ✅ pinned `numpy==2.1.3` | ✅ yes | Unconditional top-level import |
| `numba.njit` | `heuristic.py:212` | ✅ pinned `numba==0.61.0` | ✅ yes | **Conditional** — gated behind `if _USE_NUMBA:` where `_USE_NUMBA = os.environ.get("RATTLEBOT_NUMBA", "0") == "1"`. Default OFF → `njit` never imported. Even if `RATTLEBOT_NUMBA=1` and numba is missing, the `try/except ImportError` at `heuristic.py:211-220` catches and falls back to `njit = None, _NUMBA_AVAILABLE = False, _USE_NUMBA = False`. **Pure-Python path is always the shipping default.** |

**Verdict:** every third-party import is in `requirements.txt`. The numba path is double-guarded (env-var default OFF + try/except ImportError) per T-30f.

### §2.3 Engine imports (`game.*`)

Every engine import (`game.board`, `game.enums`, `game.move`) is satisfied by the tournament-side engine which is co-located with the agent package at runtime (SPEC §4.1 — engine passes `Board` instance into `play()`). These are NOT packaged into the submission zip — the tournament runs the engine from its own copy.

**Verdict:** safe. Engine surface is stable (GAME_SPEC §11 constants table, no recent breaking changes).

### §2.4 Package-internal imports

All relative (`from .xxx import ...`) — resolved within the `RattleBot/` directory shipped in the zip. Depth-1 layout matches Yolanda's successful shape (V03_UPLOAD_CHECKLIST §4). `__init__.py` eagerly imports every submodule which would surface any circular/missing-name error at import time (fail-fast).

**Verdict:** safe. `from RattleBot import PlayerAgent` resolves correctly.

---

## §3 — Requirements.txt cross-check

`requirements.txt` content (11 lines):

```
jax
scikit-learn
flax
numpy==2.1.3
numba==0.61.0
psutil==6.0.0
cython==3.0.11
torch==2.9.0
pynvml==13.0.1
# comment
scikit-optimize==0.10.2    # NOT required on submission machine
```

### §3.1 Imports RattleBot actually uses

Just two distinct third-party names: **`numpy`** (unconditional) + **`numba`** (conditional, default OFF).

### §3.2 Imports RattleBot does NOT use (listed in reqs but unneeded by agent)

`jax`, `scikit-learn`, `flax`, `psutil`, `cython`, `torch`, `pynvml`, `scikit-optimize`. None appear in the RattleBot package. Tournament provides these on the image, but we don't depend on them — fewer deps = lower version-skew risk (V03_UPLOAD_CHECKLIST §1.2).

### §3.3 Missing from reqs?

**Zero hits.** Every third-party name appearing in RattleBot source (`numpy`, `numba`) is present in `requirements.txt`. No hidden imports, no dynamic `importlib` calls in the agent package, no plugin loading, no `sys.path` manipulation at agent top-level.

### §3.4 Sandbox-sim cross-check

`tools/sandbox_sim.py:66-73` bans at import-time: `requests`, `httpx`, `aiohttp`, `websocket`, `websockets`, `paramiko`. **RattleBot imports zero of these** (grep-verified).

`tools/sandbox_sim.py:79-82` runtime-patches network functions on `socket` etc. — RattleBot never opens a socket (no network code anywhere in the package, grep-verified for `socket|urllib|requests|httpx|http\.client`).

**Sandbox-sim claims about tournament fidelity match actuals.** Zero risky imports, zero network I/O, FS writes only inside cwd (loader reads `weights.json` from the agent package directory; nothing writes).

---

## §4 — Risk verdict

**GREEN — ship the current bot.**

Rationale:
1. All third-party imports (2 distinct names) are in `requirements.txt` — `numpy` required, `numba` defensively guarded.
2. Numba is the only tournament-risky import, and it is (a) env-var-gated OFF by default (T-30f), (b) wrapped in `try/except ImportError` fallback, (c) never imported at module-load when `RATTLEBOT_NUMBA` is unset. LIVE_UPLOAD_006 confirmed pure-Python zip PASSES bytefight validation.
3. Zero network imports; zero `subprocess`; zero FS writes; zero cross-agent imports (no `FloorBot.*`, no `Yolanda.*`).
4. `__init__.py` cleanly exposes `PlayerAgent` for `from RattleBot import PlayerAgent`.
5. Sandbox simulator's declared bans match the agent's actual import profile.

No findings at severity H or M. Two L-severity observations documented in §5 for completeness.

---

## §5 — Recommendations / observations

### §5.1 (L) Numba requirement line could be made explicitly optional

**File:** `requirements.txt:5` pins `numba==0.61.0` as if required, but the agent ships with numba OFF by default. If the tournament environment dropped numba, our bot would still work (the `try/except ImportError` at `heuristic.py:218-220` handles it). Nothing to fix on our side — just an FYI that the runtime dependency is weaker than the file suggests.

### §5.2 (L) `from numba import njit` is gated on `_USE_NUMBA`, not `_NUMBA_AVAILABLE`

**File:** `heuristic.py:210-220`. The gate is `if _USE_NUMBA: from numba import njit` → if numba IS installed but `RATTLEBOT_NUMBA` is unset, the module never tries to import numba at all. This is correct behavior (saves cold-import time) but reviewers should note that `_NUMBA_AVAILABLE` only becomes `True` when BOTH the env-var opts in AND the import succeeds — not simply when numba is installed. No action needed; documenting for future auditors.

### §5.3 (INFO) No runtime install / pip / import-hook surface

Grep-verified: no `importlib`, `__import__`, `pkg_resources`, `pip`, `setuptools` calls anywhere in `3600-agents/RattleBot/*.py`. The import surface is fully static and introspectable, which is exactly what sandbox environments prefer.

---

## §6 — Command reference for re-running this audit

```bash
# List every import in the package
grep -rn "^\s*\(import \|from \)" 3600-agents/RattleBot/*.py

# Scan for risky imports
grep -rn "socket\|urllib\|requests\|httpx\|http\.client\|subprocess\|importlib" 3600-agents/RattleBot/*.py

# Scan for file writes / network attempts
grep -rn "\.write(\|open([^)]*[\"']w\|os\.system\|os\.spawn\|os\.exec" 3600-agents/RattleBot/*.py
```

All three should return zero hits inside the agent package (test files are excluded by convention — tests don't ship in the submission zip per `build_submission.py` and V03_UPLOAD_CHECKLIST §4).

---

## §7 — Final verdict line

**GREEN. Ship the current bot. No import-surface blockers. BO RUN1-v6 safe to continue; no code edits made.**

**Auditor sign-off:** 2026-04-17, post-compact audit pass.
