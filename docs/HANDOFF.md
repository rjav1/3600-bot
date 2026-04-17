# HANDOFF — Fresh Agent Onboarding

**If you are a fresh agent (AI or human) picking this project up, read this file
first. It takes you from zero to competent in ~3 minutes of reading.**

---

## 0. Single paragraph summary

You are working on a competitive Python bot (`RattleBot`) for the **CS3600
Spring 2026 Carpet/Rat tournament** at bytefight.org. The tournament grades on
ELO vs three staff reference bots (George ≥70%, Albert ≥80%, Carrie ≥90%) plus
other student teams. **Deadline: 2026-04-19 23:59 local.** Whatever is "Current"
on the tournament site at that moment is what gets graded.

The current shipped submission is `RattleBot_v03_pureonly_20260417_1022.zip`
(valid, Current on bytefight). A Bayesian-optimization tuning run for the
19-feature heuristic weights was in flight but was stopped during team wind-down
(2026-04-17 21:11) — relaunching that BO run is the single highest-leverage next
action (see §6).

---

## 1. Read these files in this order (60-90 sec each)

1. **[../CLAUDE.md](../CLAUDE.md)** — full project brief. Game rules, engine
   API, grading tiers, submission constraints. Authoritative.
2. **[../README.md](../README.md)** — how to run matches, bytefight client,
   paired runner, BO tuning.
3. **This file** (HANDOFF.md).
4. **[STATE.md](STATE.md)** — rolling snapshot. Wall-of-text; skim for "Current
   phase" and the most recent paragraph.
5. **[plan/BOT_STRATEGY.md](plan/BOT_STRATEGY.md)** + all
   `plan/*_ADDENDUM*.md` — the canonical strategic plan chain (v1.1 → V03 →
   V03_UPDATE → V04). Most recent addendum (V04) reflects ship state.
6. **[audit/AUDIT_V03.md](audit/AUDIT_V03.md)** +
   **[audit/AUDIT_V04_CHECKLIST.md](audit/AUDIT_V04_CHECKLIST.md)** — known
   bugs, resolved issues, open flags.

---

## 2. Current state at wind-down (2026-04-17 21:11 local)

### What's shipped and working

- **RattleBot v0.3 pureonly** — α-β + HMM + 19-feature heuristic. Validated on
  bytefight. Depth 13.4 ply @ 2 s move budget.
- **Bytefight programmatic client** (`tools/bytefight_client.py`) — headless
  auto-refresh via Supabase refresh_token flow. CAPSOLVER wired for Turnstile.
  Upload + set-current + poll all verified live. Scrimmage-create verified
  (CAPSOLVER solves, payload accepted) but last attempt hit a rate-limit 429.
- **Sandbox simulator** (`tools/sandbox_sim.py` + WSL path) — can reproduce the
  tournament's Linux env locally for pre-upload validation.

### Tech debt / open loose ends

- **BO RUN1-v6 was killed mid-run** (dev-heuristic stopped at trial 0 of 40).
  No `weights_v03.json` was produced. **This is the single biggest lever left**
  — a full BO tune of the 19-dim weight vector is worth ~5-10 ELO.
- **HybridBot experiment inconclusive** — MCTS-rollout + HMM-gated-SEARCH
  alternative architecture. Paired N=20 run stopped at 14/40 matches, interim
  WR = 50.0%. Not shipped. Code is in `3600-agents/HybridBot/` for reference.
- **engine/gameplay.py T-40-INFRA step 2** — JAX→numpy swap to fix Windows
  spawn-pool deadlock. Commit pending.
- **F10 feature is LOCKED at option (b)** adjacency-only. Do NOT flip it back.
  Prior saga in `plan/BOT_STRATEGY_V04_ADDENDUM.md`.

---

## 3. Critical invariants (do not break)

- **`_USE_NUMBA = False` default in `3600-agents/RattleBot/heuristic.py`.**
  Numba JIT breaks the tournament sandbox. Opt in only for local benchmarks via
  `RATTLEBOT_NUMBA=1` env var. Any submission zip must be pure-Python.
- **19 features, W_INIT shape=19.** Any new feature invalidates the running BO
  and the currently-adopted W_INIT. Coordinate carefully.
- **Time budget is 240 s global, not per-move.** Tournament sandbox is 240 s;
  local default is 360 s for headroom. Audits must use 240 s to be
  grade-signal.
- **Invalid move = instant loss.** Every integration-level guard must
  fail-closed.
- **§F-14 scrimmage budget** (user directive): real bytefight scrimmages vs
  reference bots are the ONLY grade signal. Local proxies are approximate. Run
  scrimmages 24/7 while a valid Current submission exists and budget remains.

---

## 4. Bytefight credentials

- Account: **rjavid3@gatech.edu** (NOT `rahiljav@gmail.com`)
- Team: Team 15, UUID `81513423-e93e-4fe5-8a2f-cc0423ccb953`, join code `7F5TQ36E`
- Team URL: https://bytefight.org/compete/cs3600_sp2026/team

Auth is handled headlessly by `tools/bytefight_client.py` — Supabase
refresh_token in `tools/bytefight_session.json` (gitignored). One-time setup
requires `python tools/bytefight_client.py bootstrap-auth` from a logged-in
Chrome tab. CAPSOLVER key in `CAPSOLVER_KEY` env var unlocks upload + scrimmage
(Turnstile-gated).

---

## 5. Operational protocols (from prior team)

- **PING-FIRST for live-BO edits:** while `bo_pid.txt` exists and the BO PID is
  alive, do NOT Write/Edit `3600-agents/RattleBot/*.py` or `tools/bo_tune.py`,
  not even docstrings. Prior incidents killed 5 BO runs from mid-run
  contamination.
- **Commit author identity:** `rjav1` (user's GitHub handle).
- **Never push --force, never --amend published commits, never --no-verify.**
  If a pre-commit hook fails, fix it and create a NEW commit.
- **Commit messages:** conventional-commit style (`feat(RattleBot): ...`,
  `fix(tools): ...`, `docs(audit): ...`). Subject ≤72 chars.
- **Do not commit:** `.env`, `*.har`, `tools/scratch/*`, `weights_*.json` that
  are BO-in-progress snapshots, large binaries, `__pycache__`.

---

## 6. Highest-leverage next actions if you're resuming

1. **Relaunch BO RUN1-v7** — 19-dim sequential tuning, pure-Python workers,
   catastrophe-penalty objective. Output: `weights_v03.json`. Then
   `T-40-BO-ADOPT`: load the weights, run a 20-game paired sanity vs HEAD, and
   if ≥55% WR, ship a new submission zip. See `plan/BO_TUNING.md` +
   `plan/BO_V03_RUN2_SPEC.md`.
2. **Continuous scrimmage pipeline** — use the new `bytefight_client.py` to run
   scrimmages vs George/Albert/Carrie 24/7 through the deadline. The
   `bytefight_poll.py` daemon already logs results to `tests/LIVE_SCRIMMAGE_LOG.md`.
3. **Monitor + act on competitive intel** — other student teams are active.
   The poller surfaced losses vs Team 57's `Luca.zip` and Team 65's
   `alexBot_dual_dominator.zip` on 2026-04-17. Pull replays via
   `bytefight_client.py get-match` and route to a loss-analyst.

---

## 7. Where to find things

- **Strategy:** `docs/plan/BOT_STRATEGY.md` + addenda
- **Audits:** `docs/audit/AUDIT_V0*.md`
- **Live-test trip reports:** `docs/tests/LIVE_UPLOAD_*.md`,
  `BYTEFIGHT_CLIENT_SMOKE.md`, `LIVE_SCRIMMAGE_LOG.md`
- **Decision log:** `docs/DECISIONS.md`
- **Pipeline / team model:** `docs/PIPELINE.md`, `docs/TEAM_CHARTER.md`
- **Prior handoff docs:** `docs/state/HANDOFF_TESTER_LIVE.md`,
  `docs/state/HANDOFF_GIT_COMMITTER.md`
