# v05 k1swap Upload Log

**Date:** 2026-04-18 02:18 local / 06:18 UTC
**Agent:** `v05-build-upload` (ephemeral)

## Build

- Source: `3600-agents/RattleBot/` @ HEAD (commit `d99a95d` — f1-gate-audit)
- Agent version string: RattleBot v0.4.1
- Zip: `submissions/RattleBot_v05_k1swap_20260418_021811.zip`
- Size: 47,305 bytes (47 KB) — pure Python, well under 200 MB
- SHA256: `46a39f3b782dd34e4aeed24b78bbad5119181250fa453d2819f152d5a8f48795`
- Numba stripped: no (default False in source)
- Weights bundled: none

Zip contents (9 files, all `RattleBot/*.py`):

```
  432 B  RattleBot/__init__.py
21444 B  RattleBot/agent.py
66216 B  RattleBot/heuristic.py
 6065 B  RattleBot/move_gen.py
 9838 B  RattleBot/rat_belief.py
17274 B  RattleBot/search.py
11975 B  RattleBot/time_mgr.py
 5151 B  RattleBot/types.py
 3738 B  RattleBot/zobrist.py
```

## Upload

- Endpoint: bytefight.org (team `81513423-e93e-4fe5-8a2f-cc0423ccb953`)
- **Upload UUID: `41d0abd5-cfae-48c0-973d-6b88c8459730`**
- Returned validity: `not_evaluated` (pending)
- Description: "RattleBot v0.4.1 k1swap: F-1 gate audit (d99a95d) defensive SEARCH swap when forced k=1 AND belief.max_mass > 1/6"

## Current-submission verification

Post-upload `my-team` check:

- `currentSubmissionDTO.uuid` = `379d5f82-80d4-4ff7-8430-8363e871fe68`
- `currentSubmissionDTO.name` = `RattleBot_v04_archfix_20260418_003411.zip`
- **v04 remains Current. v05 NOT set-current (per team-lead directive).**

Team-lead will flip to v05 after comparing v04 vs v05 scrim ELO.

## Rationale for the 12-LoC patch under test

On forced k=1 carpet (the only legal carpet is a -1 point 1-square roll), if
the rat-belief argmax has mass > 1/6 the swap replaces the -1 EV carpet with
a SEARCH at the argmax cell (EV = 4p - 2(1-p) = 6p - 2, > -1 iff p > 1/6).
