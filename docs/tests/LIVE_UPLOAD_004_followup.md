# LIVE_UPLOAD_004_followup — George scrimmage poll (successor pass)

**Owner:** live-tester-2
**Date:** 2026-04-17
**Status:** George scrimmage is **STILL RUNNING at ~11 minutes** elapsed. Queue backlog is the bottleneck, not our match. No final outcome available yet. No ELO delta.

---

## 1. Team-page state at poll time

Polled `https://bytefight.org/compete/cs3600_sp2026/team` at approximately 2026-04-17 ~00:33 EDT (next matchmaking cycle was at 01:26:40 remaining, so poll occurred ~1h 27m before the 2026-04-17 02:00 EDT cycle).

Match History (all four rows unchanged from predecessor's snapshot):

| Opponent | Status   | Submission         | Type       | Age  |
|----------|----------|--------------------|------------|------|
| George   | RUNNING  | Yolanda_probe.zip  | scrimmage  | 11m  |
| Team 15  | WON      | Yolanda_probe.zip  | validation | 52m  |
| Team 15  | LOST     | FloorBot.zip       | validation | 1h   |
| Team 15  | LOST     | FloorBot.zip       | validation | 1h   |

Team state unchanged: 2 members (apatel3111, Rjav), "View Submission" link present (Yolanda still Current), 0W-0D-0L record, ELO chart empty.

## 2. Why the scrimmage hasn't finished — queue congestion, not our problem

Navigated to `/queue`. At poll time: **343 matches RUNNING site-wide**. Some scrimmages have been RUNNING for **1h+**. Our Team 15 vs George match is middle-of-the-pack at 11m, not stuck. Sample from the queue (ages increasing):

- `Team 89 vs Carrie` — 6s
- `FightAI vs George` — 1m (10 copies)
- `Team ra vs Albert Lite` — 2m (10 copies)
- `Group 63 vs George` — 2m (10 copies)
- **`Team 15 vs George`** — 11m (ours, 1 copy)
- `GT_Tournament vs Albert` — 8m
- `sabrina carpeter (t80) vs Albert` — 14m (many)
- Many matches at 1h+ still RUNNING

**Interpretation:** Other teams are submitting 10x-batched scrimmages against reference bots (George/Albert/Albert Lite/Carrie) as part of their own tuning. The bytefight scheduler is not parallelizing enough to keep up — matches that complete in ~seconds on the local engine are sitting in RUNNING for 10+ minutes on the server. This is a server-side throughput issue and expected to drain before the 2026-04-19 23:59 deadline.

**Good news:** Yolanda and Team 15 resources look fine — no error/crash indicators, just queue depth.

## 3. New learnings vs the predecessor's runbook

1. **Scrimmage latency has high variance** on bytefight. §5 of HANDOFF_TESTER_LIVE said "noticeably longer than validation (>4 min)" — that's a floor, not a ceiling. Plan for **10-60 minutes** wall-time for a single scrimmage vs reference bot during active periods. Validation matches (~20s) are unaffected because they don't queue the same way.
2. **The `/queue` page is useful diagnostic context.** Showing 343 RUNNING matches tells us our own match is not stuck — it's just waiting behind 200+ other students' scrimmages. Worth checking before raising false alarms.
3. **Matchmaking cycles (daily at 00:00 EDT)** do NOT appear to fight with user-submitted scrimmages for compute — the ~1.5h-away cycle wasn't "blocking" our scrimmage. The slowness is pure queue depth.

## 4. Actions taken

- Navigated `/team` → confirmed RUNNING, recorded match history.
- Navigated `/queue` → quantified site-wide backlog (343 RUNNING, our match at 11m position).
- Did **NOT** submit any new scrimmages (§F-14 budget preserved at 1 consumed).
- Did **NOT** change Current submission, delete submissions, or modify team.
- Yolanda remains Current, Yolanda remains valid. Partner slot remains empty.

## 5. Deliverables status vs task #30

| Deliverable                                                 | Status                    |
|-------------------------------------------------------------|---------------------------|
| Poll /team for George scrimmage outcome                     | DONE (still RUNNING @11m) |
| Capture final result / score diff / duration / ELO delta    | NOT POSSIBLE YET          |
| Write LIVE_UPLOAD_004_followup.md                           | DONE (this doc)           |
| Ping committer-2 with commit request                        | PENDING                   |
| Summary to team-lead                                        | PENDING                   |

## 6. Recommendation

The scrimmage will resolve eventually (plausibly within the next 1-2 hours given typical ByteFight queue drain). **Options for team-lead:**

- **(a) Wait for autonomous resolution:** another agent pass in ~1h can capture the final outcome. This doc already has the state-of-the-world; only the W/L/T flip and ELO delta need appending.
- **(b) Proceed with v0.2 / RattleBot uploads now:** the scrimmage outcome against George (expected: Yolanda LOSS, given random-mover vs greedy-prime) is diagnostic-only. Our actual grade-floor bot will displace Yolanda anyway. The scrimmage result does not block any upload decisions.
- **(c) Do not re-scrimmage George to "get it over with":** would consume another §F-14 budget slot and would likely land behind the 10+ minute queue again.

Leaning (b) + (a) in parallel — do the real work while the scrimmage drains.

## 7. Followup-of-the-followup checklist

Whoever picks up next:

1. `GET /team`. If the George row has flipped to WON/LOST/TIE, record the result, score diff (inspect DOM near the row if the `/team` page text doesn't show it — expand the row?), and any ELO delta on the ELO History chart.
2. Append that final outcome to this file in a §8 — do not start a new `005` document for the same scrimmage.
3. If RUNNING still shows at 1h+, consider checking `/queue` again — if the site-wide queue has shrunk, our match may have a pipeline issue specific to our bot. If queue is still 300+ backed up, keep waiting.
