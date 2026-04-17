# FAKE_OPPONENTS — local replicas of staff reference bots Albert & Carrie

**Owner:** fake-opponents
**Created:** 2026-04-17
**Task:** #41
**Status:** v0.1 shipped; smoke tests PASS.

## 1. Why

Grading thresholds are above George (70 %), Albert (80 %), Carrie (90 %).
Locally we can test only vs Yolanda (random) and FloorBot (reactive) —
neither is an α-β+HMM opponent. The scrimmage budget (CON §F-14) is
scarce. These two proxies close the gap: RattleBot iterations can run
paired matches against them to get rough-but-directional "are we near
the 80 % or 90 % gate" signal without burning live scrimmages.

**Hard disclaimer:** FakeAlbert is not Albert. FakeCarrie is not Carrie.
They are best-speculation replicas built from `assignment.pdf` §9 and
`docs/research/CARRIE_DECONSTRUCTION.md`. Signal from them is **directional
only** — strong wins imply we're probably past the gate; losses imply we
probably aren't. Never use them as the sole gate for a submission decision.

## 2. FakeAlbert

Per `assignment.pdf` §9: *"expectiminimax-based bot with a very simple
heuristic and a hidden markov model to track the rat."*

| Component | Choice |
|-----------|--------|
| Search    | α-β with iterative deepening, depth cap **3** (per task spec) |
| Rat track | Inline minimal HMM forward filter (64-cell belief), `p_0 = e_{(0,0)} · T^1000` |
| Heuristic | `v = 2·score_diff + 0.3·popcount(primed) + 0.2·popcount(carpet)` (3 features, very simple) |
| SEARCH    | Root-only, gated by `belief.max > 1/3 ∧ entropy < 0.75·ln 64`; compares EV to best non-SEARCH value |
| Move ordering | Static: big carpets first, then primes, plains, 1-carpets last |
| Time/move | ~400 ms target (deadline = `min(0.4, time_left − 0.1)`) |
| TT / Zobrist | **None** (task spec: "No Zobrist, no move-ordering sophistication") |
| Fallback  | FloorBot-style carpet/prime/plain + random-valid, wrapped in `try/except` |
| LOC       | ~300 (`agent.py` + `__init__.py`) |

Files: `3600-agents/FakeAlbert/__init__.py`, `3600-agents/FakeAlbert/agent.py`.

## 3. FakeCarrie

Per `assignment.pdf` §9: *"uses the same expectiminimax and HMM structure
as Albert, but uses a more advanced heuristic that takes into account
an estimate of the potential of each cell and its distance from the bot."*

Same scaffold as FakeAlbert (α-β d=3, HMM, root-SEARCH gate, fallback)
with a different heuristic:

```
v = 2 · score_diff + 0.5 · Φ(self) − 0.3 · Φ(opp)

Φ(worker) = Σ_c  P(c) / (1 + d_Manhattan(worker, c))

P(c) = best-roll-value reachable from cell c
     = max_{direction, k ∈ [1,7]} CARPET_POINTS_TABLE[k]
       such that k contiguous PRIMED cells extend from c in that direction
     ; 0 if c is BLOCKED or CARPET
```

This implements **hypothesis H1** from
`docs/research/CARRIE_DECONSTRUCTION.md §1` — "Σ-inverse-all-cells (classic)" —
which was the minimal-parameter match to §9's wording ("cell potential ×
distance from bot") with `f(d) = 1/(1+d)`.

Parameters (β=0.5, γ=0.3) chosen mid-range of the bounds in §1 of
`CARRIE_DECONSTRUCTION.md`. Not tuned. Could be refined if FakeCarrie
turns out too strong or too weak.

Files: `3600-agents/FakeCarrie/__init__.py`, `3600-agents/FakeCarrie/agent.py`.
LOC ~380 (under 400 target).

## 4. Smoke tests (2026-04-17)

Run via `tools/scratch/smoke_fake_opponents.py` (Windows, `limit_resources=False`).
Non-paired matches (side A each time); rough signal.

| Matchup | A-wins | B-wins | Ties | A-rate | Pass? |
|---------|--------|--------|------|--------|-------|
| FakeAlbert vs Yolanda         | 5 | 0 | 0 | **100 %** | ≥ 80 % ✅ |
| FakeCarrie vs Yolanda         | 5 | 0 | 0 | **100 %** | ≥ FakeAlbert ✅ |
| FakeCarrie vs FakeAlbert      | 3 | 2 | 0 | **60 %**  | Carrie > Albert ✅ |
| RattleBot v0.2 vs FakeAlbert  | 3 | 0 | 0 | **100 %** | strong +signal ✅ |
| RattleBot v0.2 vs FakeCarrie  | 1 | 2 | 0 | **33 %**  | still below 90 % gate ⚠️ |

No crashes, no invalid moves, no timeouts. All 21 matches completed a
full 40-turn game.

### Interpretation

- FakeAlbert/FakeCarrie both beat Yolanda 5-0 — expectiminimax even at
  depth 3 with a dumb heuristic crushes random; sanity check passes.
- FakeCarrie 60 % over FakeAlbert is a weak-but-present edge. n=5 is
  too small to be statistically separated (~40 % CI at 95 %), but the
  direction matches §9's ordering. Good enough calibration to use both.
- RattleBot v0.2 is 100 % vs FakeAlbert over 3 matches (implying we're
  clearly past the Albert tier in proxy terms) and 33 % vs FakeCarrie
  (implying we're probably **not** past the Carrie tier yet).
- Small n — run with the BO-tuned RattleBot + more matches once BO is done.

### Per-move wall time (FakeAlbert)

Average match length: ~6 s with only FakeAlbert as the expectiminimax
side → ~150 ms/move — well under the 500 ms target.

FakeCarrie: ~4.5 s/match similarly → ~110 ms/move (the Σ over 64 cells
costs less than expected because most cells have P(c)=0 early in the
game).

## 5. Usage

Both bots are standard agent-folder layouts. Any tool that takes an
agent name works:

```bash
# Single match (Windows: requires PYTHONIOENCODING=utf-8 due to engine
# display-printing emoji glyphs).
python engine/run_local_agents.py FakeAlbert Yolanda

# Batch via paired runner.
python tools/paired_runner.py \
    --agents RattleBot FakeCarrie --n 20 --seed 0 \
    --no-limit-resources --quiet --parallel 4
```

For paired-runner RattleBot-vs-FakeCarrie batches: budget ~7 min/match
(RattleBot is slow); n=20 pairs → ~2.3 h on 4 workers. Include these
as standard opponents for every RattleBot version bump going forward.

## 6. Honest limits / non-goals

- **Search depth is 3**, not whatever real Albert/Carrie use. If the
  real bots search to depth 5+ they'll be materially stronger.
- **Heuristic parameters are un-tuned guesses**. Carrie's β/γ could
  plausibly be anywhere in the bounds listed in
  `CARRIE_DECONSTRUCTION.md §1`. If RattleBot dominates FakeCarrie but
  then loses to real Carrie, the parameters or functional form are
  wrong — try H2 (exp-decay) or H6 (step-threshold) from that doc.
- **No transposition table, no killer moves, no history heuristic**,
  per task-spec "no Zobrist, no move-ordering sophistication". Real
  Albert/Carrie almost certainly have some of these.
- **No adaptive time management** — just a flat ~400 ms/move cap.
- **HMM is present but not exploited aggressively**: the SEARCH gate
  is a simple `max > 1/3` threshold, not the EV-calibrated root decision
  RattleBot uses.

These simplifications are deliberate (ship-fast, correctness-first) and
they match the spirit of "very simple heuristic" in §9. If the proxy
signal turns out misaligned with real scrimmage results, the right fix
is to add one feature at a time and re-run smoke tests.

## 7. Next steps

- [x] Smoke tests pass thresholds.
- [ ] Add `FakeAlbert` and `FakeCarrie` to the default opponent list
  in any v0.3 paired-runner preset.
- [ ] Re-run RattleBot-vs-FakeCarrie with n≥20 after BO weights land —
  the n=3 signal above is only directional.
- [ ] If real Albert scrimmage results diverge materially from the
  FakeAlbert signal, log the delta and bump heuristic complexity.
