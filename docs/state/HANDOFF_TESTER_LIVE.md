# HANDOFF_TESTER_LIVE — bytefight.org live-upload runbook

**Author:** tester-live (rotating out for context hygiene, 2026-04-17)
**Scope:** Everything a successor needs to drive uploads / activations / scrimmages on **https://bytefight.org/compete/cs3600_sp2026** via Chrome MCP. Read this BEFORE the first interaction with the site — it will save you hours.

---

## 0. TL;DR state of the world

- **Account:** `rjavid3@gatech.edu` (display name `Rjav`). NOT `rahiljav@gmail.com` — that's the user's personal email, not the ByteFight login.
- **Team:** `Team 15`, team name "Welcome to ByteFight!", Team Code `7F5TQ36E`, 2 members (`apatel3111`, `Rjav`). URL: `https://bytefight.org/compete/cs3600_sp2026/team/81513423-e93e-4fe5-8a2f-cc0423ccb953`.
- **Current active submission:** `Yolanda_probe.zip` (unmodified starter random-mover). Insurance fallback only — low expected ELO. RattleBot or a fixed FloorBot should displace this before the 2026-04-19 23:59 deadline.
- **Submissions table (3 rows, snapshot at my shutdown):**

| Current | Validity | File                          | Date                      |
|---------|----------|-------------------------------|---------------------------|
| ☑       | valid    | Yolanda_probe.zip             | 4/16/2026, 9:40:50 PM EDT |
| ☐       | invalid  | FloorBot.zip (no `__init__`)  | 4/16/2026, 9:27:32 PM EDT |
| ☐       | invalid  | FloorBot.zip (with `__init__`)| 4/16/2026, 9:12:07 PM EDT |

- **FloorBot is broken on the tournament sandbox.** Local 100/100 vs Yolanda, but 0/2 on bytefight. Hypothesis 7 ("LOSS → invalid") confirmed; FloorBot has a real code-level bug against the validator opponent. Root cause UNKNOWN — see §6.
- **One scrimmage was submitted** (Yolanda vs George) and was STILL RUNNING at rotation time — successor should check `/team` for outcome.
- **Partner has not uploaded.** No overwrite risk observed yet. Partner-submission protocol R-PARTNER-01 is still unresolved in the broader planning docs.

---

## 1. Page map (URLs and when to visit each)

| URL                                                               | Use for                                                       |
|-------------------------------------------------------------------|---------------------------------------------------------------|
| `/compete/cs3600_sp2026`                                          | Rules / Overview. Sidebar lives here. No action UI.           |
| `/compete/cs3600_sp2026/leaderboard`                              | See all teams, each team's ELO, and the **scrimmage icon** per row. This is where you start scrimmages vs specific opponents (George, Albert, Carrie, other students). |
| `/compete/cs3600_sp2026/resources`                                | Unused.                                                       |
| `/compete/cs3600_sp2026/schedule`                                 | Matchmaking cycle schedule.                                   |
| `/compete/cs3600_sp2026/results`                                  | Unused in our workflow.                                       |
| `/compete/cs3600_sp2026/queue`                                    | Match queue — see what's currently queued on the servers.     |
| `/compete/cs3600_sp2026/team`                                     | Team home. `Submit Bot`, `Self Scrimmage`, `Edit Team`, `Leave Team`, and Match History live here. Also shows team ELO / ELO history / record. |
| `/compete/cs3600_sp2026/team/<team-uuid>`                         | Public team page (same as above, linked from leaderboard).    |
| `/compete/cs3600_sp2026/submissions`                              | Submissions table. Upload + activate (Current checkbox) + delete. |
| `/compete/cs3600_sp2026/join-team`                                | Appears only if you're NOT on a team — Create/Join forms.     |
| `/match/<match-uuid>`                                             | Replay page. **Returns 404 ("Match Not Found") for all validation matches** regardless of win/loss. Unknown whether it works for scrimmages or ranked matches (untested). |
| `/profile`                                                        | User profile — email, username, reset password. "Team & Competition History" says "Coming soon…". |

**Navigation gotcha:** `/compete/cs3600_sp2026/team` in the address bar sometimes redirects to `/submissions` if you navigate while a modal is open. Always verify the URL tab-context after a click.

---

## 2. Upload mechanics (the pain)

### What the UI expects

- Click `Submit Bot` → modal opens.
- Modal contents:
  - `<input type="file" id="submission" accept=".zip">` (rendered as "Choose File / No file chosen")
  - Checkbox "Set as current submission once validated" (default: **CHECKED**)
  - Cloudflare Turnstile CAPTCHA (usually auto-passes)
  - `Cancel` / `Upload` buttons
- User picks file via native OS picker → zip uploads → server validates.

### Why Chrome MCP alone can't do it

The `mcp__claude-in-chrome__upload_image` tool accepts **screenshot image IDs only** — it cannot attach an arbitrary file from disk to an `<input type="file">`. The native OS file-picker dialog that opens on `Submit Bot` click is outside the DOM and not operable.

### The workaround that actually works (USE THIS)

Read the zip locally, base64-encode it, inject a `File` object into the input via `javascript_tool`, dispatch `change` + `input` events. Exact pattern:

```bash
# 1. Encode the zip as base64
python -c "
import base64
with open(r'C:/path/to/MyBot.zip', 'rb') as f:
    data = f.read()
print(len(data))
print(base64.b64encode(data).decode())
"
```

```javascript
// 2. Paste the base64 into mcp__claude-in-chrome__javascript_tool
// (This runs in the page context.)
(() => {
  const b64 = "UEsDBBQAA..."; // the full base64 string
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  const file = new File([bytes], "MyBot.zip", {type: "application/zip"});
  const input = document.querySelector('input[type="file"]#submission');
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
  input.dispatchEvent(new Event('change', {bubbles: true}));
  input.dispatchEvent(new Event('input', {bubbles: true}));
  return JSON.stringify({
    filesCount: input.files.length,
    name: input.files[0] && input.files[0].name,
    size: input.files[0] && input.files[0].size
  });
})()
```

After that, click `Upload` via the ref you got from `read_page` (NOT by coordinate — React re-renders move things). Expect a green toast "Uploaded submission". A row appears in the Submissions table within ~1 s, initially as `not_evaluated`.

### Known failure modes during upload

- **Modal not opening on first click.** The `Submit Bot` button on the Submissions page can transiently show a **lock icon** and be `disabled=true` for ~1 minute after a failed/aborted upload. **Workaround:** use the Submit Bot button on the `/team` page — it's enabled independently of the Submissions-page state.
- **File display lag.** After `input.files = dt.files`, the visible "Choose File / Selected file: X" text may still read "No file chosen" because the UI is driven by separate React state. Don't trust the display — verify `input.files[0].name` via `javascript_tool`.
- **Checkbox re-checks itself.** The "Set as current submission once validated" checkbox can revert to checked if the file is re-injected or another dialog interaction happens. **Workaround:** verify `document.querySelector('[role="checkbox"][aria-checked]').getAttribute('aria-checked')` *immediately before* clicking Upload. Click the checkbox button via its `ref` (not by DOM manipulation) to change state — programmatic state changes don't always drive the React store.
- **Clicking `Upload` before Turnstile auto-passes.** The CAPTCHA shows "Verifying..." for ~3s then "Success!". If you click Upload during "Verifying...", the submission may silently fail. Wait for the green "Success!" checkmark before clicking Upload.

---

## 3. Validation semantics (H7 CONFIRMED)

Immediately after upload, the server runs an automatic **validation match**. The bot plays against some internal validator opponent. Our experiments:

| Upload                                 | Validation result    | Submission Validity |
|----------------------------------------|----------------------|---------------------|
| FloorBot.zip (with `__init__`)         | LOST                 | **invalid**         |
| FloorBot.zip (no `__init__`)           | LOST                 | **invalid**         |
| Yolanda_probe.zip (starter random)     | WON                  | **valid**           |

Conclusions:
- Validation = win-the-match gate. LOSS → `invalid`. WIN → `valid`.
- Sandbox is fine. `__init__.py` is fine. Zip packaging is fine.
- FloorBot has a code-level bug only manifest on the tournament sandbox that makes it lose a match Yolanda wins. See §6 for suspects.

Duration: the match runs in **~20 seconds** wall-time. Watch for the "Team 15 — [status] — [zip name] — validation — [age]" row on `/team`. Note: the age column is **relative time since the match**, not match duration (the "2m" I saw in LIVE-001 was actually "2 minutes ago", which took me a tick to realize).

### No error messages on `invalid` rows

Checked hover, click, DOM attributes, tooltips, titles, `data-*` attrs, nearby text, network requests. **Nothing.** The UI surfaces only the binary `valid`/`invalid` signal. If you need the `WinReason` (INVALID_TURN / CODE_CRASH / TIMEOUT / FAILED_INIT / POINTS-loss), you must infer it from behavior or reproduce the failure locally.

### Replays 404 for ALL validation matches

Clicking the replay icon for a validation match opens `/match/<uuid>` which returns "Match Not Found", regardless of win or loss. We do NOT know if replays work for scrimmage vs reference bots — the scrimmage I started was still RUNNING at shutdown.

---

## 4. Activation (setting Current)

On `/submissions`, each row has a checkbox in the **Current** column. To activate:

1. Click the checkbox for the row you want active. (Use the `ref` from `read_page`; clicking fires the React handler cleanly.)
2. A confirmation modal appears:
   > **Are you sure?** This will change your current submission. [Yes]
3. Click Yes.
4. The row visually highlights yellow; `aria-checked="true"` on that row's checkbox; others remain `false`.

Only ONE submission can be current at a time. Re-activating a different row silently un-currents the previous one. There's NO "deactivate all" option — to have zero current submissions, you'd have to delete them (destructive, don't).

The Team page header changes: `Submit Bot` button (no active submission) → `View Submission` link (has active submission).

---

## 5. Scrimmage vs a specific opponent

This is subtle — the obvious buttons are misleading.

- **`Self Scrimmage`** (team page, yellow button) → opens a modal titled "Scrimmage — Submit a scrimmage against yourself". This is your-current vs your-current. NOT what you want for George/Albert/Carrie tests.
- **Opponent... filter textbox** (team page Match History) → this is a filter over past matches, not a scrimmage-start control.
- **Leaderboard row's crossed-swords icon** (right column) → THIS is the per-opponent scrimmage trigger.

### Flow for scrimmaging vs George (#150 at time of writing):

1. `GET /compete/cs3600_sp2026/leaderboard`.
2. Find George's row — rank-sorted, around #150, ELO ~1147, quote "Beat George for at least a 70%".
3. Click the **crossed-swords scrimmage icon** on the far right of that row. (`find` with query "crossed swords scrimmage icon button on George's row" returns the right ref, but the visible Quote-column button is a decoy that only highlights the row.)
4. Modal: "Scrimmage — Submit a scrimmage against an opponent"
   - Select Side: Team A | Team B (A = Player A = first, B = second)
   - Number of Scrimmages: 1 (default)
   - Cloudflare Turnstile
   - Cancel / Submit
5. Click Submit. Toast: "Successfully submitted 1 scrimmage".
6. Match History adds a row: `<opponent> — RUNNING — <our current submission .zip> — scrimmage — <age>`.
7. The match takes NOTICEABLY longer than validation (>4 min observed vs ~20s for validation). Check `/team` periodically; eventually status flips to WON / LOST / TIE.

### Scrimmage budget (CON §F-14)

CON §F-14 caps elective live scrimmages. Validation matches (run automatically after upload) are NOT elective and don't count against the budget. Self-scrimmages likely don't either but I never ran one. Vs-reference-bot and vs-student scrimmages DO count.

---

## 6. FloorBot's failure — open diagnostic thread

FloorBot v1 (`3600-agents/FloorBot/`) passes 100/100 vs Yolanda locally (Windows, `limit_resources=False`) but consistently loses the tournament validation match (2/2 attempts, both `__init__.py`-bearing and single-file zip shapes).

**H7 confirmed:** validation = "win the match", and FloorBot loses to the validator opponent. So the bug is inside FloorBot's `play()` pipeline reacting to the validator's board state.

**Candidates (not yet confirmed, unranked):**

1. FloorBot returns a `Move` that `board.is_valid_move` rejects → auto-loss via `INVALID_TURN`. Suspect: `_best_carpet`, `_best_prime`, `_best_plain` — do they respect all of `is_valid_move`'s constraints? In particular, `is_cell_carpetable` rejects the opponent's cell, and carpet over an opponent-occupied square is the kind of thing `get_valid_moves` *might* enumerate even though `is_valid_move` ultimately rejects. See engine/game/board.py:564-566.
2. FloorBot times out → `TIMEOUT`. Unlikely at p99 = 0.034 ms local, but the tournament sandbox is 1.5× slower (GAME_SPEC §7). Possible pathological case we don't hit locally.
3. FloorBot's `__init__` fails → `FAILED_INIT`. Unlikely — `__init__` is `random.Random(seed)` wrapped in try/except.
4. `CODE_CRASH` — the try/except wrapper in `play()` catches most exceptions and falls back to `random.choice(valid_moves)`. But if the fallback itself crashes, we'd see this.

**Next-step diagnostics:**

- Read `engine/player_process.py` + `engine/gameplay.py` and find where WinReason is set. Add a CLI flag to `run_local_agents.py` that echoes WinReason on loss (currently it only prints summary).
- Reproduce FloorBot loss locally with `limit_resources=True` on a Linux machine (WSL should work). Seccomp/UID-drop may or may not matter — try both.
- Stub FloorBot to always return `Move.search((0, 0))` (always-valid search move) and re-upload. If THAT passes validation, FloorBot's bug is in the move-choice path; if it fails, something deeper is wrong.
- The minimal fix may be: in `_best_carpet`/`_best_prime`/`_best_plain`, before returning a Move, call `board.is_valid_move(move)` and skip if False. Current code trusts `get_valid_moves()` enumeration.

Task #24 is already in the backlog for this.

---

## 7. Hypothesis-space graveyard (so you don't re-explore)

| # | Hypothesis                                                          | Verdict                                             | How we ruled it out                                                       |
|---|---------------------------------------------------------------------|-----------------------------------------------------|---------------------------------------------------------------------------|
| H1| FloorBot just lost the validation match on merits                   | Essentially confirmed (H7)                          | Yolanda win → validation IS a win-the-match gate                          |
| H2| `FloorBot/__init__.py`'s `from .agent import PlayerAgent` re-export | **Refuted** (LIVE-002)                              | Re-uploading without `__init__.py` still failed                           |
| H3| Seccomp / sandbox kill on import or init                            | **Refuted** (LIVE-003)                              | Yolanda uses a strict subset of FloorBot's imports and passed             |
| H4| Tournament-sandbox-only bug unrelated to imports                    | Possible but specific to FloorBot                   | Yolanda passing means it's not generic                                    |
| H5| FloorBot returns invalid Move on some edge-case board state         | Still plausible, leading candidate                  | Untested — would need local sandbox repro                                 |
| H6| Opponent-specific exploitation of FloorBot's determinism            | Possible but untestable without validator identity  | Validator's identity is not surfaced in UI                                |
| H7| Validation = "win the match", LOSS → invalid                        | **Confirmed** (LIVE-003)                            | Yolanda WON validation → valid; FloorBot LOST → invalid                  |

Don't re-run experiments to test H1–H3 or H7. They're settled.

---

## 8. Safety guardrails we held (keep holding)

These came from team-lead and are our standing policy:

- **Never overwrite the partner's submission.** Before any upload, check the Submissions table for a non-zero number of rows authored by `apatel3111`. At my shutdown, the partner has not yet uploaded anything.
- **Never delete an invalid submission row.** The red trash icon next to each row presumably works, but we leave `invalid` rows as diagnostic evidence. No clicks.
- **Never leave the team, edit team membership, or change team visibility.** `Leave Team` (red button) and `Edit Team` are untouched.
- **One scrimmage per task authorization.** Per CON §F-14. Team-lead authorizes; you don't self-scrimmage for exploration.
- **Never click destructive modal language.** "This will change your current submission" is benign (team-lead explicitly vetted). If you see "delete", "remove permanently", "leave team", "this cannot be undone" — STOP and report to team-lead.

---

## 9. Tools you'll reach for / tools that fail

### Use these

| Purpose                       | Tool                                                                       |
|-------------------------------|-----------------------------------------------------------------------------|
| See what's on the page        | `mcp__claude-in-chrome__read_page` (filter "interactive" is best for clicks) |
| Text of the current view      | `mcp__claude-in-chrome__get_page_text`                                      |
| Find an element by description| `mcp__claude-in-chrome__find`                                               |
| Visual verification           | `mcp__claude-in-chrome__computer` with `action: "screenshot"`               |
| Click / hover / type / wait   | `mcp__claude-in-chrome__computer`                                           |
| Scroll to element             | `mcp__claude-in-chrome__computer` with `action: "scroll_to"` + `ref`       |
| DOM state introspection       | `mcp__claude-in-chrome__javascript_tool`                                    |
| File upload (THE workaround)  | `mcp__claude-in-chrome__javascript_tool` with base64 File-injection         |

### These don't work for this site / workflow

| Tool / approach                                             | Why not                                                                                 |
|-------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `mcp__claude-in-chrome__upload_image` to upload a zip       | Accepts screenshot IDs only; no arbitrary-file path                                      |
| `WebFetch` on bytefight.org APIs                            | CORS-blocked from the JS context; and the API is session-authenticated                    |
| Reading match replays for validation matches                | `/match/<uuid>` returns "Match Not Found" for all validation matches                     |
| Clicking `Self Scrimmage` to get a vs-George scrimmage      | That's a vs-yourself flow; use leaderboard row icons instead                             |
| Fetching match IDs from the DOM before any click            | React doesn't render match UUIDs into the DOM until you click the replay button; scrape via JS looking at the post-click network tab, or just scan `innerHTML` for a UUID regex |
| Using `read_console_messages` or `read_network_requests` to see why an upload failed | Network tracking starts only *after* you call the tool. Call it early if you want to capture an upload's POST. |

---

## 10. Tool snippet library

### A. Verify current submission state
```javascript
(() => {
  const cbs = Array.from(document.querySelectorAll('table button[role="checkbox"]'));
  return JSON.stringify(cbs.map(cb => ({
    checked: cb.getAttribute('aria-checked'),
    rowText: cb.closest('tr') && cb.closest('tr').textContent.slice(0, 100)
  })));
})()
```

### B. Confirm modal checkbox state before clicking Upload
```javascript
(() => {
  const dialog = document.querySelector('[role="dialog"]');
  const input = document.querySelector('input[type="file"]#submission');
  const cbs = dialog ? Array.from(dialog.querySelectorAll('button[role="checkbox"]')) : [];
  return JSON.stringify({
    dialogOpen: !!dialog,
    fileCount: input && input.files.length,
    fileName: input && input.files[0] && input.files[0].name,
    fileSize: input && input.files[0] && input.files[0].size,
    setAsCurrentChecked: cbs.length && cbs[0].getAttribute('aria-checked')
  });
})()
```

### C. Inject a zip into the file input
```javascript
(() => {
  const b64 = "<paste base64>";
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  const file = new File([bytes], "MyBot.zip", {type: "application/zip"});
  const input = document.querySelector('input[type="file"]#submission');
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
  input.dispatchEvent(new Event('change', {bubbles: true}));
  input.dispatchEvent(new Event('input', {bubbles: true}));
  return JSON.stringify({files: input.files.length, name: input.files[0].name, size: input.files[0].size});
})()
```

### D. Find all match UUIDs currently on the team page
```javascript
(() => {
  const uuids = new Set();
  const html = document.body.innerHTML;
  const re = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g;
  let m;
  while ((m = re.exec(html))) uuids.add(m[0]);
  return JSON.stringify(Array.from(uuids));
})()
// Team UUID = 81513423-e93e-4fe5-8a2f-cc0423ccb953 (ours).
// Others are match UUIDs.
```

---

## 11. What the successor should do first

Priority-ordered, assuming the original task #12 intent (have a 70% floor active) is what you inherit:

1. **Poll `/team`** for the status of the Yolanda-vs-George scrimmage I submitted at ~2026-04-17 00:22 EDT. Record the outcome in LIVE_UPLOAD_004.md or a follow-up file.
2. **Check `/submissions`** — confirm Yolanda is still Current. If not, ask team-lead.
3. **Check `/team` for any partner submission**. If `apatel3111` has uploaded, coordinate before your next upload.
4. **Triage FloorBot locally** (task #24). The most productive line of attack: reproduce in a Linux environment with `limit_resources=True` and instrument `WinReason` in the match logs.
5. **When RattleBot is ready**, upload it. Expect the same 20s validation match. If it WINS, activate it (1 click) to displace Yolanda. RattleBot doing multiple imports is FINE — bytefight doesn't reject `__init__.py`-bearing zips.
6. **Before the deadline**, make sure whatever is Current at 2026-04-19 23:59 is the bot we want graded.

---

## 12. Final transcript for rotation

- Active submission: **Yolanda_probe.zip** (✅ valid, ✅ current). One checkbox click saved us from landing on "no active submission" at deadline.
- FloorBot: failing on tournament, triage open (task #24), local 100/100 vs Yolanda.
- Partner: silent so far. No overwrite risks.
- Tournament sandbox: confirmed fine.
- Budget: one elective scrimmage consumed (Yolanda vs George, still running at shutdown).
- Outstanding chase: final George-scrimmage outcome.

Successor, when you take this on: read sections §0, §2, §3, §9 (tool list), §11 (priorities). Everything else is reference. Good luck.
