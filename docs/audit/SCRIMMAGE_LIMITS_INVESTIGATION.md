# SCRIMMAGE_LIMITS_INVESTIGATION — bytefight rate-limit reconnaissance

**Date:** 2026-04-17
**Author:** scrimmage-runner
**Scope:** Empirically characterize bytefight.org's scrimmage-create rate limits so the continuous scrimmage pipeline (task #78) can fire without wasting §F-14 budget on 429s.

---

## §1 Bottom-line verdict

**There is NO hard per-team cap on total scrimmage count.** Team 15 has successfully fired **≥21 scrimmages** across multiple batches on 2026-04-17 alone — all of which were queued and executed by the server. No evidence of a daily / weekly / lifetime ceiling.

**429 Too Many Requests is a CONCURRENCY cap, not a total-count cap.** Every observed 429 happened while ≥10 scrimmages were in the `waiting` or `in_progress` state. Once the queue drains, scrimmage-create succeeds again with the same client code.

**Operational implication:** the continuous-scrimmage pipeline should not worry about "running out" of scrimmages before the 2026-04-19 23:59 deadline. What it MUST do is throttle submission so that at most ~5-8 scrimmages are in flight at once.

---

## §2 Evidence

### Team 15 scrimmage history (via `list-matches --size 200`)

| Metric | Count |
|---|---|
| Total game-match records for Team 15 | **45** |
| Submission-validation records (not scrimmages) | 4 |
| Matchmaking records (automatic, not user-initiated scrimmages) | ~13 |
| Self-self + vs-reference scrimmages (user-initiated) | **~22** |

Page 2 of `list-matches` is empty → 45 is the full team history.

### Observed scrimmage batches on 2026-04-17 — all SUCCEEDED on queue

| Batch time (UTC) | Size | Composition | Outcome |
|---|---|---|---|
| 14:24 | 8 | self-self ×8 | All queued + finished |
| 20:19 | 1 | vs George | Queued + finished (team_b_win) |
| 20:21 | 2 | vs Carrie, vs Albert | Both queued + finished (both team_b_win) |
| 20:31 → 21:11 (sched) | 7 | self-self ×7 | All queued + finished (4× team_b_win, 3× team_a_win) |
| 21:11 | 3 | vs George, Albert, Carrie | All queued + finished (all team_b_win) |

**Total user-initiated scrimmages that cleared the server:** ≥21. Zero rejections for "quota exceeded", "daily limit", etc.

### When the 429s happened (from `docs/tests/BYTEFIGHT_CLIENT_SMOKE.md` §11)

| Attempt | Timestamp | Queue depth at the moment | Result |
|---|---|---|---|
| Smoke step f, attempt 1 | 2026-04-17 ~21:06 | 11+ pending/in-flight | **429** |
| Smoke step f, attempt 2 | 2026-04-17 ~21:08 (30 s backoff) | Still 10+ pending | **429** |
| §11 retry | 2026-04-17 ~21:11 | 10 `waiting` | **429** |

All 429s fired *after* CAPSOLVER Turnstile was accepted by the server — i.e. the bytefight backend explicitly validates the Turnstile token first, then rejects on concurrency grounds. This tells us the rate-limiter key is almost certainly "open scrimmage slots per team", not "IP bucket" or "global rate".

### The successful scrimmage-create on 2026-04-17T21:11 (3 vs-reference scrimmages)

These three (`2e9fb89f`, `4fbbd274`, `5e2d6a1f` vs Carrie, Albert, George) were queued despite the same agent hitting 429 moments earlier. The difference: the prior batches of 7 self-self scrimmages had just transitioned from `waiting` → `in_progress` → `finished`, draining the concurrency bucket. **The ability to submit tracks queue depth, not request count.**

### `list-matches` as the queue oracle

The `GET /api/v1/public/game-match?competitionSlug=&teamUuid=...` endpoint returns the authoritative queue state. Status transitions observed:

```
queued → in_progress → team_a_win | team_b_win | draw | error
```

Only `waiting` and `in_progress` count against the concurrency cap. `team_a_win / team_b_win / draw` are terminal and do NOT.

---

## §3 Recommended cadence

### For the continuous scrimmage loop (task #78)

- **Pre-flight every scrimmage-create** with `list_matches()` → count rows where `status in {waiting, in_progress}` AND `reason == scrimmage` AND `teamAUuid == OUR_UUID`.
- **Abort + sleep** if count ≥ 5 (safety margin below the observed 10-deep fail threshold).
- **Fire one scrimmage** every **10–15 minutes** when the queue is healthy. A typical scrimmage takes 9-15 minutes wall-clock, so at 10-min cadence the steady-state in-flight count stabilizes at ~1-2, well below the 5-8 safe zone.
- **Back off 5 minutes on 429**, then retry ONCE. If second attempt 429s, back off to 15 minutes and let the queue fully drain before retrying.
- **Do NOT fire batches** of more than 1 scrimmage per create-call at this stage of the tournament. Batches work but they frontload the concurrency bucket and risk self-inflicted 429s.
- **Prefer diverse opponents.** George (≥70% tier), Albert (≥80% tier), Carrie (≥90% tier) — rotate so no opponent is oversampled. The ladder match ELO signal converges faster with mixed-opponent data.

### Budget envelope

2026-04-17 22:00 → 2026-04-19 23:59 is ~50 hours remaining. At 1 scrimmage / 10 min that's a theoretical ceiling of 300 scrimmages. Realistic throughput is probably 100-150 after server hiccups + CAPSOLVER latency + overnight stalls. That is **vastly more** ELO signal than §F-14's "~10 slot" budget assumed pre-smoke.

---

## §4 Concrete rate-limit parameters (best estimate from observation)

| Parameter | Estimate | Confidence | Basis |
|---|---|---|---|
| Max concurrent scrimmages in `{waiting, in_progress}` per team before 429 | **~10** | Medium | 3 independent 429s each hit at queue depth 10–11 |
| Safety threshold for pre-flight abort | **5** | High | Conservative; well below observed fail point |
| Scrimmage wall-clock duration | 9–15 min | High | Observed: George match 5e2d6a1f took sched 21:11 → finished 21:20 (9 min); Carrie 2e9fb89f took 13 min |
| CAPSOLVER Turnstile solve latency | 5–13 s | High | Two smokes at 6-7 s, one at 13 s |
| `Retry-After` header on 429 | **NOT SENT** | High | Server omits header, so client must choose backoff |
| Total-count cap per team | **None observed** | Medium-High | 21+ successful scrimmages today alone, no "quota" errors |

### Other constraints observed (non-rate-limit)

- CAPSOLVER required for every scrimmage-create (Turnstile-gated); ~$0.001–0.003 per solve. 150 scrimmages ≈ $0.45 in CAPSOLVER.
- Client hard-codes 1 req/sec default cap (`tools/bytefight_client.py`) — already safely under any observed rate limit.
- Submission storage quota is 200 MB per team (abundant; each RattleBot zip is ~KB-scale).

---

## §5 Gaps — what we could not verify

1. **Is the cap exactly 10, or a sliding window?** We saw 429 at depth 10–11 and success at depth 0. Did not probe 7/8/9 to find the exact edge. Recommend: the continuous pipeline treats 5 as the threshold and stays well clear.
2. **Is the cap per-team or per-competition?** We only probed as Team 15 in `cs3600_sp2026`. Some other team firing 20 scrimmages should not affect us IF it's per-team. This is the natural assumption but not proven.
3. **IP or account rate-limiter independent of the queue cap?** Possible but no evidence. All 429s we saw correlate with queue depth, not raw request rate.
4. **Daily / weekly rollover?** Cannot falsify; we only have 2026-04-17 observations. Budget math assumes no rollover.
5. **Behavior across submission changes.** If we set-current to a different submission mid-queue, do in-flight matches still use the original? Per `list-matches` output, yes (each match record pins `submissionAName / submissionBName`). Validated implicitly by the smoke's SmokeBot set-current / revert dance.
6. **Matchmaking (auto-paired) matches and their effect on the queue cap.** Matchmaking matches show `reason=matchmaking` not `scrimmage` — unclear whether they share the concurrency bucket. Conservative default: count them too.
7. **CAPSOLVER token reuse on 429 retry.** The smoke retried with a fresh CAPSOLVER solve each time. Untested whether the server would accept the same token twice within a short window. Assume no.

---

## Appendix A — How to re-verify this investigation

```bash
# Get current queue depth
python tools/bytefight_client.py list-matches --size 50 \
  | awk '$3 ~ /waiting|in_progress/ {print}' | wc -l

# Count total team history
python tools/bytefight_client.py list-matches --size 200 | wc -l

# Fire a single scrimmage (respects client-side rate limit)
python tools/bytefight_client.py scrimmage --opponent George --count 1
```

## Appendix B — Quick cadence implementation sketch (not implemented in this doc)

```python
from tools.bytefight_client import BytefightClient
import time, random

c = BytefightClient()
OUR = "81513423-e93e-4fe5-8a2f-cc0423ccb953"

while True:
    recent = c.list_matches(size=50)
    depth = sum(1 for m in recent
                if m.get("status") in ("waiting", "in_progress")
                and m.get("reason") == "scrimmage"
                and (m.get("teamAUuid") == OUR or m.get("teamBUuid") == OUR))
    if depth >= 5:
        time.sleep(600)  # 10 min
        continue
    opp = random.choice(["George", "Albert", "Carrie"])
    try:
        c.start_scrimmage(opp, count=1)
    except Exception as e:
        if "429" in str(e):
            time.sleep(300)  # 5 min backoff
            continue
        raise
    time.sleep(600)  # 10 min cadence
```
