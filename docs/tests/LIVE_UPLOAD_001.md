# LIVE_UPLOAD_001 — FloorBot upload, VALIDATION FAILED

**Owner:** tester-live
**Date:** 2026-04-16 → 2026-04-17 (straddled midnight EDT)
**Status:** PARTIAL SUCCESS / REAL FAILURE — upload worked, submission listed, but the automatic validation match returned `LOST` and the submission is marked `invalid`. FloorBot is **NOT** the active submission. No vs-George scrimmage was run because an invalid submission cannot scrimmage. This is a real failure worth investigating before the deadline.

---

## Timeline

| Time (EDT)      | Event                                                                                       |
|-----------------|---------------------------------------------------------------------------------------------|
| 2026-04-16      | FloorBot.zip built & verified — depth-1 layout `FloorBot/agent.py` + `FloorBot/__init__.py`, 2441 bytes. |
| 2026-04-16      | First upload attempt BLOCKED — account was not on a team. Paused for team-lead.              |
| 2026-04-16 ~21:07 | User joined Team 15 ("Welcome to ByteFight!") with partner apatel3111. Team Code 7F5TQ36E.   |
| 2026-04-16 21:12:07 | Upload succeeded. UI toast "Uploaded submission". Cloudflare Turnstile CAPTCHA auto-passed. Submission row appeared with status `not_evaluated_autoset`. |
| 2026-04-16 21:12 – ~21:14 | Automatic validation match ran — status `WAITING` for ~2 minutes.                      |
| 2026-04-16 ~21:14 | Validation match ended: **LOST** (2m duration). Submission Validity flipped from `not_evaluated_autoset` to `invalid`. "Current" checkbox UNCHECKED. |

Match UUID for the validation match: `330386c2-e4d9-4caf-bb93-21481eb82877` (replay URL `https://bytefight.org/match/330386c2-...` returns "Match Not Found" — replays for invalid submissions appear to be unavailable).

---

## The zip that was uploaded

`python -m zipfile -l C:\Users\rahil\AppData\Local\Temp\FloorBot.zip`:

```
File Name                                      Modified             Size
FloorBot/agent.py                              2026-04-16 19:57:36         7269
FloorBot/__init__.py                           2026-04-16 19:57:04           58
```

2.44 KB zipped. No `__pycache__`, no `tests/`. `agent.py` is the reactive-policy body documented in `docs/plan/FLOOR_BOT.md`. `__init__.py` is `from .agent import PlayerAgent`.

**Local-match evidence FloorBot works**: per D-007, 50 matches each side vs Yolanda = 100/100 wins, 0 crashes, 0 invalid moves, p99 per-move 0.034 ms.

**On Windows, the local driver crashes with `UnicodeEncodeError` in `engine/gameplay.py::print_board`** (cp1252 can't encode the board-printing unicode glyphs) — this is a driver-side bug unrelated to FloorBot and blocks local reproduction of the tournament failure on Windows.

---

## Hypotheses for the validation-LOST result

Per `engine/player_process.py:242-256`, the tournament loader:
1. `sys.path.append(submission_dir)` (line 158)
2. `apply_seccomp()` (line 218) under `limit_resources=True`
3. `importlib.import_module("FloorBot")` — runs `__init__.py`
4. `importlib.import_module("FloorBot.agent")` — runs `agent.py`
5. Calls `module.PlayerAgent(temp_board, transition_matrix, time_left_func)`

FloorBot's `__init__.py` does `from .agent import PlayerAgent`. That's redundant with step 4 and pulls all of `agent.py`'s top-level imports in during step 3 — including `from game import board as board_mod`, etc. Yolanda ships `agent.py` only (no `__init__.py`) and presumably passes validation.

Candidates, ranked:

1. **Validation is just a match; "LOST" → `invalid` by policy.** We don't know what opponent validation uses. If validation is FloorBot vs. some reference (e.g. George), FloorBot may just have lost on merits, and the system marks any loss as `invalid`. Under this hypothesis, there is no code bug — we'd need a *stronger* bot to pass validation. (Counter-evidence: Yolanda is a random bot and presumably passes validation — so "win required" isn't the rule, or the validation opponent is even weaker than Yolanda.)
2. **The `__init__.py` re-export is the culprit.** Step-3 and step-4 both execute `agent.py`'s module body; most Python code tolerates that, but a subtle interaction with `importlib.import_module` + seccomp could trip one pass. Easy to test: drop `__init__.py`, re-zip, re-upload.
3. **Seccomp kill during import.** `apply_seccomp` is called *before* the import. If any allowed syscall we're calling is actually on the kill list on prod Linux but NOT in the local-dev allowlist, first import could kill the subprocess. Unlikely because FloorBot does no I/O, no threading, no net. But possible if `random.Random(seed)` triggers getrandom() on Python 3.12.
4. **Silent tournament-sandbox-only bug in FloorBot** that doesn't reproduce locally. Unlikely given the code is pure stdlib + `game.*`.

Best bet: **hypothesis 1 + hypothesis 2**, in that order. First, find out what validation actually checks. Second, try the `__init__.py`-free version.

---

## Account / team state (snapshot)

- **Account:** Rjav / rjavid3@gatech.edu. (NOT rahiljav@gmail.com. See `~/.claude/.../memory/reference_bytefight.md`.)
- **Team:** "Welcome to ByteFight!" (Team 15), Team Code 7F5TQ36E, Created 2026-04-16 21:07 EDT, Members: apatel3111, Rjav.
- **Team URL:** https://bytefight.org/compete/cs3600_sp2026/team/81513423-e93e-4fe5-8a2f-cc0423ccb953
- **ELO:** 1500 (baseline unchanged — the invalid submission did not move ELO; it never became active).
- **Match History (Team 15):** one row — `Team 15 — LOST — FloorBot.zip — validation — 2m`. Replay URL 404s.
- **Submissions table:** one row — `invalid / FloorBot.zip / 4/16/2026, 9:12:07 PM`. "Current" unchecked. Storage: 0.0 MB of 200 MB.

No other submissions existed at the time of upload (team was new, 0 prior submissions). No partner submission was overwritten.

---

## bytefight.org UI observations (for future automations)

- **Submit Bot modal** on `/submissions`:
  - `<input type="file" id="submission" accept=".zip">`
  - checkbox "Set as current submission once validated" — default **checked**
  - Cloudflare Turnstile CAPTCHA — auto-solved in our case
  - `Cancel` / `Upload` buttons
- The Chrome MCP `upload_image` tool does NOT accept arbitrary file paths (screenshot-image-only). **Workaround that worked**: read the zip as bytes in bash → base64 → `javascript_exec` that decodes the base64 into a `File` object, uses `DataTransfer` to attach it to `input.files`, and dispatches `change` + `input` events. The UI registered "Selected file: FloorBot.zip (2.44 KB)" within a few hundred ms.
- After clicking Upload: green toast "Uploaded submission", modal closes. Submissions table updates in ~1–2 s. Server kicks off a validation match automatically — it appears on the `/team` Match History with status `WAITING` and terminates within ~2 minutes.
- The **Current** column on Submissions shows a yellow outlined checkbox for the active submission; toggling it is how manual (de)activation works. Not tested because our submission never became valid.
- The **Self Scrimmage** button on `/team` opens the scrimmage-vs-reference-bot modal (not reached because validation failed first).
- The `Opponent…` textbox on `/team` is a **filter** on Match History, not a scrimmage trigger. Easy UI misread.
- `Create/Join Team` link DISAPPEARS from the sidebar once the user is on a team; it is replaced by `My Team` + `Submissions`.
- Replays for invalid submissions return "Match Not Found" at `/match/<uuid>`. Logs / stderr from the failed validation are not exposed in the UI we found.

---

## Followup actions (pick-up list for next agent)

1. **Check tournament `/faq` or `/resources` for the definition of "invalid"** — is it "code error" or "lost validation match"? This single piece of information resolves the ambiguity.
2. **Read `engine/gameplay.py` validation-match code path** if it exists (look for `validation`, `FAILED_INIT`, `INVALID_TURN` handling).
3. **Simplified re-upload experiment**: delete `FloorBot/__init__.py`, re-zip (depth-1 `FloorBot/agent.py` only), re-upload. If it validates, the `__init__.py` re-export is the bug — same pattern as Yolanda would apply going forward.
4. **Fix `engine/gameplay.py::print_board` unicode on Windows** so tester-local can actually drive matches. Add `import io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` or similar — blocks local repro of this failure on Windows.
5. **Ask the user** whether their partner apatel3111 has uploaded or plans to upload — this will determine whether our next attempt risks overwriting partner work.

---

## Deliverables status vs task #12

| Deliverable                                             | Status                               |
|---------------------------------------------------------|--------------------------------------|
| (1) Build FloorBot.zip with correct layout              | DONE — `C:\Users\rahil\AppData\Local\Temp\FloorBot.zip` |
| (2) Upload to bytefight.org for cs3600_sp2026           | DONE — submission row present        |
| (2a) Set as active submission                           | **NOT DONE** — submission is `invalid`, not current. |
| (3) One scrimmage match vs George                       | **NOT DONE** — invalid submissions can't scrimmage. |
| (4) docs/tests/LIVE_UPLOAD_001.md                       | DONE — this file                     |

**Live-scrimmage budget per CON §F-14: 0 consumed.** Validation match was automatic, not elective.

---

## Recommendation to team-lead

FloorBot v1 failed tournament validation. Two paths:

- **(A) Triage + fix now.** Minimal experiment: remove `FloorBot/__init__.py` and re-upload. `agent.py` is already self-contained. This matches Yolanda's shape. If validation still fails, read the gameplay-validation code and/or ask on course Piazza/Discord. Estimated effort: 30 min to 2 hours.
- **(B) Wait for RattleBot.** Per D-006, FloorBot is insurance; if it can't pass validation, we have no grade floor. Deadline is 2026-04-19 23:59. Risky.

**Strong recommendation: (A) immediately.** The fix may be a one-line change and restoring the 70% floor is worth ~30 minutes of anyone's time. tester-live will not self-initiate — awaiting go/no-go from team-lead.
