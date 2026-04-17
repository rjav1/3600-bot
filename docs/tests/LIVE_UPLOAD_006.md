# LIVE_UPLOAD_006 — pure-python v0.3 diagnostic (VALIDATION PASSED → numba is the culprit)

**Owner:** live-tester-2
**Date:** 2026-04-17
**Status:** **VALID.** `RattleBot_v03_pureonly_20260417_1022.zip` (identical to the LIVE_UPLOAD_005 failing zip except `_USE_NUMBA: bool = False`) PASSED tournament validation in 27 s. Paired with LIVE_UPLOAD_005's INVALID result on the same code with numba enabled, the disambiguation is decisive: **numba JIT is breaking in the tournament sandbox.** Ship v0.3 with `_USE_NUMBA=False`.

Yolanda remains the Current submission; pureonly NOT activated (per task instructions).

---

## 1. Artifact

| Field              | Value                                                                 |
|--------------------|-----------------------------------------------------------------------|
| Zip name           | `RattleBot_v03_pureonly_20260417_1022.zip`                            |
| Local path         | `C:\Users\rahil\AppData\Local\Temp\submissions\RattleBot_v03_pureonly_20260417_1022.zip` |
| Size               | 34 108 B                                                              |
| SHA256             | `f046631f86d987afd095840abc7ae0b467a79da0f291617f641e1488973924a8`    |
| Source             | On-disk state of `3600-agents/RattleBot/` at HEAD `b51c91d`, with ONE local edit |
| Patch applied      | `heuristic.py:131` — `_USE_NUMBA: bool = os.environ.get("RATTLEBOT_NUMBA", "1") != "0"` → `_USE_NUMBA: bool = False  # T-61 pureonly diagnostic — forced off` |
| Layout             | `RattleBot/*.py` at depth 1 (9 files, no `tests/`, no `__pycache__`)  |
| `weights.json`?    | Absent (BO still running — `_load_tuned_weights` returns None → W_INIT fallback) |
| `requirements.txt`? | Absent                                                               |

Byte-level identical to `RattleBot_v03_prebo_patched_20260417_0953.zip` (SHA256 `561bf897...`, the LIVE-005 failing zip) except one line in `heuristic.py`. Every other file hashes identically across the two zips: `agent.py 12152 B`, `move_gen.py 6065 B`, `rat_belief.py 9838 B`, `search.py 16436 B`, `time_mgr.py 6826 B`, `types.py 5151 B`, `zobrist.py 3738 B`, `__init__.py 432 B`. Only `heuristic.py` size differs (38642 → 38645 B, +3 bytes for the longer replacement string).

## 2. Upload + validation outcome

1. Extension reconnected; navigated to `/submissions`.
2. Clicked Submit Bot by **coordinate** (107, 205) — ref-click did not open the modal (same UI regression noted in LIVE-005 §5).
3. Modal opened; input empty.
4. User dropped the zip into the file picker manually (tool-size workaround from LIVE-005 §6).
5. Uploaded. Row appeared in Submissions table.
6. Validation match ran server-side. Team page shows:

```
Team 15  WON   RattleBot_v03_pureonly_20260417_1022.zip   validation   27s
```

Submissions table snapshot after validation:

```
Current  Validity  File                                                Date
         valid     RattleBot_v03_pureonly_20260417_1022.zip            4/17/2026, 10:24:00 AM
         invalid   RattleBot_v03_prebo_patched_20260417_0953.zip       4/17/2026, 10:18:10 AM
   ☑     valid     Yolanda_probe.zip                                   4/16/2026, 9:40:50 PM
         invalid   FloorBot.zip                                         4/16/2026, 9:27:32 PM
         invalid   FloorBot.zip                                         4/16/2026, 9:12:07 PM
```

Validity flipped from the "under evaluation" state to **valid**. Per H7: the bot WON its auto-validation match. The Match-History "WON" label for validations reflects "validator beaten", which just means "code ran cleanly to a winning endgame" — NOT a competitive win signal. It's the binary pass/fail gate.

Storage now 0.1 MB of 200 MB (was 0.0 — first meaningful byte count on this team's submission quota).

## 3. YES/NO disambiguation

| Zip                                                    | `_USE_NUMBA` | Validity | SHA256         |
|--------------------------------------------------------|--------------|----------|----------------|
| RattleBot_v03_prebo_patched_20260417_0953 (LIVE-005)   | True         | invalid  | 561bf897...    |
| RattleBot_v03_pureonly_20260417_1022 (LIVE-006)        | False        | valid    | f046631f...    |

All other code is byte-identical between the two zips. The only difference is one line in `heuristic.py` that decides whether the numba JIT path is taken. Pure-python is valid; numba is invalid.

**Conclusion: numba JIT is the tournament-sandbox failure.** Recommend shipping v0.3 with `_USE_NUMBA=False` as the default.

## 4. Hypothesis for WHY numba breaks in sandbox (informed guesses — cannot disambiguate from UI)

The Match-History row says "LOST" for the numba variant. Per H7 this is the binary "did not validate" signal — no replay, no WinReason surfaced. Likely causes, ranked:

1. **`@njit(cache=True)` tries to write a `__pycache__/*.nbi` cache file, seccomp blocks the filesystem write → ImportError or runtime exception.** The `limit_resources=True` path in `engine/player_process.py` applies a seccomp filter restricting filesystem calls (GAME_SPEC §7). First-call compile is fine RAM-wise, but if numba tries to persist the compiled code to disk it could fail. Workaround if we ever want numba back: `@njit(cache=False)`.
2. **Cold-compile time exceeds `init_timeout = 10 s` (with `limit_resources=True`) or burns a large chunk of the 240 s `play_time`.** Numba AOT for two non-trivial functions can take 5-15 s depending on the host CPU. If we compile lazily on first `play()`, the first turn alone consumes most of the budget → TIMEOUT later.
3. **Numba's LLVM runtime tries `execve`/`mmap PROT_EXEC` calls that the seccomp filter denies.** Numba JIT needs to generate executable memory. If the sandbox denies `mprotect(..., PROT_EXEC)` for any newly-allocated page, the JIT fails at compile time.
4. **Version mismatch.** Local numba is 0.61.0 (requirements.txt). If the tournament image pins a different numba version and the `@njit` decorators silently fail to match, we could see ImportError during module load.

Any of the above would read to the UI as a LOST validation (effectively a code crash). No way to tell which from the web without a WinReason probe.

## 5. Shipping decision

Given the deadline pressure and the clean pure-python PASS:

1. **Default `_USE_NUMBA=False` for submission zips.** This is what LIVE-006 proves works. Update agent folder's `heuristic.py` to hard-set `_USE_NUMBA = False` OR have the build pipeline force it during zip-assembly (safer since dev-heuristic still wants numba for local benchmarking).
2. **Local benchmarks can keep `_USE_NUMBA=True`** for the JIT speedup (the env var `RATTLEBOT_NUMBA=1` override is still respected). Only tournament zips strip it.
3. **Performance impact:** per dev-heuristic's T-30c-numba benchmark, numba gives ~3× speedup on the hot eval path, which translated to depth 13 (pure-py) vs 14-15 (numba) at the 2 s per-turn budget. Losing 1-2 plies of search depth is much smaller than "bot is invalid and doesn't ship at all."
4. **Submission candidate matrix:** Add a new row in `docs/plan/SUBMISSION_CANDIDATES.md` for `RattleBot_v03_pureonly` — SHA256 `f046631f...`, READY. Treat it as the strongest shippable candidate we have RIGHT NOW (until BO-tuned weights land).

## 6. Next steps (suggested; for team-lead)

- **Highest priority:** commit a permanent code path that forces `_USE_NUMBA=False` in submission builds. Options: (a) bake into a build-time flag in a new `tools/build_submission.py`; (b) change the default env var behavior to `"0"` (off) with tests that re-enable it via override; (c) dev-heuristic edits `heuristic.py:131` to `_USE_NUMBA: bool = os.environ.get("RATTLEBOT_NUMBA", "0") != "0"` (default off, local benchmarks opt-in).
- **Sandbox-sim (task #62 in flight):** retest on WSL with `limit_resources=True` and numba ON to reproduce the sandbox failure locally. The sim would also be the fastest place to disambiguate the WinReason (see §4).
- **Optional follow-up:** try `@njit(cache=False)` in a third upload to test hypothesis §4-1 specifically. Not strictly necessary for deadline (we already have a valid path).
- **v0.2_notuning candidate:** still unbuilt per SUBMISSION_CANDIDATES.md §2.2. With pureonly now valid, v0.2_notuning is a weaker fallback — lower priority to stage.
- **BO run T-20d-RUN1-v2:** whenever it completes, build v03_pureonly + BO-weights and validate. Use the pureonly recipe from §2 above + the `weights.json` rename trick from SUBMISSION_CANDIDATES.md §2.3.

## 7. Deliverables status

| Step                                                   | Status                                 |
|--------------------------------------------------------|----------------------------------------|
| Build pureonly zip (pure-python forced)                | DONE — SHA256 `f046631f...`            |
| Upload to bytefight                                    | DONE (user-assisted manual file-picker) |
| Do NOT activate                                        | Held — Yolanda still Current           |
| Validation result captured                             | **VALID (WON the validation match)**   |
| YES/NO on "is numba the problem?"                      | **YES** — §3 table is decisive         |
| LIVE_UPLOAD_006.md                                     | DONE (this file)                       |
| Ping committer-2                                       | Next                                   |

## 8. Scrimmage-budget accounting (CON §F-14)

No scrimmages run this pass. Budget unchanged: 1 consumed (Yolanda vs George from LIVE-004), ~9 remaining.

## 9. Cross-references

- `LIVE_UPLOAD_005.md` — numba-on upload that FAILED; §3 hypotheses predicted numba as cause #1. Now confirmed.
- `HANDOFF_TESTER_LIVE.md §2` — tool-size workaround for big zips is user manual drop.
- `docs/plan/SUBMISSION_CANDIDATES.md` — add v03_pureonly row when team-lead confirms the shipping plan.
- Task #62 — sandbox-sim WSL retest (in flight) will give orthogonal evidence on why numba fails.
