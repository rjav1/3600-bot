# V04_SHIP_PLAN — Authoritative critical path from BO completion to deadline lock

**Author:** plan-writer (spawned by team-lead for final-48h orchestration)
**Date:** 2026-04-17 (~T−50h to 2026-04-19 23:59 hard deadline)
**Scope:** Step-by-step plan for the remaining ~50 hours — from when BO RUN1-v7 exits and produces `weights_v03.json`, through post-BO patch adoption, bytefight upload + scrimmage validation, v0.5 iteration, and final "Current" submission lock-in.
**Status:** Planning doc only — does NOT execute anything. No edits to `3600-agents/RattleBot/*.py` or `tools/bo_tune.py` while BO PID 8868 is alive (verified alive at plan-writing time; see PING-FIRST in [HANDOFF.md §5](../HANDOFF.md)).

---

## §1 — Honest grade baseline (revised)

### 1.1 Current evidence

The prior grade anchor in [BOT_STRATEGY_V04_ADDENDUM.md §11](BOT_STRATEGY_V04_ADDENDUM.md) had:

| Threshold | Prior v0.4 target |
|-----------|-------------------|
| ≥ 70 % | 0.95 |
| ≥ 80 % | 0.68 |
| ≥ 90 % | 0.34 |

Those numbers were written before today's three new evidence streams landed. They must be revised down.

**Evidence A — reference-bot scrimmage results from the 21:11 batch (per [LIVE_SCRIMMAGE_LOG.md](../tests/LIVE_SCRIMMAGE_LOG.md) lines 71-73):**

| Opponent | Match UUID | Result |
|----------|-----------|--------|
| George   | `5e2d6a1f` | **LOST** (team_b_win, we are team A) |
| Albert   | `4fbbd274` | **LOST** (team_b_win) |
| Carrie   | `2e9fb89f` | **LOST** (team_b_win) |

All three reference bots beat us on 2026-04-17 21:11. We subsequently won 1 scrimmage vs George at 22:06 (`ed315682`, row 74). Sample is tiny but the 1/4 win rate vs George (the ≥70% floor bot) is a significant negative surprise from the prior anchor's 0.95 confidence at ≥70%.

**Evidence B — competitive-intel corpus finding from [COMPETITIVE_INTEL_APR17.md §1](../audit/COMPETITIVE_INTEL_APR17.md):**

Top 5 student teams sit at glicko 1938–2033. **Carrie sits at glicko 1910.2 — rank #6 — below all top-5 student teams.** Team 15 (us) is rank #112 at glicko 1371. The "pass ≥90%" tier is therefore not just "beat Carrie" in isolation — it's "be competitive with 5+ student teams that are already above Carrie." That's a meaningfully harder bar than the prior addendum anchored against.

**Evidence C — active-tournament matchmaking losses** ([LOSS_FORENSICS_APR17.md §1](../audit/LOSS_FORENSICS_APR17.md)):

We lost matchmaking games to `Luca.zip` (Team 57) and `alexBot_dual_dominator.zip` (Team 65) on 2026-04-17. Both clean score-exhaustion losses (no crash, no TLE). These are student agents that we are paired with at ~1500 ladder ELO — telling us our shipped build cannot cleanly beat mid-tier student teams.

### 1.2 Revised grade probabilities (current-state, pre-BO-adopt)

| Threshold | Prior anchor | **Revised (current shipped `RattleBot_v03_pureonly_20260417_1022.zip`)** | Evidence |
|-----------|--------------|-------|----------|
| ≥ 70 % | 0.95 | **0.78** | Lost 3/4 vs George in scrimmages + lost to two mid-tier student bots. George at glicko ~1144 is the 70% floor; if we can't reliably beat George our ≥70% is fragile. We are 0-3 in the 21:11 batch and 1-0 in the 22:06 solo. n=4 means wide error bars; current MLE WR vs George ≈ 25%. Still likely ≥70% due to scale-to-Albert/Carrie ladder structure, but not the 0.95 of the prior anchor. |
| ≥ 80 % | 0.68 | **0.42** | Albert scrimmage lost; George losses suggest sub-Albert strength. Top-5 student corpus shows 5+ teams well above Albert. Conservative. |
| ≥ 90 % | 0.34 | **0.12** | Top-5 student teams are at 1938-2033 glicko, all above Carrie. ≥90% grading requires being within striking distance of Carrie. The Carrie scrimmage loss and the top-5 intel taken together say current shipped build is probably sub-Carrie. BO adoption can lift this substantially. |

These are honest revisions from the evidence, not catastrophism. The baseline is weaker than we thought; the lift available from the post-BO patches is what closes the gap.

### 1.3 Post-BO-adopt-only target (projected, see §6 for detail)

With BO RUN1-v7 producing `weights_v03.json` and adoption passing the standard gate (§2 step (c)):

| Threshold | P after BO-adopt only |
|-----------|----------------------|
| ≥ 70 % | **0.90** |
| ≥ 80 % | **0.58** |
| ≥ 90 % | **0.22** |

Uplift vs 1.2 is the documented BO weight recovery of +30 to +80 ELO from [BOT_STRATEGY_V04_ADDENDUM.md §11](BOT_STRATEGY_V04_ADDENDUM.md). Full trajectory under all patches + dim-reduction + PVS is in §6.

---

## §2 — Post-BO-completion critical path (≤ 60 min wall-clock dev + ~4–8h scrimmage validation)

**Trigger:** `3600-agents/RattleBot/weights_v03.json` exists (BO RUN1-v7 wrote it) AND BO PID 8868 is dead (confirming clean exit).

**PING-FIRST clearance:** before any edit to `3600-agents/RattleBot/*.py` or `tools/bo_tune.py`, verify PID 8868 is NOT in `tasklist`. Re-read [HANDOFF.md §5](../HANDOFF.md).

### 2.1 Action sequence (strict order)

| # | Step | Owner | Est dev time | What it does |
|---|------|-------|-------------|--------------|
| a | **BO-ADOPT** — replace `W_INIT` in `3600-agents/RattleBot/heuristic.py` with `weights_v03.json` values; commit as `feat(RattleBot): adopt BO RUN1-v7 weights as W_INIT` | dev-heuristic | 20 min | Loads BO-optimized 19-dim weight vector into the default. Preserves sign-locks per [BO_TUNING.md](BO_TUNING.md). |
| b | **BO-ADOPT sanity 20-pair vs HEAD** — `python tools/paired_runner.py --agents RattleBot_preadopt RattleBot --n 10 --seed 0 --parallel 2 --out 3600-agents/matches/bo_adopt_sanity` (where `RattleBot_preadopt` is a temp fork with pre-adoption weights) | dev-heuristic | 5 min dev + 30-45 min runtime | Regression check: adopted weights should WR ≥ 50% vs pre-adopt. If < 45%, **ABORT** — BO degraded, fall back to `w_init`. Per [V04_ADDENDUM §5 adoption rule 3](BOT_STRATEGY_V04_ADDENDUM.md). |
| c | **Apply post-BO patches** (in this order):<br>1. **Exp C** (time_mgr phase re-skew) — already in `RattleBot_v2/time_mgr.py`; port to `RattleBot/time_mgr.py`<br>2. **R2** (endgame 3.5→2.5×, 220s cum ceiling) — already in `RattleBot_v2/time_mgr.py`; port<br>3. **C-1** (explicit k=1 gate confirmation per [RATTLEBOT_V2_PAIRED.md §1 P3](../tests/RATTLEBOT_V2_PAIRED.md) — NO-OP, already gated in `move_gen.py:122-123`)<br>4. **C-2** (early SEARCH lockout `turns_left > 30 & belief.max_mass < 0.35`) — not yet in v2, add to `agent.py` SEARCH gate per [COMPETITIVE_INTEL_APR17.md §5 C-2](../audit/COMPETITIVE_INTEL_APR17.md)<br>5. **Version bump** (per task #95/#96) — `RattleBot v0.2 → v0.3` in docstrings | dev-heuristic + dev-integrator | 30-45 min | Ports validated v2 patches plus the two outstanding ones (C-2, version). All edits to `3600-agents/RattleBot/` (NOT the v2 fork) after PID 8868 is dead. |
| d | **Paired 20-pair vs RattleBot_v2 (HEAD-frozen)** | tester-local | 30-60 min runtime | New `RattleBot` has BO weights + all patches; `RattleBot_v2` has the patches minus BO adoption. Delta isolates the BO contribution. Expect WR ≥ 55% (new > v2). If < 50%, investigate before shipping. |
| e | **Build submission zip** — `python tools/build_submission.py --strip-numba --weights weights_v03.json --name RattleBot_v04_boadopt_<timestamp>.zip` | dev-integrator | 5 min | Produces pure-Python zip. `--strip-numba` enforces `_USE_NUMBA=False` per [HANDOFF §3](../HANDOFF.md). Records SHA256 in `docs/plan/SUBMISSION_CANDIDATES.md`. |
| f | **Upload + set-current** — `python tools/bytefight_client.py upload <zip>` then `python tools/bytefight_client.py set-current <submission_uuid>` | tester-live | 5 min + 5-15 min server validation | Uploads + activates new submission. Watch for `submission_valid` event in poller. |
| g | **Scrimmage vs George/Albert/Carrie** — 1 each via `python tools/bytefight_client.py scrimmage --opponent George --count 1` (repeat for Albert, Carrie). Use the cadence from [SCRIMMAGE_LIMITS_INVESTIGATION §3](../audit/SCRIMMAGE_LIMITS_INVESTIGATION.md) — ≤5 concurrent. | tester-live | 15 min scheduling + 30-45 min wall-clock per scrimmage | Real ELO signal. Per §F-14 directive, this is the only grade proxy. |
| h | **Go/No-Go decision** — if ANY ref-bot loss, spawn loss-forensics re-audit BEFORE starting §3 v0.5 iteration. If all three WIN, proceed to §3. If 1-2 losses, proceed to §3 in parallel with forensics (don't block). | team-lead | — | Gate. Ref-bot losses need root-cause before we layer more changes. |

**Total post-BO critical-path wall time (best case):** ~4.5 hours (dev ~90 min + compute/scrimmage ~3h). **Deadline budget:** ≤ 6 hours with one round of investigation if step (h) flags a ref-bot loss.

### 2.2 Source references for the post-BO patches

- **Exp C + R2** — implemented in `3600-agents/RattleBot_v2/time_mgr.py`, documented in [RATTLEBOT_V2_PAIRED.md §1](../tests/RATTLEBOT_V2_PAIRED.md) (paired test *in flight* at time of writing — see §5 fallback if paired fails).
- **C-1 k=1 gate** — confirmed NO-OP in [RATTLEBOT_V2_PAIRED.md §1 P3](../tests/RATTLEBOT_V2_PAIRED.md). Patches in `move_gen.py:122-123` already enforce.
- **C-2 early SEARCH lockout** — specified in [COMPETITIVE_INTEL_APR17.md §5 C-2](../audit/COMPETITIVE_INTEL_APR17.md). Not yet applied. One of the two remaining pre-deadline patches.
- **BO-ADOPT** — procedure in [BO_TUNING.md](BO_TUNING.md); gate rule in [BOT_STRATEGY_V04_ADDENDUM.md §5](BOT_STRATEGY_V04_ADDENDUM.md).

---

## §3 — v0.5 iteration (post-BO-adopt hours 2 – 24 ≈ 2026-04-18 12:00 – 2026-04-19 00:00)

**Prerequisite:** §2 step (h) passed (no ref-bot losses, or losses root-caused and not blocking).

**Ship goal:** `RattleBot_v05_<timestamp>.zip` set as Current by 2026-04-18 18:00 (T−30h), leaving ~30h for scrimmage validation + rollback if it regresses.

### 3.1 Candidate changes (ranked by ELO/h)

All from [ARCH_CONTRARIAN_APR17.md §4](../audit/ARCH_CONTRARIAN_APR17.md). Descending ELO/h:

| # | Change | Expected ELO | Dev time | Risk | Source |
|---|--------|--------------|----------|------|--------|
| 1 | **PVS + aspiration windows** in `search.py` | +5 to +15 | 3h + 1h testing | Low (textbook α-β refactor; `test_alphabeta_matches_minimax` extensible) | [ARCH_CONTRARIAN §4 Exp B](../audit/ARCH_CONTRARIAN_APR17.md), task #92 |
| 2 | **Heuristic dim-reduction** — drop F3, F4, F18 (dead/non-discriminative) + merge F14/F15/F16 collinear kernels to one | +5 to +15 (+ bigger lift post-re-BO) | 3-5h + mandatory re-BO on 10-dim (4-6h wall) | Med — invalidates `weights_v03.json`, requires RUN1-v8. Only launch if we have ≥ 16h to deadline. | [ARCH_CONTRARIAN §4 Exp A](../audit/ARCH_CONTRARIAN_APR17.md), task #91 |
| 3 | **Tighter SEARCH gate to Bayesian EV directly** (remove 3-condition hand-gate) | +5 to +15 | 4h | Med — `best_value=0.0` edge case per V03-L-3 needs pre-fix | [ARCH_CONTRARIAN §4 Exp D](../audit/ARCH_CONTRARIAN_APR17.md) |

### 3.2 v0.5 sequencing (decision tree)

**Path A — Conservative (if §2 step d showed BO weights are fragile, or if ref-bot losses in 2g):**
- Do **only #1 (PVS)**. Low risk, compatible with current BO weights.
- Re-ship as `RattleBot_v05a_pvs_<timestamp>.zip`.
- Paired 20-game vs post-BO HEAD; ship if ≥ 55% WR.
- **Target complete by 2026-04-18 12:00 (T−36h).**

**Path B — Aggressive (if BO adoption passed cleanly with clear lift in 2d and ≥ 24h to deadline):**
- Do **#1 (PVS) + #2 (dim-reduction + BO RUN1-v8 on 10-dim)**.
- BO RUN1-v8 launches with 10-dim search space, ~4-6h wall. In parallel, PVS lands.
- When BO-v8 completes, re-adopt weights against new 10-dim vector.
- Re-ship as `RattleBot_v05b_reduced_<timestamp>.zip`.
- **Target complete by 2026-04-18 18:00 (T−30h). Strict — if not done by then, ABORT and revert to Path A output.**

**Path C (rejected pre-deadline):** #3 SEARCH gate revamp. Risk/time ratio too steep for final 24h.

### 3.3 Do NOT do in v0.5

From [BOT_STRATEGY_V04_ADDENDUM.md §12](BOT_STRATEGY_V04_ADDENDUM.md) and the task brief hard limits:

- **No new architectures** (MCTS hybrid, expectiminimax-over-rat, opening book — all deferred per v0.4 addendum).
- **No F21 belief_concentration_rate feature** — requires state-in-belief refactor, not pre-deadline.
- **No Cython AOT, no subinterpreters, no `_USE_NUMBA=True`** — per [HANDOFF §3](../HANDOFF.md) permanent invariants.
- **No F10 flips** — F10 is LOCKED at option (b) adjacency-only per [feedback_f10_locked.md memory](../../../.claude/projects/C--Users-rahil-downloads-3600-bot/memory/feedback_f10_locked.md).

---

## §4 — Final 12h lock-in (2026-04-19 12:00 onward, T−12h → T−0h)

**Goal:** whatever is Current on bytefight.org at 2026-04-19 23:59 is the v0.5-best we have, *validated* by bytefight scrimmages, not just local.

### 4.1 T−12h → T−6h (2026-04-19 12:00 – 18:00)

- **Hard stop on code changes.** No new edits to `RattleBot/*.py`, `RattleBot/weights_*.json`, or `time_mgr.py` after T−12h — ANY change opens a regression surface we can't re-validate in time.
- **Final submission matrix update.** `docs/plan/SUBMISSION_CANDIDATES.md` lists all candidate zips with SHA256 + local paired WR + bytefight scrimmage WR vs ref bots.
- **Final audit pass.** Spawn auditor with `AUDIT_V05.md` mandate:
  1. Read current `RattleBot/` code.
  2. Confirm `_USE_NUMBA = False` default.
  3. Confirm 19 features (or 10 if Path B) match the weights vector shape.
  4. Confirm 92/92 tests pass.
  5. Confirm `emergency_fallback` intact.
  6. Confirm sandbox-sim validation on WSL passes.
- **Burn remaining scrimmage slots** — at least 4 more vs each of George/Albert/Carrie at T−12 → T−6. Per [SCRIMMAGE_LIMITS_INVESTIGATION §3](../audit/SCRIMMAGE_LIMITS_INVESTIGATION.md), 10 min/scrimmage cadence = 36 scrimmages max in 6h, well within concurrency cap.

### 4.2 T−6h → T−1h (2026-04-19 18:00 – 22:59)

- **Freeze on "Current" set.** Once the best-performing zip has been identified from scrimmage data, `set-current` it. Do not change it again.
- **Verify the set-current succeeded** via `python tools/bytefight_client.py list-matches --size 10` — check that the most recent `validation` row is our intended submission.
- **Do a final SmokeBot-style validation scrimmage** — submit vs Yolanda to prove the zip runs cleanly in the sandbox. Per [LIVE_UPLOAD_006.md](../tests/LIVE_UPLOAD_006.md) protocol.

### 4.3 T−1h → T−0h (2026-04-19 22:59 – 23:59)

- **Active confirmation of Current via bytefight_client:**
  ```
  python tools/bytefight_client.py list-submissions --team 81513423-e93e-4fe5-8a2f-cc0423ccb953
  ```
  Inspect the row with `is_current=true`. Confirm its SHA256 matches `docs/plan/SUBMISSION_CANDIDATES.md` entry for the intended candidate.
- **Browser-level confirmation.** Log into https://bytefight.org/compete/cs3600_sp2026/team in a real browser. Confirm the "Current" submission UI matches the CLI output.
- **Do NOT upload or set-current in the last hour** unless fixing an outright failure. New uploads require validation runs that can take 5-15 min — not safe in the final hour.
- **At T−0, screenshot + log final state** to `docs/tests/FINAL_SUBMISSION_LOCK.md`. Team-lead declares ship.

### 4.4 What NOT to do in the final 12h

- No new scrimmage batches of > 1 per opponent at a time — keep queue shallow so no match hangs at deadline.
- No `--force` anything (force-push, force-upload). Per [HANDOFF §5](../HANDOFF.md).
- No last-minute heuristic "I bet tweaking F22 by 10% helps" — micro-tweaks with no paired validation are entropy.

---

## §5 — Fallback plan (failure handling)

### 5.1 If BO RUN1-v7 produces noise / degenerate weights (2a fails regression)

**Symptom:** Step (b) paired sanity shows BO-adopt WR < 45% vs pre-adopt.

**Response:** Revert `heuristic.py`'s `W_INIT` to the committed `w_init` values (commit SHA recorded in [BOT_STRATEGY_V04_ADDENDUM.md §5 adoption rule 3](BOT_STRATEGY_V04_ADDENDUM.md)). Ship v0.4 as patches-only (Exp C + R2 + C-2) without BO weights. Expected lift is +10 to +25 ELO vs current shipped. Per [V04 addendum §7](BOT_STRATEGY_V04_ADDENDUM.md) minimum-patch path.

### 5.2 If paired step (d) shows v0.4 regressed vs v2

**Symptom:** BO + all patches < v2 (patches-only).

**Response:** Ship `RattleBot_v2` as the v0.4 candidate instead. v2 already has Exp C + R2 (tested in [RATTLEBOT_V2_PAIRED.md](../tests/RATTLEBOT_V2_PAIRED.md), though results were pending at plan-write time). Apply C-2 and version bump, re-paired-test vs HEAD, ship if ≥ 50% WR.

### 5.3 If upload step (f) is rejected by bytefight

**Symptom:** `bytefight_client.py upload` returns a non-2xx OR the subsequent validation match ends `INVALID_TURN / CODE_CRASH / TIMEOUT`.

**Response:** Leave `RattleBot_v03_pureonly_20260417_1022.zip` as Current. Replay the failing validation locally via `tools/sandbox_sim.py` (WSL) to reproduce. Do NOT push another submission until the sandbox crash is root-caused. Sandbox failure mode precedent: numba triggered seccomp (per [LIVE_UPLOAD_006.md](../tests/LIVE_UPLOAD_006.md)). If we cannot root-cause within 4h, **PRE-BO-FALLBACK**: stay on `RattleBot_v03_pureonly_20260417_1022.zip` permanently. That zip is already Current, already validated, and won vs George today.

### 5.4 If step (h) shows ref-bot scrimmage losses after BO-adopt

**Symptom:** New v0.4 loses vs George AND/OR Albert AND/OR Carrie.

**Response:**
- **0 wins / 3 losses** — revert to `RattleBot_v03_pureonly_20260417_1022.zip`. Let loss-forensics analyze replay via `bytefight_client.py get_replay` (now implemented per [COMPETITIVE_INTEL_APR17.md tooling](../audit/COMPETITIVE_INTEL_APR17.md)).
- **1-2 wins, 1-2 losses** — proceed to §3 v0.5 iteration, but spawn parallel loss-forensics on the losses. Do NOT keep iterating while losses are unexplained.
- **3 wins / 0 losses** — proceed to §3 confidently.

### 5.5 Absolute pre-BO fallback (ship path if everything else fails)

**`RattleBot_v03_pureonly_20260417_1022.zip`** — this is the currently-Current zip, already validated on bytefight, already won a scrimmage vs George today (22:06 `ed315682`). If *every* post-BO change fails, this zip remains as the final submission. Per [HANDOFF §2](../HANDOFF.md): "If nothing else happens, v0.3-pureonly is the final submission, which per v0.3 addendum §13 should land us in the 80–90% band." (Note: §1.2 above revises this down; best honest estimate P(≥70%) ≈ 0.78, P(≥80%) ≈ 0.42 under this fallback.)

---

## §6 — Grade-probability milestones

Each milestone assumes the prior ones succeeded. Error bars reflect small-sample scrimmage uncertainty (n ≤ 10 per opponent per milestone).

| Milestone | When | P(≥70%) | P(≥80%) | P(≥90%) | Basis |
|-----------|------|---------|---------|---------|-------|
| **M0 — Current shipped** | today (T−50h) | 0.78 | 0.42 | 0.12 | §1.2 revision. Evidence: 3/4 losses to ref bots today; lost to Luca + alexBot; top-5 student corpus. |
| **M1 — Post BO-adopt only** | T−46h (§2 step e) | 0.90 | 0.58 | 0.22 | BO RUN1-v7 adoption lifts +30 to +80 ELO per [V04 addendum §11](BOT_STRATEGY_V04_ADDENDUM.md). Closes most of the George/Albert margin. Carrie gap narrows but doesn't close. |
| **M2 — Post all §2 patches (BO + Exp C + R2 + C-1 confirmed + C-2)** | T−44h (§2 step e for the full stack) | 0.93 | 0.64 | 0.28 | Exp C + R2 target the H-ALEX-1 time-overrun failure; C-2 saves ~1.5 pts/match per [COMPETITIVE_INTEL_APR17.md §5](../audit/COMPETITIVE_INTEL_APR17.md). Combined +10 to +25 ELO on top of BO. |
| **M3 — Post v0.5 Path A (PVS)** | T−36h (§3.2A) | 0.94 | 0.68 | 0.32 | PVS alone +5 to +15 ELO. Risk minimal. |
| **M4 — Post v0.5 Path B (PVS + dim-reduction + BO RUN1-v8)** | T−30h (§3.2B) | 0.95 | 0.72 | 0.38 | Full contrarian recommendation from [ARCH_CONTRARIAN §2](../audit/ARCH_CONTRARIAN_APR17.md). +15 to +30 additional ELO IF BO-v8 lands cleanly. Conditional on time. |
| **M5 — Lock-in (if Path B worked)** | T−0h | 0.95 | 0.72 | 0.38 | Same as M4; scrimmage validation eliminates downside tail. |

**Key observation:** **P(≥90%) tops out at ≈ 0.38** even with everything working. Reason: top-5 student corpus sits above Carrie; being in the ≥90% band means out-performing multiple student teams that are already north of Carrie's glicko. The architectural lift from PVS + dim-reduction isn't large enough to close that gap in the remaining time. **Pre-deadline ≥90% is a stretch goal, not a baseline expectation.** P(≥80%) = 0.72 is the realistic top-line.

### 6.1 Cumulative-risk adjustment

If we take the M4 path, the chain has 4 failure points (BO adoption, patches apply cleanly, PVS lands cleanly, BO-v8 lands cleanly), each ~0.9 conditional success. Joint: 0.66. The P values above already reflect this via the "post X" framing — they are P(grade ≥ X | we reach this milestone). If Path B doesn't reach the milestone, we fall back one row (M3 or M2 is the effective landing).

---

## §7 — Open loose ends the plan does NOT cover (flag for team-lead)

1. **BO RUN1-v7 current progress unknown.** `bo_stdout.log` shows launch but no completion. ETA from task brief ("3-4h remaining") is stale. Actual state at plan-write time: PID 8868 alive, trial 000 candidate emitted. May not complete in time for §2; if BO exceeds 12h additional wall-clock, team-lead should consider killing and adopting `w_init` per §5.1 fallback.
2. **Matchmaking queue** is separate from scrimmages and continues regardless of our actions. Matchmaking losses (Luca, alexBot) will keep accruing while we're inside the BO window. These losses cost ELO on the ladder but do NOT affect grade — grade is final ladder position at T=0, not history.
3. **Task #78 continuous scrimmage pipeline** is nominally "pending" in the task list but effectively manually driven at time of writing. Per [feedback_scrimmage_cadence.md memory](../../../.claude/projects/C--Users-rahil-downloads-3600-bot/memory/feedback_scrimmage_cadence.md), this MUST run 24/7 through the deadline. Should be kicked off immediately after §2 step (g) succeeds.
4. **HybridBot experiment** (14/40 matches at interim 50%) is suspended per [HANDOFF §2](../HANDOFF.md). Not on critical path. Stays suspended.

---

## §8 — End of plan

Team-lead owns §2 kickoff gate (when BO exits). Each section numbered for direct spawn reference (`spawn dev-heuristic to execute V04_SHIP_PLAN §2 steps a-c`). No further planning docs should be written — all deviations from this plan go in `docs/DECISIONS.md` as dated entries, not new strategy addenda.

**End of V04_SHIP_PLAN.**
