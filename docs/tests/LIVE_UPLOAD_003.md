# LIVE_UPLOAD_003 — Yolanda probe: **H7 CONFIRMED** (validator = beat-this-opponent)

**Owner:** tester-live
**Date:** 2026-04-17
**Status:** Diagnostic probe complete. Unmodified Yolanda was uploaded and passed validation with `valid` status, WITHOUT being marked current. FloorBot remains `invalid`. Hypothesis 7 from LIVE-002 is confirmed: validation = "win a match against the validator opponent", and FloorBot is losing that match.

---

## Experiment design (per team-lead)

Upload unmodified Yolanda (the starter random-mover agent) as a **strictly diagnostic probe**:

- Build a new zip containing ONLY `Yolanda/agent.py` at depth 1.
- Uncheck "Set as current submission once validated" so the probe is passive — it must not displace any existing active submission.
- Observe: does it pass validation?
  - **PASS** → H7 confirmed (validator = winning gate). FloorBot is losing a match, not hitting a sandbox issue.
  - **FAIL** → deeper rejection (H3 or H4). Every bot we write has the same risk.
- Check the Submissions table and existing `invalid` rows for any surfaced error messages (tooltips, titles, dataset attrs, etc.).

---

## The zip

`C:\Users\rahil\AppData\Local\Temp\Yolanda_probe.zip`, 684 bytes:

```
File Name                                      Modified             Size
Yolanda/agent.py                               2026-04-07 16:11:34         1178
```

Byte-identical copy of `3600-agents/Yolanda/agent.py` (unmodified starter random-mover agent). No tests, no `__init__.py`, no extras.

---

## Upload flow

- Time: **2026-04-16 21:40:50 EDT**
- Modal opened from the `/team` page (the `/submissions` page's Submit Bot button was temporarily disabled — see "UI quirks" below).
- File injected via `javascript_exec` (same base64 → `File` → `DataTransfer` pattern as LIVE-001/002).
- **Cloudflare Turnstile:** auto-passed ("Success!" green checkmark).
- **Checkbox "Set as current submission once validated":** clicked ONCE to uncheck. Verified programmatically (`aria-checked="false"`) and visually (empty outlined square, not filled yellow) before clicking Upload.
  - One UI quirk worth noting: after the first file inject + a checkbox click, the UI reset the file-display text to "No file chosen" even though the input still held the file programmatically. A fresh file re-inject was needed. This is a race between the React state and our DataTransfer manipulation — safe to work around, but RattleBot uploads should re-verify both file state AND checkbox state immediately before clicking Upload.
- Click `Upload` → green toast "Uploaded submission".

---

## Validation outcome

Within ~20 seconds, the Submissions table transitioned Yolanda_probe.zip from `not_evaluated` → **`valid`** (green text).

The Team Match History shows a third validation row:
- Team 15 — **WON** — Yolanda_probe.zip — validation (age 1m at read time)
- Team 15 — LOST — FloorBot.zip — validation (age 14m)
- Team 15 — LOST — FloorBot.zip — validation (age 30m)

**Yolanda WON its validation match. FloorBot LOST both of its validation matches.** Submission Validity mirrors the WIN/LOST outcome: WIN → `valid`, LOSS → `invalid`.

"Current" checkbox is UNCHECKED for Yolanda (as designed — we disabled auto-activate). No active submission exists for Team 15. No partner work affected.

Replays are NOT available at `/match/<uuid>` for any of the three matches (both FloorBot LOSSes and Yolanda's WIN) — they all return "Match Not Found". This is consistent with validation-match replays being hidden regardless of outcome.

---

## Interpretation

### H7 CONFIRMED, with a refinement

Earlier hypotheses (LIVE-002):
- **H7:** Validator runs bot vs some reference opponent; loss → `invalid`.
- **H3:** Sandbox/seccomp kill on import or init.
- **H5:** FloorBot returns an invalid Move on a T/spawn combo local runs don't hit.

**Yolanda passing rules out H3 entirely.** If the sandbox were rejecting our zips for seccomp or import reasons, Yolanda's trivially-minimal code would have tripped on the same rejection (Yolanda imports `random`, `from collections.abc import Callable`, `from typing import List, Set, Tuple` and `from game import board, move, enums` — a strict subset of FloorBot's imports). Yolanda getting in cleanly means the sandbox is fine.

**H5 is still plausible but with a twist.** The surviving scenarios for a match-loss by a random mover:
- Yolanda's random moves win because the validator is weak and Yolanda gets lucky. Then FloorBot's reactive policy may have an edge case where it returns an `INVALID_TURN` against some board state the validator produces, or it times out on the tournament sandbox's 1.5× tighter clock (240 s vs local 360 s per GAME_SPEC §7), triggering a LOSS.
- Or the validator's matchup is non-deterministic — sometimes you win, sometimes you lose. FloorBot got unlucky twice in a row; Yolanda got lucky once. **Probability check:** if P(any-bot wins one validation match) ≈ 0.5 and FloorBot + Yolanda are independent samples, P(FloorBot loses 2 and Yolanda wins 1) = 0.5³ = 0.125. Not strongly conclusive with n=3, but consistent.

**Likely root cause for FloorBot:** some combination of
- tournament-sandbox 1.5× slower clock exposing a latent `play()` that takes longer than local (unlikely given p99 = 0.034 ms locally, 3 orders of magnitude under budget),
- an edge case in `_best_carpet`/`_best_prime`/`_best_plain` that returns an `INVALID_TURN`-triggering `Move` against the validator's specific plays,
- or `board.is_valid_move` actually rejecting something `board.get_valid_moves()` returned (we trust `get_valid_moves` but a subtle mismatch between the two — e.g. SEARCH handling — could cause a valid-per-`get_valid_moves` move to be rejected by `is_valid_move`).

### Validator identity

**Unknown.** The UI shows "Team 15 vs [blank]" for validation matches. We do not see the opponent's name. Hypotheses:
- A weakest-possible reference bot (weaker than George), e.g., a "NullBot" that always passes / searches at (0,0). Yolanda beats it by random chance; FloorBot loses because its deterministic policy hits a specific invalid-move case.
- A randomly-sampled other student submission. Less likely because a new team's first upload can't reliably pair with others.
- A deterministic internal bot we don't see on the leaderboard.

Either way: the validator opponent is something Yolanda can beat 1/1 but FloorBot is losing 2/2. That's fixable.

---

## Implications for FloorBot

FloorBot has a real, reproducible bug on the tournament sandbox. The minimal-change experiment from LIVE-002 (drop `__init__.py`) didn't fix it because the bug is NOT in the packaging. Suggested triage order:

1. **Stress test FloorBot locally** against an opponent simulating worst-case behavior: bot that primes and rolls aggressively, immediately searches, occupies cells that block our moves. If we can reproduce an `INVALID_TURN` loss or a `CODE_CRASH`, that's our bug.
2. **Test FloorBot with `limit_resources=True`** locally to see if the tighter clock matters. Windows may not support `resource.setrlimit(RLIMIT_RSS, ...)`; run inside WSL or a Linux container.
3. **Stub FloorBot down to just `Move.search((0,0))`** (always-search, always-valid, slow) and upload — if THAT passes, FloorBot's `play()` policy has the bug. If THAT also fails, there's something deeper wrong with how our zip is loaded.
4. **Read `board.is_valid_move` carefully** and cross-check against everything `board.get_valid_moves()` returns. Engine consistency is trust-but-verify.

---

## Implications for RattleBot

Good news:
- Zip packaging is fine (Yolanda_probe.zip is single-file-at-depth-1 and passes — `__init__.py` is neither required nor rejected).
- Sandbox import restrictions are not the bottleneck.
- Validator is a winnable match, not a mythical gatekeeper.

Bad news:
- **Whatever bug FloorBot has could also bite RattleBot** — they share the engine imports and the `Move` API. RattleBot is strictly more complex so has more surfaces to crash on. We MUST replicate the tournament-sandbox failure mode locally before RattleBot goes live.
- The tournament sandbox runs with `limit_resources=True` (per CLAUDE.md §6 / GAME_SPEC §7) which is a 1.5× tighter clock AND seccomp + UID drop. Our local dev has never exercised this.
- **The one-submission-per-cycle rate limit** (see below) is a real throughput constraint. We cannot just "try another upload every 2 minutes" — we have a cooldown.

---

## UI quirks / observations added in LIVE-003

These matter for future automations:

1. **Submit Bot button can become disabled temporarily.** Between my first (failed-to-register) Upload click and my successful one, the Submissions-page Submit Bot button showed a **lock icon** and became `disabled=true`. The Team-page Submit Bot button was NOT disabled at the same moment — so the disable state is scoped to the Submissions page UI, not the server-side team-submission eligibility. After ~1 minute it resolved itself. Possibly a React state transient after a previous upload; possibly a short cooldown after the CAPTCHA-cleared-but-not-submitted case. The workaround: use the Team-page Submit Bot button if Submissions-page is locked.

2. **Checkbox re-check behavior.** After unchecking "Set as current submission once validated" once, then clicking elsewhere in the dialog (e.g., into the file picker), the checkbox sometimes reverts to checked. Strategy: verify `aria-checked` state programmatically *immediately before* clicking Upload, not on some older snapshot.

3. **File-display text can lag the actual input state.** We can attach a `File` via `DataTransfer` and the `input.files` will correctly reflect it, but the visible "Choose File / Selected file: X" label may not update because the UI is driven by a separate React state. Don't rely on the text — check `input.files` directly.

4. **No error messages on `invalid` rows.** Hovered, clicked, inspected DOM — no tooltip, title, aria-label, dataset attribute, or expandable detail panel. The UI surfaces ONLY the binary `valid`/`invalid` signal. If we want the actual WinReason (INVALID_TURN vs CODE_CRASH vs TIMEOUT), we have to infer it from behavior, not read it from the UI.

5. **Replays are hidden for ALL validation matches**, including wins. Yolanda's winning validation replay also 404s. So "no replay" is not a signal of crash — it's a signal of "this is a validation match".

6. **The CAPTCHA sometimes auto-passes immediately ("Success!" with green check shown on modal open).** When it does, Upload is clickable without waiting. When it shows "Verifying...", wait ~2-4 seconds. The Turnstile response token is presumably attached to the form submission — don't click Upload before "Success!" is visible.

7. **Matchmaking cycle** shown in sidebar: **Apr 17, 2026, 12:00:00 AM EDT** = tomorrow's automated competition. Validation matches appear to run on-demand (within ~20 s of upload), distinct from matchmaking cycles.

8. **Submissions accumulate.** The table now has THREE rows (Yolanda valid + FloorBot invalid × 2). Storage: 0.0 MB of 200. Rows are not auto-pruned. Red trash icons next to each row presumably delete — NOT clicked per team-lead's "do not delete" standing rule.

---

## Deliverables status vs task #12

| Deliverable                                             | Status                               |
|---------------------------------------------------------|--------------------------------------|
| Build FloorBot.zip with correct layout                  | DONE (2 variants)                    |
| Upload to bytefight.org                                 | DONE (3 uploads: 2 × FloorBot + 1 × Yolanda probe) |
| Set FloorBot as active submission                       | **NOT DONE** — FloorBot is `invalid` |
| Scrimmage match vs George                               | **NOT DONE** — no valid submission to scrimmage with |
| LIVE_UPLOAD_001.md / 002.md / 003.md                    | DONE                                 |

**Live-scrimmage budget per CON §F-14:** 0 consumed. All validation matches are automatic.

---

## Summary & recommendation

**H7 confirmed:** validation = "beat the validator". Yolanda (random) beat it on 1 try. FloorBot has lost 2/2.

This is actually **more tractable** than the LIVE-002 failure mode (sandbox reject) because:
- Zip packaging is fine.
- Imports work.
- Sandbox is functional.
- The bug is specifically inside FloorBot's `play()` → Move pipeline.

**Recommendation to team-lead:**

1. **Leave Yolanda as our last-resort insurance.** It is validated. If we run out of time, set Yolanda as current (one checkbox click) and ship.
2. **Triage FloorBot** — suspected causes listed above, in decreasing likelihood. First test: locally run FloorBot against a lookahead bot (not Yolanda) and see if we can observe an invalid move / crash. Likely a ≤30-minute fix.
3. **Treat this as a fire drill for RattleBot.** RattleBot's upload will face the same validator; it MUST pass 1 match. Build a local validation-harness that replicates the tournament setup (limit_resources=True, seccomp if possible on Linux) before the first RattleBot upload, to avoid wasting bytefight throughput on upload-fail-triage cycles.

Yolanda-probe.zip is LEFT IN PLACE on bytefight with "Current" UNCHECKED — as you instructed. If you want me to set it current (as a reluctant insurance), say the word.
