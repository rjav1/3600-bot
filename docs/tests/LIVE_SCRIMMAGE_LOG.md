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
