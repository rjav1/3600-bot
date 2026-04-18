# WILSON_CI_APR18_0317Z — refreshed win-rate CIs

**LAST UPDATED:** 2026-04-18T03:17Z
**Auditor:** wilson-ci-analyst (ephemeral)
**Scope:** terminal (A_WIN / B_WIN / DRAW) poller lines in `docs/tests/LIVE_SCRIMMAGE_LOG.md`, dedup'd by short match-UUID, self-play (Team-15-vs-Team-15) excluded, mapped to RattleBot POV via the `sub=` vs `opp_sub=` heuristic.
**Data source:** `docs/tests/LIVE_SCRIMMAGE_LOG.md` (267 lines). Driver: `tools/scratch/wilson_ci_0317z.py` (read-only, pure-python).
**Method:** draws count as 0.5 wins; Wilson CI computed on `(wins_eff = 2w + d, n_eff = 2·n)` with z = 1.96. This is the same convention as prior `WILSON_CI_APR18.md` (commit `b125936`).

Wilson formula (z = 1.96):
```
center      = (p + z²/(2n)) / (1 + z²/n)
halfwidth   = z · sqrt( p(1-p)/n + z²/(4n²) ) / (1 + z²/n)
CI          = center ± halfwidth
```

Mapping (verified by spot-checking 3 lines against `tools/bytefight_client.py` result parsing):
- `sub` starts with `RattleBot` → we are **A**. A_WIN = W, B_WIN = L, DRAW = D.
- `opp_sub` starts with `RattleBot` → we are **B**. B_WIN = W, A_WIN = L, DRAW = D.
- Both `RattleBot*` (self-play vs Team 15) → excluded.
- When `vs=Team 15` but only ONE side is RattleBot, the real opponent is the team that submitted the non-Rattle zip. These rows are labeled `(mm:<zipname>)` below and are matchmaking-only data.

Total terminal matches counted: **76** (18 W / 54 L / 4 D). Aggregate score 0.263 with Wilson CI [0.200, 0.338].

---

## §1 — Per-opponent table (grade-relevance ordering)

### §1.1 Reference staff bots (grade gates)

| Opponent | n | W-L-D | Score | Wilson 95% CI | Grade relevance |
|----------|---|-------|-------|---------------|-----------------|
| **Carrie** | 12 | 1-11-0 | 0.083 | [0.023, 0.258] | ≥ 90% gate |
| **Albert** | 12 | 2-9-1 | 0.208 | [0.092, 0.405] | ≥ 80% gate |
| **George** | 2 | 1-1-0 | 0.500 | [0.150, 0.850] | ≥ 70% gate (floor) |

### §1.2 Student-team opponents (Glicko descending per task brief)

| Opponent | Glicko | n | W-L-D | Score | Wilson 95% CI |
|----------|--------|---|-------|-------|---------------|
| **Team 61** | 2033 | 0 | — | — | — |
| **Michael** | 2032 | 15 | 2-12-1 | 0.167 | [0.073, 0.336] |
| **Autobots** | 1979 | 8 | 2-6-0 | 0.250 | [0.102, 0.495] |
| **Team 44** | 1955 | 0 | — | — | — |
| **Team 12** | 1938 | 0 | — | — | — |
| **Team 57** | <1910 | 16 | 5-10-1 | 0.344 | [0.204, 0.517] |
| **Yolanda** (floor) | — | 0 | — | — | — |
| **FloorBot** | — | 0 | — | — | — |

### §1.3 Other opponents observed (matchmaking-only, n ≤ 1)

| Opponent | n | W-L-D | Score | Wilson 95% CI |
|----------|---|-------|-------|---------------|
| (mm:20thAgent.zip) | 1 | 1-0-0 | 1.000 | [0.342, 1.000] |
| (mm:YolandaR3_20260414.zip) | 1 | 1-0-0 | 1.000 | [0.342, 1.000] |
| (mm:Yolanda_J.zip) | 1 | 1-0-0 | 1.000 | [0.342, 1.000] |
| (mm:rv12-3.zip) | 1 | 1-0-0 | 1.000 | [0.342, 1.000] |
| (mm:rv13-1.zip) | 1 | 1-0-0 | 1.000 | [0.342, 1.000] |
| (mm:yolanda_v21.zip) | 1 | 0-1-0 | 0.000 | [0.000, 0.658] |
| (mm:Rascal4.zip) | 1 | 0-1-0 | 0.000 | [0.000, 0.658] |
| (mm:agent4.zip) | 1 | 0-1-0 | 0.000 | [0.000, 0.658] |
| Team 65 | 1 | 0-1-0 | 0.000 | [0.000, 0.658] |
| Gold Team | 1 | 0-1-0 | 0.000 | [0.000, 0.658] |
| Abhi/Dawson | 1 | 0-0-1 | 0.500 | [0.095, 0.905] |

All single-match rows carry ±66 pp CI — **not signal**.

---

## §2 — Deltas vs prior `WILSON_CI_APR18.md` (commit `b125936`)

The earlier audit was sourced from bytefight `/api/v1/public/game-match` (86 competitive matches; includes matchmaking rows not yet in the log file). This audit is sourced from `LIVE_SCRIMMAGE_LOG.md` only (76 terminal rows), so totals are a subset. Changes since prior:

| Opponent | Prior n | Prior W-L-D | Prior CI | Now n | Now W-L-D | Now CI | Δ |
|----------|---------|-------------|----------|-------|-----------|--------|---|
| Carrie | 12 | 1-11-0 | [0.023, 0.258] | 12 | 1-11-0 | [0.023, 0.258] | **identical** — no new Carrie terminals since prior |
| Albert | 12 | 2-9-1 | [0.092, 0.405] | 12 | 2-9-1 | [0.092, 0.405] | **identical** |
| George | 3 | 1-2-0 | [0.097, 0.700] | 2 | 1-1-0 | [0.150, 0.850] | **-1 n**; earlier audit counted LIVE-004 (Yolanda-as-A-vs-George LOSS) which is a pre-poller-format row in the log and not parseable by the regex; additionally the source data method differs. 8 new George scrimmages queued at 03:11Z (see §4) not yet terminal. |
| Michael | 15 | 2-12-1 | [0.073, 0.336] | 15 | 2-12-1 | [0.073, 0.336] | **identical** |
| Autobots | 8 | 2-6-0 | [0.102, 0.495] | 8 | 2-6-0 | [0.102, 0.495] | **identical** |
| Team 57 | 16 | 5-10-1 | [0.204, 0.517] | 16 | 5-10-1 | [0.204, 0.517] | **identical** |
| Team 61 | 0 | — | — | 0 | — | — | still no data |
| Team 44 | 0 | — | — | 0 | — | — | still no data |
| Team 12 | 0 | — | — | 0 | — | — | still no data |

**Bottom line:** **zero new terminal results for any primary opponent** between the prior audit timestamp and 03:17Z. All targeted primary n, W-L-D, and CIs are unchanged. 8 George scrimmages submitted 6 minutes before this audit are still `queued`; expect that bucket to expand to n≈10 within the next ~30 min.

---

## §3 — Grade-relevant readout

With no new terminal results vs George/Albert/Carrie since prior, the grade-probability picture is unchanged from `WILSON_CI_APR18.md §3`:

- **≥ 70% (George floor):** George WR point estimate = 0.500 on n=2 with CI [0.150, 0.850] — uselessly wide; the 8-match George batch fired at 03:11Z is the single most-important upcoming CI tightener.
- **≥ 80% (Albert):** Albert WR = 0.208 on n=12, CI upper bound 0.405 < 0.5 — we are materially below Albert.
- **≥ 90% (Carrie):** Carrie WR = 0.083 on n=12, CI upper bound 0.258 — Carrie is out of reach absent a large v0.4 lift.

---

## §4 — Queued-but-unresolved (exists in log, not counted)

From a scan of non-terminal poller lines:

- **George × 8** queued at 03:11:51Z (match IDs: `bee8b879`, `cf38e87b`, `8b7226f5`, `cf0f474e`, `66b5ffa4`, `676e976a`, `fcb9fed4`, `6648b9a2`). Will resolve ~03:25-03:40Z. Post-resolution George n jumps to ~10, CI width shrinks from 0.70 to ~0.35.
- **Autobots** `dd841e17`, `e326a9d7` in-progress.
- Assorted Michael/Team-57 rows all terminal now.

---

## §5 — Caveats & assumptions

1. **A_WIN/B_WIN → RattleBot W/L mapping** is done from the `sub=` vs `opp_sub=` fields in the poller line. For rows where we are the submitter (scrimmages we initiated, `sub=RattleBot*.zip`), we are always A — A_WIN = W. For rows where the opponent initiated (matchmaking with `opp_sub=RattleBot*.zip`), we are always B — B_WIN = W. I did **not** cross-reference `docs/intel/replays/` to verify the A/B side assignment on every row; the assumption is that bytefight's `A_WIN`/`B_WIN` tokens in the poller correspond to `teamA` vs `teamB` in the upstream API, and that bytefight's `teamA` is always the first-named submitter. This matches the prior audit's methodology (§5 of `WILSON_CI_APR18.md`). **If this mapping is inverted, flip all W/L tallies** — I'd be happy to run a cross-check if a replay-indexed lookup is needed.
2. **LIVE-004 pre-poller row** (line 12 of the log, Yolanda-vs-George LOSS from ~2026-04-17 00:22) is **not** parseable by the poller-format regex; it's not counted here. Prior audit counted it from the bytefight API directly.
3. **Draw handling:** draws count as 0.5 wins, Wilson computed on `(2w+d, 2n)`. Alternative (treat draws as missing) would widen CIs by ~1-3 pp but not shift point estimates materially.
4. **Self-play exclusion:** rows where both `sub` and `opp_sub` start with `RattleBot` (n ≈ 10 observed) are excluded.
5. **First-mover / side-bias** is not corrected; CI absorbs it consistently.
6. **Log staleness:** the log may lag the live bytefight API by one poll cycle (~1 min). At 03:17Z I see results up to 03:10:51Z. 8 George matches queued at 03:11:51Z are pending.

---

## §6 — Reproducibility

```bash
python tools/scratch/wilson_ci_0317z.py
```

Driver at `tools/scratch/wilson_ci_0317z.py`. Read-only (no scrimmages fired, no auth-refresh, no write beyond stdout). Uses only stdlib (`re`, `math`, `pathlib`, `collections`).

---

**End of WILSON_CI_APR18_0317Z.**
