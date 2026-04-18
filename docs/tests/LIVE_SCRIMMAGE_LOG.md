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
