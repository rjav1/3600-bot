# LIVE_UPLOAD_005 — RattleBot v0.3-prebo upload (VALIDATION FAILED)

**Owner:** live-tester-2
**Date:** 2026-04-17
**Status:** **INVALID** — RattleBot_v03_prebo_patched_20260417_0953.zip uploaded, lost validation match → marked `invalid` by bytefight. Per H7 this means the bot lost the auto-validation game. Yolanda remains the Current submission; no partner work touched; no scrimmage vs George run (task step 4 was gated on validation PASS).

---

## 1. Artifact

| Field              | Value                                                                 |
|--------------------|-----------------------------------------------------------------------|
| Zip name           | `RattleBot_v03_prebo_patched_20260417_0953.zip`                       |
| Local path         | `C:\Users\rahil\AppData\Local\Temp\submissions\RattleBot_v03_prebo_patched_20260417_0953.zip` |
| Size               | 34 110 B                                                              |
| SHA256             | `561bf897b7ed7c1029710ebe5d27ac790f5b30b77114e3320be07d3c12225a12`    |
| Source commit      | `b51c91d` on origin/main (HEAD at build time; docs on top of c0d8f3a) |
| Layout             | `RattleBot/*.py` at depth 1 (9 files, no `tests/`, no `__pycache__`)  |
| Members            | `__init__.py` (432 B), `agent.py` (12 152), `heuristic.py` (38 642), `move_gen.py` (6 065), `rat_belief.py` (9 838), `search.py` (16 436), `time_mgr.py` (6 826), `types.py` (5 151), `zobrist.py` (3 738) |
| `weights.json`?    | No (BO run T-20d-RUN1-v2 still in flight — agent falls back to W_INIT per `_load_tuned_weights`) |
| `requirements.txt`? | No — tournament env pre-installs numba/jax/numpy/etc. per CLAUDE.md line 108 |

## 2. Upload flow

1. Pulled latest from origin (HEAD = b51c91d, post-c0d8f3a T-30e fix).
2. Built zip via Python `zipfile.ZIP_DEFLATED` from disk (not from `git show`) — captures on-disk working-copy state.
3. Verified layout with `python -m zipfile -l`: 9 members, all at `RattleBot/` depth 1, tests excluded.
4. Chrome MCP extension reconnected after /chrome nudge.
5. Navigated to `/submissions`, clicked Submit Bot (by coordinate; ref-click didn't register — **see §5 UI note**).
6. Modal opened. Planned to inject via base64/DataTransfer but hit assistant-side tool-size limits — 45 480-char base64 doesn't fit in a single `javascript_tool` text parameter (practical ceiling ≈ 4 600 chars observed).
7. **User performed the file-picker step manually** via OS file dialog. Upload succeeded ("Uploaded submission" toast — not captured in text but implied by row appearance).
8. Submission row appeared in `/submissions` table. Validation ran server-side.
9. Validation completed in ~1-2 minutes (consistent with LIVE-003's ~20s + queue time).
10. Outcome: **LOST → Validity = invalid**. Submissions table shows:

```
Current  Validity  File                                              Date
         invalid   RattleBot_v03_prebo_patched_20260417_0953.zip     4/17/2026, 10:18:10 AM
   ☑     valid     Yolanda_probe.zip                                 4/16/2026, 9:40:50 PM
         invalid   FloorBot.zip                                       4/16/2026, 9:27:32 PM
         invalid   FloorBot.zip                                       4/16/2026, 9:12:07 PM
```

And Match History:

```
Team 15  LOST  RattleBot_v03_prebo_patched_20260417_0953.zip  validation  1m
```

No new row type. No visible WinReason. No replay (match page still 404s per INTEL_PROBE.md).

## 3. What happened — H7 re-stated

From LIVE-003 / HANDOFF_TESTER_LIVE §3: validation = win-the-match gate. LOST → `invalid`. This is the same outcome FloorBot had twice in LIVE-001/002, and is the opposite of Yolanda's LIVE-003 validation WIN. Conclusion: **RattleBot v0.3-prebo, with W_INIT hardcoded weights and all of the T-20f/T-20c.1/T-20g/T-30b/T-30c-numba/T-30d code paths active, loses the tournament-validator match**. The local test suite (34/34 or whatever it is now) and local self-play vs Yolanda/FloorBot do not reproduce this.

Do NOT claim which WinReason caused the loss — the UI surfaces no detail. Possibilities, ranked by prior likelihood:

1. **CODE_CRASH on the first numba-compile warm-up.** `heuristic.py _USE_NUMBA=True` triggers `@njit` compile on first call from inside `play()`. If the sandbox's Python/numba combo differs from ours (or numba tries to write a cache file the sandbox blocks), the first `play()` raises. The bot has a try/except fallback in `play()` (D-006) — but if the exception happens *before* the fallback can engage (e.g., at import time, not during `play`), it's a CODE_CRASH → auto-loss.
2. **INVALID_TURN from a move the new features return.** T-30b added F17 priming-lockout and F18 opp-belief-proxy (14 total). If the heuristic weights (W_INIT still 14-dim) push the search toward a move that fails `is_valid_move` on the validator-opponent's board but passes on Yolanda/FloorBot's typical boards, that's INVALID_TURN → auto-loss.
3. **TIMEOUT from numba first-call compile blowing the init or early-turn budget.** `init_timeout = 10 s` under `limit_resources=True` (GAME_SPEC §7). A cold numba compile can take >10s on some platforms. If `warm_numba_kernels()` is called from `__init__` and the JIT is slow, FAILED_INIT fires. Alternatively if kernels compile lazily inside `play()` at turn 1, the per-turn timer can eat most of the 240 s budget in one shot.
4. **MEMORY_ERROR.** The numba code-caching and/or F17/F18 precompute may exceed 1.5 GB RSS under limit_resources. Less likely — local profiling was well under.
5. **FAILED_INIT.** Same as (3) but at __init__ time specifically. Includes numba import, weights loading (no weights.json so it's a no-op), and precompute paths (Zobrist tables, belief p_0 = e_0 @ T^1000, etc.).

I cannot disambiguate these from the UI. Need to pull the RattleBot source path the sandbox-sim exercises (tools/sandbox_sim.py or similar per task #37) and run a Linux `limit_resources=True` reproduction.

## 4. Scrimmage decision

Per task-56 step 4: scrimmage vs George was contingent on validation **PASS**. It failed. **Did NOT run the scrimmage.** §F-14 budget unchanged (1 consumed so far: the original Yolanda vs George).

## 5. UI note: ref-click vs coordinate-click

The Submit Bot button at `/submissions` did NOT open the modal when clicked via `computer.left_click` with `ref=ref_43` (the ref returned by `find`). It DID open when clicked by coordinate `(107, 205)`. Possibly a ref-targeting regression on this specific React handler. **Workaround for the next tester: use coordinate clicks, not ref clicks, for the Submit Bot button.** Add this to HANDOFF_TESTER_LIVE.md §2 or its successor.

## 6. Tool-size constraint on big zips (new learning)

Yolanda_probe.zip (684 B) base64 = ~920 chars → fits in one `javascript_tool` call. RattleBot v0.3-prebo (34 110 B) base64 = 45 480 chars → does NOT fit. Observed practical ceiling on a single JS tool call: ~4 600 chars (tool cut off my 5 000-char chunk). Chunked injection (10+ calls of `window.__rb_b64 += "..."`) is possible but burns a lot of agent turns.

Faster path the next tester should try first:

- **Manual file-picker upload by the user** (what we did this pass). User selected the zip from the file dialog; we observed the result via Chrome MCP. Minimal friction.
- Alternatively: a local HTTPS server (not HTTP — CORS) serving the zip with `Access-Control-Allow-Origin: https://bytefight.org`, then page-side `fetch()` + `Blob()` + inject. Unproved.

Record this as R-LIVE-05 in whatever hand-off doc succeeds HANDOFF_TESTER_LIVE.md.

## 7. Yolanda collateral update (context for next rotation)

Between LIVE-004 and this pass, matchmaking happened. Yolanda played 10 non-validation matches all LOST → record is 0W-0D-10L. ELO dropped from 1500 provisional to ~1350-1400. Unchanged state: Yolanda still Current (checkbox ☑), still valid, partner still silent (apatel3111 never uploaded). Tester-live's George scrimmage also now shows **LOST** (was RUNNING at rotation; now finalized). None of this blocks anything — Yolanda remains the insurance floor.

## 8. Immediate next actions

1. **Dev-heuristic / dev-integrator: triage why v0.3-prebo loses sandbox validation.** Task #24 was closed for FloorBot as "could not reproduce" — but we now have a different bot failing the same gate. The sandbox-sim (task #37, completed) should be re-run with v0.3-prebo to see if it fails locally under `limit_resources=True`. If yes, iterate until it passes. If no (sandbox-sim passes but bytefight fails), we have a tournament-only bug that needs the `docs/tests/SANDBOX_SIM.md` approach sharpened.
2. **DO NOT re-upload without a fix.** Each failed upload eats a submissions-table slot. We have 0.0 MB / 200 MB used — no disk pressure — but it clutters the table.
3. **Team-lead: consider whether to activate Yolanda hunter-protocol.** With v0.3-prebo invalid and v0.2-tuned pending BO completion + its own validation, we may end up at the deadline with Yolanda as the only valid submission. That's the insurance the plan was designed for, but the floor is low (0W-10L so far under matchmaking).
4. **v0.2_notuning backup** is still unbuilt per `docs/plan/SUBMISSION_CANDIDATES.md §2.2`. Might be worth building soon as a "simpler than v0.3, but newer than v0.1" bridge candidate.

## 9. Deliverables status

| Step                                                   | Status                       |
|--------------------------------------------------------|------------------------------|
| Pull latest + rebuild zip at HEAD (b51c91d)            | DONE                         |
| Upload to bytefight                                    | DONE (user-assisted manual)  |
| Do NOT activate                                        | Held — Yolanda still Current |
| Validation result captured                             | **INVALID (LOST)**           |
| Scrimmage vs George (contingent on PASS)               | Skipped — validation failed  |
| LIVE_UPLOAD_005.md                                     | DONE (this file)             |
| Ping committer-2                                       | Next                         |

## 10. Scrimmage-budget accounting (CON §F-14)

Total elective scrimmages used so far: **1** (Yolanda vs George, LIVE-004). This pass added **0**. Remaining per team-lead's ~10-slot estimate: ~9.
