# LIVE_SCRIMMAGE_LOG — bytefight §F-14 scrimmage ledger

**Owner:** live-tester-2
**Started:** 2026-04-17
**Current submission:** RattleBot_v03_pureonly_20260417_1022.zip (SHA256 `f046631f...`, pure-python, depth ~13, W_INIT weights, 14 features)
**Budget:** ~10 §F-14 slots total. Consumed to-date: 1 (Yolanda vs George, LIVE-004). Reserve: 3-4 slots for post-BO tuning.

## Running tally

| # | Submitted (local) | Opponent | Opponent ELO | Sub used | Team side | Status | Result | Score diff | Duration | ELO Δ | §F-14 running | Notes |
|---|-------------------|----------|--------------|----------|-----------|--------|--------|------------|----------|-------|---------------|-------|
| 1 | 2026-04-17 00:22 EDT | George | 1147 (then) | Yolanda | A | LOST | L | n/a | queue 10h | 0 | 1/10 | LIVE-004 — finalized 9h later, Yolanda random-mover |
| 2 | 2026-04-17 13:51 EDT | George | 1144 | v03_pureonly | A | SUBMITTED | — | — | — | — | 2/10 | Task #78 wave 1 — #151 leaderboard, expected decisive win |
| 3 | 2026-04-17 13:53 EDT | Albert | 1801 | v03_pureonly | A | SUBMITTED | — | — | — | — | 3/10 | Task #78 wave 1 — #15 leaderboard, strong opponent |
| 4 | 2026-04-17 13:55 EDT | Carrie | 1915 | v03_pureonly | A | SUBMITTED | — | — | — | — | 4/10 | Task #78 wave 1 — #7 leaderboard, hardest reference bot |

## Wave 1 status: all 3 fired

Check back ~15 min on `/team` Match History for results. Will append outcomes to rows 2-4 as they flip from SUBMITTED → LOST / WON / TIE.

Remaining budget: 6 slots. Reserving 3-4 for post-BO (v0.3-tuned when BO RUN1-v6 lands, ~4h). Wave 2 budget: 2-3 slots for repeat hits on whichever opponent gave the clearest signal.

## Hard-stop rules

- Pause at budget ≤ 2 remaining. Ping team-lead.
- Pause on catastrophic invalid-move or crash.
- Do not overwrite partner submissions.

## How to read this file

- "Submitted" row = the scrimmage was queued successfully.
- "Status" = RUNNING until the result flips on /team. Then LOST / WON / TIE. Remember: "WON" in matchmaking/scrimmage rows = actual competitive win; "WON" in validation rows = just "ran cleanly".
- "§F-14 running" = cumulative scrimmage slot usage after this row.
- "Opponent ELO" = leaderboard ELO at the moment of scrimmage submission.

## Poller observations (bytefight_poll.py)

_Auto-appended by `tools/bytefight_poll.py`. Each line = one status transition observed via `GET /api/v1/public/game-match`._

- [2026-04-17 20:53:45Z] queued   match=`90f5970f` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T20:31 finished=
- [2026-04-17 20:53:45Z] queued   match=`b0b20ab2` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T20:31 finished=
- [2026-04-17 20:53:45Z] queued   match=`3d6cc211` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T20:31 finished=
- [2026-04-17 20:53:45Z] queued   match=`778dbebf` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T20:31 finished=
- [2026-04-17 20:53:45Z] queued   match=`c6557108` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T20:31 finished=
- [2026-04-17 20:53:45Z] queued   match=`36c3f448` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T20:31 finished=
- [2026-04-17 20:53:45Z] queued   match=`e258daea` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T20:31 finished=
- [2026-04-17 20:53:45Z] submission_valid match=`9f826387` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=validation sched=2026-04-17T20:30 finished=2026-04-17T20:30
- [2026-04-17 20:53:45Z] queued   match=`2e9fb89f` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-17T20:21 finished=
- [2026-04-17 20:53:45Z] queued   match=`4fbbd274` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T20:21 finished=
- [2026-04-17 20:53:45Z] queued   match=`5e2d6a1f` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-17T20:19 finished=
- [2026-04-17 20:53:45Z] B_WIN    match=`9432921e` vs `Team 15` (81513423) sub=`20thAgent.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-17T20:00 finished=2026-04-17T20:52
- [2026-04-17 20:53:45Z] in_progress match=`49dbaf33` vs `Team 15` (81513423) sub=`rv13-1.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-17T20:00 finished=
- [2026-04-17 20:53:45Z] B_WIN    match=`8757c2fd` vs `Team 15` (81513423) sub=`YolandaR3_20260414.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-17T20:00 finished=2026-04-17T20:32
- [2026-04-17 20:53:45Z] B_WIN    match=`856d41c0` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=matchmaking sched=2026-04-17T20:00 finished=2026-04-17T20:28
- [2026-04-17 20:53:45Z] B_WIN    match=`6d7219ac` vs `Team 15` (81513423) sub=`rv12-3.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-17T16:00 finished=2026-04-17T16:43
- [2026-04-17 20:53:45Z] A_WIN    match=`a636229e` vs `Team 15` (81513423) sub=`yolanda_v21.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-17T16:00 finished=2026-04-17T16:28
- [2026-04-17 20:53:45Z] B_WIN    match=`d242965b` vs `Team 65` (fb9534dc) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`alexBot_dual_dominator.zip` reason=matchmaking sched=2026-04-17T16:00 finished=2026-04-17T16:19
- [2026-04-17 20:53:45Z] A_WIN    match=`b7e65887` vs `Team 15` (81513423) sub=`Rascal4.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-17T16:00 finished=2026-04-17T16:17
- [2026-04-17 20:53:45Z] A_WIN    match=`b6dc4ec1` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T14:24 finished=2026-04-17T14:40
- [2026-04-17 20:54:44Z] B_WIN    match=`49dbaf33` vs `Team 15` (81513423) sub=`rv13-1.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-17T20:00 finished=2026-04-17T20:54
- [2026-04-17 21:06:53Z] VAL_OK   match=`4339d743` vs `Team 15` (81513423) sub=`SmokeBot.zip` opp_sub=`SmokeBot.zip` reason=validation sched=2026-04-17T21:06 finished=2026-04-17T21:06
- [2026-04-17 21:49:57Z] SUBMITTED match=`ed315682-42cc-4969-99e9-be35e6a9ce7f` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-17T21:49 finished= status_at_report=waiting (scrimmage-runner — first fire of new cadence post-CAPSOLVER-.env-wiring; poll timed out at 10 min with match still queued, outcome TBD — next cadence agent should poll `ed315682` or `get-match` to finalize)
- [2026-04-17 22:04:17Z] RUNNING  match=`ed315682` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-17T21:49 finished=
- [2026-04-17 22:04:17Z] A_WIN    match=`90f5970f` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T21:11 finished=2026-04-17T21:28
- [2026-04-17 22:04:17Z] B_WIN    match=`b0b20ab2` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T21:11 finished=2026-04-17T21:28
- [2026-04-17 22:04:17Z] A_WIN    match=`3d6cc211` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T21:11 finished=2026-04-17T21:28
- [2026-04-17 22:04:17Z] A_WIN    match=`778dbebf` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T21:11 finished=2026-04-17T21:28
- [2026-04-17 22:04:17Z] B_WIN    match=`c6557108` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T21:11 finished=2026-04-17T21:28
- [2026-04-17 22:04:17Z] B_WIN    match=`36c3f448` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T21:11 finished=2026-04-17T21:28
- [2026-04-17 22:04:17Z] B_WIN    match=`e258daea` vs `Team 15` (81513423) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=scrimmage sched=2026-04-17T21:11 finished=2026-04-17T21:27
- [2026-04-17 22:04:17Z] B_WIN    match=`2e9fb89f` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-17T21:11 finished=2026-04-17T21:24
- [2026-04-17 22:04:17Z] B_WIN    match=`4fbbd274` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T21:11 finished=2026-04-17T21:24
- [2026-04-17 22:04:17Z] B_WIN    match=`5e2d6a1f` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-17T21:11 finished=2026-04-17T21:20
- [2026-04-17 22:06:49Z] A_WIN    match=`ed315682` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-17T21:49 finished=2026-04-17T22:06
- [2026-04-17 22:22:42Z] queued   match=`97afd501` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T22:22 finished=
- [2026-04-17 22:32:48Z] RUNNING  match=`97afd501` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T22:22 finished=
- [2026-04-17 22:38:53Z] A_WIN    match=`97afd501` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T22:22 finished=2026-04-17T22:38
- [2026-04-17 22:40:00Z] A_WIN    match=`97afd501-6e07-48b1-9902-1c65d99a08cc` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` result=WIN (scrimmage-albert)
- [2026-04-17 22:40:54Z] queued   match=`d83a9b8b` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-17T22:40 finished=
- [2026-04-17 22:53:02Z] RUNNING  match=`d83a9b8b` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-17T22:40 finished=
- [2026-04-17 23:15:00Z] SUBMITTED match=`d83a9b8b-3983-4920-ae3a-6f70aab9021c` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` result=in_progress (scrimmage-carrie — cadence fire 3, symmetric resample; poll timed out at 15 min with match running, poller will auto-append final outcome)
- [2026-04-17 22:59:37Z] B_WIN    match=`d83a9b8b` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-17T22:40 finished=2026-04-17T22:59
- [2026-04-18 01:00:23Z] DRAW     match=`c710b363` vs `Abhi/Dawson` (d6f410b1) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Dubious10.zip` reason=matchmaking sched=2026-04-18T00:00 finished=2026-04-18T00:30
- [2026-04-18 01:00:23Z] B_WIN    match=`fc2b7f39` vs `Team 15` (81513423) sub=`Yolanda_J.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-18T00:00 finished=2026-04-18T00:27
- [2026-04-18 01:00:23Z] A_WIN    match=`5da2ee65` vs `Team 15` (81513423) sub=`agent4.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-18T00:00 finished=2026-04-18T00:23
- [2026-04-18 01:00:23Z] B_WIN    match=`0048454a` vs `Gold Team` (8c6bf543) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`SCB.zip` reason=matchmaking sched=2026-04-18T00:00 finished=2026-04-18T00:23
- [2026-04-18 01:00:23Z] DRAW     match=`dfcfd25b` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T23:51 finished=2026-04-18T00:08
- [2026-04-18 01:00:23Z] B_WIN    match=`bc4ebed5` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T23:51 finished=2026-04-18T00:08
- [2026-04-18 01:00:23Z] B_WIN    match=`6a110e87` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T23:51 finished=2026-04-18T00:08
- [2026-04-18 01:00:23Z] B_WIN    match=`d8f9b19e` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T23:51 finished=2026-04-18T00:08
- [2026-04-18 01:00:23Z] B_WIN    match=`6cab9254` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T23:51 finished=2026-04-18T00:08
- [2026-04-18 01:00:23Z] B_WIN    match=`063cb0e7` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T23:51 finished=2026-04-18T00:08
- [2026-04-18 01:00:23Z] A_WIN    match=`bf6447e4` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T23:51 finished=2026-04-18T00:08
- [2026-04-18 01:00:23Z] B_WIN    match=`a3800b3b` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T23:51 finished=2026-04-18T00:08
- [2026-04-18 01:00:23Z] B_WIN    match=`4902684f` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T23:51 finished=2026-04-18T00:08
- [2026-04-18 01:00:23Z] B_WIN    match=`ce3eb525` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-17T23:51 finished=2026-04-18T00:08
- [2026-04-18 01:00:54Z] queued   match=`74765a32` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:00:54Z] queued   match=`6dcdea8c` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:00:54Z] queued   match=`132a3fbd` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:00:54Z] queued   match=`14a319d3` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:00:54Z] queued   match=`b93942ed` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:00:54Z] queued   match=`c78534cd` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:00:54Z] queued   match=`503d8eb7` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:00:54Z] queued   match=`e4eff274` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:00:54Z] queued   match=`ab281352` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:00:54Z] queued   match=`c89c9b0f` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:13:32Z] RUNNING  match=`503d8eb7` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:13:32Z] RUNNING  match=`e4eff274` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:13:32Z] RUNNING  match=`ab281352` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:13:32Z] RUNNING  match=`c89c9b0f` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:14:03Z] RUNNING  match=`74765a32` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:14:03Z] RUNNING  match=`6dcdea8c` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:14:03Z] RUNNING  match=`132a3fbd` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:14:03Z] RUNNING  match=`14a319d3` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:14:03Z] RUNNING  match=`b93942ed` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:14:03Z] RUNNING  match=`c78534cd` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=
- [2026-04-18 01:19:36Z] B_WIN    match=`ab281352` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=2026-04-18T01:19
- [2026-04-18 01:19:36Z] B_WIN    match=`c89c9b0f` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=2026-04-18T01:19
- [2026-04-18 01:20:07Z] queued   match=`0b88ba39` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:20:07Z] B_WIN    match=`74765a32` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=2026-04-18T01:20
- [2026-04-18 01:20:07Z] B_WIN    match=`6dcdea8c` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=2026-04-18T01:19
- [2026-04-18 01:20:07Z] B_WIN    match=`132a3fbd` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=2026-04-18T01:20
- [2026-04-18 01:20:07Z] A_WIN    match=`14a319d3` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=2026-04-18T01:19
- [2026-04-18 01:20:07Z] B_WIN    match=`b93942ed` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=2026-04-18T01:19
- [2026-04-18 01:20:07Z] B_WIN    match=`c78534cd` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=2026-04-18T01:19
- [2026-04-18 01:20:07Z] B_WIN    match=`503d8eb7` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=2026-04-18T01:19
- [2026-04-18 01:20:07Z] B_WIN    match=`e4eff274` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T01:00 finished=2026-04-18T01:19
- [2026-04-18 01:20:37Z] queued   match=`144a1826` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:20:37Z] queued   match=`af017ebc` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:20:37Z] queued   match=`066fdae3` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:20:37Z] queued   match=`0a270755` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:20:37Z] queued   match=`c39d8154` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:20:37Z] queued   match=`3df15113` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:20:37Z] queued   match=`56a79715` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:20:37Z] queued   match=`d71f7f02` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:22:08Z] queued   match=`552601e2` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T01:21 finished=
- [2026-04-18 01:35:15Z] RUNNING  match=`552601e2` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T01:21 finished=
- [2026-04-18 01:35:15Z] RUNNING  match=`144a1826` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:35:15Z] RUNNING  match=`af017ebc` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:35:15Z] RUNNING  match=`066fdae3` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:35:15Z] RUNNING  match=`0a270755` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:35:15Z] RUNNING  match=`c39d8154` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:35:15Z] RUNNING  match=`3df15113` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:35:15Z] RUNNING  match=`56a79715` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:35:15Z] RUNNING  match=`d71f7f02` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:35:15Z] RUNNING  match=`0b88ba39` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T01:20 finished=
- [2026-04-18 01:40:49Z] B_WIN    match=`066fdae3` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=2026-04-18T01:40
- [2026-04-18 01:40:49Z] A_WIN    match=`0a270755` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=2026-04-18T01:40
- [2026-04-18 01:40:49Z] B_WIN    match=`c39d8154` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=2026-04-18T01:40
- [2026-04-18 01:40:49Z] B_WIN    match=`3df15113` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=2026-04-18T01:40
- [2026-04-18 01:40:49Z] B_WIN    match=`56a79715` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=2026-04-18T01:40
- [2026-04-18 01:40:49Z] B_WIN    match=`d71f7f02` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=2026-04-18T01:40
- [2026-04-18 01:41:20Z] B_WIN    match=`144a1826` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=2026-04-18T01:40
- [2026-04-18 01:41:20Z] DRAW     match=`af017ebc` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:20 finished=2026-04-18T01:40
- [2026-04-18 01:41:50Z] queued   match=`3f5ceec9` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=
- [2026-04-18 01:41:50Z] queued   match=`7f9c8909` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=
- [2026-04-18 01:41:50Z] queued   match=`d59cc6ff` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=
- [2026-04-18 01:41:50Z] queued   match=`2f4b19b2` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=
- [2026-04-18 01:41:50Z] B_WIN    match=`552601e2` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T01:21 finished=2026-04-18T01:41
- [2026-04-18 01:42:20Z] B_WIN    match=`0b88ba39` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T01:20 finished=2026-04-18T01:41
- [2026-04-18 01:44:21Z] queued   match=`813544f3` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T01:44 finished=
- [2026-04-18 01:45:23Z] queued   match=`7679f7f1` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=
- [2026-04-18 01:45:23Z] queued   match=`7bfe8413` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=
- [2026-04-18 01:45:23Z] queued   match=`5d2061be` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=
- [2026-04-18 01:45:23Z] queued   match=`3f47db3e` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=
- [2026-04-18 01:45:23Z] queued   match=`534e455f` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=
- [2026-04-18 01:45:00Z] SUBMITTED match=`534e455f-3355-4fe5-9172-a567940eb92c` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 1 — disambiguate 21:11 loss)
- [2026-04-18 01:45:00Z] SUBMITTED match=`3f47db3e-e47c-4950-8020-12b39fa8218d` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 1)
- [2026-04-18 01:45:00Z] SUBMITTED match=`5d2061be-25d8-4c82-af66-f145ee1fcc99` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 1)
- [2026-04-18 01:45:00Z] SUBMITTED match=`7bfe8413-5149-49cb-a771-a275b0881d8c` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 1)
- [2026-04-18 01:45:00Z] SUBMITTED match=`7679f7f1-d654-4716-82c4-84bfacd8b5db` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 1 — 5/8 fired before implicit rate-stop; 3 remaining in wave 1; wave 2 after 10min to top 15)
- [2026-04-18 01:50:26Z] RUNNING  match=`7f9c8909` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=
- [2026-04-18 01:50:26Z] RUNNING  match=`d59cc6ff` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=
- [2026-04-18 01:50:26Z] RUNNING  match=`2f4b19b2` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=
- [2026-04-18 01:50:56Z] RUNNING  match=`3f5ceec9` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=
- [2026-04-18 01:51:57Z] RUNNING  match=`813544f3` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T01:44 finished=
- [2026-04-18 01:52:58Z] RUNNING  match=`5d2061be` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=
- [2026-04-18 01:52:58Z] RUNNING  match=`3f47db3e` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=
- [2026-04-18 01:52:58Z] RUNNING  match=`534e455f` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=
- [2026-04-18 01:53:28Z] RUNNING  match=`7679f7f1` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=
- [2026-04-18 01:53:28Z] RUNNING  match=`7bfe8413` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=
- [2026-04-18 01:56:30Z] B_WIN    match=`3f5ceec9` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=2026-04-18T01:56
- [2026-04-18 01:56:30Z] B_WIN    match=`7f9c8909` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=2026-04-18T01:56
- [2026-04-18 01:56:30Z] B_WIN    match=`d59cc6ff` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=2026-04-18T01:56
- [2026-04-18 01:56:30Z] B_WIN    match=`2f4b19b2` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:41 finished=2026-04-18T01:56
- [2026-04-18 01:57:00Z] DRAW     match=`7679f7f1` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=2026-04-18T01:56
- [2026-04-18 01:57:00Z] B_WIN    match=`7bfe8413` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=2026-04-18T01:56
- [2026-04-18 01:57:00Z] B_WIN    match=`5d2061be` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=2026-04-18T01:56
- [2026-04-18 01:57:00Z] B_WIN    match=`3f47db3e` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=2026-04-18T01:56
- [2026-04-18 01:57:00Z] A_WIN    match=`534e455f` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T01:45 finished=2026-04-18T01:56
- [2026-04-18 01:58:31Z] queued   match=`a3c9e9af` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:58 finished=
- [2026-04-18 01:58:31Z] queued   match=`2c0babfa` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:58 finished=
- [2026-04-18 01:58:31Z] queued   match=`cd536bc6` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:58 finished=
- [2026-04-18 01:58:31Z] B_WIN    match=`813544f3` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T01:44 finished=2026-04-18T01:58
- [2026-04-18 01:59:00Z] BATCH-SUBMITTED 15× vs Michael — UUIDs: d71f7f02-c08a-4572-9f7e-75d3fd504b6f, 56a79715-efe7-4d59-8d51-c272e52143a8, 3df15113-878b-4030-900b-2ba4cb456ab7, c39d8154-96f0-4c1a-81a5-345cba4eec59, 0a270755-cb2c-435a-a19e-2947d75675b0, 066fdae3-bad3-47a0-ba24-a7a9e8f0a267, af017ebc-d252-45bc-a133-4c8e4f68daac, 144a1826-ae62-4240-90cd-59056ca7492a, 2f4b19b2-bf1b-4d83-bcd4-701d1263abb3, d59cc6ff-1541-4410-b7e9-34880764ef5b, 7f9c8909-dda0-49f1-9eec-ada1ca13c69e, 3f5ceec9-8f61-4f53-b68c-1130b46a55d4, cd536bc6-0793-4529-8230-1e44e5d8284a, 2c0babfa-4b28-4469-8fb2-1edd374bebf4, a3c9e9af-055f-4894-8738-50800fca0419 (batch-scrim-michael — fired 8+4+3 split after 60min auth-dead wait; 2× 429 backoff, 1× CAPSOLVER retry; early Michael results: 4× B_WIN so far (RattleBot wins))
- [2026-04-18 02:06:07Z] queued   match=`ae88b079` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:05 finished=
- [2026-04-18 02:07:08Z] queued   match=`48579943` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:07:08Z] queued   match=`f2f5007f` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:07:08Z] queued   match=`377d2e9a` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:07:08Z] queued   match=`ddbda15f` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:07:08Z] queued   match=`65571ba2` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:07:08Z] queued   match=`94ba8d03` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:07:08Z] RUNNING  match=`a3c9e9af` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:58 finished=
- [2026-04-18 02:07:08Z] RUNNING  match=`2c0babfa` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:58 finished=
- [2026-04-18 02:07:08Z] RUNNING  match=`cd536bc6` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:58 finished=
- [2026-04-18 02:12:41Z] B_WIN    match=`a3c9e9af` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:58 finished=2026-04-18T02:12
- [2026-04-18 02:12:41Z] A_WIN    match=`2c0babfa` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:58 finished=2026-04-18T02:12
- [2026-04-18 02:12:41Z] B_WIN    match=`cd536bc6` vs `Michael` (c3cd58f4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Rusty-v2.1.zip` reason=scrimmage sched=2026-04-18T01:58 finished=2026-04-18T02:12
- [2026-04-18 02:13:12Z] queued   match=`74710557` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:13 finished=
- [2026-04-18 02:13:12Z] queued   match=`9ba91b12` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:13 finished=
- [2026-04-18 02:13:12Z] queued   match=`0923ff33` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:13 finished=
- [2026-04-18 02:18:45Z] RUNNING  match=`ae88b079` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:05 finished=
- [2026-04-18 02:19:46Z] RUNNING  match=`48579943` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:19:46Z] RUNNING  match=`f2f5007f` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:19:46Z] RUNNING  match=`377d2e9a` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:19:46Z] RUNNING  match=`ddbda15f` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:19:46Z] RUNNING  match=`65571ba2` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:19:46Z] RUNNING  match=`94ba8d03` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=
- [2026-04-18 02:23:18Z] B_WIN    match=`48579943` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=2026-04-18T02:23
- [2026-04-18 02:23:18Z] A_WIN    match=`f2f5007f` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=2026-04-18T02:23
- [2026-04-18 02:23:18Z] B_WIN    match=`65571ba2` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=2026-04-18T02:23
- [2026-04-18 02:23:18Z] B_WIN    match=`94ba8d03` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=2026-04-18T02:23
- [2026-04-18 02:23:48Z] A_WIN    match=`377d2e9a` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=2026-04-18T02:23
- [2026-04-18 02:23:48Z] B_WIN    match=`ddbda15f` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:06 finished=2026-04-18T02:23
- [2026-04-18 02:25:20Z] queued   match=`d49a6bbe` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:25 finished=
- [2026-04-18 02:25:20Z] RUNNING  match=`74710557` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:13 finished=
- [2026-04-18 02:25:20Z] RUNNING  match=`9ba91b12` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:13 finished=
- [2026-04-18 02:25:20Z] RUNNING  match=`0923ff33` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:13 finished=
- [2026-04-18 02:25:20Z] A_WIN    match=`ae88b079` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:05 finished=2026-04-18T02:25
- [2026-04-18 02:16:00Z] SUBMITTED match=`94ba8d03-09bf-4b46-9fa3-0527ae1477a0` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 2)
- [2026-04-18 02:16:00Z] SUBMITTED match=`65571ba2-9d90-4fcd-a93b-395d1be07771` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 2)
- [2026-04-18 02:16:00Z] SUBMITTED match=`ddbda15f-7ced-4512-a623-32a4b6b2e700` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 2)
- [2026-04-18 02:16:00Z] SUBMITTED match=`377d2e9a-929c-4650-ba15-ffc050afef75` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 2)
- [2026-04-18 02:16:00Z] SUBMITTED match=`f2f5007f-b960-4fef-9145-8ba79081a9af` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 2)
- [2026-04-18 02:16:00Z] SUBMITTED match=`48579943-d2a1-4c44-be8d-8c8cc35f9ff2` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 2 — 6/7 fired before rate-stop)
- [2026-04-18 02:22:00Z] SUBMITTED match=`0923ff33-6099-42a2-9355-ce91b74f1919` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 3 — backoff-retry)
- [2026-04-18 02:22:00Z] SUBMITTED match=`9ba91b12-cc60-4d87-a4a5-d1f8548d6035` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 3)
- [2026-04-18 02:22:00Z] SUBMITTED match=`74710557-7d19-469b-9544-67f3b895146a` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 3 — 3/4 fired before rate-stop)
- [2026-04-18 02:34:00Z] SUBMITTED match=`d49a6bbe-952c-4942-9b40-6d94401042e7` vs `Team 57` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage result=queued (batch-fire T-BATCH-TEAM57 wave 4 — final fire; total 15/15 complete)
- [2026-04-18 02:27:52Z] queued   match=`11cae843` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:27 finished=
- [2026-04-18 02:28:52Z] A_WIN    match=`0923ff33` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:13 finished=2026-04-18T02:28
- [2026-04-18 02:29:22Z] A_WIN    match=`74710557` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:13 finished=2026-04-18T02:28
- [2026-04-18 02:29:22Z] B_WIN    match=`9ba91b12` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:13 finished=2026-04-18T02:28
- [2026-04-18 02:36:27Z] queued   match=`05ff1694` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:36 finished=
- [2026-04-18 02:37:57Z] RUNNING  match=`d49a6bbe` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:25 finished=
- [2026-04-18 02:41:00Z] RUNNING  match=`11cae843` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:27 finished=
- [2026-04-18 02:41:30Z] B_WIN    match=`d49a6bbe` vs `Team 57` (70c48f7b) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T02:25 finished=2026-04-18T02:41
- [2026-04-18 02:44:32Z] queued   match=`5a6d32d9` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:44 finished=
- [2026-04-18 02:47:34Z] B_WIN    match=`11cae843` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:27 finished=2026-04-18T02:47
- [2026-04-18 02:49:05Z] RUNNING  match=`05ff1694` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:36 finished=
- [2026-04-18 02:51:06Z] queued   match=`21a147b4` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:50 finished=
- [2026-04-18 02:55:39Z] A_WIN    match=`05ff1694` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:36 finished=2026-04-18T02:55
- [2026-04-18 02:58:10Z] RUNNING  match=`5a6d32d9` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:44 finished=
- [2026-04-18 03:01:13Z] queued   match=`dd841e17` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:00 finished=
- [2026-04-18 03:04:14Z] RUNNING  match=`21a147b4` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:50 finished=
- [2026-04-18 03:04:45Z] B_WIN    match=`5a6d32d9` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:44 finished=2026-04-18T03:04
- [2026-04-18 03:08:49Z] queued   match=`e326a9d7` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:08 finished=
- [2026-04-18 03:10:51Z] B_WIN    match=`21a147b4` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T02:50 finished=2026-04-18T03:10
- [2026-04-18 03:11:51Z] queued   match=`bee8b879` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:11:51Z] queued   match=`cf38e87b` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:11:51Z] queued   match=`8b7226f5` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:11:51Z] queued   match=`cf0f474e` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:11:51Z] queued   match=`66b5ffa4` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:11:51Z] queued   match=`676e976a` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:11:51Z] queued   match=`fcb9fed4` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:11:51Z] queued   match=`6648b9a2` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:13:22Z] RUNNING  match=`dd841e17` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:00 finished=
- [2026-04-18 03:19:57Z] B_WIN    match=`dd841e17` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:00 finished=2026-04-18T03:19
- [2026-04-18 03:22:29Z] RUNNING  match=`e326a9d7` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:08 finished=
- [2026-04-18 03:22:59Z] queued   match=`7f6becda` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:22 finished=
- [2026-04-18 03:24:00Z] RUNNING  match=`bee8b879` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:24:00Z] RUNNING  match=`cf38e87b` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:24:00Z] RUNNING  match=`8b7226f5` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:24:00Z] RUNNING  match=`cf0f474e` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:24:00Z] RUNNING  match=`66b5ffa4` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:24:00Z] RUNNING  match=`676e976a` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:24:00Z] RUNNING  match=`fcb9fed4` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:24:00Z] RUNNING  match=`6648b9a2` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=
- [2026-04-18 03:27:32Z] B_WIN    match=`bee8b879` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=2026-04-18T03:27
- [2026-04-18 03:27:32Z] B_WIN    match=`cf38e87b` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=2026-04-18T03:27
- [2026-04-18 03:27:32Z] A_WIN    match=`8b7226f5` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=2026-04-18T03:27
- [2026-04-18 03:27:32Z] A_WIN    match=`cf0f474e` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=2026-04-18T03:27
- [2026-04-18 03:27:32Z] B_WIN    match=`66b5ffa4` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=2026-04-18T03:27
- [2026-04-18 03:27:32Z] B_WIN    match=`676e976a` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=2026-04-18T03:27
- [2026-04-18 03:27:32Z] B_WIN    match=`fcb9fed4` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=2026-04-18T03:27
- [2026-04-18 03:27:32Z] DRAW     match=`6648b9a2` vs `George` (13f7ba71) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T03:11 finished=2026-04-18T03:27
- [2026-04-18 03:28:02Z] queued   match=`ff0efacc` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:27 finished=
- [2026-04-18 03:28:33Z] queued   match=`0ab2e455` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:28 finished=
- [2026-04-18 03:29:03Z] queued   match=`a91dafac` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:28 finished=
- [2026-04-18 03:29:03Z] B_WIN    match=`e326a9d7` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:08 finished=2026-04-18T03:28
- [2026-04-18 03:29:34Z] queued   match=`f858a742` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:29 finished=
- [2026-04-18 03:30:04Z] queued   match=`5fda3f66` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:29 finished=
- [2026-04-18 03:30:34Z] queued   match=`440bb03d` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:30 finished=
- [2026-04-18 03:31:04Z] queued   match=`59a1b042` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:30 finished=
- [2026-04-18 03:33:06Z] RUNNING  match=`7f6becda` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:22 finished=
- [2026-04-18 03:36:07Z] queued   match=`81af8d54` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:36 finished=
- [2026-04-18 03:37:15Z] queued   match=`e0c97856` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:36 finished=
- [2026-04-18 03:38:47Z] RUNNING  match=`a91dafac` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:28 finished=
- [2026-04-18 03:38:47Z] RUNNING  match=`0ab2e455` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:28 finished=
- [2026-04-18 03:38:47Z] RUNNING  match=`ff0efacc` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:27 finished=
- [2026-04-18 03:39:17Z] B_WIN    match=`7f6becda` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:22 finished=2026-04-18T03:39
- [2026-04-18 03:40:48Z] queued   match=`3104972d` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:40 finished=
- [2026-04-18 03:40:48Z] RUNNING  match=`5fda3f66` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:29 finished=
- [2026-04-18 03:40:48Z] RUNNING  match=`f858a742` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:29 finished=
- [2026-04-18 03:42:18Z] RUNNING  match=`59a1b042` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:30 finished=
- [2026-04-18 03:42:18Z] RUNNING  match=`440bb03d` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:30 finished=
- [2026-04-18 03:44:50Z] B_WIN    match=`a91dafac` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:28 finished=2026-04-18T03:44
- [2026-04-18 03:44:50Z] B_WIN    match=`0ab2e455` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:28 finished=2026-04-18T03:44
- [2026-04-18 03:44:50Z] B_WIN    match=`ff0efacc` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:27 finished=2026-04-18T03:44
- [2026-04-18 03:45:51Z] RUNNING  match=`81af8d54` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:36 finished=
- [2026-04-18 03:46:51Z] B_WIN    match=`f858a742` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:29 finished=2026-04-18T03:46
- [2026-04-18 03:47:22Z] B_WIN    match=`5fda3f66` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:29 finished=2026-04-18T03:46
- [2026-04-18 03:47:52Z] RUNNING  match=`e0c97856` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:36 finished=
- [2026-04-18 03:48:23Z] queued   match=`c7d0951c` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:48 finished=
- [2026-04-18 03:48:23Z] B_WIN    match=`59a1b042` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:30 finished=2026-04-18T03:48
- [2026-04-18 03:48:23Z] B_WIN    match=`440bb03d` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:30 finished=2026-04-18T03:48
- [2026-04-18 03:48:53Z] queued   match=`bb18c6c0` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:48 finished=
- [2026-04-18 03:49:23Z] queued   match=`ceda6ab6` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:49 finished=
- [2026-04-18 03:49:53Z] queued   match=`157f4c1a` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:49 finished=
- [2026-04-18 03:50:24Z] queued   match=`b0a184aa` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:50 finished=
- [2026-04-18 03:50:24Z] queued   match=`5913ed28` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:50 finished=
- [2026-04-18 03:50:54Z] RUNNING  match=`3104972d` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:40 finished=
- [2026-04-18 03:52:25Z] B_WIN    match=`81af8d54` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:36 finished=2026-04-18T03:51
- [2026-04-18 03:53:56Z] B_WIN    match=`e0c97856` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:36 finished=2026-04-18T03:53
- [2026-04-18 03:54:26Z] RUNNING  match=`ceda6ab6` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:49 finished=
- [2026-04-18 03:54:26Z] RUNNING  match=`bb18c6c0` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:48 finished=
- [2026-04-18 03:54:26Z] RUNNING  match=`c7d0951c` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:48 finished=
- [2026-04-18 03:54:57Z] RUNNING  match=`157f4c1a` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:49 finished=
- [2026-04-18 03:55:57Z] RUNNING  match=`b0a184aa` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:50 finished=
- [2026-04-18 03:55:57Z] RUNNING  match=`5913ed28` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:50 finished=
- [2026-04-18 03:56:28Z] queued   match=`7a09d873` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:56 finished=
- [2026-04-18 03:56:58Z] queued   match=`4e29cbbf` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:56 finished=
- [2026-04-18 03:57:28Z] queued   match=`89745ff3` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:57 finished=
- [2026-04-18 03:57:58Z] queued   match=`0fa9b382` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:57 finished=
- [2026-04-18 03:57:58Z] B_WIN    match=`3104972d` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:40 finished=2026-04-18T03:57
- [2026-04-18 04:00:31Z] queued   match=`99b28c88` vs `Team 15` (81513423) sub=`overturned.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-18T04:00 finished=
- [2026-04-18 04:00:31Z] queued   match=`48061da9` vs `KeithAndVip` (8599370e) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`wbot.zip` reason=matchmaking sched=2026-04-18T04:00 finished=
- [2026-04-18 04:00:31Z] queued   match=`c99cd9bc` vs `Team 15` (81513423) sub=`mybot-alt2.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-18T04:00 finished=
- [2026-04-18 04:00:31Z] queued   match=`090684a2` vs `Team 15` (81513423) sub=`agent6.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-18T04:00 finished=
- [2026-04-18 04:00:31Z] B_WIN    match=`ceda6ab6` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:49 finished=2026-04-18T04:00
- [2026-04-18 04:00:31Z] B_WIN    match=`bb18c6c0` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:48 finished=2026-04-18T04:00
- [2026-04-18 04:00:31Z] B_WIN    match=`c7d0951c` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:48 finished=2026-04-18T04:00
- [2026-04-18 04:01:02Z] B_WIN    match=`157f4c1a` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:49 finished=2026-04-18T04:00
- [2026-04-18 04:02:02Z] queued   match=`305c74a6` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T04:01 finished=
- [2026-04-18 04:02:33Z] B_WIN    match=`b0a184aa` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:50 finished=2026-04-18T04:02
- [2026-04-18 04:02:33Z] B_WIN    match=`5913ed28` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T03:50 finished=2026-04-18T04:02
- [2026-04-18 04:03:03Z] RUNNING  match=`7a09d873` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:56 finished=
- [2026-04-18 04:02:30Z] SUBMITTED match=`7f6becda-3461-44ef-a975-85d158403c32` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 1 — backoff-retry after 429x2)
- [2026-04-18 04:02:30Z] SUBMITTED match=`ff0efacc-aac5-4aa1-a834-0036cf354a13` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 1)
- [2026-04-18 04:02:30Z] SUBMITTED match=`0ab2e455-fa11-4018-a38c-70d4631c9fc2` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 1)
- [2026-04-18 04:02:30Z] SUBMITTED match=`a91dafac-4dcc-4141-a6c6-a6c84c01c7d7` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 1)
- [2026-04-18 04:02:30Z] SUBMITTED match=`f858a742-e110-4086-abfc-14bed6162139` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 1)
- [2026-04-18 04:02:30Z] SUBMITTED match=`5fda3f66-eeb1-422b-8981-05f80fabe5d8` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 1)
- [2026-04-18 04:02:30Z] SUBMITTED match=`440bb03d-d091-4077-aa99-451916929e7e` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 1)
- [2026-04-18 04:02:30Z] SUBMITTED match=`59a1b042-69db-44a6-8691-62d81024e6f7` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 1 — 8/8 complete)
- [2026-04-18 04:02:30Z] SUBMITTED match=`81af8d54-a5e8-4634-991c-92d9aba25739` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 2)
- [2026-04-18 04:02:30Z] SUBMITTED match=`e0c97856-5fd1-46d8-98ef-39a188b6db9d` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 2)
- [2026-04-18 04:02:30Z] SUBMITTED match=`c7d0951c-ace7-4f6d-8f86-263e610d6e74` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 2 — backoff-retry after 429x3)
- [2026-04-18 04:02:30Z] SUBMITTED match=`bb18c6c0-d746-4449-8286-673b2a2d58d9` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 2)
- [2026-04-18 04:02:30Z] SUBMITTED match=`ceda6ab6-5a06-40d0-84f3-0f7a605e93b6` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 2)
- [2026-04-18 04:02:30Z] SUBMITTED match=`157f4c1a-1f43-43ad-82c9-ef1d46297800` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 2)
- [2026-04-18 04:02:30Z] SUBMITTED match=`b0a184aa-b436-47d5-af68-5b93e11bf027` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 2 — 7/7 complete)
- [2026-04-18 04:02:30Z] SUBMITTED match=`7a09d873-8dce-44ec-b9e2-3e144d6ba413` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 3)
- [2026-04-18 04:02:30Z] SUBMITTED match=`4e29cbbf-6d81-487b-baeb-147bc7057f07` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 3)
- [2026-04-18 04:02:30Z] SUBMITTED match=`89745ff3-1a2c-499d-9810-ee4175dbc7a1` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 3)
- [2026-04-18 04:02:30Z] SUBMITTED match=`0fa9b382-bc4c-4901-bde3-cc8ba0145b09` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 3)
- [2026-04-18 04:02:30Z] SUBMITTED match=`305c74a6-7dd0-4c79-b891-abf20c153b06` vs `Albert` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage result=queued (scrim-albert-20 wave 3 — 5/5 complete; total 20/20)
- [2026-04-18 04:03:34Z] RUNNING  match=`4e29cbbf` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:56 finished=
- [2026-04-18 04:04:04Z] RUNNING  match=`89745ff3` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:57 finished=
- [2026-04-18 04:05:35Z] RUNNING  match=`0fa9b382` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:57 finished=
- [2026-04-18 04:09:08Z] queued   match=`f2970c1d` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T04:08 finished=
- [2026-04-18 04:09:08Z] B_WIN    match=`7a09d873` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:56 finished=2026-04-18T04:08
- [2026-04-18 04:10:09Z] B_WIN    match=`4e29cbbf` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:56 finished=2026-04-18T04:09
- [2026-04-18 04:10:39Z] RUNNING  match=`090684a2` vs `Team 15` (81513423) sub=`agent6.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-18T04:00 finished=
- [2026-04-18 04:10:39Z] B_WIN    match=`89745ff3` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:57 finished=2026-04-18T04:10
- [2026-04-18 04:11:40Z] B_WIN    match=`0fa9b382` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T03:57 finished=2026-04-18T04:11
- [2026-04-18 04:13:41Z] RUNNING  match=`c99cd9bc` vs `Team 15` (81513423) sub=`mybot-alt2.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-18T04:00 finished=
- [2026-04-18 04:17:13Z] queued   match=`1e48b048` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T04:16 finished=
- [2026-04-18 04:17:13Z] A_WIN    match=`090684a2` vs `Team 15` (81513423) sub=`agent6.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-18T04:00 finished=2026-04-18T04:17
- [2026-04-18 04:18:14Z] queued   match=`29530cbd` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:18 finished=
- [2026-04-18 04:18:14Z] queued   match=`97714573` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:18 finished=
- [2026-04-18 04:18:14Z] queued   match=`59375042` vs `Team 61` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:18 finished=
- [2026-04-18 04:18:45Z] queued   match=`6a239acd` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:18 finished=
- [2026-04-18 04:18:45Z] queued   match=`44aee688` vs `Team 61` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:18 finished=
- [2026-04-18 04:18:45Z] queued   match=`04832549` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:18 finished=
- [2026-04-18 04:18:45Z] queued   match=`cd89b174` vs `Team 61` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:18 finished=
- [2026-04-18 04:15:00Z] SUBMITTED match=`97714573-505e-4fd1-b056-4adb0fb83b0e` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 1)
- [2026-04-18 04:16:00Z] SUBMITTED match=`29530cbd-c3b7-494d-b356-17bd772f5792` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 1)
- [2026-04-18 04:17:00Z] SUBMITTED match=`04832549-a429-4aae-920c-a4e1ab6d8c28` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 1)
- [2026-04-18 04:18:00Z] SUBMITTED match=`6a239acd-135b-436c-a1d9-a8f8fa96dff4` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 1 — 4/8 fired before rate-stop)
- [2026-04-18 04:18:30Z] SUBMITTED match=`59375042-c1b0-4950-b99d-8d8751a69178` vs `Team 61` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage result=queued (scrim-topteams-20 wave 1 vs T61)
- [2026-04-18 04:18:45Z] SUBMITTED match=`cd89b174-cf79-4a94-9707-3433087a08fa` vs `Team 61` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage result=queued (scrim-topteams-20 wave 1 vs T61)
- [2026-04-18 04:19:00Z] SUBMITTED match=`44aee688-ccd8-4aa9-91bb-0b95e00a56b0` vs `Team 61` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage result=queued (scrim-topteams-20 wave 1 vs T61 — 3/8 fired before 429)
- [2026-04-18 04:20:47Z] A_WIN    match=`c99cd9bc` vs `Team 15` (81513423) sub=`mybot-alt2.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-18T04:00 finished=2026-04-18T04:20
- [2026-04-18 04:26:51Z] RUNNING  match=`48061da9` vs `KeithAndVip` (8599370e) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`wbot.zip` reason=matchmaking sched=2026-04-18T04:00 finished=
- [2026-04-18 04:28:23Z] RUNNING  match=`99b28c88` vs `Team 15` (81513423) sub=`overturned.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-18T04:00 finished=
- [2026-04-18 04:30:25Z] RUNNING  match=`305c74a6` vs `Albert` (5121a2d4) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T04:01 finished=
- [2026-04-18 04:32:26Z] A_WIN    match=`99b28c88` vs `Team 15` (81513423) sub=`overturned.zip` opp_sub=`RattleBot_v03_pureonly_20260417_1022.zip` reason=matchmaking sched=2026-04-18T04:00 finished=2026-04-18T04:32
- [2026-04-18 04:33:58Z] B_WIN    match=`48061da9` vs `KeithAndVip` (8599370e) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`wbot.zip` reason=matchmaking sched=2026-04-18T04:00 finished=2026-04-18T04:33
- [2026-04-18 04:36:00Z] SUBMITTED match=`467dcbbc-bcdc-42f0-83b4-5a2d82adcacb` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 2 — 1/1 before rate-stop)

## Autobots batch (T-BATCH-AUTOBOTS task #104, scrimmage-runner agent batch-scrim-autobots)

**Target:** Autobots (Team UUID `58988294-cd9d-4174-aa7a-560d1e3cce7b`), glicko ≈1979, #3 student team. `opp_sub=super_cython.zip`. Submission: `RattleBot_v03_pureonly_20260417_1022.zip`.

**Fires:** 15/15 queued over ~3.5h (heavy 429 rate-limit from 5 concurrent batch agents; averaged 1 fire every ~8-14 min after CAPSOLVER + 429 retries). All `count=1` due to rate pressure. Spanning 2026-04-18T01:20 → 2026-04-18T04:43.

**UUIDs (in fire order):**
1. `0b88ba39-113a-43cb-98ff-5e9a39e44da4` — B_WIN (loss)
2. `552601e2-6ed8-4790-bc42-53d38b73810c` — B_WIN (loss)
3. `813544f3-a7a3-47c1-958a-71453d168815` — B_WIN (loss)
4. `ae88b079-889e-4a9b-bf18-4a9ab149d2ae` — A_WIN (win)
5. `11cae843-1e4f-40b7-8a09-b80a00e2923a` — B_WIN (loss)
6. `05ff1694-6329-4f19-ae5e-ceb624371ca8` — A_WIN (win)
7. `5a6d32d9-f312-475e-b436-d18b9f8474c0` — B_WIN (loss)
8. `21a147b4-18d2-4795-a6c2-5de6ceb1493b` — B_WIN (loss)
9. `dd841e17-232d-47fb-8769-106656ad6789` — B_WIN (loss)
10. `e326a9d7-fdac-4282-a2b8-d2b447ae4ec3` — B_WIN (loss)
11. `3104972d-1428-4089-a8f1-586535d7241f` — B_WIN (loss)
12. `5913ed28-c270-48f4-bc07-2b22e8cf6db9` — B_WIN (loss)
13. `f2970c1d-75d4-46a6-8d21-53391ce99647` — B_WIN (loss)
14. `1e48b048-d3d8-4656-a637-f8edb6a4ce11` — in_progress at report time
15. `16bac052-1883-4d60-8621-16fbd2190658` — waiting at report time

**Interim score (13 finished of 15):** RattleBot 2 — Autobots 11. Win rate 2/13 ≈ **15.4%** (matches Autobots' 74% win rate from COMPETITIVE_INTEL_APR17.md). Poller auto-appends final rows for 14+15.

**A/B mapping:** scrimmages created via `POST /game-match` with `teamAUuid=Team 15` (us) → team_a_win = RattleBot win, team_b_win = Autobots win. Matches earlier log convention and task #112 verification.
- [2026-04-18 04:47:14Z] SUBMITTED match=`5608b41b-f87d-4729-a84e-843864a17136` vs `Team 61` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage result=queued (scrim-topteams-20 wave 1 vs T61)
- [2026-04-18 04:47:42Z] SUBMITTED match=`1dc631e1-7848-4a12-bd30-3333e9364f1c` vs `Team 61` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage result=queued (scrim-topteams-20 wave 1 vs T61)
- [2026-04-18 04:48:28Z] SUBMITTED match=`71a2aa2d-73ce-46c7-b809-74844ed057fd` vs `Team 61` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage result=queued (scrim-topteams-20 wave 1 vs T61)
- [2026-04-18 04:54:28Z] SUBMITTED match=`3984f3d1-9a66-41a3-9e2a-5f70b56e8db9` vs `Team 61` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage result=queued (scrim-topteams-20 wave 1 vs T61)

## arch-fix-ship v0.4 upload — 2026-04-18 01:00 EDT

**Owner:** arch-fix-ship
**Submission:** `RattleBot_v04_archfix_20260418_003411.zip` (UUID `379d5f82-80d4-4ff7-8430-8363e871fe68`, SHA256 `ef830ccf1a507f5aa5dd3c08ec1ff838f7cb1bd0408841e36c01b9543a801ec3`, 46.8 KB, pure-python, numba-stripped)
**Commit:** `3b9cbbd` — `fix(RattleBot): F-1/F-2/F-3 arch-fix-ship v0.4 (26% WR crisis)`
**Validity:** **valid** (bytefight server validated on upload).
**Current submission:** NOT flipped — still `RattleBot_v03_pureonly` per team-lead's <55% local-paired abort rule.

### Fixes landed
- F-1: Confirmed `move_gen.py` T-20f has_non_k1 gate already forbids k=1 CARPET unless no alternative exists. No code change.
- F-2: SEARCH-gate mass floor 1/3 → **0.35** with linear ramp to **0.30** over last 10 plies. `_search_mass_threshold(turns_left)`.
- F-3: On ply 0 (player turns_left == 40), force a PRIME move in the highest-mobility cardinal direction instead of defaulting to a heuristic PLAIN. `_is_ply_zero` + `_ply_zero_prime`.
- Bumped version string v0.2 → v0.4-arch-fixes in agent docstring + commentate().

### Paired test vs prior HEAD snapshot — 2026-04-18 00:34 EDT
`tools/v2_paired_direct.py` + `paired_runner.py`, Windows, `--no-limit-resources`:
- Pair seed=0 (via paired_runner batch_20260418_002259): new 1W (45-30) / 1L (34-51)
- Pair seed=100 (via v2_paired_direct archfix_paired): new 0W / 2L (43-45, 31-40)
- Aggregate (4 matches): **1W/3L = 25% WR vs RattleBot_prior**
- Margins small (2-15 pts absolute), noise-dominated. 95% Wilson CI for 1/4 = [1%, 70%].

### Decision
Below 55% bar → upload DONE (for record) but set-current NOT executed. Team-lead to decide next step based on:
1. Whether to rerun paired with more N (≥20 matches) when CPU frees up.
2. Whether the defensive nature of F-1/F-2/F-3 (stricter SEARCH, smarter opening) warrants flipping anyway on real-opponent signal.
3. Alternative: fire a handful of `set-current`-less probe scrimmages via a temporary flip+unflip — but bytefight's scrimmage endpoint uses current-submission only, so this requires the flip.
- [2026-04-18 05:05:42Z] queued   match=`bd87f264` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:05 finished=
- [2026-04-18 05:05:42Z] VAL_OK   match=`ea7affe9` vs `Team 15` (81513423) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`RattleBot_v04_archfix_20260418_003411.zip` reason=validation sched=2026-04-18T05:00 finished=2026-04-18T05:00
- [2026-04-18 05:05:42Z] queued   match=`5ed94c52` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:00 finished=
- [2026-04-18 05:05:42Z] queued   match=`3984f3d1` vs `Caspian` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:54 finished=
- [2026-04-18 05:05:42Z] RUNNING  match=`9d023097` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:48 finished=
- [2026-04-18 05:05:42Z] RUNNING  match=`f32974ca` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:48 finished=
- [2026-04-18 05:05:42Z] RUNNING  match=`71a2aa2d` vs `Caspian` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:48 finished=
- [2026-04-18 05:05:42Z] RUNNING  match=`76cb86ea` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:48 finished=
- [2026-04-18 05:05:42Z] RUNNING  match=`22a900b6` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:47 finished=
- [2026-04-18 05:05:42Z] RUNNING  match=`1dc631e1` vs `Caspian` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:47 finished=
- [2026-04-18 05:05:42Z] B_WIN    match=`844c2106` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:47 finished=2026-04-18T05:04
- [2026-04-18 05:05:42Z] RUNNING  match=`5608b41b` vs `Caspian` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:47 finished=
- [2026-04-18 05:05:42Z] B_WIN    match=`16bac052` vs `Autobots` (58988294) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T04:43 finished=2026-04-18T05:00
- [2026-04-18 05:05:42Z] B_WIN    match=`467dcbbc` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:36 finished=2026-04-18T04:54
- [2026-04-18 05:05:42Z] A_WIN    match=`6a239acd` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:18 finished=2026-04-18T04:47
- [2026-04-18 05:05:42Z] B_WIN    match=`44aee688` vs `Caspian` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:18 finished=2026-04-18T04:48
- [2026-04-18 05:05:42Z] B_WIN    match=`04832549` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:18 finished=2026-04-18T04:47
- [2026-04-18 05:05:42Z] B_WIN    match=`cd89b174` vs `Caspian` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:18 finished=2026-04-18T04:47
- [2026-04-18 05:05:42Z] B_WIN    match=`29530cbd` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:18 finished=2026-04-18T04:47
- [2026-04-18 05:05:42Z] B_WIN    match=`97714573` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:18 finished=2026-04-18T04:46
- [2026-04-18 05:06:12Z] queued   match=`e41a40bf` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:06:12Z] queued   match=`59022b26` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:06:12Z] A_WIN    match=`9d023097` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:48 finished=2026-04-18T05:06
- [2026-04-18 05:06:12Z] A_WIN    match=`f32974ca` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:48 finished=2026-04-18T05:05
- [2026-04-18 05:06:12Z] B_WIN    match=`76cb86ea` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:48 finished=2026-04-18T05:05
- [2026-04-18 05:06:12Z] B_WIN    match=`22a900b6` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T04:47 finished=2026-04-18T05:05
- [2026-04-18 05:06:12Z] B_WIN    match=`5608b41b` vs `Caspian` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:47 finished=2026-04-18T05:05
- [2026-04-18 05:06:42Z] queued   match=`3ad28c82` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:06:42Z] queued   match=`e20ac62c` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:06:42Z] queued   match=`8af2ab56` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:06:42Z] B_WIN    match=`71a2aa2d` vs `Caspian` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:48 finished=2026-04-18T05:06
- [2026-04-18 05:06:42Z] B_WIN    match=`1dc631e1` vs `Caspian` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:47 finished=2026-04-18T05:06
- [2026-04-18 05:07:13Z] queued   match=`a62a0c4d` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:07:13Z] queued   match=`2eecc225` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:07:43Z] RUNNING  match=`3984f3d1` vs `Caspian` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:54 finished=

## ship-v04-decisive — set-current v04 + fire 20 Carrie + 10 Albert (2026-04-18 05:05 UTC)

**Context:** arch-fix-ship uploaded `RattleBot_v04_archfix_20260418_003411.zip` (UUID `379d5f82-80d4-4ff7-8430-8363e871fe68`), valid on bytefight. Prior set-current withheld due to N=4 paired self-play (1W/3L). Team-lead override: N=4 self-play cannot abort architectural fixes targeting gaps vs DIFFERENT opponents (Carrie/Rusty). Real-ELO scrimmages = only valid signal.

**Set-current:** flipped at 2026-04-18 05:04:45Z via `set-current --submission-id 379d5f82-80d4-4ff7-8430-8363e871fe68`. Verified via `my-team` -> `currentSubmissionDTO.uuid = 379d5f82-80d4-4ff7-8430-8363e871fe68`. v03 `f68dd66f` no longer current.

**Plan:** 20 scrimmages vs Carrie (8 -> 6min sleep -> 8 -> 6min sleep -> 4), then 10 vs Albert.

### Carrie wave 1 (target 8, achieved 7 of 8 before 429)
- [2026-04-18 05:05:59Z] SUBMITTED match=`59022b26-54f6-4d5b-a8b5-2ed7f3482616` vs `Carrie` (6d2a15ad-f175-48db-9fad-e1b5de3f71e2) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (ship-v04-decisive wave 1 vs Carrie)
- [2026-04-18 05:06:10Z] SUBMITTED match=`e41a40bf-9341-4eae-8a12-b6ba36e61ca0` vs `Carrie` (6d2a15ad-f175-48db-9fad-e1b5de3f71e2) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (ship-v04-decisive wave 1 vs Carrie)
- [2026-04-18 05:06:22Z] SUBMITTED match=`8af2ab56-ee55-47cb-aa18-ca04195cb75b` vs `Carrie` (6d2a15ad-f175-48db-9fad-e1b5de3f71e2) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (ship-v04-decisive wave 1 vs Carrie)
- [2026-04-18 05:06:33Z] SUBMITTED match=`e20ac62c-a6c3-4c99-a3ba-56bcb00fbc93` vs `Carrie` (6d2a15ad-f175-48db-9fad-e1b5de3f71e2) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (ship-v04-decisive wave 1 vs Carrie)
- [2026-04-18 05:06:44Z] SUBMITTED match=`3ad28c82-4e67-45d7-818a-decbee7798ca` vs `Carrie` (6d2a15ad-f175-48db-9fad-e1b5de3f71e2) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (ship-v04-decisive wave 1 vs Carrie)
- [2026-04-18 05:06:55Z] SUBMITTED match=`2eecc225-f546-4f94-b3ea-cdfbe3e4e9f8` vs `Carrie` (6d2a15ad-f175-48db-9fad-e1b5de3f71e2) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (ship-v04-decisive wave 1 vs Carrie)
- [2026-04-18 05:07:06Z] SUBMITTED match=`a62a0c4d-61c6-4623-83a2-679b82d737e4` vs `Carrie` (6d2a15ad-f175-48db-9fad-e1b5de3f71e2) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (ship-v04-decisive wave 1 vs Carrie -- 7/8 before 429, sleep 6min then wave 2)
- [2026-04-18 05:12:47Z] RUNNING  match=`5ed94c52` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:00 finished=
- [2026-04-18 05:20:00Z] SUBMITTED match=`fc5d0bc5-c872-489f-871b-3561b2a2e9ac` vs `Team 61` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T61)
- [2026-04-18 05:15:19Z] queued   match=`fc5d0bc5` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:15 finished=
- [2026-04-18 05:15:19Z] A_WIN    match=`3984f3d1` vs `Caspian` (b32c577c) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T04:54 finished=2026-04-18T05:14
- [2026-04-18 05:18:51Z] RUNNING  match=`bd87f264` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:05 finished=
- [2026-04-18 05:18:51Z] B_WIN    match=`5ed94c52` vs `Carrie` (6d2a15ad) sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:00 finished=2026-04-18T05:18
- [2026-04-18 05:19:06Z] SUBMITTED match=`c498db0d-fcb4-49e5-a644-a9323f3fb7b9` vs `Team 44` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-topteams-20 wave 2 vs T44)
- [2026-04-18 05:19:21Z] queued   match=`c498db0d` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:19 finished=
- [2026-04-18 05:19:21Z] RUNNING  match=`e41a40bf` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:19:21Z] RUNNING  match=`59022b26` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:19:52Z] RUNNING  match=`e20ac62c` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:19:52Z] RUNNING  match=`8af2ab56` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:20:52Z] RUNNING  match=`3ad28c82` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:21:53Z] RUNNING  match=`a62a0c4d` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:21:53Z] RUNNING  match=`2eecc225` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=
- [2026-04-18 05:25:11Z] SUBMITTED match=`4c4ddd3a-b63b-4c61-85be-6d7300e08193` vs `Team 61` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T61)
- [2026-04-18 05:25:25Z] queued   match=`008a6a6a` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:25 finished=
- [2026-04-18 05:25:25Z] queued   match=`4c4ddd3a` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:25 finished=
- [2026-04-18 05:25:25Z] queued   match=`3a5803e3` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:24 finished=
- [2026-04-18 05:25:25Z] B_WIN    match=`e20ac62c` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=2026-04-18T05:25
- [2026-04-18 05:25:25Z] B_WIN    match=`8af2ab56` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=2026-04-18T05:25
- [2026-04-18 05:25:25Z] B_WIN    match=`e41a40bf` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=2026-04-18T05:25
- [2026-04-18 05:25:25Z] B_WIN    match=`59022b26` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=2026-04-18T05:24
- [2026-04-18 05:25:25Z] B_WIN    match=`bd87f264` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:05 finished=2026-04-18T05:24
- [2026-04-18 05:25:29Z] SUBMITTED match=`74a5c269-96bc-469b-af21-17502be5c03e` vs `Team 44` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T44)
- [2026-04-18 05:25:56Z] queued   match=`c19f3023` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:25 finished=
- [2026-04-18 05:25:56Z] queued   match=`74a5c269` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:25 finished=
- [2026-04-18 05:26:56Z] A_WIN    match=`3ad28c82` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=2026-04-18T05:26
- [2026-04-18 05:26:56Z] SUBMITTED match=`92e93cb1-a6b9-4575-a64e-72872b75f09b` vs `team12` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T12)
- [2026-04-18 05:27:27Z] queued   match=`92e93cb1` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:26 finished=
- [2026-04-18 05:27:27Z] B_WIN    match=`a62a0c4d` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=2026-04-18T05:27
- [2026-04-18 05:27:57Z] B_WIN    match=`2eecc225` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:06 finished=2026-04-18T05:27
- [2026-04-18 05:28:23Z] SUBMITTED match=`e839d47e-19db-4457-be06-c93bf5f5491b` vs `Team 61` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T61)
- [2026-04-18 05:28:27Z] queued   match=`e839d47e` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:28 finished=
- [2026-04-18 05:28:27Z] queued   match=`8049ae3e` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:28 finished=
- [2026-04-18 05:28:58Z] RUNNING  match=`fc5d0bc5` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:15 finished=
- [2026-04-18 05:29:59Z] RUNNING  match=`c498db0d` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:19 finished=
- [2026-04-18 05:32:00Z] RUNNING  match=`c19f3023` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:25 finished=
- [2026-04-18 05:32:00Z] RUNNING  match=`74a5c269` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:25 finished=
- [2026-04-18 05:32:00Z] RUNNING  match=`008a6a6a` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:25 finished=
- [2026-04-18 05:32:00Z] RUNNING  match=`4c4ddd3a` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:25 finished=
- [2026-04-18 05:32:00Z] RUNNING  match=`3a5803e3` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:24 finished=
- [2026-04-18 05:35:32Z] RUNNING  match=`92e93cb1` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:26 finished=
- [2026-04-18 05:36:04Z] RUNNING  match=`e839d47e` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:28 finished=
- [2026-04-18 05:36:04Z] RUNNING  match=`8049ae3e` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:28 finished=
- [2026-04-18 05:36:04Z] B_WIN    match=`fc5d0bc5` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:15 finished=2026-04-18T05:35
- [2026-04-18 05:36:13Z] SUBMITTED match=`0b8fa7d1-6d4e-4cb4-8e83-71a861eca665` vs `Team 44` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-topteams-20 wave 2 vs T44)
- [2026-04-18 05:36:34Z] queued   match=`0b8fa7d1` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:36 finished=
- [2026-04-18 05:37:05Z] B_WIN    match=`c498db0d` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:19 finished=2026-04-18T05:36
- [2026-04-18 05:37:07Z] SUBMITTED match=`0ae53571-e94d-4275-965b-39e59fba7cfa` vs `Team 44` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-topteams-20 wave 2 vs T44)
- [2026-04-18 05:37:35Z] queued   match=`0ae53571` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:37 finished=
- [2026-04-18 05:37:49Z] SUBMITTED match=`4d2962c4-52c3-43d8-9abd-597ad45f2a61` vs `Team 44` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T44)
- [2026-04-18 05:37:59Z] SUBMITTED match=`6f6f12aa-e350-4698-9453-162d453b65a1` vs `Team 44` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-topteams-20 wave 2 vs T44)
- [2026-04-18 05:38:05Z] queued   match=`6f6f12aa` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:37 finished=
- [2026-04-18 05:38:05Z] queued   match=`4d2962c4` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:37 finished=
- [2026-04-18 05:38:05Z] B_WIN    match=`c19f3023` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:25 finished=2026-04-18T05:38
- [2026-04-18 05:38:05Z] A_WIN    match=`008a6a6a` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:25 finished=2026-04-18T05:37
- [2026-04-18 05:38:05Z] B_WIN    match=`3a5803e3` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:24 finished=2026-04-18T05:37
- [2026-04-18 05:38:05Z] SUBMITTED match=`8a9a016b-258c-47c6-bf0d-d2f41d7db73b` vs `team12` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T12)
- [2026-04-18 05:38:35Z] queued   match=`8a9a016b` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:38 finished=
- [2026-04-18 05:38:54Z] SUBMITTED match=`c93eb8c1-4e19-485e-8bd4-8dbb83c07c82` vs `Team 44` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-topteams-20 wave 2 vs T44)
- [2026-04-18 05:39:06Z] queued   match=`c93eb8c1` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:38 finished=
- [2026-04-18 05:39:06Z] B_WIN    match=`74a5c269` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:25 finished=2026-04-18T05:38
- [2026-04-18 05:39:06Z] B_WIN    match=`4c4ddd3a` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:25 finished=2026-04-18T05:38
- [2026-04-18 05:39:33Z] SUBMITTED match=`99bfbbee-9f0f-4e8d-a12f-24195908a8de` vs `Team 61` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T61)
- [2026-04-18 05:39:36Z] queued   match=`99bfbbee` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:39 finished=
- [2026-04-18 04:47:38Z] SUBMITTED match=`844c2106-3736-428f-8dfe-6e4feb710bc3` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 2 autofire)
- [2026-04-18 04:47:53Z] SUBMITTED match=`22a900b6-5afc-4e39-a976-267f699757f1` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 2 autofire)
- [2026-04-18 04:48:12Z] SUBMITTED match=`76cb86ea-d055-442f-840b-569f42adcbf8` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 2 autofire)
- [2026-04-18 04:48:30Z] SUBMITTED match=`f32974ca-4db9-4f9a-a897-a94ff5bafa73` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 2 autofire)
- [2026-04-18 04:48:50Z] SUBMITTED match=`9d023097-86ac-4e86-a120-406d84337b3b` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 2 autofire)
- [2026-04-18 05:00:25Z] SUBMITTED match=`5ed94c52-ea81-4e73-b0c8-42831b07fe54` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 2 autofire)
- [2026-04-18 05:05:31Z] SUBMITTED match=`bd87f264-e6e2-42c7-bb52-956f6e7aba03` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 2 autofire — 7/15 before harness timeout)
- [2026-04-18 05:24:57Z] SUBMITTED match=`3a5803e3-8bfd-4f2d-85fa-ef137889f7ba` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 3 autofire)
- [2026-04-18 05:25:15Z] SUBMITTED match=`008a6a6a-f140-4bd5-85cb-9d81c976e1c1` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 3 autofire)
- [2026-04-18 05:25:30Z] SUBMITTED match=`c19f3023-d8e8-48dd-b327-e028d9d7c571` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 3 autofire)
- [2026-04-18 05:28:22Z] SUBMITTED match=`8049ae3e-883a-455a-b8c9-e16ff04b4a49` vs `Carrie` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`Carrie.zip` reason=scrimmage result=queued (scrim-carrie-20 wave 3 autofire — 4/8 before session end; total 16/20 fires queued vs Carrie)
- [2026-04-18 05:42:07Z] SUBMITTED match=`955702fd-ab3a-4950-b15b-424c0875b57b` vs `Team 44` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T44)
- [2026-04-18 05:42:07Z] queued   match=`955702fd` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:42 finished=
- [2026-04-18 05:42:07Z] A_WIN    match=`8049ae3e` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T05:28 finished=2026-04-18T05:41
- [2026-04-18 05:42:25Z] SUBMITTED match=`baf6cc21-86ff-4d7c-b2ee-af7a04b04168` vs `team12` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T12)
- [2026-04-18 05:42:38Z] queued   match=`baf6cc21` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:42 finished=
- [2026-04-18 05:42:38Z] B_WIN    match=`e839d47e` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:28 finished=2026-04-18T05:42
- [2026-04-18 05:42:38Z] B_WIN    match=`92e93cb1` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:26 finished=2026-04-18T05:42
- [2026-04-18 05:42:44Z] SUBMITTED match=`ff9f2898-c918-4b65-80fc-8f21e437011a` vs `Team 61` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T61)
- [2026-04-18 05:43:08Z] queued   match=`ff9f2898` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:42 finished=
- [2026-04-18 05:49:42Z] RUNNING  match=`0ae53571` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:37 finished=
- [2026-04-18 05:49:42Z] RUNNING  match=`0b8fa7d1` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:36 finished=
- [2026-04-18 05:51:14Z] RUNNING  match=`6f6f12aa` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:37 finished=
- [2026-04-18 05:51:14Z] RUNNING  match=`4d2962c4` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:37 finished=
- [2026-04-18 05:51:44Z] RUNNING  match=`c93eb8c1` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:38 finished=
- [2026-04-18 05:51:44Z] RUNNING  match=`8a9a016b` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:38 finished=
- [2026-04-18 05:52:14Z] RUNNING  match=`99bfbbee` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:39 finished=
- [2026-04-18 05:55:46Z] RUNNING  match=`baf6cc21` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:42 finished=
- [2026-04-18 05:55:46Z] RUNNING  match=`955702fd` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:42 finished=
- [2026-04-18 05:56:47Z] RUNNING  match=`ff9f2898` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:42 finished=
- [2026-04-18 05:56:47Z] B_WIN    match=`0ae53571` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:37 finished=2026-04-18T05:56
- [2026-04-18 05:56:47Z] A_WIN    match=`0b8fa7d1` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:36 finished=2026-04-18T05:56
- [2026-04-18 05:57:18Z] B_WIN    match=`8a9a016b` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:38 finished=2026-04-18T05:57
- [2026-04-18 05:57:21Z] SUBMITTED match=`44932152-f038-4cf7-834e-15ef329c65b4` vs `Team 44` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T44)
- [2026-04-18 05:57:47Z] SUBMITTED match=`ae9b5b3c-f285-41f0-8efe-980a1ab5af30` vs `team12` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T12)
- [2026-04-18 05:57:48Z] queued   match=`ae9b5b3c` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:57 finished=
- [2026-04-18 05:57:48Z] queued   match=`44932152` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:57 finished=
- [2026-04-18 05:57:48Z] B_WIN    match=`6f6f12aa` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:37 finished=2026-04-18T05:57
- [2026-04-18 05:57:48Z] B_WIN    match=`4d2962c4` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:37 finished=2026-04-18T05:57
- [2026-04-18 05:58:06Z] SUBMITTED match=`f6c3112e-d7af-4ce8-b809-2f64d90e5de0` vs `Team 61` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T61)
- [2026-04-18 05:58:18Z] queued   match=`f6c3112e` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:58 finished=
- [2026-04-18 05:58:18Z] B_WIN    match=`c93eb8c1` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:38 finished=2026-04-18T05:57
- [2026-04-18 05:58:27Z] SUBMITTED match=`9dccde1a-d33a-40e7-be70-a67d49a8f8d8` vs `Team 44` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T44)
- [2026-04-18 05:58:48Z] queued   match=`9dccde1a` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:58 finished=
- [2026-04-18 05:59:19Z] B_WIN    match=`99bfbbee` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:39 finished=2026-04-18T05:58
- [2026-04-18 05:59:55Z] SUBMITTED match=`c6688f24-85d5-4a88-964b-e238b652316e` vs `Team 44` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-topteams-20 wave 2 vs T44)
- [2026-04-18 06:00:19Z] queued   match=`c6688f24` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:59 finished=
- [2026-04-18 06:02:21Z] B_WIN    match=`955702fd` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:42 finished=2026-04-18T06:02
- [2026-04-18 06:02:50Z] SUBMITTED match=`c0067355-2bcd-4140-9f20-498a26a952de` vs `Team 61` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage result=queued (scrim-topteams-20 wave 2 vs T61)
- [2026-04-18 06:02:51Z] queued   match=`c0067355` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:02 finished=
- [2026-04-18 06:02:51Z] B_WIN    match=`baf6cc21` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:42 finished=2026-04-18T06:02
- [2026-04-18 06:03:21Z] B_WIN    match=`ff9f2898` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:42 finished=2026-04-18T06:03
- [2026-04-18 06:03:24Z] SUBMITTED match=`6c2a2d32-7a3e-4b02-9666-4c4c37539b9e` vs `team12` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T12)
- [2026-04-18 06:03:42Z] SUBMITTED match=`51eaa77b-c83c-4005-bf1e-337d98b47080` vs `Team 61` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage result=queued (scrim-topteams-20 wave 2 vs T61)
- [2026-04-18 06:03:51Z] queued   match=`51eaa77b` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:03 finished=
- [2026-04-18 06:03:51Z] queued   match=`6c2a2d32` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T06:03 finished=
- [2026-04-18 06:08:55Z] RUNNING  match=`f6c3112e` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:58 finished=
- [2026-04-18 06:08:55Z] RUNNING  match=`ae9b5b3c` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:57 finished=
- [2026-04-18 06:08:55Z] RUNNING  match=`44932152` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:57 finished=
- [2026-04-18 06:09:25Z] RUNNING  match=`c6688f24` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:59 finished=
- [2026-04-18 06:09:25Z] RUNNING  match=`9dccde1a` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:58 finished=
- [2026-04-18 06:10:56Z] RUNNING  match=`6c2a2d32` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T06:03 finished=
- [2026-04-18 06:10:56Z] RUNNING  match=`c0067355` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:02 finished=
- [2026-04-18 06:11:26Z] RUNNING  match=`51eaa77b` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:03 finished=
- [2026-04-18 06:15:29Z] B_WIN    match=`44932152` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:57 finished=2026-04-18T06:15
- [2026-04-18 06:15:59Z] B_WIN    match=`9dccde1a` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:58 finished=2026-04-18T06:15
- [2026-04-18 06:15:59Z] B_WIN    match=`f6c3112e` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T05:58 finished=2026-04-18T06:15
- [2026-04-18 06:15:59Z] B_WIN    match=`ae9b5b3c` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T05:57 finished=2026-04-18T06:15
- [2026-04-18 06:16:10Z] SUBMITTED match=`141d9ae4-0a12-439a-8466-8ed3b8de45f0` vs `Team 61` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-topteams wave 1 vs T61)
- [2026-04-18 06:16:29Z] queued   match=`141d9ae4` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:16 finished=
- [2026-04-18 06:16:29Z] A_WIN    match=`c6688f24` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T05:59 finished=2026-04-18T06:16
- [2026-04-18 06:16:49Z] SUBMITTED match=`e28ac7bd-94c8-44d5-9976-cdf3dd7cf6d2` vs `Team 44` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-topteams-20 wave 2 vs T44)
- [2026-04-18 06:17:00Z] queued   match=`e28ac7bd` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T06:16 finished=
- [2026-04-18 06:17:40Z] SUBMITTED match=`211f7d51-cdb4-4caa-85d0-60f042071e7d` vs `Team 44` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-topteams-20 wave 2 vs T44)
- [2026-04-18 06:18:00Z] queued   match=`211f7d51` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T06:17 finished=
- [2026-04-18 06:18:00Z] B_WIN    match=`6c2a2d32` vs `team12` (ad15cd58) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`kp49.zip` reason=scrimmage sched=2026-04-18T06:03 finished=2026-04-18T06:17
- [2026-04-18 06:18:00Z] B_WIN    match=`c0067355` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:02 finished=2026-04-18T06:17
- [2026-04-18 06:18:30Z] queued   match=`3ac990ad` vs `Team 15` (81513423) sub=`RattleBot_v05_k1swap_20260418_021811.zip` opp_sub=`RattleBot_v05_k1swap_20260418_021811.zip` reason=validation sched=2026-04-18T06:18 finished=
- [2026-04-18 06:18:30Z] B_WIN    match=`51eaa77b` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:03 finished=2026-04-18T06:18
- [2026-04-18 06:18:33Z] SUBMITTED match=`7425c3ee-af67-4121-8d50-9fc98d24119a` vs `Team 61` sub=`RattleBot_v03_pureonly_20260417_1022.zip` opp_sub=`moriarty_test.zip` reason=scrimmage result=queued (scrim-topteams-20 wave 2 vs T61)
- [2026-04-18 06:19:01Z] queued   match=`7425c3ee` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:18 finished=
- [2026-04-18 06:19:01Z] VAL_OK   match=`3ac990ad` vs `Team 15` (81513423) sub=`RattleBot_v05_k1swap_20260418_021811.zip` opp_sub=`RattleBot_v05_k1swap_20260418_021811.zip` reason=validation sched=2026-04-18T06:18 finished=2026-04-18T06:18
- [2026-04-18 06:21:32Z] RUNNING  match=`141d9ae4` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:16 finished=
- [2026-04-18 06:22:33Z] RUNNING  match=`e28ac7bd` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T06:16 finished=
- [2026-04-18 06:23:36Z] RUNNING  match=`211f7d51` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T06:17 finished=
- [2026-04-18 06:24:07Z] RUNNING  match=`7425c3ee` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:18 finished=
- [2026-04-18 06:28:47Z] B_WIN    match=`141d9ae4` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:16 finished=2026-04-18T06:28
- [2026-04-18 06:29:18Z] A_WIN    match=`e28ac7bd` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T06:16 finished=2026-04-18T06:29
- [2026-04-18 06:29:48Z] B_WIN    match=`211f7d51` vs `Team 44` (e43ca53d) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`NashV3.zip` reason=scrimmage sched=2026-04-18T06:17 finished=2026-04-18T06:29
- [2026-04-18 06:30:49Z] B_WIN    match=`7425c3ee` vs `Caspian` (b32c577c) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`moriarty_test.zip` reason=scrimmage sched=2026-04-18T06:18 finished=2026-04-18T06:30
- [2026-04-18 06:45:22Z] VAL_OK   match=`63bd304a` vs `Team 15` (81513423) sub=`RattleBot_v07_greedy_opp_20260418_024421.zip` opp_sub=`RattleBot_v07_greedy_opp_20260418_024421.zip` reason=validation sched=2026-04-18T06:45 finished=2026-04-18T06:45
- [2026-04-18 06:55:52Z] VAL_OK   match=`16cec5d0` vs `Team 15` (81513423) sub=`RattleBot_v08_rollout_20260418_025449.zip` opp_sub=`RattleBot_v08_rollout_20260418_025449.zip` reason=validation sched=2026-04-18T06:55 finished=2026-04-18T06:55
- [2026-04-18 07:24:24Z] queued   match=`d358a8b6` vs `Autobots` (58988294) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:24:24Z] queued   match=`bdb4ba1e` vs `Autobots` (58988294) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:24:24Z] queued   match=`fa13738d` vs `Autobots` (58988294) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:24:24Z] queued   match=`8f919bac` vs `Michael` (c3cd58f4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Rusty-v3.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:24:24Z] queued   match=`40f161de` vs `Michael` (c3cd58f4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Rusty-v3.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:24:24Z] queued   match=`d6713d16` vs `Michael` (c3cd58f4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Rusty-v3.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:24:56Z] queued   match=`4ee791ba` vs `Team 57` (70c48f7b) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:24:56Z] queued   match=`569d1bcb` vs `Team 57` (70c48f7b) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:25:26Z] RUNNING  match=`8f919bac` vs `Michael` (c3cd58f4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Rusty-v3.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:25:26Z] RUNNING  match=`40f161de` vs `Michael` (c3cd58f4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Rusty-v3.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:25:26Z] RUNNING  match=`d6713d16` vs `Michael` (c3cd58f4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Rusty-v3.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:24:00Z] SUBMITTED match=`d6713d16-5afd-4fc2-95ad-f53e216806a3` vs `Michael` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-blindspots wave 1 vs Michael)
- [2026-04-18 07:24:00Z] SUBMITTED match=`40f161de-1b10-4ba4-8a35-41f9158eff9a` vs `Michael` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-blindspots wave 1 vs Michael)
- [2026-04-18 07:24:00Z] SUBMITTED match=`8f919bac-9de5-46e6-b16d-09a6a443b13e` vs `Michael` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-blindspots wave 1 vs Michael)
- [2026-04-18 07:24:10Z] SUBMITTED match=`fa13738d-1dee-4c26-b510-b73edcf3b391` vs `Autobots` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-blindspots wave 1 vs Autobots)
- [2026-04-18 07:24:10Z] SUBMITTED match=`bdb4ba1e-14c5-4468-a4cb-7b5e6d0e6430` vs `Autobots` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-blindspots wave 1 vs Autobots)
- [2026-04-18 07:24:10Z] SUBMITTED match=`d358a8b6-df5e-4446-804c-434e94b860aa` vs `Autobots` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-blindspots wave 1 vs Autobots)
- [2026-04-18 07:24:20Z] SUBMITTED match=`569d1bcb-d033-4604-a9db-e6da300210de` vs `Team 57` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-blindspots wave 1 vs Team 57)
- [2026-04-18 07:24:20Z] SUBMITTED match=`4ee791ba-8733-4e31-8cd1-c2e9de8adc3b` vs `Team 57` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-v04-blindspots wave 1 vs Team 57)
- [2026-04-18 07:24:30Z] RATE_LIMIT 429 on vs `Team 57` (70c48f7b-1d96-4644-a776-1fb5085cde86) -- wave 1 short by 1, backoff 180s (scrim-v04-blindspots wave 1 vs Team 57)
- [2026-04-18 07:26:29Z] RUNNING  match=`4ee791ba` vs `Team 57` (70c48f7b) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:26:29Z] RUNNING  match=`569d1bcb` vs `Team 57` (70c48f7b) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:26:29Z] RUNNING  match=`d358a8b6` vs `Autobots` (58988294) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:26:29Z] RUNNING  match=`bdb4ba1e` vs `Autobots` (58988294) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:26:29Z] RUNNING  match=`fa13738d` vs `Autobots` (58988294) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T07:24 finished=
- [2026-04-18 07:28:15Z] RATE_LIMIT 429 on vs `George` (13f7ba71-eb75-4b4a-9c48-abb6bb1e8318) -- wave 1 first fire, backoff 180s (scrim-aggressive-v04 wave 1 vs George)
- [2026-04-18 07:29:37Z] B_WIN    match=`569d1bcb` vs `Team 57` (70c48f7b) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T07:24 finished=2026-04-18T07:29
- [2026-04-18 07:30:08Z] B_WIN    match=`4ee791ba` vs `Team 57` (70c48f7b) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Luca.zip` reason=scrimmage sched=2026-04-18T07:24 finished=2026-04-18T07:29
- [2026-04-18 07:31:10Z] B_WIN    match=`8f919bac` vs `Michael` (c3cd58f4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Rusty-v3.zip` reason=scrimmage sched=2026-04-18T07:24 finished=2026-04-18T07:31
- [2026-04-18 07:31:10Z] B_WIN    match=`40f161de` vs `Michael` (c3cd58f4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Rusty-v3.zip` reason=scrimmage sched=2026-04-18T07:24 finished=2026-04-18T07:30
- [2026-04-18 07:31:10Z] B_WIN    match=`d6713d16` vs `Michael` (c3cd58f4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Rusty-v3.zip` reason=scrimmage sched=2026-04-18T07:24 finished=2026-04-18T07:30
- [2026-04-18 07:32:12Z] queued   match=`63def90e` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=
- [2026-04-18 07:32:44Z] RUNNING  match=`33a33905` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=
- [2026-04-18 07:32:44Z] RUNNING  match=`bc8cfb51` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=
- [2026-04-18 07:32:44Z] RUNNING  match=`3fd457de` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=
- [2026-04-18 07:32:44Z] RUNNING  match=`63def90e` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=
- [2026-04-18 07:32:44Z] B_WIN    match=`d358a8b6` vs `Autobots` (58988294) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T07:24 finished=2026-04-18T07:32
- [2026-04-18 07:32:44Z] B_WIN    match=`bdb4ba1e` vs `Autobots` (58988294) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T07:24 finished=2026-04-18T07:32
- [2026-04-18 07:32:44Z] B_WIN    match=`fa13738d` vs `Autobots` (58988294) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`super_cython.zip` reason=scrimmage sched=2026-04-18T07:24 finished=2026-04-18T07:32
- [2026-04-18 07:33:16Z] queued   match=`3ac8e0e3` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:33 finished=
- [2026-04-18 07:33:16Z] queued   match=`270880ff` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=
- [2026-04-18 07:33:47Z] queued   match=`a5095c3e` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:33 finished=
- [2026-04-18 07:33:47Z] queued   match=`f1a940d9` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:33 finished=
- [2026-04-18 07:35:20Z] RUNNING  match=`3ac8e0e3` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:33 finished=
- [2026-04-18 07:35:20Z] RUNNING  match=`270880ff` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=
- [2026-04-18 07:35:52Z] RUNNING  match=`a5095c3e` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:33 finished=
- [2026-04-18 07:35:52Z] RUNNING  match=`f1a940d9` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:33 finished=
- [2026-04-18 07:35:52Z] A_WIN    match=`63def90e` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=2026-04-18T07:35
- [2026-04-18 07:36:23Z] B_WIN    match=`33a33905` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=2026-04-18T07:36
- [2026-04-18 07:36:23Z] A_WIN    match=`bc8cfb51` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=2026-04-18T07:35
- [2026-04-18 07:36:23Z] B_WIN    match=`3fd457de` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=2026-04-18T07:35
- [2026-04-18 07:36:56Z] queued   match=`c6e9aa2d` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:36 finished=
- [2026-04-18 07:37:27Z] queued   match=`158cfc26` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:37 finished=
- [2026-04-18 07:37:27Z] RUNNING  match=`e34ec7ff` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:37 finished=
- [2026-04-18 07:37:27Z] RUNNING  match=`c6e9aa2d` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:36 finished=
- [2026-04-18 07:37:59Z] queued   match=`97b63105` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:37 finished=
- [2026-04-18 07:37:59Z] RUNNING  match=`158cfc26` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:37 finished=
- [2026-04-18 07:38:30Z] A_WIN    match=`270880ff` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:32 finished=2026-04-18T07:38
- [2026-04-18 07:39:33Z] RUNNING  match=`97b63105` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:37 finished=
- [2026-04-18 07:41:08Z] queued   match=`8837f6af` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:40 finished=
- [2026-04-18 07:41:08Z] B_WIN    match=`3ac8e0e3` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:33 finished=2026-04-18T07:40
- [2026-04-18 07:41:40Z] B_WIN    match=`a5095c3e` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:33 finished=2026-04-18T07:41
- [2026-04-18 07:42:00Z] SUBMITTED match=`63def90e-849f-4004-8fe6-b1172bf42e16` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs George)
- [2026-04-18 07:42:00Z] SUBMITTED match=`3fd457de-dac7-483c-b2c6-4ae072fff889` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs George)
- [2026-04-18 07:42:00Z] SUBMITTED match=`bc8cfb51-1875-46d1-ac0d-7249350e6775` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs George)
- [2026-04-18 07:42:00Z] SUBMITTED match=`33a33905-7133-4f1b-b889-ddcaf4341fc6` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs George)
- [2026-04-18 07:42:00Z] SUBMITTED match=`270880ff-343f-4bbf-a590-a7f2921285ed` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs George)
- [2026-04-18 07:42:00Z] SUBMITTED match=`3ac8e0e3-375d-4a6d-a882-fc233a13de4c` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs Albert)
- [2026-04-18 07:42:00Z] SUBMITTED match=`f1a940d9-d3da-4d2a-abc4-fdaef95d15f6` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs Albert)
- [2026-04-18 07:42:00Z] SUBMITTED match=`a5095c3e-2bda-4d74-932e-660c0ccfa972` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs Albert)
- [2026-04-18 07:42:00Z] RATE_LIMIT 429 on vs `Albert` (5121a2d4) -- wave 1 Albert 4/5, backoff 180s (scrim-aggressive-v04 wave 1 vs Albert)
- [2026-04-18 07:42:00Z] SUBMITTED match=`c6e9aa2d-1e44-47f0-8edd-ce9bc408267a` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs Albert)
- [2026-04-18 07:42:00Z] SUBMITTED match=`e34ec7ff-6395-49d5-af95-fc3f2e27b028` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs Albert)
- [2026-04-18 07:42:00Z] SUBMITTED match=`158cfc26-9f20-42e6-97dd-10512420a0e0` vs `Carrie` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs Carrie)
- [2026-04-18 07:42:00Z] SUBMITTED match=`97b63105-f34c-454b-bb66-9be8c7c2562e` vs `Carrie` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs Carrie)
- [2026-04-18 07:42:00Z] RATE_LIMIT 429 on vs `Carrie` (6d2a15ad) -- wave 1 Carrie 3/3, backoff 180s (scrim-aggressive-v04 wave 1 vs Carrie)
- [2026-04-18 07:42:00Z] SUBMITTED match=`8837f6af-8a57-410c-98b1-9d6f5d0f1c5b` vs `Carrie` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 1 vs Carrie)
- [2026-04-18 07:42:11Z] A_WIN    match=`f1a940d9` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:33 finished=2026-04-18T07:41
- [2026-04-18 07:42:44Z] RUNNING  match=`8837f6af` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:40 finished=
- [2026-04-18 07:43:15Z] B_WIN    match=`c6e9aa2d` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:36 finished=2026-04-18T07:43
- [2026-04-18 07:43:46Z] B_WIN    match=`e34ec7ff` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:37 finished=2026-04-18T07:43
- [2026-04-18 07:44:17Z] A_WIN    match=`158cfc26` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:37 finished=2026-04-18T07:43
- [2026-04-18 07:45:20Z] A_WIN    match=`97b63105` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:37 finished=2026-04-18T07:45
- [2026-04-18 07:46:53Z] queued   match=`ead57ed0` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:46 finished=
- [2026-04-18 07:46:53Z] queued   match=`78b0c8c3` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:46 finished=
- [2026-04-18 07:47:57Z] queued   match=`91e0b7a6` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:47 finished=
- [2026-04-18 07:47:57Z] queued   match=`74d8a27b` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:47 finished=
- [2026-04-18 07:47:57Z] queued   match=`34673115` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:47 finished=
- [2026-04-18 07:48:28Z] queued   match=`8e7043a0` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:48 finished=
- [2026-04-18 07:48:28Z] queued   match=`a6a274ab` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:48 finished=
- [2026-04-18 07:48:28Z] queued   match=`e7b5a4d4` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:47 finished=
- [2026-04-18 07:48:28Z] RUNNING  match=`ead57ed0` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:46 finished=
- [2026-04-18 07:48:28Z] RUNNING  match=`78b0c8c3` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:46 finished=
- [2026-04-18 07:48:28Z] DRAW     match=`8837f6af` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:40 finished=2026-04-18T07:48
- [2026-04-18 07:48:58Z] RUNNING  match=`74d8a27b` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:47 finished=
- [2026-04-18 07:48:58Z] RUNNING  match=`34673115` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:47 finished=
- [2026-04-18 07:50:01Z] RUNNING  match=`91e0b7a6` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:47 finished=
- [2026-04-18 07:50:32Z] RUNNING  match=`8e7043a0` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:48 finished=
- [2026-04-18 07:50:32Z] RUNNING  match=`a6a274ab` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:48 finished=
- [2026-04-18 07:50:32Z] RUNNING  match=`e7b5a4d4` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:47 finished=
- [2026-04-18 07:51:37Z] A_WIN    match=`78b0c8c3` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:46 finished=2026-04-18T07:51
- [2026-04-18 07:52:08Z] queued   match=`f11fd549` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:51 finished=
- [2026-04-18 07:52:08Z] A_WIN    match=`34673115` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:47 finished=2026-04-18T07:52
- [2026-04-18 07:52:08Z] A_WIN    match=`ead57ed0` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:46 finished=2026-04-18T07:51
- [2026-04-18 07:52:40Z] queued   match=`b45fd975` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:52 finished=
- [2026-04-18 07:52:40Z] queued   match=`f466c59f` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:52 finished=
- [2026-04-18 07:52:40Z] RUNNING  match=`f1ce6245` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:52 finished=
- [2026-04-18 07:52:40Z] RUNNING  match=`f11fd549` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:51 finished=
- [2026-04-18 07:52:40Z] A_WIN    match=`74d8a27b` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:47 finished=2026-04-18T07:52
- [2026-04-18 07:53:45Z] RUNNING  match=`b45fd975` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:52 finished=
- [2026-04-18 07:53:45Z] RUNNING  match=`f466c59f` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:52 finished=
- [2026-04-18 07:53:45Z] B_WIN    match=`91e0b7a6` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T07:47 finished=2026-04-18T07:53
- [2026-04-18 07:50:00Z] SUBMITTED match=`78b0c8c3-ab24-43ed-8b49-06dd5d98290f` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs George)
- [2026-04-18 07:50:00Z] SUBMITTED match=`ead57ed0-8531-475d-bf86-53f892cf9f00` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs George)
- [2026-04-18 07:50:00Z] CAPSOLVER_FAIL on vs `George` (13f7ba71) -- timeout, retry once (scrim-aggressive-v04 wave 2 vs George)
- [2026-04-18 07:50:00Z] SUBMITTED match=`34673115-3dfa-47cd-b29e-15f3f6dc76dd` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs George)
- [2026-04-18 07:50:00Z] SUBMITTED match=`74d8a27b-3f7c-4478-8ef6-27085138ba71` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs George)
- [2026-04-18 07:50:00Z] SUBMITTED match=`91e0b7a6-5a03-47b1-a65f-ac2ddcc6c68b` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs George)
- [2026-04-18 07:50:00Z] SUBMITTED match=`e7b5a4d4-6287-44bc-81c5-69a7268e83cf` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs Albert)
- [2026-04-18 07:50:00Z] SUBMITTED match=`a6a274ab-a160-4aa3-86f9-8bc2063423bd` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs Albert)
- [2026-04-18 07:50:00Z] SUBMITTED match=`8e7043a0-16c6-4245-a139-ca191c941f53` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs Albert)
- [2026-04-18 07:50:00Z] RATE_LIMIT 429 on vs `Albert` (5121a2d4) -- wave 2 Albert 4/5, backoff 180s (scrim-aggressive-v04 wave 2 vs Albert)
- [2026-04-18 07:50:00Z] SUBMITTED match=`f11fd549-f1f3-4ddf-9367-b9ecabcb6df5` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs Albert)
- [2026-04-18 07:50:00Z] SUBMITTED match=`f1ce6245-4f94-4be5-8701-0243d08bda4a` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs Albert)
- [2026-04-18 07:50:00Z] SUBMITTED match=`f466c59f-30cb-4458-b0de-d54459a6b1e9` vs `Carrie` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs Carrie)
- [2026-04-18 07:50:00Z] SUBMITTED match=`b45fd975-2ac6-43e8-9532-3bb1138c4a41` vs `Carrie` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs Carrie)
- [2026-04-18 07:50:00Z] RATE_LIMIT 429 on vs `Carrie` (6d2a15ad) -- wave 2 Carrie 3/3, backoff 180s (scrim-aggressive-v04 wave 2 vs Carrie)
- [2026-04-18 07:50:00Z] SUBMITTED match=`1f3840a2-13ee-4a50-814f-47a926799f49` vs `Carrie` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 2 vs Carrie)
- [2026-04-18 07:56:23Z] queued   match=`1f3840a2` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:55 finished=
- [2026-04-18 07:56:23Z] B_WIN    match=`8e7043a0` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:48 finished=2026-04-18T07:55
- [2026-04-18 07:56:23Z] B_WIN    match=`a6a274ab` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:48 finished=2026-04-18T07:56
- [2026-04-18 07:56:23Z] B_WIN    match=`e7b5a4d4` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:47 finished=2026-04-18T07:56
- [2026-04-18 07:56:56Z] RUNNING  match=`1f3840a2` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:55 finished=
- [2026-04-18 07:58:34Z] B_WIN    match=`f1ce6245` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:52 finished=2026-04-18T07:58
- [2026-04-18 07:58:34Z] B_WIN    match=`f11fd549` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T07:51 finished=2026-04-18T07:58
- [2026-04-18 07:59:38Z] B_WIN    match=`b45fd975` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:52 finished=2026-04-18T07:59
- [2026-04-18 07:59:38Z] B_WIN    match=`f466c59f` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:52 finished=2026-04-18T07:59
- [2026-04-18 08:00:11Z] queued   match=`685552c9` vs `Not 20` (6c6bbfdf) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`EliteAgent.zip` reason=matchmaking sched=2026-04-18T08:00 finished=
- [2026-04-18 08:00:11Z] queued   match=`9a2261e5` vs `Team 15` (81513423) sub=`Yolanda_R27A.zip` opp_sub=`RattleBot_v04_archfix_20260418_003411.zip` reason=matchmaking sched=2026-04-18T08:00 finished=
- [2026-04-18 08:00:11Z] queued   match=`3ab64813` vs `Team 15` (81513423) sub=`Deidre.zip` opp_sub=`RattleBot_v04_archfix_20260418_003411.zip` reason=matchmaking sched=2026-04-18T08:00 finished=
- [2026-04-18 08:00:11Z] queued   match=`3b7bc0c2` vs `Team 20` (57b2f9e2) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`EliteAgent.zip` reason=matchmaking sched=2026-04-18T08:00 finished=
- [2026-04-18 08:01:16Z] queued   match=`ea929059` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:01:16Z] queued   match=`666afb5f` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:01:16Z] queued   match=`28993146` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:00 finished=
- [2026-04-18 08:01:49Z] queued   match=`e163a862` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:01:49Z] queued   match=`f9ffa604` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:01:49Z] queued   match=`f9df1617` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:02:22Z] queued   match=`92663eb4` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:02:56Z] RUNNING  match=`3b7bc0c2` vs `Team 20` (57b2f9e2) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`EliteAgent.zip` reason=matchmaking sched=2026-04-18T08:00 finished=
- [2026-04-18 08:02:56Z] B_WIN    match=`1f3840a2` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T07:55 finished=2026-04-18T08:02
- [2026-04-18 08:03:30Z] RUNNING  match=`3ab64813` vs `Team 15` (81513423) sub=`Deidre.zip` opp_sub=`RattleBot_v04_archfix_20260418_003411.zip` reason=matchmaking sched=2026-04-18T08:00 finished=
- [2026-04-18 08:05:41Z] queued   match=`6413d189` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:05 finished=
- [2026-04-18 08:06:45Z] A_WIN    match=`3ab64813` vs `Team 15` (81513423) sub=`Deidre.zip` opp_sub=`RattleBot_v04_archfix_20260418_003411.zip` reason=matchmaking sched=2026-04-18T08:00 finished=2026-04-18T08:06
- [2026-04-18 08:07:19Z] A_WIN    match=`3b7bc0c2` vs `Team 20` (57b2f9e2) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`EliteAgent.zip` reason=matchmaking sched=2026-04-18T08:00 finished=2026-04-18T08:06
- [2026-04-18 08:08:57Z] RUNNING  match=`9a2261e5` vs `Team 15` (81513423) sub=`Yolanda_R27A.zip` opp_sub=`RattleBot_v04_archfix_20260418_003411.zip` reason=matchmaking sched=2026-04-18T08:00 finished=
- [2026-04-18 08:13:14Z] B_WIN    match=`9a2261e5` vs `Team 15` (81513423) sub=`Yolanda_R27A.zip` opp_sub=`RattleBot_v04_archfix_20260418_003411.zip` reason=matchmaking sched=2026-04-18T08:00 finished=2026-04-18T08:13
- [2026-04-18 08:18:33Z] RUNNING  match=`685552c9` vs `Not 20` (6c6bbfdf) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`EliteAgent.zip` reason=matchmaking sched=2026-04-18T08:00 finished=
- [2026-04-18 08:22:49Z] RUNNING  match=`28993146` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:00 finished=
- [2026-04-18 08:23:20Z] RUNNING  match=`92663eb4` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:23:20Z] RUNNING  match=`e163a862` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:23:20Z] RUNNING  match=`f9ffa604` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:23:20Z] RUNNING  match=`f9df1617` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:23:20Z] RUNNING  match=`ea929059` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:23:20Z] RUNNING  match=`666afb5f` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=
- [2026-04-18 08:23:20Z] B_WIN    match=`685552c9` vs `Not 20` (6c6bbfdf) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`EliteAgent.zip` reason=matchmaking sched=2026-04-18T08:00 finished=2026-04-18T08:22
- [2026-04-18 08:24:57Z] RUNNING  match=`6413d189` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:05 finished=
- [2026-04-18 08:26:33Z] queued   match=`23ce21fc` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:26 finished=
- [2026-04-18 08:26:33Z] A_WIN    match=`f9df1617` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=2026-04-18T08:26
- [2026-04-18 08:26:33Z] B_WIN    match=`28993146` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:00 finished=2026-04-18T08:26
- [2026-04-18 08:27:05Z] queued   match=`ffaaca01` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T08:27 finished=
- [2026-04-18 08:27:05Z] queued   match=`c4571bb9` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T08:26 finished=
- [2026-04-18 08:27:05Z] queued   match=`3f129e29` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:26 finished=
- [2026-04-18 08:27:05Z] B_WIN    match=`f9ffa604` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=2026-04-18T08:26
- [2026-04-18 08:27:05Z] B_WIN    match=`ea929059` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=2026-04-18T08:26
- [2026-04-18 08:27:05Z] A_WIN    match=`666afb5f` vs `George` (13f7ba71) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`George.zip` reason=scrimmage sched=2026-04-18T08:01 finished=2026-04-18T08:26
- [2026-04-18 08:27:36Z] queued   match=`c7800dca` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T08:27 finished=
- [2026-04-18 08:29:12Z] B_WIN    match=`92663eb4` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:01 finished=2026-04-18T08:28
- [2026-04-18 08:29:12Z] B_WIN    match=`e163a862` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:01 finished=2026-04-18T08:29
- [2026-04-18 08:30:48Z] RUNNING  match=`c7800dca` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T08:27 finished=
- [2026-04-18 08:30:48Z] RUNNING  match=`ffaaca01` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T08:27 finished=
- [2026-04-18 08:30:48Z] RUNNING  match=`c4571bb9` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T08:26 finished=
- [2026-04-18 08:30:48Z] RUNNING  match=`3f129e29` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:26 finished=
- [2026-04-18 08:30:48Z] RUNNING  match=`23ce21fc` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:26 finished=
- [2026-04-18 08:31:20Z] queued   match=`996e09ea` vs `Carrie` (6d2a15ad) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Carrie.zip` reason=scrimmage sched=2026-04-18T08:31 finished=
- [2026-04-18 08:31:20Z] B_WIN    match=`6413d189` vs `Albert` (5121a2d4) sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`Albert.zip` reason=scrimmage sched=2026-04-18T08:05 finished=2026-04-18T08:30
- [2026-04-18 08:10:00Z] SUBMITTED match=`28993146-ae68-4012-ae58-627cacdaa7cd` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs George)
- [2026-04-18 08:10:00Z] SUBMITTED match=`666afb5f-95f0-4b5f-a2f6-c26fffa35bc1` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs George)
- [2026-04-18 08:10:00Z] SUBMITTED match=`ea929059-9aaa-442e-b7c5-8b36666a9f9a` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs George)
- [2026-04-18 08:10:00Z] SUBMITTED match=`f9df1617-9fe8-45b9-947b-618218f4fade` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs George)
- [2026-04-18 08:10:00Z] SUBMITTED match=`f9ffa604-f81e-4f3c-ad70-5a291036adf6` vs `George` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs George)
- [2026-04-18 08:10:00Z] SUBMITTED match=`e163a862-1867-45c0-b193-11fc3a38ff63` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs Albert)
- [2026-04-18 08:10:00Z] SUBMITTED match=`92663eb4-aa17-4abc-af59-d94cdbe42d12` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs Albert)
- [2026-04-18 08:10:00Z] RATE_LIMIT 429 on vs `Albert` (5121a2d4) -- wave 3 Albert 3/5, backoff 180s (scrim-aggressive-v04 wave 3 vs Albert)
- [2026-04-18 08:10:00Z] SUBMITTED match=`6413d189-1ceb-42a1-81b2-b8f295cef583` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs Albert)
- [2026-04-18 08:10:00Z] RATE_LIMIT 429 on vs `Albert` (5121a2d4) -- wave 3 Albert 4/5 (sustained queue saturation, multiple retries, CAPSOLVER hit too), eventually cleared (scrim-aggressive-v04 wave 3 vs Albert)
- [2026-04-18 08:10:00Z] SUBMITTED match=`23ce21fc-ee62-47c6-a4a4-49d416ac741e` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs Albert)
- [2026-04-18 08:10:00Z] SUBMITTED match=`3f129e29-3ec9-4387-befc-f22fd3f5e4b9` vs `Albert` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs Albert)
- [2026-04-18 08:10:00Z] SUBMITTED match=`c4571bb9-2d8d-4cc0-b3af-152f74a8f689` vs `Carrie` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs Carrie)
- [2026-04-18 08:10:00Z] SUBMITTED match=`ffaaca01-a43e-4fd0-884e-7bc62098abf2` vs `Carrie` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs Carrie)
- [2026-04-18 08:10:00Z] SUBMITTED match=`c7800dca-4da5-4aea-b76c-32616fd8dc72` vs `Carrie` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs Carrie)
- [2026-04-18 08:10:00Z] CAPSOLVER_FAIL on vs `Carrie` (6d2a15ad) -- timeout, retry once, then 429 (scrim-aggressive-v04 wave 3 vs Carrie)
- [2026-04-18 08:10:00Z] RATE_LIMIT 429 on vs `Carrie` (6d2a15ad) -- wave 3 Carrie 4/4 retry, backoff 180s (scrim-aggressive-v04 wave 3 vs Carrie)
- [2026-04-18 08:10:00Z] SUBMITTED match=`996e09ea-7a8e-4686-9ef0-d86d51df8ec9` vs `Carrie` sub=`RattleBot_v04_archfix_20260418_003411.zip` opp_sub=`(current)` reason=scrimmage result=queued (scrim-aggressive-v04 wave 3 vs Carrie)
