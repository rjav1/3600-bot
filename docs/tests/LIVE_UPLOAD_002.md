# LIVE_UPLOAD_002 — FloorBot (no `__init__.py`) re-upload: STILL INVALID

**Owner:** tester-live
**Date:** 2026-04-17
**Status:** Hypothesis-2 experiment from LIVE-001 was **REFUTED**. Stripping `FloorBot/__init__.py` did not change the outcome — the second upload also landed as `invalid` after a very short validation match. FloorBot v1 is NOT deployable as-is.

---

## Experiment

Per team-lead direction: re-zip FloorBot **without** `__init__.py` (match Yolanda's single-file shape) and re-upload. If validation passes, `__init__.py`'s `from .agent import PlayerAgent` re-export was the bug.

### The new zip

Built at `C:\Users\rahil\AppData\Local\Temp\FloorBot_noinit.zip`:

```
File Name                                      Modified             Size
FloorBot/agent.py                              2026-04-16 19:57:36         7269
```

2276 bytes zipped. Only `FloorBot/agent.py` at depth 1 — nothing else. Verified with `python -m zipfile -l` before upload.

`agent.py` content is byte-identical to the version that was in LIVE-001's zip. No code changes.

### Upload

- **Time:** 2026-04-16 21:27:32 EDT.
- **Method:** Same Chrome-MCP `javascript_exec` base64-inject-into-`input[type=file]#submission` workaround as LIVE-001. Cloudflare Turnstile auto-verified. `Set as current submission once validated` checkbox left at its default (checked). Click `Upload`.
- **Toast:** "Uploaded submission" — green, confirmed.
- **Submissions table** now shows two rows, both `invalid`:
  - `invalid / FloorBot.zip / 4/16/2026, 9:27:32 PM` (new, no `__init__.py`)
  - `invalid / FloorBot.zip / 4/16/2026, 9:12:07 PM` (old, with `__init__.py`)
- Storage: 0.0 MB of 200 MB (both zips are tiny).

### Validation match

- Match entry appeared on the `/team` page with status `WAITING`.
- Within **~1 minute** (much faster than LIVE-001's ~2 minutes), status flipped to **LOST**.
- Match History now shows two LOST-validation rows (no successful matches, no active submission).
- Match UUIDs visible in DOM (extracted via JS, excluding the team UUID `81513423-...`):
  - `9de7da14-cdf0-482a-87fb-d7c8553ef052`
  - `0923cdee-89e3-4e04-9b48-0e2faa3cf64b`
  - (Which is which is not distinguishable from the page — the replay URLs return "Match Not Found" for invalid submissions, same as LIVE-001.)

### Clarification on the "2m" / "48s" figures from LIVE-001

Looking at the screenshots again, the times in the Match History column are **wall-clock time since the match ran**, not match durations. When I saw "2m" in LIVE-001 I read it as a 2-minute match duration; it was actually "2 minutes ago". Current screenshots show the rows as "1m" (new upload, just now) and "17m" (old upload, 17 minutes back from now). So both validation matches almost certainly completed in a few seconds to a minute — which suggests the failure is **early** (e.g. crash during `__init__` or first `play()` call), not a 40-turn game loss on merits.

That observation **strengthens hypothesis 3 (seccomp kill) and weakens hypothesis 1 (lost on merits)** from LIVE-001.

---

## Outcome

**Refuted:** Hypothesis 2 ("`__init__.py` re-export is the bug") is wrong. The single-file zip behaves identically to the package zip.

**New leading hypotheses** (updated from LIVE-001):

### H3 (was #3) — Seccomp or sandbox rejection on import or init

The tournament sandbox applies `seccomp` before `importlib.import_module`. If any module FloorBot transitively imports does a forbidden syscall on first load (e.g. `setaffinity`, `clone3`), the process is killed. That would:
- take seconds, not minutes — matches the observed timing.
- leave no replay — matches the "Match Not Found".
- mark the submission `invalid` — matches what we see.

Candidates inside FloorBot's imports:
- `import random` — `random.Random(seed)` calls `os.urandom()` under the hood on init. On Linux+seccomp, `getrandom(2)` should be allowed (it's standard), but `/dev/urandom` reads via `open`/`read` are possible too. Unlikely to be the root cause.
- `from collections.abc import Callable` — pure stdlib, safe.
- `from typing import List, Optional, Tuple` — pure, safe.
- `from game import board as board_mod` and friends — whatever the engine imports transitively (likely `numpy`). If `numpy`'s first-use triggers `openat("/sys/...")` or `prctl` calls that seccomp kills, we'd see this. But Yolanda imports the same `game.board` and works.

### H5 (NEW) — First `play()` returns an invalid `Move` that the tournament engine rejects

Specifically, if FloorBot's first move is somehow out-of-bounds or tries to carpet onto the opponent's cell, the engine returns `INVALID_TURN` and the game ends immediately (on turn 0 or 1). Since FloorBot locally plays 100/100 wins vs Yolanda on Windows with no invalids, this should NOT happen — but the local runs are on Windows with `limit_resources=False` and a different `T` distribution. Worth considering.

Specifically suspicious in `agent.py`:
- `_best_carpet` requires `CARPET_POINTS_TABLE.get(m.roll_length, -999)` > 1. If `m.roll_length` is somehow 0 or negative (shouldn't happen — `board.get_valid_moves()` should only return valid ones), this could trip.
- `_line_potential` starts `for _ in range(BOARD_SIZE - 1)` which on the first iteration steps 1 cell; should be safe.
- `_safe_fallback` returns `Move.search((0, 0))` as absolute last resort — `(0,0)` is inside bounds, search always valid.

### H6 (NEW) — The tournament engine validates against a specific opponent whose type our bot can't handle gracefully

E.g. if the validator is FloorBot-vs-some-specific-bot that immediately primes 7 squares and rolls a CARPET-7, FloorBot may hit a `NotImplementedError` somewhere downstream. Unlikely — we read through the code and there are no NotImplementedErrors in FloorBot.

### H7 (NEW, STRONGEST) — Bytefight considers a LOST validation match an `invalid` submission, AND the validator is significantly stronger than FloorBot

Explanation: FloorBot's local win-rate vs Yolanda is 100%, but Yolanda is a random-mover. If the validator uses a reference bot at George's level, FloorBot could lose cleanly — and the system calls that result `invalid` to block weak bots from the leaderboard. In that case, the "fix" is **FloorBot isn't strong enough to clear validation** and we need a stronger insurance bot.

This would explain:
- why stripping `__init__.py` made no difference (not a code issue).
- why replays 404 (maybe the system doesn't store invalid-submission replays regardless of reason).
- why Yolanda isn't also marked invalid if it passes validation — unless Yolanda also fails validation and nobody has tested it recently. We don't have evidence either way.

But note: the LIVE-001 trip report already questioned this hypothesis because *if* validation required "win vs validator", Yolanda (random mover) couldn't have been kept as a reference bot. Unless validation is more lenient on reference bots than on team submissions. Unclear.

---

## Implications for RattleBot (team-lead's caveat)

Team-lead asked me to note:

> RattleBot IS a genuine multi-file package (rat_belief.py, search.py, etc.), so it needs `__init__.py`. If this experiment showed bytefight rejects `__init__.py`-bearing zips, that's critical for RattleBot.

**Good news:** This experiment shows that bytefight does NOT reject `__init__.py`-bearing zips for a reason specific to `__init__.py`. Both zips failed the same way. So RattleBot's multi-file package layout is **not** the bottleneck we should be worried about.

**Bad news:** Whatever actually is breaking FloorBot is likely to break RattleBot too (since RattleBot is a strict superset: more imports, more code, same sandbox). We need to understand the root cause **before** RattleBot ships live. If H7 is correct (FloorBot just isn't strong enough), RattleBot may pass because RattleBot is supposed to be stronger. If H3 or H5 is correct, RattleBot will fail too.

---

## Recommended next experiments (not run — need team-lead go-ahead)

In order of cheapness:

1. **Zip-and-submit Yolanda unchanged** to confirm Yolanda passes current-day validation. This establishes the floor: if even Yolanda is invalid, validation ≠ "beat a reference bot". If Yolanda passes, validation likely requires a win, and FloorBot's losses to the validator are our real failure.
   - Risk: None — Yolanda is already in the repo as a known baseline.
   - Cost: 5 minutes. Does not consume §F-14 scrimmage budget (validation is automatic).
   - Implication gate: if Yolanda fails too, the validator has rejected *something* that has nothing to do with bot strength — focus on sandbox/import hypotheses.

2. **Add extensive print-to-stderr logging in FloorBot `__init__` and first `play()` call** and re-upload. See if anything surfaces in UI (doesn't seem to, but worth checking).
   - Risk: Tiny.
   - Cost: 10 minutes.

3. **Ask on Piazza / course Discord** what "invalid" means on the Submissions page.
   - Risk: User has to do this — outside the bot automation scope.
   - Cost: user-time, not agent-time. Highest information-per-minute.

4. **Read `engine/gameplay.py`** for the `validation` match path and any logging that surfaces validation-match outcomes. Look for what distinguishes `invalid` from `lost_valid`.

---

## UI / flow observations added in LIVE-002

- The Submissions table accumulates rows — each upload adds a new row regardless of success/failure. Previous submissions remain listed, not replaced. We now have 2 invalid FloorBot.zip entries.
- The "red trash can" icon next to each row (ref_1456 in LIVE-001) presumably deletes the submission. **NOT CLICKED** — per the initial task constraint ("Do NOT delete… any existing submission").
- The Match History column 4 shows relative-time ("1m", "17m"), not match duration. Correcting LIVE-001's 2m / 48s framing.
- `/match/<uuid>` for invalid validation matches returns "Match Not Found" — no replay, no logs, no stderr. This is opaque.
- The Submit Bot modal opens fresh each click; file input and CAPTCHA reset. The checkbox "Set as current submission once validated" stays at its default **checked** each time.

---

## Deliverables status vs task #12

| Deliverable                                             | Status                               |
|---------------------------------------------------------|--------------------------------------|
| (1) Build FloorBot.zip with correct layout              | DONE (twice)                         |
| (2) Upload to bytefight.org for cs3600_sp2026           | DONE (twice)                         |
| (2a) Set as active submission                           | **NOT DONE** — both submissions `invalid`. No active submission exists. |
| (3) One scrimmage match vs George                       | **NOT DONE** — can't scrimmage invalid submissions. |
| (4) docs/tests/LIVE_UPLOAD_001.md                       | DONE (prior turn)                    |
| (4) docs/tests/LIVE_UPLOAD_002.md                       | DONE (this file)                     |

**Live-scrimmage budget per CON §F-14: still 0 consumed.** Both validation matches are automatic.

---

## Ping to team-lead

Experiment complete. Hypothesis 2 (`__init__.py` issue) is **refuted**. 

Strongest remaining hypotheses:
- **H7** (validation = "must win vs strong validator"; FloorBot just too weak).
- **H3** (seccomp kill on import).
- **H5** (FloorBot returns an invalid Move in an edge case we don't hit locally).

**Strongly recommend running experiment 1** (zip-and-submit Yolanda) to distinguish H7 from H3/H5. That's a 5-minute test that would drastically narrow the hypothesis space and cost nothing else.

FloorBot is NOT our 70% floor anymore. We need to understand the root cause before RattleBot ships.
