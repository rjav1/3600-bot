# SCRIMMAGE_WAVE_AUDIT — Correctness Risks of the 10-Opponent Batch Fire

**Auditor:** auditor
**Date:** 2026-04-17
**Scope:** the ~165-scrimmage, 10-opponent staggered batch-fire in progress per team-lead's GO memo. Audits correctness + data-integrity risks, not strategy.
**Sources:**
- `tools/bytefight_client.py` (start_scrimmage at line 559; set_current_submission at line 526)
- `tools/bytefight_poll.py` (match record fields at line 94-103)
- `docs/audit/SCRIMMAGE_LIMITS_INVESTIGATION.md` (queue-depth cap)
- `docs/tests/LIVE_SCRIMMAGE_LOG.md` (poller evidence).

---

## §1 — Current-submission drift risk

**Verdict: LOW RISK. Submission is pinned at scrimmage-create time, not at match-run time.**

Evidence:
- `start_scrimmage` at `bytefight_client.py:559-581` sends a POST to `/api/v1/game-match` with body containing ONLY `competitionSlug`, `ladder`, `teamAUuid`, `teamBUuid`, `count`, `matchSettings`. **No `submissionUuid` is sent.** The server looks up each team's Current submission at the moment the request is processed.
- The poller log (`bytefight_poll.py:94-95`, `LIVE_SCRIMMAGE_LOG.md`) shows every match record carries `submissionAName` and `submissionBName` fields populated at creation. Once created, these fields are immutable on the match record (verified empirically in SCRIMMAGE_LIMITS_INVESTIGATION §5 item 5 — in-flight matches keep their original submissions after set-current dances).
- Therefore: if another agent calls `set-current` mid-wave, only scrimmages CREATED AFTER the set-current call will use the new submission. Already-queued + already-running matches retain the original.

**Implication for the wave in progress:** as long as no agent calls `set-current` between the fire-calls of a single batch, every match in that batch uses the submission that was Current when the fire happened. If `set-current` fires between batches, later batches switch submissions — data-integrity-wise this is a SEGMENTATION not a CORRUPTION: each match record is self-describing via `submissionAName/B`, so post-hoc analysis can group by submission cleanly.

**Mitigation already in place:** `start_scrimmage` implicitly pulls Current at server-processing time, so the risk boundary is "time of POST" not "time of execution". At 1 req/sec default client rate and the staggered schedule (2-min offsets between agents), no two `start_scrimmage` calls collide on the same TCP connection.

**Residual risk:** if an agent OTHER than the scrimmage batch agents runs `set-current` (e.g., post-BO adoption attempting to promote a new weights_v03.json zip), any in-flight batch currently sending requests WILL see the new submission ID from the very next POST onward. **Recommendation: gate `set-current` on a "no batches running" check, OR explicitly record the pre-call + post-call submission in the LIVE_SCRIMMAGE_LOG so analysis can segment data.** The user / team-lead controls the only realistic source of a mid-wave set-current, so ops discipline is sufficient — no code change needed.

---

## §2 — Team-A vs Team-B match semantics

**Verdict: SIDES ARE FIXED — we are always Team A. Scoring is side-agnostic (win/loss only), but RATING change may differ per side.**

Evidence:
- `start_scrimmage` at `bytefight_client.py:563-570`:
  ```python
  body = {
      "competitionSlug": self.competition_slug,
      "ladder": ladder,
      "teamAUuid": self.team_uuid,    # ← OURS, always
      "teamBUuid": opponent_uuid,     # ← OPPONENT
      "count": int(count),
      ...
  }
  ```
  We are unconditionally Team A. Opponent is always Team B.
- Match records in poller log show result codes `team_a_win / team_b_win / draw` — side-labelled, not player-labelled. A `team_a_win` always means our side won. A `team_b_win` always means we lost.
- Game-engine-wise: per `GAME_SPEC.md` §1-2, Player A moves first. Since the tournament engine binds our scrimmage request as Team A → we MOVE FIRST on every scrimmage in the batch.

**Correctness implications:**
1. **First-mover advantage:** Player A gets turn-0 visibility into rat sensor data but cannot see Player B's initial move; Player B gets one extra turn of sensor data before their move. For a small-board game with 80 total plies, first-mover advantage is plausible but small (SPEC §1.5 notes A moves first without quantifying).
2. **ELO-accuracy:** by always being Team A, our measured win-rate has a consistent side-bias. The true opponent-specific WR would average our_A_WR and our_B_WR. Current batch never samples the B-side, so measured WR is slightly biased. For ELO ordering vs the reference set (George/Albert/Carrie) this is fine because the same bias applies to every opponent — ranking is preserved.
3. **Replay-symmetry sampling:** if we want to check "would we win from the B side too", we'd need to fire scrimmages where they queue us. **The current wave does not test B-side.** Low priority given the time pressure.

**No blocker.** Sides are locked by client design; tracked and transparent in match records.

---

## §3 — Replay availability for all ~165 matches

**Verdict: MEDIUM RISK. Download replays proactively for any we want for loss-forensics; don't assume long-term retention.**

Evidence and gaps:
- `get_replay()` is implemented per T-86 (task #86 completed). No endpoint documentation in our repo mentions a retention window.
- SCRIMMAGE_LIMITS_INVESTIGATION §5 item 1: not investigated. "Replay retention window on bytefight" is unknown to us.
- Empirically, all matches finished on or before 2026-04-17 appear to still have replay data (no 404s reported in LOSS_FORENSICS work).

**Recommendation:**
- **Do NOT assume indefinite retention.** If a match finishes on 2026-04-17 and we try to pull its replay on 2026-04-19, it may be gone.
- **Proactive download:** add a background step to the batch pipeline that, on match finish (poller status transition `queued/in_progress → team_a_win/team_b_win/draw`), immediately calls `get_replay(match_uuid)` and persists to `docs/tests/replays/<match_uuid>.json` (or similar). Tiny disk cost (few MB total); eliminates the risk entirely.
- **Post-deadline archival:** before 2026-04-19 23:59, run one sweep over all ~165 match UUIDs to download any missing replays. This is the belt-and-suspenders pass.

No immediate blocker. Flag to team-lead / poller-owner as a defensive add-on.

---

## §4 — Post-deadline cutoff risk

**Verdict: MEDIUM RISK. Matches queued before 23:59 but not executed may or may not complete. Front-load the wave.**

Evidence:
- `CLAUDE.md` §6 says "Whatever is uploaded/activated on bytefight.org at that moment is what gets graded" (emphasis on _activated_, i.e. Current at deadline).
- No explicit statement about whether scrimmages in the queue at 23:59 count for grading or get dropped.
- Staff bots (George/Albert/Carrie) are ELO-scored; each completed scrimmage vs them provides a datapoint. **If a scrimmage against Carrie completes at 2026-04-20 00:15 (15 min after deadline), there is no published guarantee it counts for the final ELO calculation.**
- The tournament grading pipeline reportedly uses the leaderboard ELO at 23:59 as the freeze point. Scrimmages that finish AFTER 23:59 update the leaderboard post-freeze and do NOT affect the grade.

**Operational implication:**
- The 10-agent stagger has the last batch (`alexbot`, offset 1080 s = 18 min) starting its FIRST sub-batch at ~18 min after team-lead's GO, THEN the second sub-batch 10 min later. For each batch's ~15 scrimmages at steady-state cadence (1 scrimmage every ~10-15 min due to queue cap), the tail of a 15-scrimmage batch finishes ~3-4 hours after the last fire.
- Current time: ~2026-04-17 22:00 (per HANDOFF §2 wind-down was 21:11; we're later). Deadline: 2026-04-19 23:59 → **~50 hours of runway.**
- **No cutoff risk at this schedule**, BUT: if the team triggers a second wave of 165 scrimmages in the final 12 hours, the tail could spill past 23:59.

**Recommendation:**
- Front-load against staff bots (George/Albert/Carrie) — these are the ELO-grade signal. Finish all staff-bot scrimmages within the first 24 hours; use the last 24 for top-student-team data (which is nice-to-have but doesn't directly grade).
- Do NOT queue a fresh batch after 2026-04-19 18:00 (last 6 hours). Allow buffer for queue to drain pre-freeze.
- If team decides to fire post-18:00: accept that those may not count. Flag explicitly.

No blocker IF team follows the stagger + cadence; document-flag only.

---

## §5 — Self-play duplicate filtering

**Verdict: CLEAR-CUT. Filter by `teamAUuid != teamBUuid` to exclude self-plays.**

Evidence:
- LIVE_SCRIMMAGE_LOG poller lines for scheduled 2026-04-17T20:31 show 7 matches where the poller renders as `vs Team 15 (81513423)` and `sub=RattleBot_v03_pureonly... opp_sub=RattleBot_v03_pureonly...` — these are self-self. All 7 have `teamAUuid == teamBUuid == 81513423...` (our UUID).
- `bytefight_poll.py:94-95` reads `submissionAName` and `submissionBName` separately. Self-plays have these equal.
- Filter logic: **`team_b_uuid != OUR_UUID (= 81513423-e93e-4fe5-8a2f-cc0423ccb953)`**. Any analysis tallying win-rates MUST apply this filter before computing WR; otherwise self-plays inflate the sample and average toward 50% by construction.
- `bytefight_client.py:630` `_fmt_matches` already renders `teamAUuid == teamBUuid` as `(self)` — the client recognizes the pattern.

**Recommendation for the 10-opponent wave:**
- The wave is firing against named opponents (George, Albert, Carrie, Team 61, etc.) so each individual batch DOES have `teamBUuid != OUR_UUID`. Self-plays in the wave should be zero unless a coordination bug sends `opponent=Team 15` accidentally.
- **The risk is from the EXISTING 7 self-play matches in the queue** that predate this wave (per poller log). When tallying live WR post-wave, exclude these 7 + any future self-plays by filtering `teamBUuid != OUR_UUID AND reason == "scrimmage"`.
- **Minor implementation note:** the poll/tally scripts should include an explicit assert or filter; otherwise a manual "hey we're at 60% WR" message from the poller would be wrong by 10+ pp if self-plays haven't been stripped.

No blocker on the wave itself; operational note for the analysis step.

---

## §6 — Concrete blockers or risks (right now)

**TL;DR — No STOP-the-wave blockers. Four medium flags to watch.**

| # | Flag | Severity | Owner | Action |
|---|------|----------|-------|--------|
| F-1 | set-current mid-wave from a non-batch agent (e.g. BO-adoption) could silently switch which submission later batches use | MEDIUM | orchestrator | Hold off `set-current` calls until the 165-scrimmage wave finishes; or record timestamps in LIVE_SCRIMMAGE_LOG for later segmentation |
| F-2 | Replay retention window unknown; a match from 2026-04-17 may have replay dropped by 2026-04-19 if retention is < 48 h | MEDIUM | live-tester-2 / poller owner | Download replays proactively on match-finish event OR do an archival sweep before 2026-04-19 18:00 |
| F-3 | Post-deadline cutoff: scrimmages queued after 2026-04-19 18:00 may not count for grading | MEDIUM | orchestrator | No new fire after 18:00 on 2026-04-19; 6-hour buffer for queue drain |
| F-4 | Self-play matches inflate sample — tally scripts MUST filter `teamBUuid != OUR_UUID` | LOW | anyone computing live WR | Add filter to tally; 7 known self-plays exist in current queue already |

**Recommendations for the in-flight wave:**
1. Continue the staggered fire as planned (staff bots first, then student teams).
2. Add `get_replay(match_uuid)` calls on every `queued/in_progress → terminal` transition in `bytefight_poll.py` — protects against F-2.
3. Do NOT run `set-current` or upload new submissions while any wave batch is still firing its initial salvo. Once all batches' first salvos have completed (~22 min after GO), new set-current is safer but should still be time-stamped in LIVE_SCRIMMAGE_LOG.
4. Before computing any aggregate WR from the wave, apply the `teamBUuid != OUR_UUID` filter.

---

## §7 — Verdict summary

- §1 current-submission drift: **LOW RISK** — pinned at POST time; in-flight matches unaffected.
- §2 Team-A/B semantics: **NO RISK** — sides locked; small and uniform bias preserved across opponents.
- §3 replay availability: **MEDIUM** — unknown retention; proactive download recommended.
- §4 post-deadline cutoff: **MEDIUM** — 50 h runway is adequate; enforce 18:00 on deadline day as no-new-fire cutoff.
- §5 self-play filtering: **LOW** — single-line filter suffices; 7 known contaminants already identified.
- §6 concrete blockers: **NONE.** Wave is safe to continue as planned.

**Overall: GREEN (proceed) with 4 MEDIUM operational notes flagged for the pipeline/poller owner.**

---

## §8 — Command reference

```bash
# Count in-flight queue depth (pre-flight check, still valuable during wave)
python tools/bytefight_client.py list-matches --size 50 \
  | awk '/waiting|in_progress/ {print}' | wc -l

# Filter current team's scrimmages excluding self-plays
python tools/bytefight_client.py list-matches --size 200 \
  | awk '$2 != "(self)" && /scrimmage/ {print}'

# Download replay for a specific match
python tools/bytefight_client.py get-replay --match-uuid <uuid>
```

---

**End of SCRIMMAGE_WAVE_AUDIT.**
