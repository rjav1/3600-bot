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
