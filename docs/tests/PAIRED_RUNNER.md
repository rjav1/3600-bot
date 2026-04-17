# PAIRED_RUNNER — Paired-Match Batch Harness

**Location:** `tools/paired_runner.py`
**Doc version:** v1.0 (2026-04-16)
**Owner:** tester-local

## Why this exists

Per `docs/research/CONTRARIAN_SCOPE.md` §F-14 (and §B-3 / §C-1 for the
CI math), unpaired 50-match runs on this game have a 95% CI of roughly
±14pp on win-rate. That is nowhere near tight enough to detect the
5pp version-over-version improvements `docs/plan/BOT_STRATEGY.md` §5
expects between RattleBot v0.1 → v0.5. Paired-match evaluation —
**same seeded transition matrix, same spawn, same corner blockers,
same rat walk; sides A/B swapped between the two matches of a pair** —
cancels board noise and cuts effective variance by roughly 3×. With
N ≥ 100 pairs and a binomial sign test, we can reliably distinguish
a 5pp improvement at p < 0.05.

> "(a) Use paired-match design (same T, same spawns, same seeds — both
> bots see identical boards; only the agent differs). Paired variance
> is much lower." — CONTRARIAN_SCOPE §B-3, endorsed by BOT_STRATEGY v1.1 §6.1.

This tool is the single statistical gate for every future RattleBot
bump: `v0.X` is only promoted over `v0.(X-1)` if it clears the paired
gate at the thresholds in BOT_STRATEGY.md §6.1.

## Usage

Run from the repository root. No bot code is modified by this tool.

```bash
# Smoke test — expect FloorBot >= 95% of 20 matches.
python3 tools/paired_runner.py --agents FloorBot Yolanda --n 10 --seed 0

# Full promotion gate — RattleBot v0.X vs v0.(X-1) at 100 pairs.
python3 tools/paired_runner.py --agents RattleBot FloorBot --n 100 --seed 42 --quiet

# Parallel run (Linux; sequential fallback on Windows if spawn fails).
python3 tools/paired_runner.py --agents RattleBot FloorBot --n 200 --seed 1 --parallel 4 --quiet

# Opt out of limit_resources (required on Windows; see "Known limitations").
python3 tools/paired_runner.py --agents RattleBot FloorBot --n 20 --seed 0 --no-limit-resources
```

### Flags

| Flag | Default | Meaning |
|------|---------|---------|
| `--agents A B` | (required) | Two agent directory names under `3600-agents/`. |
| `--n INT` | (required) | Number of PAIRS; actual matches = `2 * N`. |
| `--seed INT` | `0` | Root seed. Pair `i` uses `seed + i`. |
| `--limit-resources` / `--no-limit-resources` | `--limit-resources` | Enable/disable the engine's `limit_resources=True` path. |
| `--tournament-budget` | off | **Linux/WSL only.** Enforce tournament-accurate `play_time=240s` + `init_timeout=10s` without requiring the Linux-only seccomp/setrlimit/UID-drop stack. Monkey-patches `apply_seccomp` / `drop_priveliges` / `resource.setrlimit` to no-ops, then calls `play_game(limit_resources=True)` so the engine picks the tournament clock values. Propagates only under fork-multiprocessing; refuses to run on Windows (spawn doesn't inherit the parent's patches → every child would crash on `import resource` and produce silent FAILED_INIT TIEs). Use for the T-30a time-audit gate — it measures clock behavior (TIMEOUT / depth / time-remaining), not syscall isolation. |
| `--parallel INT` | `1` | Worker processes, capped to 8. |
| `--out PATH` | `3600-agents/matches/batch_TIMESTAMP/` | Output directory. |
| `--quiet` | off | Redirect per-match engine stdout to `/dev/null` inside workers. |

### Outputs

Inside `--out`:

```
summary.json                  # aggregate stats + CIs + sign-test p-value
matches/
  pair_0000_m1_<A>_vs_<B>.json   # full per-match record including history
  pair_0000_m2_<B>_vs_<A>.json   # swapped-sides half of pair 0
  pair_0001_m1_<A>_vs_<B>.json
  ...
```

Each `pair_XXXX_m{1,2}_*.json` contains the usual engine history blob
(from `engine/board_utils.py::get_history_json` — identical format to
`run_local_agents.py` output) plus the agent identities, winner,
win-reason, score, rat-capture counts, elapsed time, and per-move
timing derived from the `a_time_left`/`b_time_left` deltas.

`summary.json` groups the numbers you actually care about:

- `matches.{wins_a, wins_b, ties, winrate_a, winrate_a_wilson95}` —
  per-match totals + Wilson 95% CI.
- `pairs.{pair_wins_a, pair_wins_b, pair_ties, paired_sign_test_p,
  decisive_pairs}` — pair-level sweeps + two-sided binomial sign test
  over the decisive pairs. This is the statistic BOT_STRATEGY.md §6.1
  references.
- `errors.{crashes_*, timeouts_*, invalid_*}` — per-agent failure
  counts (attributed to the loser of a decisive match).
- `score.mean_score_diff_a_minus_b` — mean (A − B) point differential.
- `rat.{captures_a, captures_b, captures_per_match_*}` — bonus
  instrumentation per D-011 item 13 and CON-STRAT §A.
- `timing.{a_max_move_s, b_max_move_s}` — largest single-move wall
  clock observed across the batch (derived from the history timeseries).

## Sample output (smoke test, 2026-04-16)

```
python3 tools/paired_runner.py --agents FloorBot Yolanda --n 10 --seed 0 --no-limit-resources --quiet
```

Produced `3600-agents/matches/batch_20260416_211828/summary.json`:

```
A = FloorBot   B = Yolanda
pairs = 10   matches = 20   seed = 0
limit_resources = False   parallel = 1
wall = 68.5s

Matches:  A wins   20   B wins    0   ties    0   A winrate 1.000 (Wilson95 0.839–1.000)
Pairs:    A sweeps 10   B sweeps    0   split    0   sign-test p = 0.001953
Errors:   A crash 0  timeout 0  invalid 0   |   B crash 0  timeout 0  invalid 0
Score:    mean(A − B) = +24.55
Rat:      A caught 0 (0.00/match)   B caught 0 (0.00/match)
Timing:   A max per-move 0.00s   B max per-move 0.00s
```

Passes the smoke criterion (FloorBot wins ≥ 95% of 20 matches) with
room to spare. Paired sign-test p = 0.00195 (2 × 0.5¹⁰) — well below
the 0.05 promotion threshold. FloorBot's max per-move wall time is
0.46 ms, three orders of magnitude under budget.

Reproducibility verified: pair 0's match 1 and match 2 have identical
`spawn_a = [3, 5]` and identical rat trajectories for the first several
turns; pair 1 uses a different seed and picks a different spawn. Rat
captures are 0 in this batch because neither bot issues SEARCH moves
yet; that figure will become meaningful once RattleBot lands.

## Promotion protocol (for future dev agents)

BOT_STRATEGY.md v1.1 §6.1 defines the RattleBot promotion gate. The
paired runner is how that gate is measured. In plain language:

> Any RattleBot v0.X improvement must beat v0.(X-1) at paired sign-test
> p < 0.05 on N ≥ 100 pairs under `--limit-resources` before it is
> allowed to supersede the current candidate. "Beat" means `pair_wins_a
> > pair_wins_b` with statistical significance, not just a raw win-rate
> bump.

Concrete numeric gates, copied from BOT_STRATEGY.md §6.1:

| Gate | Requirement |
|------|-------------|
| Fast-track | `wins_a / n_matches ≥ 0.65` over 100 pairs (200 matches). |
| Standard   | `wins_a / n_matches ≥ 0.58` over 200 pairs (400 matches). |
| Crash-free | `crashes_a + timeouts_a + invalid_a == 0` across the full run. |

If **either** fast-track or standard passes AND the crash-free gate
passes, the candidate is promotion-eligible pending audit sign-off.

## Known limitations

1. **`--limit-resources` is Linux-only.** The engine's enforcement path
   uses `resource.setrlimit`, `seccomp`, and `prctl` — none exist on
   Windows. The runner detects Windows and transparently falls back to
   `--no-limit-resources`, emitting a warning. Under the fallback the
   engine gives each agent `play_time = 360s` instead of `240s` and
   `init_timeout = 20s` instead of `10s`. **Interpretation:** local
   Windows benchmarks will be optimistic on time-critical bots. For
   the pre-submission promotion gate, run on Linux (WSL is acceptable)
   with `--limit-resources`.

2. **Agent stochasticity is not reproducible across pairs.** Agent
   subprocesses have independent `random` state, so two matches in a
   pair can make different move choices even on identical boards. That
   is the intended design of paired-match testing: *board noise* is
   cancelled (same T, spawn, rat walk), *agent noise* is not, because
   we want to measure agent strength, not agent determinism.

3. **Parallel mode on Windows can be flaky.** `multiprocessing.spawn`
   re-imports this module in each worker, which in turn imports
   `engine/gameplay.py` and `jax`. If `jax` compilation collides or
   memory pressure spikes, the pool silently drops. The runner
   handles this by catching the pool exception and falling back to
   sequential execution for the remaining pairs. Check `summary.json`
   `errored_pairs` if anything went wrong; the runner never hard-kills
   user processes.

4. **Rat-capture attribution is index-based.** We attribute each
   captured rat to the player who moved on that turn, using the
   `turn_index % 2` convention. This is correct for normal play but
   would misattribute if we ever let the engine record partial turns.
   It matches the invariant in `engine/game/history.py::record_turn`.

5. **Per-move timing is engine-reported, not wall-clock.** We derive
   per-move times from the `a_time_left` / `b_time_left` deltas in the
   history. Those are the engine's own `timer` values from
   `run_timed_play`. Good enough for `T-TIME-1`/`T-TIME-2` gates; if
   you need sub-millisecond fidelity on a single agent call path,
   instrument inside the agent.

6. **Output directory is gitignored.** `3600-agents/matches/` is in
   `.gitignore` — commit the runner script and this doc only, never
   the per-match JSONs or `summary.json`.

## Example: checking RattleBot v0.1 against FloorBot

Once RattleBot v0.1 is wired (T-16), the first real use of this tool:

```bash
python3 tools/paired_runner.py \
    --agents RattleBot FloorBot \
    --n 100 --seed 42 \
    --parallel 4 --quiet
```

Inspect `summary.json`:

- If `pair_wins_a > pair_wins_b` and `paired_sign_test_p < 0.05` AND
  `winrate_a >= 0.65` AND zero errors on the A side → green-light for
  v0.1 → v0.2 promotion.
- If `winrate_a < 0.50` → v0.1 is no better than FloorBot and needs
  re-work before any v0.2 effort is spent.
- If `winrate_a ∈ [0.50, 0.65)` → re-run with `--n 200` for the standard
  gate (`winrate_a >= 0.58` over 200 pairs).

If any of `crashes_a`, `timeouts_a`, or `invalid_a` is non-zero,
promotion is **blocked** regardless of the win-rate. The auditor
signs off on this per BOT_STRATEGY.md §6.1 condition (4).
