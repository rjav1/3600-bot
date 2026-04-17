# BOT_STRATEGY v0.3 Addendum — Closing the Carrie Gap

**Author:** strategy-architect
**Date:** 2026-04-17 (T − 50 h to submission lock, approx)
**Status:** Proposed. Extends `docs/plan/BOT_STRATEGY.md` v1.1 §4 (v0.3 row) and `docs/plan/BOT_STRATEGY_V02_ADDENDUM.md` §7 with specifics informed by real evidence. Supersedes nothing.
**Scope:** v0.3 + a compressed v0.4/v0.5 path to deadline. Assumes BO RUN1 lands on schedule; contingency in §6 if it doesn't.
**Inputs consulted:**
- `docs/plan/BOT_STRATEGY.md` v1.1 (primary)
- `docs/plan/BOT_STRATEGY_V02_ADDENDUM.md` (v0.2 baseline + §7 v0.3 preview)
- `docs/tests/SEARCH_STATS_V02.md` (depth-9 baseline, 22k nps, 97.9 % cutoff-on-first)
- `docs/audit/SEARCH_PROFILE.md` (top-5 bottlenecks; "do now" +1 ply available; make/unmake → +0.6 ply)
- `docs/research/ALT_ARCH_MCTS.md` (MCTS preliminary 2-1, 0 captures, hybrid recommended in §6.2)
- `docs/research/CARRIE_DECONSTRUCTION.md` (H1–H8 formula hypotheses)
- `docs/plan/FAKE_OPPONENTS.md` (v0.2 vs FakeAlbert 3-0, vs FakeCarrie 1-2)
- `docs/research/TABLEBASE_FEASIBILITY.md` (tablebase = time_mgr tweak; book defer)
- `docs/plan/BO_TUNING.md` (RUN1 in flight, ETA 5.3 h)
- `docs/audit/V01_LOSS_ANALYSIS.md`, `docs/audit/AUDIT_V01.md` (v0.1 baseline)
- task list current state (#30, #31, #44, #46, #48 in flight; #49 = this doc)

---

## §1 — Evidence summary (what changed since v0.2 addendum)

### 1.1 Proxy scrimmage results (unpaired, small n, directional only per FAKE_OPPONENTS.md)

| Matchup | Result | Interpretation |
|---|---|---|
| RattleBot v0.2 vs FakeAlbert | **3-0 (100 %)** | **Past the 80 % Albert tier on proxy.** FakeAlbert is α-β depth-3 + minimal HMM + 3-feature heuristic. We crushed it. |
| RattleBot v0.2 vs FakeCarrie | **1-2 (33 %)** | **NOT past the 90 % Carrie tier.** FakeCarrie is same α-β depth-3 but with Carrie-style Σ P(c)/(1+d) heuristic. Our disadvantage against the stronger leaf is real and the gap is the v0.3 problem. |
| MctsBot vs RattleBot v0.2 | **2-1 preliminary (pair 0000 = sweep, margin +88 pts)** | MCTS carpet-greedy rollout is surprisingly competitive on open-board seeds but **catches 0 rats** vs RattleBot's 3-5/match. HMM-gated SEARCH is a structural edge worth ~ 20 pts/game we must preserve. |

### 1.2 Depth profile (SEARCH_PROFILE.md)

- **Pure-Python ceiling:** depth 11 at 2 s, depth 13 at 6 s (v0.2 baseline is depth 9 at 2 s — we are 2 plies below ceiling).
- **Top-5 bottleneck fix chain yields +0.6 to +1.1 plies** (T-20g "do now" bundle + make/unmake).
- At 50–80 ELO/ply (team-lead's stated conversion) that's **+50 to +180 ELO from depth alone** before any heuristic improvement.
- Profile attribution: 36 % leaf eval (F14/15/16 `_cell_potential_vector` is 24 %), 31 % `forecast_move` deep-copy, 17 % `ordered_moves` rebuild. Move-ordering itself is **not** the bottleneck anymore (SEARCH_STATS_V02 shows 97.9 % cutoff-on-first at depth 9, 49.8 % TT hit-rate — all tiers firing).

### 1.3 Time-budget reality at 240 s

- v0.2 currently runs per-turn ceiling 6 s (post-T-20a), which fits 6 s × 40 = 240 s total = tournament budget exactly **if every turn maxes out**. We won't; adaptive multipliers + easy-turn 0.6× compression keep mean usage at ~4 s/turn per BO_TUNING and V01_LOSS_ANALYSIS notes.
- **Audit needed (T-30a below):** run a 20-match v0.2-vs-v0.2 gauntlet under `limit_resources=True` (real seccomp on Linux/WSL) and verify 0 TIMEOUTs and mean depth ≥ 5.0. If mean depth drops below 5.0 under tournament clock, hard-flip to a 5.5 s flat schedule per BOT §7 row 14.

### 1.4 BO RUN1 state (BO_TUNING.md)

- In flight (PID 15388, ETA 5.3 h from task-brief timestamp). Will produce `weights_v02.json`.
- Objective: RattleBot-vs-FloorBot paired win-rate, 20 pairs/trial × 40 trials × 24 h cap.
- If RUN1 lands with ≥ +30 ELO vs `w_init` → weights adopted → FakeCarrie gate could shift from 33 % up (how much is unknowable until we re-test).
- If RUN1 lands with < +30 ELO → fall back to `w_init` per BOT §7 row 9; weight-tuning is not the v0.3 lever.

### 1.5 What v0.3 inherits from v0.2

From `BOT_STRATEGY_V02_ADDENDUM.md` + the completed tasks in #14–#40:
- 9-feature linear heuristic (F1/F3/F4/F5/F7/F11/F12 + F8 opp_line_threat + F13 belief_COM_dist). Plus the T-20c.1 multi-scale kernels F14/F15/F16 (the `_cell_potential_vector` in SEARCH_PROFILE is this).
- Per-turn ceiling lifted 3 s → 6 s (T-20a); single-source `safety_s` in `time_mgr` (T-20b).
- Move-ordering stack verified by T-20e instrumentation (hash/killer/history all firing; TT 49.8 %).
- `weights.json` loader + fallback wired in `agent.py` (T-20c.1 / T-20d).
- Opp-model interface stub in `opp_model.py` (T-20f), default `self-play`, bound behind env flag.
- Fallback `_emergency_fallback` preserved in `agent.py` top-level try/except (BOT §6.2).

---

## §2 — v0.3 Core Decision: Hybrid vs More Iteration on v0.2

**Decision: STACK MORE ITERATION ON v0.2 as the primary v0.3 candidate. The MCTS+HMM hybrid (task #48) is a parallel side-track built as a submission alternative, not the default promotion target.**

### 2.1 Why more iteration beats the hybrid as primary

1. **MCTS's structural handicap is verified.** ALT_ARCH_MCTS §4.1: MCTS over uniform-prior SEARCH gives up ~20 pts/game in captures that HMM-gated SEARCH captures cleanly. Fixing that inside MCTS requires real IS-MCTS determinization, which is ≥ 1 dev-day of risky new code. At T-50h with a single dev-search agent, the cost is ≥ 16 % of remaining budget for an unproven rewrite.
2. **Depth is on the table cheaply.** SEARCH_PROFILE item #1 (valid_search_moves tuple cache) is a 10-minute change for +0.4 ply. Item #2 (P-vec LRU) is 30 minutes for another +0.3 ply. Item #4 (MoveKey once) is 30 minutes for +0.15 ply. Total "do now" bundle: **~1.5 h dev for +0.6–0.85 ply ≈ +40–60 ELO**. That dwarfs any MCTS exploration upside.
3. **Carrie gap is a heuristic/depth problem, not an architecture problem.** FakeCarrie's Σ P(c)/(1+d) formula has the same FUNCTIONAL FORM as our F5 (`our_cell_potential`). What differs is calibration: her coefficient and distance kernel vs ours. BO RUN1 targets this exact axis. MCTS does not help here.
4. **Time risk is asymmetric.** If the hybrid ships and has a latent bug in the 240 s sandbox (seccomp, JIT, IPC jitter), we lose the submission. If we stack on v0.2 and a feature misfires, we revert to v0.2-w_init and still have a strong submission. Inertia is safety.

### 2.2 Why the hybrid is still pursued (as a side-track)

Per ALT_ARCH_MCTS §6.2 recommendation:
- On **easy open-board seeds**, MCTS's carpet-greedy rollout finds 50+ pt chains that our α-β may miss because of depth limits. Pair 0000 was a +88 pt sweep.
- **The hybrid (task #48)** is a minimal-change bolt-on: MCTS policy on move/carpet root decisions when `belief_entropy > threshold`, HMM-gated SEARCH unchanged. Preserves our capture edge.
- Task #48 stays **pending but staffed separately** (alt-arch-mcts or fresh agent). It is NOT on v0.3's critical path. Success criterion: hybrid beats v0.3 on paired ≥ 55 % over 50 matches. If it does, it promotes to v0.4 submission candidate.

### 2.3 "Three bets, ranked" summary

| Rank | Bet | Driver | Owner | Status |
|------|-----|--------|-------|--------|
| 1 (primary) | Stack depth + BO weights on v0.2 | SEARCH_PROFILE "do now" + BO RUN1 | dev-search (T-20g, in flight) + dev-heuristic | Primary v0.3 candidate |
| 2 (parallel) | Feature expansion — 2 new high-ROI features | Heuristic-quality lever (see §4) | dev-heuristic (T-30b below) | v0.3 parallel track |
| 3 (side) | Hybrid MCTS + HMM (task #48) | Open-board ceiling | alt-arch-mcts or dev-search-2 | v0.4 candidate only |

---

## §3 — Shortest path from 33 % → 60 %+ vs real Carrie

The team-lead's question. Answer is **a stack of small wins**, because no single lever adds 25 pp alone.

### 3.1 Budget allocation (~ 50 h remaining)

| Bucket | Hours | Expected ELO Δ | Stackable? |
|--------|-------|----------------|------------|
| Depth via "do now" SEARCH_PROFILE items 1+2+4 | 2 | +40 to +60 | Yes, with all below |
| Depth via make/unmake (item 3 + 5) | 5–8 | +50 to +70 | Yes (requires property test) |
| BO RUN1 weights adoption (if ≥ +30 ELO gate passes) | 0 (already running) | +30 to +80 | Yes |
| F17 priming-lockout + F18 opp-belief (see §4) | 4 | +20 to +40 | Yes |
| Endgame tablebase = extend search last 6 plies (TABLEBASE §B) | 2 | +10 to +20 | Yes |
| Hybrid MCTS bolt-on (task #48, side-track) | 8–12 | +0 to +50 (conditional) | Independent |
| **v0.3 total (sum excluding hybrid side-track)** | **13–16 dev-h + BO parallel** | **+150 to +270 ELO** | |

**Conversion math:** the FakeAlbert 100 % / FakeCarrie 33 % proxy split implies we need ~+200 ELO (half-Carrie to above-Carrie) to cross. +150 to +270 centered is +210. This is tight but inside the plausible range. The biggest risk is BO RUN1 failing to deliver — see §6.

### 3.2 Critical path (sequencing)

```
  [T-46g landing] ──► [T-30a timing audit] ──► dev green-light
                                                │
  [BO RUN1 complete]  ──────────────────────────┤
                                                │
  [T-30b features F17+F18] ──► [T-30c make/unmake] ──► [T-30d endgame extend]
                                                │
                                                ▼
                                         v0.3 gate (§5)
```

- **Parallel Wave 1 (now):** T-30a (timing audit, dev-integrator), BO RUN1 continues (dev-heuristic + BO harness, already running), T-46 T-20g (dev-search, already in flight).
- **Wave 2 (Wave 1 complete):** T-30b (features), T-30c (make/unmake).
- **Wave 3 (Wave 2 complete):** T-30d (endgame extend); v0.3 gate gauntlet.

---

## §4 — Feature expansion: which ones, and why

Current 9 features: F1, F3, F4, F5, F7, F11, F12, F8, F13. Plus T-20c.1 multi-scale P-vec kernels F14/F15/F16 (implicit in `_cell_potential_vector`, weighted implicitly through F5/F7).

### 4.1 F17 — `priming_lockout_penalty` (RECOMMENDED)

**Definition:** for each primed cell owned by us, check whether a legal roll of length ≥ 2 through that cell is still possible before the game ends. If NO — i.e. the prime is locked out by the opponent parking on the required path OR by the game running out of turns OR by no carpet ray of k ≥ 2 reaching any scoring k — mark that prime as "dead" and penalize with `−F17_w` per dead prime.

**Why it fits the Carrie gap:**
- V01_LOSS_ANALYSIS found that RattleBot v0.1 has a "priming-without-roll" failure mode: it primes aggressively (F3 rewards popcount) but gets blocked before rolling, so the primes are +1 pt each that blocks our own mobility (BOT §2 and SPEC §2.2 — we can't plain-step onto PRIMED).
- Locally, each dead prime is −1 in score (we gained +1 priming it) plus −N in denied future mobility. F17 makes this cost explicit in the leaf.
- Research HEURISTIC §D.1 touches this indirectly via F10 (opp_mobility_denied) but from the OPPONENT side. F17 is the symmetric self-penalty.

**Compute cost:**
- Per primed cell, scan 4 rays checking if an eventual `k ≥ 2` carpet is reachable. O(4 × 7) = 28 scans per primed cell; typical mid-game ≤ 10 primed cells; total ≤ 280 ops = ≤ 3 µs per leaf. Within the 100 µs leaf budget.
- Can reuse `_ray_reach` (already hot; SEARCH_PROFILE item #2 caches it).

**Expected ELO Δ:** +10 to +25. Mechanism: penalizes 1–2 bad primes per game (each worth ~−3 pts when dead), converts to ~2–5 pt swing per game, ~3–8 pp win-rate.

**`w_init` bound:** sign negative, initial `−0.25` (dead prime ≈ lost +1 + opp bonus; match F4's positive 0.2 magnitude).
**BO bound:** `w17 ∈ [−2.0, 0.0]`.

### 4.2 F18 — `opp_belief_proxy` (RECOMMENDED)

**Definition:** a cheap model of the opponent's belief about the rat. Not a full HMM — a **single-number proxy**: estimated entropy of the opponent's posterior, derived from:
- Turns since last mutual rat capture (both `board.player_search` and `board.opponent_search` history).
- Number of opp-observations (proxy: turn count × 1, since each opp turn generates one sensor reading for them).
- If we observed `board.opponent_search.result == True`, we know opp's belief just reset to `p_0`; set their entropy to `H(p_0) ≈ 5.2 bits`.

`F18 = H_opp_estimated`. Higher = opp's belief is diffuse = opp is unlikely to make a +EV search = we can defer blocking searches.

**Why it fits:**
- BOT §7 row 5 flip-trigger: "opp captures rat > 40 % of games → add opp-belief predictor". We don't currently track this and can't fire the trigger cleanly.
- Carrie and Albert both run HMM per SPEC and CARRIE_DECONSTRUCTION. Their belief has a trajectory; if we model it (even crudely), we can **time our SEARCH moves to capture before they do** and avoid the belief-reset-to-p_0 cost on our own posterior.
- ALT_ARCH_MCTS §5 findings: MCTS +88 on open boards suggests greedy carpet-grabbing WITHOUT speculating about opp-searches. F18 inverts this: when opp's F18 is low (their belief is concentrated), we race; when high, we prime/carpet safely.

**Compute cost:** O(1) per leaf — just read `board.opponent_search` and a stored counter.

**Expected ELO Δ:** +5 to +20. Smaller than F17 because the signal is indirect and correlated with F11/F12 (our own belief entropy).

**`w_init`:** sign positive (high opp-entropy = we have the info edge = good for us), initial `+0.10`. **BO bound:** `w18 ∈ [0.0, 0.5]`.

### 4.3 F19 — `rolls_remaining_potential` (STRETCH — include only if time permits)

**Definition:** sum over all primed cells of `CARPET_POINTS_TABLE[max_roll_length_possible(cell)] × P(we_can_roll_before_turn_80)`. Where `P(we_can_roll_before_turn_80) = min(1.0, (80 − turn_count) / path_length)`.

**Why:** captures the **endgame discount** that F5 (current cell-potential) doesn't. In the last 10 turns, a k=5 roll requires you to already be on a usable cell AND have the turns to walk to it. F19 penalizes far-from-usable primes as time runs out.

**Expected ELO Δ:** +3 to +10. Low-magnitude, late-game only. Cut first if time-pressed.

**Skip rationale:** this is essentially what the endgame tablebase extension (§5.1) does implicitly via deeper search. Ship the tablebase extend instead.

### 4.4 Recommendation

- **Add F17 and F18 in v0.3.** Both are cheap (< 5 µs combined), both attack documented failure modes (V01_LOSS_ANALYSIS, BOT §7 row 5 trigger).
- **Retune with BO RUN2** (task #45, currently pending) using the 11-feature vector. RUN2 starts after RUN1 weights land and validates its win against RUN1.
- **DEFER F19** unless v0.3 is clean by T-24h. Endgame tablebase handles the same signal geometrically.

---

## §5 — Additional v0.3 levers (non-feature)

### 5.1 Endgame extend — the "tablebase" that isn't (TABLEBASE §B)

TABLEBASE_FEASIBILITY §B concluded that an offline tablebase is dominated by `time_mgr.classify` assigning a critical multiplier to the last 5–8 turns, letting the existing α-β reach depth 8–10 on the reduced subtree.

**Implementation (T-30d):**
- In `time_mgr.classify()`, add a branch: if `turns_left ≤ 5 AND turns_left ≥ 2`, return `"critical"` AND raise the multiplier cap for these turns from 2.5× to **3.5×**. The branch factor drops (fewer primable cells remain), so depth gain per second is steeper in endgame.
- Concrete: at turn 35 with 5 turns left and 40 s remaining, current classify yields ~ 8 s budget (1.6× × base_5s); with endgame branch it yields 8 s × (3.5/2.5) ≈ 11 s.
- Risk: TIMEOUT. Mitigation: preserve `time_left() - 0.5` hard cap (BOT §2.e) — multiplier doesn't override the hard stop.

**Expected ELO Δ:** +10 to +20. Endgame moves are the most point-sensitive (one missed k=5 roll = 10 pts). Deeper search there is high-ROI.

**Risk:** LOW. This is a 10-line change in `time_mgr.py` behind an existing switch point.

### 5.2 Depth via "do now" + make/unmake (T-20g + T-30c)

Already covered by SEARCH_PROFILE. Recapping for completeness:

- **T-20g (in flight):** SEARCH_PROFILE items #1 + #2a + #4 bullet 1. +0.6–0.85 ply. LOW/MEDIUM risk.
- **T-30c (new, v0.3):** SEARCH_PROFILE item #3 (make/unmake) + item #5 (incremental Zobrist). +0.65 ply. HIGH risk — requires bytewise property test.

Property test spec (T-30c):
```
for each move m in get_valid_moves(exclude_search=False):
    before = board.clone()  # masks + workers + points + turn_count + side
    undo = board.make_move(m)
    # ... test some operation on the mutated board ...
    board.unmake_move(undo, m)
    assert board == before  # bytewise
```
Covers all 4 move types (PLAIN, PRIME, CARPET k∈[1,7], SEARCH — SEARCH never enters _alphabeta but we test for completeness).

**Cumulative depth target v0.3:** depth 11 at 2 s budget, depth 13 at 6 s budget (matches SEARCH_PROFILE §5 aggressive claim).

### 5.3 MCTS+HMM hybrid (task #48) — side-track specification

Per ALT_ARCH_MCTS §6.2. Implementation sketch:
- At the root, run α-β+HMM as current. If `belief_entropy > 4.5` AND `turns_left > 10`, ALSO run 200 MCTS iterations over the non-SEARCH root moves.
- Combine: if MCTS's most-visited root move has a different move-type than α-β's pick AND MCTS's mean reward > α-β's heuristic value by ≥ 1.0 pt, play MCTS's pick. Otherwise play α-β's pick.
- SEARCH decisions stay 100 % HMM-gated (our capture edge).

**v0.4 gate:** hybrid ≥ 55 % paired vs v0.3 over 50 matches under `limit_resources=True`. If gate passes, hybrid replaces v0.3 as the submission candidate. If it fails, hybrid stays as insurance (like FloorBot) and v0.3 is the submission.

---

## §6 — Contingency plan: BO RUN1 yields < +5 pp improvement

Team-lead's explicit ask. If RUN1's tuned weights fail the BOT §7 row 9 gate (< +30 ELO vs `w_init`) or produce flat improvement (< +5 pp paired win-rate), we ship `w_init`. But weight-tuning is not done — the contingency is:

### 6.1 RUN2: different objective (already planned — task #45)

BO RUN2 runs with a **different objective**: RattleBot-vs-RattleBot paired self-play instead of RattleBot-vs-FloorBot. This changes the fitness landscape:
- RUN1 optimizes "beat a reactive/greedy opponent" — FloorBot has no HMM, no depth, no search.
- RUN2 optimizes "beat a strong opponent that thinks like you" — better reflects Carrie-tier opposition.
- Risk of overfitting to self-play exists (Goodhart); mitigate by cross-validating RUN2 winners vs Yolanda, FloorBot, FakeAlbert, FakeCarrie.

**Compute cost:** same as RUN1, ~ 5 h parallelized. Starts immediately after RUN1 lands.

### 6.2 RUN3 (new, only if RUN1 AND RUN2 both fail): narrower search over high-impact dims

If RUN1 and RUN2 both fail to beat `w_init` by +30 ELO, the 9-dim BO surface is too noisy OR the bounds are too wide. Narrow:
- Fix F1, F3, F4 at `w_init` (these are known-good; they encode the rules).
- Tune ONLY F5 (cell-potential coefficient), F7 (opp cell-potential), F11/F12 (belief terms), F8/F13 — the 6 dims where signal is strongest.
- 15 trials × 30 pairs × ~30 s/match ≈ 4 h parallelized.

### 6.3 Non-tuning plan B

If ALL three BO runs fail, we have a hard signal: **weight-tuning is not the lever**. Pivot to:
- F17 + F18 feature additions (§4) with hand-tuned weights, evaluated against FakeCarrie (plausible +10–25 ELO).
- Make/unmake (T-30c) for +0.6 ply (+30–50 ELO).
- Endgame extend (T-30d) for +10–20 ELO.
- Hybrid MCTS bolt-on (task #48) as the speculative shot for the ceiling.
- Result: v0.3 submitted with `w_init` weights + new features + depth gains. Target FakeCarrie win-rate: 40–50 % (below "past Carrie gate" but above the 33 % baseline).

### 6.4 Do NOT give up

BO signal is ONE axis. The plan's center-estimate +210 ELO breakdown above does not depend on any single BO run landing. Depth (cheap) + features (cheap) + endgame extend (cheap) alone give +80 to +130 ELO, enough to push FakeCarrie from 33 % toward 45–50 %. That's not 60 %, but it's a real improvement and combined with tuning runs 2 + 3 we still have ceiling.

---

## §7 — Tournament-time budget audit (T-30a, new in v0.3)

Team-lead's explicit ask (b). Current local runs use `play_time = 360` (local, `limit_resources=False`). Real tournament is 240 s (`limit_resources=True`). Verify v0.2 survives.

**T-30a spec:**
- Run 20 paired matches of RattleBot_v0.2 vs RattleBot_v0.2 under `limit_resources=True` (WSL required on Windows per SANDBOX_SIM.md).
- Measure: mean depth achieved, max per-turn wall-time, number of TIMEOUTs, number of INVALID_TURN / CODE_CRASH.
- Pass: 0 TIMEOUTs, 0 CODE_CRASH, mean depth ≥ 5.0, max per-turn ≤ 6.5 s.
- Fail: if any TIMEOUTs → flip `time_mgr` to flat 5.5 s + 0.5 s reserve per BOT §7 row 14. If mean depth < 5.0 → investigate whether `forecast_move` allocations are 2× slower under seccomp (possible; seccomp adds a tiny syscall cost but fork overhead is the concern).
- Also verify: `agent.py` `__init__` completes in ≤ 8 s (tournament init_timeout = 10 s; T-30a adds a 2 s safety margin).

**Owner:** dev-integrator or tester-local (whoever has WSL).
**Hours:** 1.5 h (mostly WSL setup if not already done + 30-match runtime).
**Blocker for v0.3 ship:** YES — v0.3 cannot be uploaded live until T-30a passes.

---

## §8 — v0.3 exit gate (supersedes D-009 where numerically stricter)

Promotion to live submission on bytefight.org requires ALL of:

1. **Paired local vs v0.2** (regression check): ≥ 55 % over 100 paired matches under `limit_resources=True`. Wilson 95 % lower bound ≥ +5 pp.
2. **Paired local vs FloorBot:** ≥ 70 % over 100 paired matches. Stricter than D-009's 65 %/100 because v0.3 stacks depth + features on top of v0.2; we should be clearly dominant.
3. **Paired vs FakeCarrie (proxy):** ≥ 50 % over 30 pairs. This is the Carrie gap metric — 50 % on proxy is the "probably past the gate" threshold. Lower would not be a disaster but signals the 90 % threshold is at risk.
4. **Crash gate:** 0 INVALID_TURN / TIMEOUT / CODE_CRASH across ≥ 200 matches (unchanged from D-009 condition 2).
5. **T-LIVE-1 v0.3 live scrimmage:** ≥ 3 wins of 5 vs George AND ≥ 1 non-loss of 3 vs Albert. Unchanged from D-009.
6. **T-30a sandbox audit:** PASS per §7 above.
7. **AUDIT_V03.md:** per D-009 condition 4. Auditor enumerates: T-HMM-1/2, T-SRCH-1/2/3/4, T-HEUR-1/2 all PASS; new T-HEUR-5 (F17+F18 correctness unit tests) PASS; zero OPEN severity-Critical; make/unmake property test PASS; `emergency_fallback` try/except verified.

If any condition fails, hold v0.3 and ship v0.2 as the fallback (v0.2 is itself above the gate for George/Albert per §1.1 results).

---

## §9 — Sequencing by ELO-per-hour (team-lead's ask f)

Deadline is T-50 h. Ordered by `ELO_Δ / hour`:

| Order | Task | ELO Δ | Hours | ELO/h | Owner |
|-------|------|-------|-------|-------|-------|
| **1** | T-20g "do now" bundle (SEARCH_PROFILE items 1 + 4 bullet 1 + 2a) | +40–60 | 2 | **~25** | dev-search (in flight as task #46) |
| **2** | T-30a tournament-clock sandbox audit | +0 (guard) / −∞ if TIMEOUT | 1.5 | — (blocker) | dev-integrator |
| **3** | BO RUN1 weights adoption IF gate passes | +30–80 | 0 (already running; 5 h wall) | ∞ | dev-heuristic |
| **4** | T-30d endgame extend (time_mgr.classify branch) | +10–20 | 0.5 | **~30** | dev-integrator |
| **5** | T-30b F17 priming-lockout + F18 opp-belief-proxy | +15–45 | 4 | ~7.5 | dev-heuristic |
| **6** | T-30c make/unmake + incremental Zobrist (SEARCH_PROFILE 3+5) | +40–70 | 6 | ~9 | dev-search |
| **7** | BO RUN2 (self-play objective) — blocks on RUN1 done | +10–30 (if RUN1 <+30) | 0 (5 h wall) | — | dev-heuristic |
| 8 | Task #48 hybrid bolt-on (v0.4 candidate, side-track) | +0–50 cond. | 8–12 | ~1–5 | alt-arch-mcts |
| 9 | F19 rolls_remaining (stretch) | +3–10 | 1.5 | ~5 | dev-heuristic |
| 10 | Opening book (DEFERRED per TABLEBASE §A.6) | +10–20 | 6–14 | ~1 | NOT SCHEDULED |

**Recommendation:** run items 1–6 in parallel where possible, serialized where dependent:
- Wave 1 (now): items 1 (in flight), 2, 3 (in flight). No new agent spawns needed beyond dev-integrator for item 2.
- Wave 2 (after Wave 1): items 4, 5, 6 can all run in parallel (different files) — 6 is the long pole at 6 h.
- Wave 3: item 7 after RUN1 lands AND either adopts RUN1 or triggers RUN2.
- Side-track: item 8 runs independently, staffed by alt-arch-mcts. Not on critical path.

**Cumulative v0.3 critical-path hours:** 1.5 (T-30a) + 0 (wait for BO RUN1) + 6 (make/unmake, T-30c) + 1 (gate gauntlet) ≈ **8.5–10 h** with the other tasks in parallel. Leaves ~ 40 h for live scrimmage, v0.4 polish, and final submission activation.

---

## §10 — What v0.4 / v0.5 look like (preview)

Compressed because deadline pressure; not detailed.

### v0.4 (target T-20h, ≈ 30 h from now)
- Adopt winning tuning weights (RUN1 or RUN2 or hand-tuned `w_init` + F17/F18).
- If hybrid (task #48) passes its gate, promote hybrid as v0.4 submission candidate.
- Second live scrimmage wave: ≥ 10 live matches across {George, Albert, Carrie} to unblock dev-opponent-model per D-010 precondition.
- Goal: beat Albert ≥ 55 % live, beat Carrie ≥ 50 % live.

### v0.5 (target T-8h, final)
- Opponent-specific exploit track (T-24 if live scrimmages ≥ 10): implement `carrie_greedy` min-node estimator. Per CARRIE_DECONSTRUCTION H1–H8, the minimal reading is Σ P(c) / (1 + d) with modest coefficients; this is easy to ape inside the `opp_model.get_model("carrie_greedy")` stub.
- Optional MCTS+HMM hybrid if §5.3 passed gate.
- Final submission zip: `RattleBot_v0.5_carrie_killer.zip` with weights.json committed, 9/11-feature heuristic, make/unmake search, endgame extend.
- T-6 h activation + orchestrator confirmation per BOT §10 T-27.

### The "we didn't reach v0.4" path
If dev slips and v0.3 is the final submission at T-6 h, we ship v0.3 (pipeline expected ELO puts us in the 75–85 % band). FloorBot remains as fallback at ≥ 70 %. Worst case: we score in the Albert bracket. Reasonable worst-case grade: 80 %.

---

## §11 — Risk register delta for v0.3

New risks beyond `BOT_STRATEGY_V02_ADDENDUM.md §6`:

| ID | Risk | Mitigation | Owner |
|----|------|-----------|-------|
| R-V03-MAKEUNMAKE-01 | `make_move / unmake_move` has off-by-one bug on CARPET roll_length, corrupts board mid-tree silently | Property test in `tests/test_make_unmake.py`: for each of 4 move types × 4 directions × 7 roll lengths, `apply → unmake → assert bytewise equality`. Ships BEFORE integration. | dev-search |
| R-V03-F17-OVERSHOOT | F17 penalty magnitude is too large, bot under-primes globally (never lines up a k=5+ roll) | BO RUN2 tunes; monitor mean primed-popcount per game, gate at ≥ 5 on mid-game. If drops below 3, reduce w17 magnitude. | dev-heuristic |
| R-V03-ENDGAME-TIMEOUT | Endgame extend multiplier 3.5× trips TIMEOUT on a critical turn | `time_left() - 0.5` hard cap (unchanged BOT §2.e) overrides multiplier; unit test: `test_time_mgr_endgame_cap_respects_hard_stop`. | dev-integrator |
| R-V03-HYBRID-SANDBOX | MCTS hybrid has undetected `limit_resources=True` issue (seccomp on the numpy RNG path?) | T-30a audit run includes hybrid variant if it ships; fall back to non-hybrid if sandbox fails. | dev-integrator, alt-arch-mcts |
| R-V03-BO-OVERFIT | BO RUN1 overfits to FloorBot; wins on FloorBot paired but loses on FakeCarrie | Per v0.3 gate condition 3 (FakeCarrie ≥ 50 %), RUN1 weights rejected if they regress on FakeCarrie proxy. | dev-heuristic |
| R-V03-TIME-COMPRESS | T-50h remaining, v0.3 tasks slip; v0.4/v0.5 compressed to < 10 h total | §10 "didn't reach v0.4" path spec'd; FloorBot fallback stays armed; v0.3 is a graceful floor at ~80 % | orchestrator |

---

## §12 — Work breakdown for orchestrator

New task IDs proposed. Orchestrator assigns real IDs; ordering reflects ELO/h ranking.

- **T-30a (new) — dev-integrator: tournament-clock sandbox audit.** 1.5 h. BLOCKER for v0.3 ship. Runs 20 paired v0.2-vs-v0.2 matches under `limit_resources=True` + reports mean-depth, TIMEOUTs, max-per-turn. Writes `docs/tests/SANDBOX_AUDIT_V02.md`.
- **T-30b (new) — dev-heuristic: F17 `priming_lockout_penalty` + F18 `opp_belief_proxy`.** 4 h. Adds 2 features, updates `N_FEATURES=11`, writes unit tests T-HEUR-5-a (F17 dead-prime cases) and T-HEUR-5-b (F18 post-capture reset), updates `w_init` to 11 slots. Then invokes BO RUN2 queue.
- **T-30c (new) — dev-search: SEARCH_PROFILE items #3 + #5 (make/unmake + incremental Zobrist).** 6 h. Includes property test `tests/test_make_unmake.py` that must pass BEFORE integration merge. Expected +0.65 ply.
- **T-30d (new) — dev-integrator: endgame extend — `time_mgr.classify()` branch for turns_left ≤ 5.** 0.5 h. Unit test + 10-match smoke. Multiplier cap raised 2.5× → 3.5× but `time_left - 0.5` hard cap preserved.
- **T-45 (already pending — promote) — dev-heuristic: BO RUN2 self-play objective.** Blocks on RUN1 gate. If RUN1 < +30 ELO, RUN2 starts. If RUN2 < +20 ELO vs `w_init`, fallback to hand-tuned + F17/F18 only.
- **T-48 (already pending — keep pending) — alt-arch-mcts or dev-search-2: hybrid MCTS+HMM bolt-on.** Side-track. NOT on v0.3 critical path. Gate: ≥ 55 % paired vs v0.3 for v0.4 promotion.
- **T-30e (new) — tester-local: v0.3 gate gauntlet.** 1 h. 100 paired v0.3 vs v0.2 + 100 paired v0.3 vs FloorBot + 30 pairs vs FakeCarrie + 20 pairs vs FakeAlbert. Writes `docs/tests/RESULTS_V03.md`. BLOCKER for v0.3 live promotion.
- **T-30f (new) — auditor: write `docs/audit/AUDIT_V03.md`.** 1.5 h. Per v0.3 gate condition 7 above. Enumerates all tests + the new property test. Auditor signs off.
- **T-30g (new) — tester-live: v0.3 live upload + scrimmage.** 1 h + scrimmage wait time. 5 vs George + 3 vs Albert. Writes `docs/tests/ELO_LEDGER.md` entry.
- **T-30h (new, conditional) — dev-integrator: promote v0.3 to live submission.** 15 min. IFF all gate conditions met. Updates SUBMISSION_CANDIDATES.md; orchestrator confirms.

**Parallelization:** T-30a and T-30b can run in parallel with T-30c. T-30d can run in parallel with T-30b/c. T-30e after all four land. T-30f can begin reading docs after T-30e finishes its gauntlet.

---

## §13 — Commitments summary

If this plan is ratified:

- **Agent folder remains `3600-agents/RattleBot/`**. No new agent directory for v0.3 (it's an iteration of RattleBot).
- **Feature count: 9 → 11** (add F17, F18). `N_FEATURES = 11` in `heuristic.py`.
- **Depth target v0.3:** depth 11 at 2 s, 13 at 6 s (pure-Python ceiling per SEARCH_PROFILE).
- **BO:** up to 3 runs (RUN1 in flight, RUN2 queued, RUN3 conditional). Winner validates against FakeCarrie proxy before adoption.
- **Live scrimmage budget:** v0.3 consumes 8 matches (5 George + 3 Albert). Total live budget ≤ 30 matches through deadline per CON §F-14.
- **Fallback hierarchy:**
  1. v0.3 submission at T-6h (target, P ≈ 0.7).
  2. v0.2 submission if v0.3 fails gate (P ≈ 0.25 that we fall back — still in Albert bracket).
  3. FloorBot as final fallback if v0.2 has a latent bug (P < 0.05; FloorBot is 100 % vs Yolanda, untested live).
- **NO new architectures beyond hybrid bolt-on.** No MCTS rewrite. No NN. No null-move. No beam. Binding per BOT §8.
- **Grade probability under this plan:**
  - P(≥ 70 %): 0.92 (slightly up from v0.2's 0.91 because v0.3 stacks on a working v0.2)
  - P(≥ 80 %): 0.62 (up from 0.55 — FakeAlbert proxy already crossed)
  - P(≥ 90 %): 0.32 (up from 0.25 — v0.3 stacks add +150–270 ELO if all levers land; hybrid is optional upside)

**Deltas vs v0.2 addendum §7 v0.3 preview:**
- v0.2 preview expected "+50 to +100 over v0.2 (mostly from make/unmake)". v0.3 plan is MORE ambitious: +150 to +270 because we have the new evidence showing SEARCH_PROFILE "do now" is cheaper than expected, BO RUN1 is running, and F17/F18 are cheap and targeted.
- v0.2 preview deferred hybrid entirely. v0.3 plan keeps hybrid as a non-critical-path side bet — acknowledging the preliminary 2-1 MCTS signal without committing.

---

## §14 — End of addendum

**v0.3 summary:** 6 tracked tasks (T-30a through T-30f) with combined expected ELO Δ of **+150 to +270** layered on v0.2. Critical path ≈ 10 h; parallelized with concurrent BO runs and the hybrid side-track. Every task has a gate in §8 and a revert path. Contingency for BO failure documented in §6. FloorBot remains the floor safety net.

**Handoff:** after this doc lands, team-lead should:
1. Spawn dev-integrator for T-30a (sandbox audit) as a priority-1 blocker — needs to complete before ANY v0.3 live upload.
2. Confirm BO RUN1 is still in flight; queue RUN2 to auto-start on RUN1 exit.
3. Spawn dev-heuristic for T-30b (F17+F18); BLOCK T-45 (RUN2) until T-30b's 11-feature code lands.
4. Spawn dev-search for T-30c (make/unmake) with property-test-first policy.
5. Spawn tester-local for T-30e, auditor for T-30f, tester-live for T-30g in Wave 3.

**Files produced/modified by v0.3:**
- `3600-agents/RattleBot/heuristic.py` (F17, F18; N_FEATURES=11; updated W_INIT)
- `3600-agents/RattleBot/time_mgr.py` (endgame extend branch in `classify`)
- `3600-agents/RattleBot/search.py` + `move_gen.py` + `zobrist.py` (make/unmake + incremental hash)
- `engine/game/board.py` (new: `make_move`, `unmake_move`, cache of `valid_search_moves`) — coordinate with game-analyst on any engine edits
- `3600-agents/RattleBot/types.py` (finalize Undo dataclass — v0.2 shipped as stub)
- `3600-agents/RattleBot/tests/test_make_unmake.py` (NEW property test)
- `3600-agents/RattleBot/tests/test_heuristic_f17_f18.py` (NEW)
- `3600-agents/RattleBot/weights.json` (updated by BO RUN2 if gate passes)
- `docs/tests/RESULTS_V03.md` (NEW — T-30e gate gauntlet)
- `docs/tests/SANDBOX_AUDIT_V02.md` (NEW — T-30a)
- `docs/audit/AUDIT_V03.md` (NEW — T-30f)
- `docs/tests/ELO_LEDGER.md` (updated — T-30g)
- `docs/plan/SUBMISSION_CANDIDATES.md` (updated — T-30h if promotion)

**End of BOT_STRATEGY_V03_ADDENDUM.**
