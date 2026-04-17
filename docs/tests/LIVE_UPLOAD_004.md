# LIVE_UPLOAD_004 — Yolanda activation + George scrimmage

**Owner:** tester-live
**Date:** 2026-04-17
**Status:** Yolanda_probe.zip is now the ACTIVE submission for Team 15. Scrimmage vs George was submitted and was still RUNNING at agent shutdown time (4+ minutes elapsed). No partner submission has appeared.

---

## 1. Activation

**Before:** 3 submissions present, all "Current" checkboxes unchecked.
- Yolanda_probe.zip — valid, Current ☐
- FloorBot.zip (no `__init__`) — invalid, Current ☐
- FloorBot.zip (with `__init__`) — invalid, Current ☐

**Action:** On `/submissions`, clicked the Current checkbox for Yolanda's row.

**Confirmation modal appeared** — NOT destructive language:
> **Are you sure?**
> This will change your current submission.
> [Yes]  [X close]

Clicked `Yes`. Expected per the UX of activating a submission. No further prompts.

**After (verified both visually and via `aria-checked`):**
- Yolanda_probe.zip — valid, **Current ☑** (row visibly highlighted yellow)
- FloorBot.zip × 2 — invalid, Current ☐ (unchanged)

Secondary confirmation: the Team-page header changed from "Submit Bot" button (appears when no current submission) to "**View Submission**" link (appears when one is current).

**Partner check:** Team 15 still has 2 members (apatel3111, Rjav); no partner-authored submission has appeared. No overwrite.

---

## 2. Scrimmage vs George

### How to scrimmage vs a reference bot (documented for successor)

The **Self Scrimmage** button on the Team page opens a "Submit a scrimmage against *yourself*" modal — NOT vs an opponent. That's a dead end for this task.

The correct path is **Leaderboard → George's row → Scrimmage icon** (crossed-swords icon at the rightmost column). George is listed on the leaderboard at **rank #150, ELO 1147, quote "Beat George for at least a 70%"**. (CLAUDE.md §5 describes George as the ≥70% floor bot.)

The leaderboard column schema is: `Rank | Elo | Team | Quote | Scrimmage`. The Scrimmage column renders a crossed-swords icon button (`aria-label` = none, button text = empty) per row. There's also a clickable button rendering the Quote text — clicking *that* just highlights the row, not opens the modal.

### Scrimmage modal

Clicked George's crossed-swords scrimmage icon. Modal appeared:

- **Heading:** "Scrimmage — Submit a scrimmage against an opponent"
- **Select Side:** Team A (default, yellow-highlighted) | Team B
- **Number of Scrimmages:** 1 (default)
- Cloudflare Turnstile: Success!
- Cancel / Submit

Kept defaults (Team A, 1 scrimmage). Clicked Submit.

**Toast:** "Successfully submitted 1 scrimmage" (green).

### Scrimmage result

Timestamp: ~2026-04-17 00:22 EDT.

Match History added a new row: **George — RUNNING — Yolanda_probe.zip — scrimmage — 4m (at shutdown)**.

The scrimmage was STILL RUNNING at the time team-lead issued the rotation/shutdown request. Scrimmage matches take noticeably longer than validation matches (observed duration: 4+ minutes still running, vs. ~20s for validation). Plausible reasons:
- Validation matches are against a weak/fast opponent.
- Scrimmage vs George involves more deliberate turns (George plays greedy prime+carpet with opportunistic rat-search per CLAUDE.md §5).
- Queue lag — the scrimmage may be waiting for compute.

**Successor action:** navigate to `/team` to check the final outcome. Expected: eventual terminal state of WIN / LOST / TIE, and an ELO delta on the ELO history chart. Current ELO is provisional **1500** ("#?" rank on the leaderboard because we haven't played enough ranked matches yet).

### Expected outcome (prior)

Yolanda is a random mover. George has no lookahead but greedily extends primes and rolls carpets plus opportunistic rat-search. Expected win rate for Yolanda vs George: **very low** (probably <10%). This scrimmage is more about measuring the harness than getting an encouraging result. The Yolanda-as-insurance plan assumes Yolanda beats **nothing but other random bots** — its ELO floor is the validator's ELO (whatever that is). Per the leaderboard, teams below rank #150 (George) are where Yolanda would plausibly rank. Grade implication: Yolanda-as-submission probably lands **below 70%** in the final tournament. So this submission is a LAST RESORT, not a goal.

### UI learning: scrimmage budget

The task docs (CON §F-14) cap live scrimmages at a small number. This task used **1 scrimmage** (George) as explicitly authorized by team-lead. The FloorBot validation matches and Yolanda's validation match are **automatic** and don't count against this budget (they're run server-side, not elective).

---

## 3. Current state of the Submissions table (snapshot at shutdown)

| Current | Validity | File                          | Date                      |
|---------|----------|-------------------------------|---------------------------|
| **☑**   | valid    | Yolanda_probe.zip             | 4/16/2026, 9:40:50 PM EDT |
| ☐       | invalid  | FloorBot.zip (no `__init__`)  | 4/16/2026, 9:27:32 PM EDT |
| ☐       | invalid  | FloorBot.zip (with `__init__`)| 4/16/2026, 9:12:07 PM EDT |

Storage: 0.0 MB of 200 MB. No partner submission. Team members unchanged.

---

## 4. Team record

- Record: `0W - 0D - 0L` on the ranked table (validation + scrimmage runs don't populate the record).
- ELO: provisional **1500**, `#?` rank on leaderboard.
- ELO history chart: empty at shutdown (scrimmage still pending).
- Matchmaking cycle: next at 2026-04-17 00:00 EDT (about 1h35m from shutdown).

---

## 5. Deliverables status vs task #12

| Deliverable                                                 | Status                                 |
|-------------------------------------------------------------|----------------------------------------|
| Build a FloorBot.zip                                        | DONE (2 variants)                      |
| Upload to bytefight.org                                     | DONE (3 uploads)                       |
| Set active submission                                       | **DONE** — Yolanda, not FloorBot.      |
| One scrimmage vs George                                     | SUBMITTED (pending outcome at shutdown) |
| LIVE_UPLOAD_001/002/003/004.md                              | DONE                                   |

Task #12's primary intent — "have SOMETHING valid active on bytefight" — is **achieved for the first time** via Yolanda-as-insurance. FloorBot is not fixed; that is now a separate task (#24 "Triage FloorBot validation bug — reproduce locally").

---

## 6. Scrimmage-budget accounting (CON §F-14)

| When                    | What                                          | §F-14 cost |
|-------------------------|-----------------------------------------------|------------|
| 2026-04-16 21:12 EDT    | FloorBot v1 upload → auto-validation LOST     | 0 (auto)   |
| 2026-04-16 21:27 EDT    | FloorBot no-init upload → auto-validation LOST| 0 (auto)   |
| 2026-04-16 21:40 EDT    | Yolanda probe upload → auto-validation WON    | 0 (auto)   |
| 2026-04-17 00:22 EDT    | Yolanda vs George scrimmage SUBMITTED         | **1**      |

Total elective scrimmages used by tester-live: **1**. Budget remaining per original CON §F-14 assumption: depends on team-lead's bookkeeping. The two FloorBot validation LOSSES and the Yolanda validation WIN are not elective scrimmages.

---

## Successor: follow-up checklist

1. **Check the George scrimmage outcome** at https://bytefight.org/compete/cs3600_sp2026/team — it should have transitioned from `RUNNING` to WON/LOST/TIE (most likely LOST, given Yolanda is random).
2. **Note the ELO delta** on the ELO History chart. First real ELO data point for Team 15.
3. **The replay URL** will be the button next to the result row. Check if it works for scrimmages vs George (we saw replays 404 for all validation matches; unclear whether scrimmage replays are likewise hidden).
4. **Do NOT delete the invalid FloorBot rows** — they remain diagnostic evidence and team-lead ruled them protected.
5. **Read `docs/state/HANDOFF_TESTER_LIVE.md`** for the full UI / flow / hypothesis knowledge transfer.
