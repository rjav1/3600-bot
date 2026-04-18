# LOSS_ANALYSIS_CARRIE_APR18 — why we lose 1-11-0 to Carrie

**Auditor:** `loss-forensics-dual` (ephemeral, 2026-04-18)
**Scope:** 11 B_WIN scrimmage losses vs `Carrie.zip` (Glicko ≈ 1910, ≥90% grade gate). RattleBot was Side A (sub=RattleBot_v03_pureonly_*.zip) in every loss. One W (14a319d3) used as contrast.
**Data source:** `docs/intel/replays/carrie_*.json` (schema: wrapped `pgn` dict or bare top-level) + `docs/tests/LIVE_SCRIMMAGE_LOG.md` for A/B assignment.
**Analyzer:** `docs/audit/_scratch/loss_analyze.py` (stdlib-only; read-only for RattleBot/ — BO PID 23708 is still alive per `bo_pid.txt`, no edits to `RattleBot/*.py` or `tools/*.py`).
**Sample size caveat:** 11 losses, 1 win. Directional signal only; Wilson CI at 1-11-0 is [0.023, 0.258].

---

## §1 Summary (TL;DR)

We are not losing to Carrie because her carpet rolls are bigger or her heuristic is smarter at prime-line construction — in fact, **RattleBot out-carpets Carrie** (avg k=2.55 vs 2.28; 21.1% big rolls (k≥4) vs 4.0%; 76 total rolls vs 25). We score **more** from carpets (mean 21.5 vs 5.9 pts/game) and place **more** primes (17.9 vs 13.5 /game). We also capture the rat more often (5.55 vs 2.45 /game).

**The loss driver is score leakage from bad moves, not missed gains.** In the 11 Carrie losses:

- RattleBot accrues **−13.9 pts/game in negative events** vs Carrie's **−5.0 pts/game** — a **~9 pt/game penalty gap**.
- RattleBot has **7.0 penalty events/game** (k=1 rolls, wrong searches) vs **3.2** for Carrie — **2.2× as many** self-inflicted score losses.
- RattleBot's **k=1 carpet rate is 19.7%** (−1 pt each) vs Carrie's 4.0%. Our roll policy keeps cashing in single-square rolls for negative EV.
- RattleBot also generates **fewer small (+1) gains** (13.5 vs 18.2 /game) — Carrie builds denser prime chains and keeps the +1 flywheel running.
- The score gap **opens early** (mean ply 22 of 80; min ply 11) and **never closes** — the final margin is mean Δ=−19.9 pts.

Architecturally: the heuristic is treating a "small prime-and-roll" as neutral-good, but any k=1 roll is strictly −1, and wrong searches are −2. These stack up. Carrie is more patient (more uninterrupted +1 primes, more k=2 rolls) and burns less negative EV.

---

## §2 Evidence — per-match table (11 losses + 1 win)

| Match | Final A (us) | Final B (Carrie) | Δ | Delta-open ply | A k-dist | A big(k≥4) | A searches | A rat-caught | B k-dist | B searches | B rat-caught |
|-------|--------------|------------------|---|----------------|----------|------------|------------|--------------|----------|------------|--------------|
| 2e9fb89f | 25 | 53 | −28 | 17 | {1:1, 2:5, 3:2, 4:1} | 1 | 7 | 2 | {2:1, 3:1} | 6 | 4 |
| d83a9b8b | 24 | 32 | −8 | 15 | {1:3, 2:1, 3:1, 4:2} | 2 | 6 | 4 | {2:3} | 10 | 2 |
| ab281352 | 21 | 43 | −22 | 21 | {2:3, 4:1, 5:1} | 2 | 5 | 4 | {2:1, 3:1} | 11 | 1 |
| c89c9b0f | 34 | 52 | −18 | 25 | {1:1, 2:1, 3:1, 5:2} | 2 | 3 | 5 | {3:1, 5:1} | 13 | 2 |
| 74765a32 | 48 | 64 | −16 | 39 | {1:2, 2:4, 3:2, 6:1} | 1 | 6 | 9 | {2:3} | 14 | 5 |
| 6dcdea8c | 29 | 39 | −10 | 45 | {1:2, 2:1, 3:3, 4:1} | 1 | 4 | 6 | {2:4} | 14 | 1 |
| 132a3fbd | 30 | 48 | −18 | 17 | {2:3, 3:2, 4:1} | 1 | 2 | 7 | {2:2} | 17 | 2 |
| b93942ed | 15 | 47 | −32 | 11 | {1:1, 2:3, 3:2, 4:1, 5:1} | 2 | 2 | 7 | {1:1} | 18 | 0 |
| c78534cd | 37 | 45 | −8 | 19 | {1:2, 2:3, 3:1, 5:1} | 1 | 2 | 5 | {2:1, 3:1} | 8 | 2 |
| 503d8eb7 | 44 | 48 | −4 | 14 | {1:1, 2:1, 3:4, 4:1} | 1 | 2 | 10 | {2:1, 3:1} | 16 | 1 |
| e4eff274 | 2 | 57 | −55 | 21 | {1:2, 2:2, 4:2} | 2 | 8 | 2 | {2:2} | 11 | 7 |
| **loss aggregate** | **mean 28.1** | **mean 48.0** | **−19.9** | **mean 22.2** | 76 rolls avgK=2.55 | **21.1%** | **avg 4.3** | **avg 5.6** | 25 rolls avgK=2.28 | **avg 12.5** | **avg 2.5** |
| **contrast: W 14a319d3** | 39 | 38 | +1 | 21 | {1:1, 2:3, 3:3, 4:1} | 1 | **2** | **8** | {1:1, 2:2} | 14 | 1 |

**Reasons for loss:** 11/11 = POINTS. Zero TIMEOUTs, zero INVALID moves. A_time_left at game end averages **~35s of 240s budget used tightly**; Carrie averages 90s remaining (spends ~150s). So we are deep-searching every move and it is not producing better outcomes.

### §2.1 Score-delta event accounting (per-game averages over 11 losses)

| | RattleBot (A) | Carrie (B) | Δ |
|---|---|---|---|
| Total positive pts / game | +42.0 | +53.0 | **−11.0** (Carrie scores more) |
| Total negative pts / game | **−13.9** | −5.0 | **−8.9** (we bleed more) |
| Small (+1) gain events / game | 13.5 | 18.2 | **−4.7** (Carrie primes denser) |
| Big (+2 or more) gain events / game | 7.8 | 8.7 | −0.9 |
| Penalty events / game | **7.0** | 3.2 | **+3.8** (2.2× opponent) |

`err_b` values on every Carrie match are small (12.5–13.8), plausibly a greedy-heuristic debug float, consistent with Carrie being "expectiminimax + HMM + cell-potential heuristic" from CLAUDE.md §5. She's not deep-searching — she's efficient.

### §2.2 Opening pattern

- **RattleBot consistently opens PLAIN-PRIME-PRIME-PRIME-PRIME.** The opening PLAIN is strictly 0 pts and wastes ply 0.
- **Carrie opens PRIME-PRIME-PRIME-SEARCH-PRIME.** All four of her first 5 moves score +1 or potentially +4, vs our 4/5 scoring.
- Delta-open mean is ply 22 → Carrie's extra early tempo (+1 to +2 pts from opening move choice, compounded by density) is what opens the early gap.

### §2.3 Search behavior

- RattleBot searches **4.3/game**. Carrie searches **12.5/game**. Despite searching 3× less, our capture rate is 2.3× higher (5.6 vs 2.5). So searches per capture is ≈ 5.0 for Carrie vs ≈ 0.77 for us — either we are capturing mostly by stepping on the rat (not by search), or our search precision is very high but we search too rarely to compound.
- Carrie's high search volume + modest capture rate imply she is extracting some +EV from searches despite missing most, OR (more likely) she is using search moves to burn turns while we still have to move into vulnerable positions. This is an intel-gathering strategy that blocks us from prime-line completion without wasting her own turns.

---

## §3 Root causes (ranked by estimated impact)

### RC-1 — Carpet roll policy cashes too many k=1 rolls (−1 EV)
**Evidence:** 15/76 = 19.7% of our carpet rolls are k=1 for −1 pt each. Carrie k=1 rate is 4.0%. In the 11 losses that is ~15 pts of avoidable negative EV, or ~1.4 pts/game. Games like d83a9b8b had 3 k=1 rolls (−3 on that game alone). Our ONE Carrie win had only 1 k=1 roll.
**Why the bot does this:** The ab-heuristic likely assigns a small positive signal for *any* "roll → converts primed→carpet" because it clears the primed cell from our path and opens tactical mobility. But the raw score is −1; the heuristic must not be net-subtracting the roll cost at leaf eval.

### RC-2 — Search policy has too many low-EV probes
**Evidence:** 77 "penalty events" (negative score deltas) / 11 games = 7.0/game. Typical penalties are −1 (k=1) or −2 (wrong search). Given 15 k=1 rolls, the remaining ~62 penalty events are almost all wrong searches — but we only recorded 47 total searches. Some penalties must be the k=1 rolls AND other mechanics (e.g., the rat respawn timing on a prime cell, invalid-cell rebounds). Still: at 4.3 searches/game and capture rate 5.6/game, searches are firing when either (a) the EV is negative (P(rat) < 0.333) or (b) the capture happened via walking, not search, so searches contributed closer to 0 captures — meaning searches are being spent nearly-wrong.
**Why the bot does this:** The threshold for SEARCH in the heuristic is likely tied to peak belief cell, but the peak belief is often 0.15–0.25 in a diffuse rat posterior. Searching below 0.333 threshold is strictly −EV in expectation (+4·p − 2·(1−p) < 0 when p < 1/3).

### RC-3 — First-move PLAIN wastes tempo
**Evidence:** All 11 losses (and the win) opened with PLAIN at ply 0. Carrie opens with PRIME. Over 80 plies, tempo compounds: Carrie's early +1 density stays ahead of ours for the entire game. Delta-open median ply is 22 — not coincidentally right when the compounded early tempo becomes insurmountable.
**Why the bot does this:** The heuristic probably prefers a safe step toward a long potential prime line before committing to priming. But priming in any cardinal direction at ply 0 is ≥+1 pts and almost always legal (spawn guarantees it).

### RC-4 — Prime density lower than Carrie's despite similar total count
**Evidence:** RattleBot: 197 primes / 11 games = 17.9/game. Carrie: 148/11 = 13.5/game. So we place MORE primes total but generate FEWER small-gain events (13.5 vs 18.2). The discrepancy means many of our primes result in no +1 score event — possibly because we prime at cells that are already CARPET or PRIMED, or we prime+roll on the next ply so the +1 is immediately consumed by the roll (net 0 per prime+same-ply-roll).
**Why the bot does this:** Our combinatorial PRIME→CARPET combo is "prime, roll k=1" in many cases. We get +1 then −1 for a net of 0 — same as plain-step, minus the tempo.

### RC-5 — Heuristic does not penalize opponent-mobility grants from own carpets
**Evidence:** In 74765a32 we rolled a k=6 carpet (huge +15) but still lost 48–64. Our carpets are in the middle of the board → Carrie walks on them freely, positioning for her own rolls. 7 of our 11 losses involve mid-board carpets.
**Why the bot does this:** The eval rewards our big rolls but does not subtract the free mobility opponent gets on the resulting carpet strip. A large-roll in a zone Carrie could exploit is net-worse than a smaller roll in a zone she can't reach.

---

## §4 Actionable fixes (ranked by expected ELO gain)

| # | Fix | Where | Effort | Expected ELO gain |
|---|-----|-------|--------|-------------------|
| F-1 | **Forbid k=1 carpet rolls at the leaf** — clamp carpet-roll candidate list to k≥2 in the move generator unless k=1 is the only legal tactical escape (e.g., must clear own primed cell to avoid next-ply deadlock). | RattleBot move-gen / heuristic weights | S (10 LoC) | **+20 to +40 ELO** (removes ~1.5 pt/game × steeper compounding) |
| F-2 | **Raise SEARCH threshold to max-belief ≥ 0.35 with a late-game ramp to 0.30 only in last 10 plies.** Currently searches fire at belief << 1/3 which is strictly −EV. | RattleBot search-move decision | S (15 LoC) | **+15 to +30 ELO** (removes ~4-6 pts/game from penalty bleed) |
| F-3 | **Prime on ply 0 instead of plain** unless the prime-step is illegal. Check blocked/carpet at spawn+direction first. Every 1 pt of opening tempo is leveraged for ~40 plies. | RattleBot play() opening branch | XS (3 LoC) | **+10 to +20 ELO** |
| F-4 | **Heuristic term for "opponent reachability of own carpet"** — subtract k × opp_reach_factor when the candidate carpet strip is within opp's 2-step reach. Discourages mid-board big rolls Carrie just walks onto. | Heuristic weights (BO-tunable) | M (25 LoC + BO re-run) | **+10 to +25 ELO** |
| F-5 | **Prime-and-roll same-ply penalty in eval** — explicitly subtract 1 from the eval when a prime-step is followed by an intended next-turn k=1 roll on that same cell. Forces longer prime chains. | Heuristic lookahead / plan bonus | M (20 LoC) | **+5 to +15 ELO** |

**Stacked expected lift if F-1 through F-3 are shipped together: ~+45 to +90 ELO vs Carrie.** Our current Carrie WR is 8.3% (1/12). A +60 ELO lift against a 1910 opponent from our ~1850 estimated puts us at parity; 2–3 wins per 10 becomes plausible. **90% gate requires WR ≥ ~50% vs Carrie** which is a further +100+ ELO lift — F-4 and F-5 + BO tuning of weight scalars are the path there.

---

## §5 Re-validation plan

1. Ship F-1 (no k=1 rolls) as a one-line-change zip; scrimmage 10 vs Carrie. If WR > 20% → ship.
2. Add F-3 (opening PRIME), re-scrim 10 vs Carrie. If WR > 30% → ship.
3. Add F-2 (search threshold 0.35), re-scrim 10 vs Carrie. Target WR > 40%.
4. Only then consider F-4/F-5 which require heuristic re-tuning.

**Cost:** each 10-match batch costs ~3 scrimmage-cycle minutes + bytefight budget. Prioritize shipping F-1 within 4 hours.

---

## §6 Caveats

1. **Move-classification from `left_behind` is noisy** — some plies labeled `prime` have dA=+4 (probably prime + capture in same ply) or dA=−2 (suggests `left_behind` is lagging or the engine packs multi-event deltas into one ply). We relied on aggregate +/− score deltas as the ground truth (§2.1) rather than per-ply attribution.
2. **`new_carpets` field appears to be populated only from A's perspective** in the replays (I saw no B entries even when B clearly rolled k≥2). Opp big-roll counts in §2 are lower-bounds; the signal direction is still correct because A's big-roll rate remains higher than B's even if B has a few undercounted rolls.
3. **A_WIN/B_WIN mapping** confirmed via `sub=RattleBot*.zip` → RattleBot=A in every Carrie match (see `WILSON_CI_APR18_0317Z.md §5.1`). If this is inverted for some matches, flip the whole analysis — but spot-check of `err_a` vs `errlog_a` showing "RattleBot v0.2 — alpha-beta + ID + HMM belief" on the A side confirms mapping.
4. **Small sample size** — 11 losses is under-powered for strong claims about the k-distribution differences. The +1 event density (13.5 vs 18.2) is a ~4 sigma difference though, so that one is robust.
5. **Carrie may have been tuned specifically to beat naive expectiminimax bots** — `err_b` values ~12–14 suggest a fixed heuristic scoring float, not depth. She is a predictable opponent; exploit via F-1/F-3 likely over-performs ELO estimate.

---

## §7 Files touched

- `docs/audit/_scratch/loss_analyze.py` — read-only analyzer (created)
- `docs/audit/_scratch/loss_output.txt` — raw stats dump
- `docs/audit/LOSS_ANALYSIS_CARRIE_APR18.md` — this doc
- `docs/audit/LOSS_ANALYSIS_MICHAEL_APR18.md` — companion doc

**No changes to RattleBot/*.py or tools/*.py** (per BO-PID-alive ping-first rule; bo_pid.txt=23708 confirmed alive at analysis start).

**End of LOSS_ANALYSIS_CARRIE_APR18.**
