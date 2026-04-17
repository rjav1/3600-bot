# 3600-bot — CS3600 Spring 2026 Tournament

Competitive Python bot for the **CS3600 Spring 2026 Carpet/Rat tournament** at
[bytefight.org/compete/cs3600_sp2026](https://bytefight.org/compete/cs3600_sp2026).

**Deadline:** 2026-04-19 23:59 local. Whatever is `Current` on bytefight.org at
that moment is what gets graded.

**Current submission:** `RattleBot_v03_pureonly_20260417_1022.zip` — valid,
Current, pure-Python, 19-feature α-β + HMM.

---

## Quick start

- **Human (you):** read this file, then [CLAUDE.md](CLAUDE.md) for the full
  project brief (game rules, API, grading tiers).
- **Fresh AI agent:** read [docs/HANDOFF.md](docs/HANDOFF.md) FIRST — it's the
  3-minute onboarding for picking up where the prior team left off.
- **Existing AI agent:** your rolling status is in [docs/STATE.md](docs/STATE.md)
  and the decision log is in [docs/DECISIONS.md](docs/DECISIONS.md).

---

## Repo map

| Path                       | Contents                                                                      |
|----------------------------|-------------------------------------------------------------------------------|
| `CLAUDE.md`                | Full project brief: game rules, engine API, grading tiers, submission rules. |
| `3600-agents/`             | Our bots (RattleBot = ship) + reference opponents (Yolanda, FakeCarrie, etc).|
| `engine/`                  | Tournament-simulator code: game loop, sandboxed subprocess, board helpers.   |
| `tools/`                   | `paired_runner.py`, `bo_tune.py`, `build_submission.py`, `bytefight_client.py`, `sandbox_sim.py`. |
| `docs/`                    | Strategy, audits, decisions, trip reports, handoffs. See [docs/INDEX.md](docs/INDEX.md). |
| `requirements.txt`         | Tournament lib set (jax, numpy, numba, etc). Tournament runs Python 3.12 on x86_64 Linux. |

---

## Running things locally

```bash
# Self-play match (Yolanda = reference random-mover agent)
python3 engine/run_local_agents.py RattleBot Yolanda

# Batch paired matches (use this to measure win-rate)
python3 tools/paired_runner.py --agents RattleBot Yolanda --n-pairs 20

# Build a tournament-safe submission zip (numba stripped, pure-Python only)
python3 tools/build_submission.py --agent RattleBot --strip-numba \
  --weights weights_v03.json

# Upload + scrimmage programmatically (headless, auto-refresh JWT)
python3 tools/bytefight_client.py list-submissions
python3 tools/bytefight_client.py upload <zip>   # needs CAPSOLVER_KEY env
python3 tools/bytefight_client.py scrimmage --opponent George
```

See [tools/BYTEFIGHT_CLIENT.md](tools/BYTEFIGHT_CLIENT.md) for the full client
reference (including the one-time `bootstrap-auth` step).

---

## Key facts

- **Architecture:** expectiminimax + α-β + Zobrist TT + iterative deepening +
  HMM rat-belief grid. Depth 13.4 at 2 s per-move budget (pure-Python).
- **Heuristic:** 19-feature linear eval. See
  [docs/plan/BOT_STRATEGY.md](docs/plan/BOT_STRATEGY.md) for the full feature list.
- **Submission safety:** `_USE_NUMBA=False` by default — numba JIT breaks the
  tournament sandbox. Opt in via `RATTLEBOT_NUMBA=1` for local benchmarks only.
- **Time budget:** 240 s tournament-global across 40 turns (~6 s/turn). See
  `3600-agents/RattleBot/time_mgr.py`.
- **Invalid move = loss.** Any integration-level guard must fail-closed.
