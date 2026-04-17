# SUBMISSION_CANDIDATES — pre-staged zips for deadline activation

**Owner:** live-tester-2
**Last updated:** 2026-04-17
**Deadline:** 2026-04-19 23:59 EDT
**Safety-net principle:** every plausible candidate is built, hashed, and ready to upload. Decision at T-6h is reduced to "pick row, upload, activate" — not "build + pick + upload + activate under time pressure."

---

## 1. Candidate matrix

Zips live at `C:\Users\rahil\AppData\Local\Temp\submissions\`. Source column identifies the exact git commit (so any candidate can be rebuilt byte-for-byte from repo state). Status column marks readiness.

| # | Name                        | Zip filename                                           | Source (commit)             | Layout               | Size (B) | SHA256                                                              | vs Yolanda | vs FloorBot | Status       |
|---|-----------------------------|--------------------------------------------------------|-----------------------------|----------------------|----------|---------------------------------------------------------------------|------------|-------------|--------------|
| 1 | Yolanda_floor               | `Yolanda_probe.zip` (legacy path, see §1.1)            | n/a (starter bot)           | `Yolanda/agent.py`   | 684      | `e77f49ea66654a7260e7ac2a5ac339cbb38ea4880d3341e06edb1cf67057acfd`   | n/a        | 0/20 (T-17) | **LIVE** — Current submission on ByteFight, validated 2026-04-16 21:40 EDT |
| 2 | RattleBot_v01_snapshot      | `RattleBot_v01_snapshot_20260416_2320.zip`             | `09b182d` (T-18 audit PASS) | `RattleBot/*.py`     | 20 723   | `4d387a2686d241e31a7695c1e68349eb8b66319352339c952e3033ffa208e713`   | 5/5 (T-16) | pending     | **READY** — audit-approved v0.1, 34/34 pytest PASS, not uploaded |
| 3 | RattleBot_v02_notuning      | (pending T-20f completion + W_INIT freeze)              | tbd (post-T-20f)            | `RattleBot/*.py`     | —        | —                                                                   | pending    | pending     | NOT BUILT    |
| 4 | RattleBot_v02_tuned         | (pending T-20d BO run completion)                       | tbd (post-T-20d + weights.json) | `RattleBot/*.py`+`weights.json` | — | —                                                                   | pending    | pending     | NOT BUILT    |

### 1.1 Yolanda legacy path note

Yolanda_floor lives at `C:\Users\rahil\AppData\Local\Temp\Yolanda_probe.zip` (NOT inside the `submissions/` subdir) because it predates this matrix by ~5 hours. The tester-live predecessor built it straight to the temp dir, then uploaded it and set it Current. We do not move / rename / copy it because any such operation would produce a new file with different mtime and the LIVE-004 upload-time metadata would no longer match. If at any point we need a clean Yolanda zip rebuild, the recipe is:

```bash
python -c "
import zipfile, io, os
body = open('3600-agents/Yolanda/agent.py','rb').read()
with zipfile.ZipFile('Yolanda_probe.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('Yolanda/agent.py', body)
"
```

…but this is NOT byte-identical to the live zip (compression defaults, file metadata differ). Treat the legacy file as canonical.

## 2. Build recipes (for reproducibility)

### 2.1 RattleBot_v01_snapshot — commit `09b182d`

```bash
cd C:/Users/rahil/downloads/3600-bot
TS=$(date +%Y%m%d_%H%M)
OUT="C:/Users/rahil/AppData/Local/Temp/submissions/RattleBot_v01_snapshot_${TS}.zip"
python -c "
import zipfile, subprocess
commit = '09b182d'
files = subprocess.check_output(['git','ls-tree','-r','--name-only', commit, '3600-agents/RattleBot/'], text=True).strip().split('\n')
files = [f for f in files if '/tests/' not in f and '__pycache__' not in f]
with zipfile.ZipFile(r'$OUT','w', zipfile.ZIP_DEFLATED) as z:
    for f in files:
        arcname = f.replace('3600-agents/','',1)  # RattleBot/agent.py at root
        content = subprocess.check_output(['git','show', f'{commit}:{f}'])
        z.writestr(arcname, content)
"
```

This extracts the nine v0.1 files (agent, heuristic, search, move_gen, rat_belief, time_mgr, types, zobrist, __init__) and drops `tests/` and `__pycache__/` to keep the zip lean. Verified 34/34 pytest in source form.

### 2.2 RattleBot_v02_notuning — to build when weights are frozen (post-T-20f, pre-T-20d)

```bash
# When T-20f lands: 22aa02b or later but before weights.json is updated by BO
# Build the same way as v01, but from a commit on main that includes T-20f's k=1/SEARCH-gate fixes.
# Expected commit range: 22aa02b..(next feat before weights.json change)
COMMIT="22aa02b"   # update when freezing
TS=$(date +%Y%m%d_%H%M)
OUT="C:/Users/rahil/AppData/Local/Temp/submissions/RattleBot_v02_notuning_${TS}.zip"
# same zipfile recipe as §2.1, with COMMIT substituted
```

### 2.3 RattleBot_v02_tuned — to build after T-20d-RUN1 completes

**CRITICAL packaging detail (from dev-heuristic, 2026-04-17):** The BO run writes winning weights to `3600-agents/RattleBot/weights_v02.json`, but `agent.py::_load_tuned_weights` (lines 45-63) only auto-loads a sibling file named **literally `weights.json`**. So for this candidate we must **rename** `weights_v02.json` → `weights.json` inside the zip, right next to `agent.py`. If it stays named `weights_v02.json` the agent silently falls back to hard-coded `W_INIT` — the submission would be v02_notuning masquerading as v02_tuned.

```bash
# Requires: BO run complete (weights_v02.json written), T-20f fixes merged, tests pass.
# Expected commit range: post-task-#44 completion on main.
COMMIT="<post-T-20d>"                                  # update after task #44 lands
WEIGHTS_SRC="3600-agents/RattleBot/weights_v02.json"   # what BO writes
TS=$(date +%Y%m%d_%H%M)
OUT="C:/Users/rahil/AppData/Local/Temp/submissions/RattleBot_v02_tuned_${TS}.zip"

python -c "
import zipfile, subprocess
commit = '${COMMIT}'
out = r'${OUT}'
files = subprocess.check_output(['git','ls-tree','-r','--name-only', commit, '3600-agents/RattleBot/'], text=True).strip().split('\n')
files = [f for f in files if '/tests/' not in f and '__pycache__' not in f and f.endswith('.py')]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in files:
        arcname = f.replace('3600-agents/','',1)
        z.writestr(arcname, subprocess.check_output(['git','show', f'{commit}:{f}']))
    # Inject weights.json — rename from weights_v02.json.
    w = subprocess.check_output(['git','show', f'{commit}:${WEIGHTS_SRC}'])
    z.writestr('RattleBot/weights.json', w)   # <-- LITERAL name matters
"
# Expect zip size ~21-25 KB (v01 is 20.7 KB; weights.json adds ~300 B).
```

**Verification after build (mandatory before upload):**

```bash
python -c "
import zipfile, tempfile, subprocess, os
zpath = r'${OUT}'
tmp = tempfile.mkdtemp()
with zipfile.ZipFile(zpath) as z: z.extractall(tmp)
assert os.path.isfile(os.path.join(tmp,'RattleBot','weights.json')), 'weights.json missing at zip root'
env = dict(os.environ, PYTHONPATH=f'{tmp};engine;3600-agents')
out = subprocess.check_output(['python','-c','from RattleBot.agent import _load_tuned_weights; w=_load_tuned_weights(); assert w is not None, \"fell back to None — weights not loaded\"; print(\"weights shape:\", w.shape, \"first 3:\", w[:3].tolist())'], env=env, text=True)
print(out)
"
```

Expected stdout contains `weights shape:` and a non-None array of N_FEATURES floats. Anything else = broken zip, DO NOT upload.

## 3. Pre-upload validation checklist (per candidate)

Before any upload (v0.2 or later), run this locally:

1. **Layout check:** `python -c "import zipfile; z=zipfile.ZipFile('<file>'); print(z.namelist())"` — member 0 must be `<BotName>/<first-file>.py` (no `3600-agents/` prefix, no extra top-level directory).
2. **Test suite:** `PYTHONPATH="engine;3600-agents" python -m pytest 3600-agents/<BotName>/tests/ -v` — must be 100% green.
3. **Smoke match:** `python engine/run_local_agents.py <BotName> Yolanda` — must complete, bot should win (Yolanda is random-mover).
4. **SHA256 record:** `python -c "import hashlib; print(hashlib.sha256(open('<zip>','rb').read()).hexdigest())"` — add row to matrix above.
5. **Time discipline:** ensure no per-move wall-time exceeds the tournament's 6s (local benchmarks show v0.1 max = ~3s, v0.2 max = ~6s with new ceiling — see T-20a notes).

## 4. Activation decision rule

At T-6h, T-1h, and T-0, the following decision tree fires (in order — first hit wins):

### T-6h pre-deadline

```
IF v0.2_tuned exists AND v0.2_tuned vs FloorBot paired ≥ 65% on 100 matches AND v0.2_tuned vs Yolanda paired ≥ 95% AND 0 crashes over 200 matches
   → ACTIVATE v0.2_tuned

ELSE IF v0.2_notuning vs FloorBot paired ≥ 60% on 100 matches
   → ACTIVATE v0.2_notuning

ELSE IF v0.1_snapshot already uploaded and valid
   → ACTIVATE v0.1_snapshot

ELSE
   → KEEP Yolanda_floor (grade floor ~0-10%, insurance only)
```

Exit condition: one of these is Current on ByteFight and has a green "valid" status.

### T-1h pre-deadline (confirmation pass)

- Re-query ByteFight `/submissions` — confirm Current checkbox is set and Validity is valid on the intended candidate.
- If the candidate's validation came back `invalid` (loss to validator), IMMEDIATELY fall back one row: v0.2_tuned → v0.2_notuning → v0.1_snapshot → Yolanda.
- Verify partner hasn't overwritten (per R-PARTNER-01). If they have, DO NOT overwrite their submission without team-lead approval.

### T-0 (last-minute)

- Snapshot `/team` page: record whatever is Current at 23:59:00 EDT. That's what gets graded.
- Do NOT attempt any upload after T-0:05; server clock may lag local clock and late uploads may not count.

## 5. Adding future candidates

New rows go above the "pending" block but below the current filled rows. Required fields:

- **Name:** `<botname>_<variant>` (e.g., `RattleBot_v03`, `RattleBot_v02_aggressive_search`).
- **Zip filename:** `<name>_<YYYYMMDD_HHMM>.zip` in `C:\Users\rahil\AppData\Local\Temp\submissions\`.
- **Source commit:** full commit hash.
- **Layout:** zipfile top-level entries (e.g., `RattleBot/*.py`).
- **Size (B):** actual zip file size.
- **SHA256:** `hashlib.sha256(open(path,'rb').read()).hexdigest()`.
- **vs Yolanda / vs FloorBot:** paired-runner (`tools/paired_runner.py`) outputs from task #22's harness. Format: `wins/total (source)`.
- **Status:** one of `NOT BUILT`, `READY`, `UPLOADED`, `LIVE`.

## 6. Constraints respected on this pass

- No uploads to ByteFight (zero §F-14 cost consumed).
- No changes to the live Yolanda submission (still Current).
- No new scrimmages.
- No deletion of any existing file.
- Did NOT modify commit 09b182d's tree — used `git show`/`ls-tree` read-only.
- SHA256 captured for both candidates allows future integrity verification.

## 7. Known risks

- **R-43-01** (medium): SHA256 on a zipfile built with Python's `ZipFile` depends on insertion order + compression defaults. If someone rebuilds from §2.1 and gets a different SHA, that's not a corruption signal — it's just a rebuild artifact. The source commit is authoritative, not the SHA.
- **R-43-02** (low): `C:\Users\rahil\AppData\Local\Temp\` can be cleaned by Windows / user. Before the deadline window, copy the candidate zips to a persistent location (e.g., `C:\Users\rahil\downloads\3600-bot\submissions_archive\`, gitignored) and update paths here.
- **R-43-03** (medium): The v0.1 snapshot's `__init__.py` imports `from . import rat_belief, search, heuristic, move_gen, time_mgr, zobrist, types`. If ByteFight's sandbox dislikes imports-in-__init__ (unconfirmed — LIVE-002 tested removing __init__.py; LIVE-003 confirmed Yolanda works single-file), the fallback single-file `RattleBot_v01_singlefile` variant would need to be built separately. **Not built this pass.** Suggested follow-up if v0.1 upload fails.
- **R-43-04** (low): File timestamps in the zip may be 1980-01-01 (zipfile default for writestr). Probably harmless on ByteFight's sandbox which only cares about content. If ByteFight rejects on mtime, switch to `ZipInfo(file_mode=0o644)` with a real date_time.
