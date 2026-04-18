# V06_FAILURE_DIAGNOSIS_APR18 — Why v06 (F-2 revert to flat 1/3) went 0–1W / 22L

**Auditor:** `v06-loss-diagnostic` (ephemeral, 2026-04-18)
**Scope:** commit `26627b7` (v06-f2-revert-ship) + 3 v06 bytefight replays (Albert ×2, Carrie ×1) + ledger v06 results in `docs/tests/LIVE_SCRIMMAGE_LOG.md` + v03/v04 replay baselines in `docs/intel/replays/`.
**Mode:** read-only for code. No edits to `RattleBot/*.py` or `tools/*.py`. No BO running (no `tools/bo_pid.txt`).

---

## §1 TL;DR

**v06 went 1W/22L terminal on bytefight (Albert 0/13, Carrie 0/6, George 1/3).** Under v04's per-opponent base rates (A≈6%, C≈24%, G≈60%) the expected wins were ~3.6; observed ≤1. **P(≤1 | p=0.164) ≈ 0.09**, P(0 | p=0.164) ≈ 0.02 — genuinely below v04, not a coin-flip fluke.

**Root cause (confidence HIGH):** v06 is **not** a clean "F-2 revert only" change as the commit message claims. The working tree as-shipped included **two** changes on top of v04:

1. **F-2 revert** — `_search_mass_threshold()` flipped from 0.35 (+ endgame ramp to 0.30) back to flat 1/3. This alone would be modest.
2. **F-3 ply-window extension** — `_is_ply_zero()` was simultaneously widened from `turns_left >= 40` (ply 0 only) to `turns_left >= 38` (plies 0, 1, 2). This is the v0.4.2 "Opening-PRIME hardening" change described in the docstring. **The original v06 commit message did not call this out as part of the ship** — it is presented as a pre-existing v0.4.2 piece, but it is in fact shipped together with the F-2 revert inside `fb6c16dc`.

The v06 replays show a **distinctive move-distribution collapse** that only makes sense if BOTH changes are active. See §2.

## §2 Move-distribution evidence (n=3 v06 replays vs n=6 v04 vs n=12 v03 Albert)

Per-game averages from decomposed `left_behind` + `new_carpets`:

| Sample              | plain | **prime** | **carpet** | **search** | A srch h/m | A srch EV | A crp pts | B crp pts | A final | B final |
|---------------------|-------|-----------|------------|------------|------------|-----------|-----------|-----------|---------|---------|
| **v06 all (n=3)**   | 8.7   | **16.0**  | **2.3**    | **13.0**   | 14 / 25    | **+6**    | **3.7**   | 23.7      | 21.7    | 38.7    |
| v06 Albert (n=2)    | 9.5   | 16.0      | 2.0        | 12.5       | 9 / 16     | +4        | 2.5       | 23.5      | 20.5    | 44.5    |
| v06 Carrie (n=1)    | 7.0   | 16.0      | 3.0        | 14.0       | 5 / 9      | +2        | 6.0       | 24.0      | 24.0    | 27.0    |
| v04 Albert (n=6)    | 13.7  | 13.3      | 2.8        | 10.2       | 26 / 35    | **+34**   | 6.8       | 22.3      | 25.8    | 45.3    |
| v03 Albert (n=12)   | 12.1  | 14.2      | 3.4        | 10.2       | 56 / 67    | **+90**   | 7.9       | 21.2      | 29.7    | 42.7    |

Key deltas vs v04 Albert baseline:

- **Priming up +2.7 per game** (13.3 → 16.0). F-3 extended to plies 0/1/2 mechanically adds ~2 forced primes in the opening that the v04 search would have cashed out as PLAIN or short CARPET. Matches the docstring claim ("Carrie/Rusty open PRIME×3+").
- **Carpet rolls down −0.5 per game** (2.8 → 2.3) and, critically, **all k=2 rolls** in 2 of 3 replays (crp_lens=[2,2] or [2,2,2]). Zero k≥3 rolls in the losses. We prime MORE but roll SHORTER and FEWER. This is the *same* carpet collapse ALBERT_REGRESSION_APR18 flagged for v04, made worse.
- **Searches up +2.8 per game** (10.2 → 13.0) with **EV collapse** (+34/6 games = +5.7/game → +6/3 games = +2/game). The flat 1/3 threshold lets in low-quality searches (hit rate dropped to 14/39 ≈ 36%, right at the break-even), whereas v04's 0.35 floor kept us at 26/61 ≈ 43% hits with much higher conviction.

Opening-move verification: **all 3 v06 replays open `prime-prime-prime`** (F-3 extended firing). v04 replays open `prime-prime-plain` / `prime-plain-prime` / `prime-prime-search` (F-3 ply-0 only, then search takes over).

## §3 Mechanism — why is this worse than v04?

**F-3 @ plies 0/1/2 forces 3 primes in a row, placing them by the "most-open-neighbors" heuristic with no lookahead.** That:

- Burns our ply 0, 1, 2 on PRIME regardless of position quality. When the corner rectangle puts us in a tight spawn, the 3 forced primes cannot line up collinearly — we get an L-shape or scattered primes that support only k=2 rolls later. The v06 Albert replays all cap at k=2 rolls ([2,2] or [2,2,2]).
- Leaves the opponent 3 unchecked plies to build THEIR own prime chain. Albert/Carrie (expectiminimax + cell-potential) uses those 3 plies to construct a true collinear prime line — hence their k=3/k=4/k=5 rolls (see 4585b43c: B rolled [5,2,1,2,1,3,2]).
- The forced-prime placements are **chosen by a one-ply greedy heuristic** (`_landing_score` = count of non-blocked cardinal neighbors), not by the search. This is strictly worse than the alpha-beta search picking a PRIME when the search agrees it's best.

**F-2 revert simultaneously removes the "don't search on 0.33–0.35 belief" guard.** With plies 0/1/2 locked to PRIME, by ply 3 we're 3 primes deep and the belief distribution is still near-uniform (our rat-belief hasn't had many observations yet). The flat 1/3 gate fires marginal searches *right when the belief is noisiest*. EV collapses from +5.7/game (v04) to +2/game (v06). We are paying 2 points per wrong guess and getting no information-multiplier bounce.

**The two effects compound:** F-3 extended steals our tempo; F-2 revert then squanders the recovered tempo on low-EV searches instead of building and rolling carpets. Net: our carpet engine collapses (3.7 pts/game vs v04's 6.8), our search EV collapses (+2/game vs v04's +5.7), and our total score drops ~4 pts/game. Against Albert/Carrie who are already outscoring us by 15–20 pts, that's enough to turn marginal losses into blowouts.

## §4 Alternative hypotheses ranked

**H1 (accepted, HIGH confidence): F-2 revert + F-3 extension compound into carpet-chain collapse + low-EV search blooming.** All three replay signatures match: +2.7 primes, −0.5 carpets, +2.8 searches, EV halved. Statistical p ≈ 0.02 vs v04 baseline.

**H2 (partial, MEDIUM): F-3 extension alone is the main culprit, F-2 revert is ~neutral.** Plausible — v04 + F-3-extension was never A/B tested. The prime-up/carpet-down pattern is most consistent with extra forced primes. The search-EV collapse could be a secondary effect from being 3 primes deep by ply 3.

**H3 (REJECTED, LOW): Small-sample noise.** P(0/22 | p=0.164) ≈ 0.02 makes random noise implausible as sole cause. With 1W/23 if we're more generous, P ≈ 0.09 — still below the 10% threshold and the mechanistic replay pattern is corroborating.

**H4 (REJECTED, LOW): Upload/bundle regression (different binary than intended).** `errlog_a` in v06 replays reads `RattleBot v0.4.3 — alpha-beta + ID + HMM belief (ceiling=6.0s)`, matches the commit docstring bump. VAL_OK match a353394e confirmed the zip ran cleanly. Not a packaging bug.

## §5 Recommendation

**Primary (HIGHEST leverage, LOW risk): Ship `v07` = v04 baseline with F-2 revert to 1/3 **only** — revert F-3 ply-window back to `turns_left >= 40` (ply 0 only).** This isolates the F-2 change as originally described in `ALBERT_REGRESSION_APR18.md §4`. Predicted outcome: modest improvement vs Albert (the F-2 intent), no regression vs Carrie/George.

- One-line diff in `_is_ply_zero()`: `return tl >= 38` → `return tl >= 40`.
- Keep flat 1/3 threshold (F-2 revert) as-is.
- Keep F-3 ply-0 PRIME (the original v04 change).
- Fire 15–20 scrim wave post-upload; need ≥2 Albert wins to beat v04's 1/17 = 5.9% baseline convincingly.

**Secondary (if Primary shows no Albert improvement at n=15): try F-3-OFF entirely.** `_is_ply_zero()` returns False always, so the alpha-beta search gets ply 0 too. This tests whether F-3 itself is the liability. CLAUDE.md §7 warning against forced-prime lock-in supports this.

**Do NOT:** re-ship v06 as-is. Do NOT tune weights as a fix (mechanistic issue, not weights). Do NOT flip F-2 mid-scrimmage without a terminal W-L delta to read — we already learned that lesson.

**Uncertainty caveat:** n=22 is small; per-opponent n is much smaller (Albert 13, Carrie 6, George 3). The replay analysis is strong but rests on 3 decomposed games. A 30–40 game sample on v07 (F-2 revert + F-3-off-ply-1-2) would be the real test. If v07 doesn't decisively beat v04 in 30 games, the F-2 direction itself may be wrong and we should stop chasing it.

## §6 Appendix — tools used

```bash
# v06 replay fetch (done this session)
python tools/bytefight_client.py replay --match-uuid 4585b43c-b224-436f-b93f-34c7b93d289b --save docs/intel/replays/v06/albert_4585b43c.json
python tools/bytefight_client.py replay --match-uuid 329b0e28-a510-4b71-9346-83dcdd69142d --save docs/intel/replays/v06/albert_329b0e28.json
python tools/bytefight_client.py replay --match-uuid 9a8ad957-eada-4bbe-8678-f4f114dffdb9 --save docs/intel/replays/v06/carrie_9a8ad957.json

# Decomposition script: inline py -3 walking pgn fields
#   left_behind[idx] -> move_type string
#   new_carpets[idx] -> list of newly carpeted cells (len = roll k)
#   a_turns_left drops -> A ply index; b_turns_left drops -> B ply index
```

---

**End of V06_FAILURE_DIAGNOSIS_APR18.**
