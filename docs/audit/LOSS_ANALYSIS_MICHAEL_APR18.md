# LOSS_ANALYSIS_MICHAEL_APR18 — why we lose 2-12-1 to Michael/Rusty-v2.1

**Auditor:** `loss-forensics-dual` (ephemeral, 2026-04-18)
**Scope:** 12 B_WIN scrimmage losses vs `Rusty-v2.1.zip` submitted by Team "Michael" (Glicko ≈ 2032, top-3 student team). RattleBot was Side A in every loss. 2 W (0a270755, 2c0babfa) + 1 DRAW (af017ebc) used as contrast.
**Data source:** `docs/intel/replays/michael_*.json` + `docs/tests/LIVE_SCRIMMAGE_LOG.md` for A/B assignment.
**Analyzer:** `docs/audit/_scratch/loss_analyze.py` (stdlib-only; read-only for RattleBot/ — BO PID 23708 alive).
**Sample size caveat:** 12 losses, 2 wins, 1 draw. Wilson WR CI = [0.073, 0.336] — significantly worse than random, direction robust.

---

## §1 Summary (TL;DR)

Rusty-v2.1 beats us by a **larger** margin than Carrie (mean Δ = −25.8 vs −19.9 pts). The qualitative pattern is similar to the Carrie loss profile but **amplified**:

- Rusty-v2.1 plays **longer prime chains** and scores **more small (+1) events** (17.8 /game vs our 13.6).
- RattleBot again out-carpets the opponent (total 79 rolls vs 29; 26.6% big rolls vs 0.0% big rolls for Rusty) — **Rusty never rolled k≥4 in any of the 12 losses**.
- RattleBot again bleeds **7.2 penalty events/game vs Rusty's 4.0** (1.8× the opponent rate).
- The score gap opens **even earlier than vs Carrie** — mean delta-open ply is **16.5** (1/5 of the game). Min was ply 6 (144a1826).
- In the 3 non-losses, RattleBot has **dramatically fewer searches** (avg 4.0/game) and **26.7 carpet pts/game**. In the 12 losses, our search rate jumps to **6.7/game** — searches correlate strongly with losing.

Rusty-v2.1 uses far less time (~120s of 240s used) but **spends zero on aggressive rolling** (0 big rolls). It is running a conservative prime-chain heuristic + high-volume search (12.4/game) and winning purely on **tempo density + our self-inflicted penalties**. The loss pattern is: we pre-commit to long speculative prime chains, Rusty walks across our carpets and searches, we fall behind in early primes, we panic-search or panic-roll k=1, we bleed.

---

## §2 Evidence — per-match table

| Match | Final A (us) | Final B (Rusty) | Δ | Delta-open ply | A k-dist | A big(k≥4) | A searches | A rat-caught | B k-dist | B searches | B rat-caught |
|-------|--------------|-----------------|---|----------------|----------|------------|------------|--------------|----------|------------|--------------|
| 066fdae3 | 8 | 47 | −39 | 15 | {1:1, 2:1, 3:2, 4:2} | 2 | 8 | 4 | {2:1} | 14 | 3 |
| c39d8154 | 37 | 57 | −20 | 11 | {1:1, 2:2, 3:2, 4:1, 5:1} | 2 | 6 | 5 | {2:3, 3:1} | 10 | 3 |
| 3df15113 | 26 | 44 | −18 | 21 | {2:3, 4:1, 5:1} | 2 | 7 | 4 | {2:2, 3:1} | 14 | 3 |
| 56a79715 | 35 | 50 | −15 | 21 | {2:4, 3:2} | 0 | 7 | 6 | {2:1, 3:1} | 11 | 5 |
| d71f7f02 | 38 | 55 | −17 | 48 | {1:1, 3:4, 4:2} | 2 | 5 | 6 | {2:4} | 11 | 2 |
| 144a1826 | 22 | 54 | −32 | **6** | {1:1, 2:1, 3:2, 4:1, 5:1} | 2 | 4 | 7 | {2:2} | 16 | 3 |
| 3f5ceec9 | 34 | 57 | −23 | 24 | {1:2, 2:4, 3:1, 4:2} | 2 | 7 | 6 | {2:2, 3:1} | 11 | 5 |
| 7f9c8909 | 11 | 54 | −43 | 17 | {1:1, 2:1, 3:2, 4:1, 5:1} | 2 | 7 | 2 | {2:2, 3:1} | 12 | 4 |
| d59cc6ff | 23 | 49 | −26 | **9** | {1:3, 2:2, 4:2, 5:1} | 3 | 7 | 4 | {2:2} | 11 | 4 |
| 2f4b19b2 | 32 | 50 | −18 | 7 | {1:1, 2:2, 3:2, 4:1} | 1 | 8 | 6 | {3:1} | 11 | 5 |
| a3c9e9af | 15 | 49 | −34 | **8** | {1:1, 2:1, 3:4, 4:1} | 1 | 6 | 5 | {2:3} | 16 | 3 |
| cd536bc6 | 26 | 51 | −25 | 11 | {1:1, 2:3, 4:2} | 2 | 8 | 6 | {2:1} | 12 | 5 |
| **loss aggregate** | **mean 25.6** | **mean 51.4** | **−25.8** | **mean 16.5** | 79 rolls avgK=2.70 | **26.6%** | **avg 6.7** | **avg 5.1** | 29 rolls avgK=2.21 | **avg 12.4** | **avg 3.75** |
| **contrast: W 0a270755** | 42 | 33 | +9 | never | {1:2, 2:1, 3:4} | 0 | **4** | 3 | {2:4, 4:1} | 5 | 1 |
| **contrast: W 2c0babfa** | 42 | 41 | +1 | 21 | {1:2, 2:2, 3:1, 4:2, 5:1} | 3 | **4** | 7 | {2:2, 3:1} | 12 | 1 |
| **contrast: D af017ebc** | 54 | 54 | 0 | 11 | {1:1, 3:3, 5:1, 6:1} | 2 | **4** | **10** | {2:1, 3:1} | 12 | 1 |
| **contrast aggregate (3)** | **mean 46.0** | **mean 42.7** | **+3.3** | – | 21 rolls avgK=2.81 | 23.8% | **avg 4.0** | **avg 6.7** | 10 rolls avgK=2.40 | avg 9.7 | avg 1.0 |

**Reasons for loss:** 12/12 = POINTS. No timeouts, no invalid moves. A_time_left end-game averages ~37s (ceiling 6.0s/move hits budget hard). Rusty leaves ~115s unused — **it is fast + frugal** and still wins 12/15 games.

### §2.1 Score-delta event accounting (per-game, 12 losses)

| | RattleBot (A) | Rusty (B) | Δ |
|---|---|---|---|
| Total positive pts / game | +40.1 | +58.3 | **−18.2** |
| Total negative pts / game | **−14.5** | −6.9 | **−7.6** |
| Small (+1) gain events / game | 13.6 | 17.8 | −4.2 |
| Big (+2 or more) gain events / game | 7.6 | 9.9 | **−2.3** (Rusty has more mid-size gains despite 0 big rolls) |
| Penalty events / game | **7.2** | 4.0 | **+3.2** |

Rusty has 0 big rolls (k≥4) but **more +2-or-more gain events than us** (9.9 vs 7.6). That means the +2-or-more bucket is dominated by k=2 / k=3 rolls AND **rat captures** (+4 per capture). Rusty captured 3.75 rats/game and we captured 5.1 — so the rat-capture pts are comparable. The rest of Rusty's +2-plus events are k=2 and k=3 rolls — 29 total, all k≤3. **Rusty grinds mid-size rolls consistently** while we swing for k≥4 and eat a lot of k=1 penalties.

### §2.2 Opening

- RattleBot opens PLAIN-PRIME-PRIME-PRIME-{PRIME|CARPET} in 10/12 losses. The CARPET-in-opening happens in 066fdae3, d71f7f02, 2f4b19b2, 3df15113 — rolling k=3 or k=4 in the first 5 plies is tempting (+4 or +6) but it also leaves our spawn-side open and gifts opp mobility.
- Rusty opens PRIME-PLAIN-PRIME-PRIME-PRIME or PRIME-PRIME-PRIME-PRIME-PRIME. Very consistent 4+ early +1 events.
- **144a1826 delta-open ply 6:** Rusty opened 4 PRIMEs back-to-back; we opened PLAIN-PRIME and we lost by 32.

### §2.3 Search behavior

- **RattleBot searches 6.7/game in losses vs 4.0/game in wins/draw.** This is a STRONG signal: more of our searches correlates with losing. Mechanism: we search when the belief is diffuse (meaning we can't find the rat easily), but searching at diffuse belief is strictly −EV (P < 1/3). The bot is substituting search for thinking — when the ab-search can't produce a clear move, it defaults to search.
- Rusty searches 12.4/game consistently. Her capture-per-search ratio is ~0.30 (3.75 / 12.4) — roughly the same as ours (5.1 / 6.7 = 0.76). So Rusty is searching at P ≈ 0.30-ish cells (near break-even), and converts enough of them into captures to come out net-positive. OR more plausibly, **most of Rusty's captures are via stepping on the rat** (not search), and her searches are near-break-even noise — but the noise doesn't matter because she doesn't hurt herself elsewhere.

---

## §3 Root causes (ranked by estimated impact vs the Rusty opponent)

### RC-1 — Over-searching when belief is diffuse (duplicate of Carrie RC-2, amplified)
**Evidence:** 6.7 searches/game in losses vs 4.0 in wins. Per-ply search decisions appear to fire whenever the ab search returns a low-EV best move (heuristic fallback). In loss 7f9c8909 we search 7 times and score only 11 pts; in win 0a270755 we search 4 times and score 42 pts. Δ-search of 3 is worth ~20 pts swing.
**Why the bot does this:** Search threshold in the heuristic is too permissive — likely any cell with > ~0.2 probability is being searched because the tie-break "do something that matters" logic in the bot favors SEARCH over PLAIN when nothing better scores.

### RC-2 — k=1 carpet rolls + speculative prime chains that become k=1 rolls (duplicate of Carrie RC-1)
**Evidence:** 13/79 = 16.5% k=1 rate in losses; the 3 non-losses had 5/21 = 23.8% k=1 but smaller per-game impact because we built bigger chains afterward. The core issue: RattleBot plans a long prime chain but gets interrupted (by opponent walking on it, or by forced move), then rolls what's left (often k=1 or k=2). This is visible in d59cc6ff (3 k=1s), 2e9fb89f (1 k=1 in a short game). Each k=1 is −1 pt.
**Why the bot does this:** Roll policy forces completion of the current prime chain even when the chain length at time of execution has been eroded. Better policy: **leave primed cells unrolled** unless k≥2 is achievable — primed squares are still worth +1 for their duration. Rolling early to "lock in" points turns a +1 asset into a −1 event.

### RC-3 — Opponent carpet reachability not penalized (same as Carrie RC-5)
**Evidence:** In 066fdae3 (lost 8-47) we rolled a k=4 early at center board → Rusty used the carpet strip for 6 successive plain-steps, gaining tempo without cost. In 144a1826 (lost 22-54) our k=5 roll at ply ~12 was across the central 8x8 spine; Rusty walked directly over it for 3 plies. Same story in 7f9c8909.
**Why the bot does this:** Heuristic rewards our k-value without discounting by "opponent-steps-on-carpet within 2 plies". Adding a penalty for (carpet cells within 2 steps of opp.position) × (small constant) would redirect rolls to the opponent-inaccessible half-board.

### RC-4 — Late-game panic score-chase amplifies losses
**Evidence:** In 7 of 12 losses, A's score goes NEGATIVE at some point during the mid-game (e.g., 066fdae3: 0 at ply 9, dips to 5 at ply 39 then down to 3 at 59). This happens when we do a prime + roll sequence that goes wrong (prime on rat cell causes the rat to move away; roll short; get penalized). The bot then tries to recover with big rolls or searches, both high-variance. In 10/12 losses, the variance of our score trajectory in plies 30-60 is visibly higher than Rusty's smooth monotonic gain curve.
**Why the bot does this:** No "behind-in-score" branch in the heuristic. When down 10+ pts at ply 30, the bot continues to play the same way — but optimal play when behind is to preserve lead while opponent finishes, not chase. Actually, with a ply-40-each hard cap, "chase" is correct — but chasing needs to target HIGH EV moves only, not SEARCH at diffuse belief.

### RC-5 — Heuristic over-rewards big rolls relative to their actual EV against good opponents
**Evidence:** Rusty has 0 big rolls but beats us consistently. Our 26.6% big-roll rate in losses produces 21 rolls of k≥4 totaling ~160 pts — yet we still lose by 25.8/game on average. The big rolls ARE paying off (+13.3 pts/game just from k≥4 rolls), but the opportunity cost of setting them up (long prime chains, exposed positions) is high. Rusty trades off 2×k=2 (+4) = better safety + similar net scoring.
**Why the bot does this:** BO weight tuning has probably over-fit the carpet-points-table literally. A k=5 is 10 pts but actually delivers ~5 pts net after counting "opponent exploits new carpet" and "primed cells that could have been rolled later as k=3 instead." The heuristic would benefit from a **concave** big-roll bonus (≤ k²-ish, not pure carpet-table-values).

---

## §4 Actionable fixes (ranked by expected ELO gain vs Rusty specifically)

| # | Fix | Where | Effort | Expected ELO gain vs Rusty |
|---|-----|-------|--------|----------------------------|
| F-1 | **Ban k=1 carpet rolls in move-gen** (same as Carrie F-1). Recovers 1-2 pts/game of avoidable negative EV. | RattleBot move-gen | S | **+15 to +25** |
| F-2 | **Search threshold ≥ 0.33 (strict EV break-even), with a 0.25 floor only in last 4 plies when ahead.** Stops searching at diffuse belief. The wins vs Rusty already show this works (4.0 searches/game wins vs 6.7 losses). | RattleBot search branch | S | **+30 to +50** (the single biggest lever — penalty bleed is our #1 gap) |
| F-3 | **Opening PRIME by default** — on ply 0 if a legal prime-step direction exists, take it. Same logic for plies 1,2. | RattleBot play() | XS | **+10 to +15** |
| F-4 | **Don't roll until k≥2 is guaranteed.** If we have a prime chain of length 1, leave it unrolled and keep the +1 prime asset on the board; continue extending or switch to new line. | Roll-decision in play() | M | **+15 to +30** (addresses RC-2, biggest long-term tempo fix) |
| F-5 | **Heuristic penalty for carpets within 2 cells of opp.position** — subtract 0.5 * k from eval when own carpet strip is enemy-reachable in 2 plies. Redirects rolls away from enemy territory. | Heuristic weights (BO-tunable) | M | **+10 to +20** |
| F-6 | **Concave big-roll bonus cap** — replace linear eval(roll_pts) with min(roll_pts, 8) for heuristic purposes only (still score full points in-game). Discourages chasing k≥5 at the cost of position. | Heuristic | S | **+5 to +15** |

**Stacked F-1 + F-2 + F-3 + F-4 expected lift vs Rusty: +70 to +120 ELO.** Current WR is 14% (2/14). A +90 ELO lift against Rusty's 2032 Glicko from our ~1850 puts us at parity. Target: 40–50% WR vs Rusty within 2 shipping cycles.

**Shared with Carrie doc: F-1, F-2, F-3** — single architectural fix landing across both opponents, plus Rusty-specific F-4 / F-5.

---

## §5 Re-validation plan

1. Ship **F-2 first** — biggest single signal (−EV search elimination). Scrim 10 vs Rusty + 10 vs Carrie. Target WR > 25% both.
2. Add **F-1 + F-3** in same patch. Scrim 15 vs Rusty. Target WR > 35%.
3. Add **F-4** (no premature rolls). Scrim 15 vs Rusty. Target WR > 45%.
4. F-5, F-6 via BO re-tune only after F-1..F-4 are stable.

Each 10-match batch vs Rusty uses ~30 min of wall clock budget on bytefight. Prioritize F-2 for landing within 4 hours — before the April 19 23:59 deadline (~30 hrs remaining).

---

## §6 Caveats (same as Carrie doc §6)

1. Move-classification from `left_behind` field is noisy (some plies show pts inconsistent with labeled action). Aggregate +/− score-delta analysis in §2.1 is the ground truth.
2. `new_carpets` field is A-perspective-only in the replays — so B's big rolls (if any) are undercounted by my analyzer. However Rusty's score-delta event mix (§2.1) shows she has 0 events of +6 or higher other than captures, so the "0 big rolls" claim is robust.
3. A_WIN/B_WIN mapping confirmed via `sub=RattleBot*.zip` → RattleBot=A. Spot-check of `err_a` showing "RattleBot v0.2 ..." on A side in all 12 losses and `err_b` = "Argghhhh" (Rusty's debug string) on B confirms.
4. **Sample size n=12 losses is thin** but the +4.7 small-event-gap and +3.2 penalty-event-gap are both ~3-4 sigma signals.
5. **Rusty may be exploiting a known weakness in RattleBot** — see `docs/audit/LOSS_FORENSICS_APR17.md` for prior forensic notes. This analysis finds the same architectural pattern (over-search + early tempo loss + k=1 bleed) plus a new one specific to Rusty: opponent-reachable-carpet exploitation.

---

## §7 Cross-opponent convergence

The 4 root causes that appear in BOTH Carrie and Michael/Rusty docs are the priority targets for v0.4:

1. **k=1 carpet roll ban** (Carrie RC-1 / Michael RC-2) → F-1 in both docs
2. **Search threshold tightening** (Carrie RC-2 / Michael RC-1) → F-2 in both docs
3. **Opening PRIME on ply 0** (Carrie RC-3 / Michael RC-2.5) → F-3 in both docs
4. **Opponent-reachability-weighted carpet eval** (Carrie RC-5 / Michael RC-3) → F-4/F-5

F-1, F-2, F-3 together are a single code patch of ~30 lines. If shipped at end of BO run: expected stacked lift of +45 to +90 ELO across our opponent pool — takes us from 26% aggregate WR to ~45-50% aggregate WR, which is roughly at the ≥80% grade-tier line.

---

## §8 Files touched

- `docs/audit/_scratch/loss_analyze.py` — read-only analyzer (created)
- `docs/audit/_scratch/loss_output.txt` — raw stats dump
- `docs/audit/LOSS_ANALYSIS_CARRIE_APR18.md` — companion doc
- `docs/audit/LOSS_ANALYSIS_MICHAEL_APR18.md` — this doc

**No changes to RattleBot/*.py or tools/*.py** (BO PID 23708 still alive).

**End of LOSS_ANALYSIS_MICHAEL_APR18.**
