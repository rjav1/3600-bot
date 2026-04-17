# LIVE_UPLOAD_001 — FloorBot upload attempt (BLOCKED)

**Owner:** tester-live
**Date:** 2026-04-16
**Status:** BLOCKED — account is not on a team; no submission UI is reachable until a team exists. Paused for team-lead guidance per instructions ("PAUSE and ping team-lead rather than guessing").

---

## Summary

- FloorBot.zip was built successfully and verified (see §Zip below).
- Chrome MCP confirmed login at bytefight.org.
- Profile email is **rjavid3@gatech.edu** (username **Rjav**), not rahiljav@gmail.com as noted in the task briefing / CLAUDE.md. The gatech.edu email is the authoritative Banner/Canvas account for CS3600; rahiljav@gmail.com appears to be the user's personal email, not the one tied to the ByteFight account.
- The CS3600 sp2026 competition sidebar shows **Create/Join Team** but no active team. Profile page shows "Team & Competition History: Coming soon...". Therefore the account has no team and no active submission.
- No "Submit" / "Upload" UI is reachable on any of the visible pages (Overview, Leaderboard, Resources, Schedule, Results, Match Queue, Create/Join Team). Upload presumably lives on the team page, which does not exist yet.

**No team was created. No zip was uploaded. No scrimmage was played.** All three require team-lead approval first because creating a team (a) modifies account state publicly and (b) locks in a team name visible on the leaderboard.

---

## Zip build — verified correct

Location: `C:\Users\rahil\AppData\Local\Temp\FloorBot.zip` (not in repo)

`python -m zipfile -l`:

```
File Name                                      Modified             Size
FloorBot/agent.py                              2026-04-16 19:57:36         7269
FloorBot/__init__.py                           2026-04-16 19:57:04           58
```

Depth-1 layout `FloorBot/agent.py` + `FloorBot/__init__.py` — matches CLAUDE.md §6 spec. Tests directory and `__pycache__` (cpython-313 bytecode) were deliberately excluded — they'd be regenerated on import anyway, and tournament runs Python 3.12.

Total zip size: ~3 KB, well under the 200 MB limit.

---

## bytefight.org UI observations (for future automations)

Layout of the tournament site as of 2026-04-16:

- **Top nav:** ByteFight logo, HOME, COMPETE, DEVS, PAST YEARS, FAQ, FEATURE REQUEST, Instagram, Discord, User menu (icon).
- **User menu:** Profile, Log out. Click the user icon in the top-right to reveal.
- **Profile page** (`/profile`): shows Username, Email, Account Created date, Edit Profile, Reset Password. "Team & Competition History" section exists but says "Coming soon..." (even for users without teams — unclear if it populates after joining one).
- **Competition sidebar** (`/compete/cs3600_sp2026`):
  - Overview (rules)
  - Leaderboard
  - Resources
  - Schedule
  - Results
  - Match Queue
  - Create/Join Team
  - Next Matchmaking Cycle countdown (e.g. "03:33:10, Apr 17 2026 12:00 AM EDT")
- **No Submit / Upload link is visible in the sidebar** for a user who is not on a team. The upload UI almost certainly lives on the individual team page (`/compete/cs3600_sp2026/team/<id>` or similar) once a team exists.
- **Create Team form:** Team Name input + "Display team members publicly (you can always change this later)" checkbox (default: checked/yellow) + Create Team button.
- **Join Team form:** Team Code input + Join Team button. Hint text: "Ask a team member for the code found at the top of their team page."

Implication: **once a team is created, we should look for a team-page link in the sidebar or under /compete/cs3600_sp2026/team/ for the upload element.**

---

## Blocker and next-step question for team-lead

Should I:

1. **Create a team named e.g. "FloorBot" or "rahil-solo"** under the current account (Rjav / rjavid3@gatech.edu)? This is public (the team name appears on the leaderboard). Default visibility is "display team members publicly" — I would leave that as-is unless told otherwise. Partner-submission protocol (CONTRARIAN_SCOPE §B-7 / §E-6) is unresolved: the partner may already have a team or expect a specific team name.
2. **Join an existing team?** If the partner has already created a team, I need the team code to join. No evidence of an existing team in the current account.
3. **Wait entirely?** If team creation is gated on the partner or on a course announcement, I should pause the upload workflow until that's resolved.

Without explicit authorization for option 1 or 2, I am stopping here per the Step-2 guardrail ("If NOT logged in, STOP" — the spirit applies: if the account is in an unexpected state, don't guess).

---

## Followup actions (when unblocked)

Next time we upload, we should:

- Expect the upload element to live on the team page, not the competition root.
- Have the team name decided in advance (it's public) and have the partner coordination sorted.
- The CS3600 account email is `rjavid3@gatech.edu` — note this in future runbooks. CLAUDE.md's mention of `rahiljav@gmail.com` is out-of-date or referred to a different service.
- Batch uploads per CON §F-14 — this first upload counts as the one-time baseline.

---

## Deferred deliverables

- Submission ID / version: N/A (no upload occurred).
- Scrimmage match details: N/A (no scrimmage occurred — would have exceeded §F-14 budget anyway with no live submission to scrimmage against).
- ELO movement: N/A.
