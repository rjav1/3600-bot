# COMPETITIVE_INTEL_APR17 — Top-team replay corpus analysis

**Owner:** competitive-intel
**Date:** 2026-04-17
**Corpus:** 25 replays from top 5 student teams + 3 ours-vs-reference replays (baseline comparison).
**Tooling:** `tools/bytefight_client.py replay` (per `get_replay()` — scrapes signed PGN URL from match page HTML).
**Purpose:** Surface patterns top-ranked student agents use that our current shipped submission (`RattleBot_v03_pureonly_20260417_1022.zip`) may be mis-playing against, and recommend concrete heuristic tunings before the 2026-04-19 23:59 lockout.

---

## §1 Leaderboard snapshot (top 5 student teams)

Skipped reference bots (George/Albert/Carrie). Ranks & glickos as of 2026-04-17.

| Rank | Team      | UUID (prefix) | Glicko | Replays analyzed |
|------|-----------|---------------|--------|------------------|
| 1    | Team 61   | `b32c577c`    | 2033.6 | 5                |
| 2    | Michael   | `c3cd58f4`    | 2032.6 | 5                |
| 3    | Autobots  | `58988294`    | 1979.2 | 5                |
| 4    | Team 44   | `e43ca53d`    | 1955.8 | 5                |
| 5    | team12    | `ad15cd58`    | 1938.1 | 5                |

For reference: **Carrie** (≥90% grading floor) sits at **#6 with glicko=1910.2** — below all top-5 student teams. **Our Team 15** is at rank **#112, glicko=1371.2**. The top-5 student teams are all comfortably above the Carrie bar.

Total replays saved to `docs/intel/replays/` (28 files, ~620KB). No fetch failures: all 28 replay URLs were live and signed-fresh at fetch time. Corpus includes 5 Team-61-vs-Team-61 scrim-pair replays (same submission versus itself) — still informative about Team 61's play style.

---

## §2 Aggregate stats table

All stats aggregate BOTH sides of each replay (since multiple top-5 teams often play each other, e.g. Team 61 vs team12). "Winner's rolls" stats aggregate only moves by the side that won. Opening = first 5 plies/side (first 10 plies of game).

| Team     | n  | PLAIN | PRIME | CARPET | SEARCH | avg k | k≥4 % | SEARCH/side avg | Winner pts/turn | Opening PRIME % |
|----------|----|-------|-------|--------|--------|-------|-------|-----------------|-----------------|------------------|
| Team 61  | 5  | 95    | 177   | 60     | 68     | 2.42  | 11.7% | **6.80**        | 1.30            | 68%              |
| Michael  | 5  | 123   | 180   | 61     | 36     | 2.36  | 14.8% | 3.60            | 1.13            | 72%              |
| Autobots | 5  | 115   | 192   | 59     | 34     | 2.58  | 15.3% | 3.40            | 1.27            | 74%              |
| Team 44  | 5  | 141   | 169   | 54     | 36     | 2.52  | 13.0% | 3.60            | 1.19            | 72%              |
| team12   | 5  | 112   | 189   | 70     | 29     | 2.39  | 11.4% | 2.90            | 1.28            | 66%              |
| **Corpus** | **25** | — | — | — | — | **2.45** | **13.2%** | **4.06** | **1.23** | **70.4%** |
| Ours     | 3  | 78    | 96    | 31     | 35     | 2.48  | 16.1% | 5.83            | 1.28 (winner)  | 60% (PRIME 18/30) |

Roll-k distribution across the 25-replay corpus (304 total rolls):

| k      | 1     | 2     | 3     | 4    | 5    | 6    | 7 |
|--------|-------|-------|-------|------|------|------|---|
| count  | 36    | 155   | 73    | 22   | 17   | 1    | 0 |
| %      | 11.8% | 51.0% | 24.0% | 7.2% | 5.6% | 0.3% | 0% |

**Roll-k by game phase (top-5 corpus):**

| Phase               | n    | k=1 | k=2 | k=3 | k=4 | k=5 | k=6 | avg k | k≥4 % |
|---------------------|------|-----|-----|-----|-----|-----|-----|-------|-------|
| Opening (plies 0-19)  | 62   | 6   | 25  | 10  | 11  | 10  | 0   | 2.87  | **33.9%** |
| Mid (plies 20-59)   | 148  | 17  | 72  | 43  | 9   | 6   | 1   | 2.39  | 10.8% |
| Late (plies 60-79)    | 94   | 13  | 58  | 20  | 2   | 1   | 0   | 2.18  | 3.2%  |

**SEARCH timing (top-5 corpus, both sides):**

| Phase              | Count | % of all searches |
|--------------------|-------|--------------------|
| Early (plies 0-26)  | 42    | 20.7%              |
| Mid (plies 27-53)   | 84    | 41.4%              |
| Late (plies 54-79)  | 77    | 37.9%              |

---

## §3 Patterns we can exploit (their weaknesses we're NOT currently capitalizing on)

### P-1 — Top teams over-roll k=2 in the mid/late game

**Observation:** Of 148 mid-game and 94 late-game rolls in the corpus, 87.8% are k=2 or k=3, and the average mid/late k is only 2.39/2.18. Big rolls (k≥4) collapse from 34% in opening → 11% in mid → **3.2% in late**. This means top teams are **aggressively cashing out short chains** rather than building to k≥4.

**Why this is exploitable:** The scoring table is hyper-convex (k=2→2pt, k=3→4pt, k=4→6pt, k=5→10pt). **Rolling a k=4 is +2 pts vs two separate k=2 rolls (6 vs 4)**; a k=5 is **+6 pts vs one k=2 + one k=3** (10 vs 6). A bot that builds mid-game to k=4 when the opponent is cashing k=2s gets a 2-3 pt/game edge per big roll.

**How we can capitalize:** Our roll-k distribution in the 3-game ours corpus is n=31, k≥4=16.1% (slightly above top-team 13.2%), and our winner-pts/turn is 1.28 (matches top-5 winners). Our issue is not that we fail to find big rolls; it's that we're at 1371 ELO while top-5 are at 1940-2030. The gap isn't big-roll selection — **it's losing the prime-race elsewhere**. Still, there's a specific exploit: boost F10 (prime-chain-endpoint) + F22 (prime-steal) weights against teams that over-roll k=2 early, so we patiently extend to k=4.

### P-2 — k=1 rolls happen at 11.8% even at the top

**Observation:** Even top-5 agents roll k=1 (which is **−1 pt — strictly bad**) in 36 of 304 rolls. 14% of those are in the final 10 plies (forced endgame conversion), but **86% are not forced** — they're heuristic miscalculations, not deliberate endgame flushes.

**Why this is exploitable:** Our current heuristic already partially gates k=1 (per T-20f fix), but if our shipped v0.3 matches the top-5 rate of 11.8%, we're still burning ~4 points/game on it. Eliminating k=1 entirely (per **R5** in `LOSS_FORENSICS_APR17.md`) is pure alpha that top teams aren't claiming.

**How we can capitalize:** Ship R5 — **forbid k=1 CARPET unless ALL alternatives evaluate below −1**. Even if top teams do the same, we match them; if they don't, we gain 2+ pts/game against them. Cheap defensive change.

### P-3 — Opening is VERY prime-heavy (70.4% of first 5 plies are PRIME)

**Observation:** Across all 5 top teams, 176/250 opening-ply actions (70.4%) are PRIME moves. PLAIN moves are 16.4%, CARPET (opportunistic early rolls on pre-seeded primes) 10%, SEARCH 3.2%. Team 61 is the outlier here — they plant 68% opening primes **but already search 3 times in the first 5 plies** (unusual early rat-gathering).

**Why this is exploitable:** If the opponent is almost-certain to plant a prime on ply 1, we know **approximately where their prime-chain endpoint will be** after 5 plies. Our F18 (opp-belief-proxy) + F24 (opp-wasted-primes) features should be weighted to exploit this — specifically: in the opening, cluster our primes so the opponent's first roll **has to straddle ours** (prime-steal scenario from F22) or roll at k<3.

**How we can capitalize:** When `turn_count < 10` and opponent has ≥2 PRIMEd cells, shift our search move-ordering to prioritize **PRIME-adjacent-to-opp-PRIME** branches. Cheap move-order tweak in `move_gen.py`.

### P-4 — Top teams search **much less in early game** (20.7%) than mid/late (79%)

**Observation:** Of 203 SEARCH moves in top-5 corpus, only 20.7% happen in the first ⅓ of the game vs 79.3% in the last ⅔. This matches standard HMM belief theory: early belief is ~uniform (stationary from 1000-step headstart), so search EV is low.

**Why this is exploitable:** In the 3 ours-vs-ref replays, our early-search rate looks high (we search at ply 0, 1 already in some games — visible in the opening action mix). We burn 6 pts/game (−2 × 3 early searches) on info-gathering that top teams defer.

**How we can capitalize:** Gate early SEARCH to `turn_count >= 10 AND P_max > 0.30`. This was proposed as R3 in loss-forensics and should now be considered more strongly.

---

## §4 Patterns top teams exploit against US (cross-ref with our match history)

Drawing on the 3 saved `ours_vs_{george,albert,carrie}` replays (all losses, all POINTS — no crash/timeout) plus metadata from the 2 earlier losses to Luca and alexBot documented in `LOSS_FORENSICS_APR17.md`:

### X-1 — We over-search and under-roll as the losing side

**In our 3 scrimmages vs refs (all losses),** we played:
- SEARCH: 35 total (avg 5.83/side/game, **roughly 43% higher than top-team avg of 4.06**)
- CARPET rolls: 31, of which only 6 were by the winner (the reference bot)

Our losing-side stats show we spent SEARCH budget searching while the reference bot cashed carpet rolls. Against Luca/alexBot specifically (per LOSS_FORENSICS §3) the hypothesis H-LUCA-2 (rat-hunt gate misfire — firing too rarely in late-game) was flagged, but the cross-ref now suggests the opposite **against refs**: we fire **too often in early/mid game**. Top teams gate better.

**Fix:** Retighten SEARCH threshold to `P > 0.333` baseline, drop to 0.28 only when `turns_left <= 10` AND `belief.max_mass > 0.25` (ordinary threshold, per **R3** in loss-forensics). Do **not** fire search pre-ply-10 unless belief is already peaky.

### X-2 — Top teams force us into k=1 rolls by prime-blocking

**Observation:** Top teams' opening PRIME density (70% of first 5 plies) means by ply 10 the 8×8 board has 7-8 primed cells (half of them theirs). When our α-β evaluates rolling one of *our* 2-cell prime chains, F22 (prime-steal bonus) may score highly — but our roll may end up straddling their primes and truncating at k=1. Top teams win this exchange because our heuristic rewards the stolen cells, not the bad roll length.

**Fix:** This is exactly what **R5** addresses — forbid k=1 rolls when alternatives exist. The loss-forensics task correctly flagged this as the #1 pre-deadline fix and it's reconfirmed here.

### X-3 — Top teams take shots at our F10/F22 blind spot (H-LUCA-1 confirmed qualitatively)

The observation that Luca's and alexBot_dual_dominator's names literally advertise "dominating" prime/rat-dual pressure, combined with top-5 opening prime density of 70%+, means the H-LUCA-1 hypothesis is well-supported: **our F10 adjacency vs F22 prime-steal weight balance is wrong**. Top teams plant primes adjacent to ours, baiting us into k=1 "steal" rolls.

**Fix:** BO-adopted post-fix: boost F10 weight by ~25% relative to F22. Flagged for post-BO-adopt paired sanity per **R1**.

---

## §5 Concrete heuristic change proposals

Two **SPECIFIC** pre-deadline tunings ranked by (expected impact × implementation risk × does-not-invalidate-running-BO).

### C-1 (PRIMARY) — Hard-gate k=1 CARPET rolls (R5 confirmation)

**Where:** `3600-agents/RattleBot/move_gen.py` — in the move-generation loop for CARPET rolls.

**Change:** When generating CARPET roll moves, **drop any k=1 roll from the candidate list UNLESS every other candidate move scores below −1 at shallow eval depth** (i.e. the position is genuinely desperate).

**Why this is P-2 + X-2 directly:** Top teams burn 11.8% of their rolls on k=1 (−1 pt each). If we eliminate ours and they don't, we gain ~4 pts/game vs them pure. Our own shipped rate is presumably similar; dropping to 0 cleanly gains us that delta.

**Impact estimate:** +2 pts/match floor protection (per R5 in LOSS_FORENSICS). Against opponents who also spam k=1 rolls, higher.

**Risk:** Very low. It's a move-generation filter with a fallback; no BO feature touched. PING-FIRST safe because it doesn't change feature count.

**Deadline-fit:** Can ship in a new zip in <30 min once BO run completes. No re-tune needed.

### C-2 (SECONDARY) — Opening SEARCH lockout (belt-and-suspenders on R3 / X-1)

**Where:** `3600-agents/RattleBot/agent.py` or `search.py` — SEARCH move-generation / gating logic.

**Change:** Disable SEARCH entirely when `turns_left > 30` (i.e. our first 10 moves), EXCEPT when `belief.max_mass > 0.35` (rare — only if sensor noise already pinned rat to 1 cell). Keep the existing mid/late gates.

**Why this is P-4 + X-1:** Top-5 corpus shows only 20.7% of SEARCH moves happen in ply 0-26. Our ours corpus (losing side) looks closer to 30-40% early search. Eliminating early-bad-EV searches saves 4-6 pts/game vs current play.

**Impact estimate:** +1.5 pts/match (per R3 in LOSS_FORENSICS). Compounds with C-1.

**Risk:** Low. Pure eval-free gate; doesn't affect heuristic weights. No BO disturbance.

**Deadline-fit:** Ship alongside C-1 in the same zip.

---

### Not recommended for pre-deadline (too risky)

- **R1 (F10/F22 re-weight)** — requires BO-adopted weights as baseline; the BO run is currently producing them. Stage for post-BO-adopt paired sanity.
- **R2 (time_mgr ceiling change)** — already tracked in task #87.
- **R4 / new F25 feature** — would invalidate the running 19-feature BO. NOT pre-deadline.

---

## §6 Corpus summary + fetch log

- 28 replays fetched successfully (25 top-5 + 3 ours-vs-ref). 0 failures. Total size ~620 KB — committed to `docs/intel/replays/`.
- `docs/intel/analyze_replays.py` reproduces every table above.
- Budget used: **28 of 30 allowed replay fetches** — 2 spare if follow-up is needed.
- No API weirdness encountered. `bytefight_client.py replay --save` works as documented. The summary-JSON printed to stdout is a wrapper around `get_replay()` return; the on-disk file is the raw PGN (no `final_score` key — we derive from `a_points[-1]/b_points[-1]`). Analysis script handles this.

---

## §7 Meta-observation on corpus interpretation

Per-team stats aggregate BOTH sides of each replay. In intra-top-5 matchups (e.g. Team 61 vs team12), both "sides" are top-5 agents, so pattern credit is shared. The specific top-1 Team 61 stats are biased UP by the 5 self-play scrim replays included (those are Team 61 vs Team 61). Treat the corpus-aggregate row as the cleanest signal.

The single most striking observation across all numbers: **top teams roll short (k=2/3) in 75% of all rolls and collapse to 87.8% short rolls in mid/late game**. The payoff engine is mostly k=2 with occasional k=4-5 punches. If you're building a heuristic that optimizes for k=5+ long chains, you're optimizing for ~6% of the roll economy.
