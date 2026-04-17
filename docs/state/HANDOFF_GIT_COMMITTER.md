# Handoff — git-committer

**From:** git-committer v1 (rotating out for context hygiene, 2026-04-17)
**To:** git-committer v2 (successor)
**Repo:** https://github.com/rjav1/3600-bot (main)
**Account:** `rjav1 <rahiljav@gmail.com>` — confirm every time you commit (§7).

This is a flat dump of every non-obvious convention and lesson from the first rotation. Read all of it once before touching git — most of it came from fixing a mistake.

---

## 1. Your job in one sentence

Teammates finish work and ping you; you stage ONLY what they pinged (never `git add .`), write a conventional-commit message, commit, `git push origin main`, report the hash back to the pinging teammate AND to team-lead. You are persistent — do NOT mark your task completed; stay active for the life of the project.

When idle, just wait. Do not poll, do not re-scan. Your process idles automatically after each turn.

---

## 2. Commit-subject conventions (conventional-commits style)

Format: `type(scope): subject` — keep subject ≤ 72 chars, imperative mood, lowercase after the colon unless proper noun.

Observed types and scopes used on this repo:

| Type | Scope | Example |
|------|-------|---------|
| `feat` | `RattleBot` | `feat(RattleBot): T-13 rat_belief.py v0.1 — HMM forward filter (13/13 tests, 0.032 ms/call)` |
| `feat` | `floorbot` | `feat(floorbot): ship FloorBot v1 — 70%-tier insurance reactive agent` |
| `feat` | `tools` | `feat(tools): T-17 paired-match batch runner — 20/20 FloorBot v Yolanda smoke, p=0.00195` |
| `docs` | `research` | `docs(research): land RESEARCH_HMM_RAT.md — Bayesian filter for rat tracking` |
| `docs` | `research` | `docs(research): amend RESEARCH_HMM_RAT.md §E.6 SEARCH-node belief handling` |
| `docs` | `synthesis` | `docs(synthesis): land SYNTHESIS.md — wave-1 research consolidated for Strategy-Architect` |
| `docs` | `plan` | `docs(plan): ratify BOT_STRATEGY v1.1 — D-008–D-011 (contrarian arbitration)` |
| `docs` | `spec` | `docs(spec): add authoritative GAME_SPEC and log 3 engine gotchas` (game-analyst) |
| `docs` | `tests` | `docs(tests): LIVE-003 — Yolanda probe VALID; H7 confirmed, H3 refuted` |
| `docs` | `audit` | `docs(audit): RattleBot v0.1 audit — PASS (amber), 0 critical / 0 high / 3 medium / 4 low` |
| `docs` | `claude` | `docs(claude): correct bytefight.org account email (rjavid3@gatech.edu) + add team URL` |
| `docs` | `state` | `docs(state): HANDOFF_GIT_COMMITTER — conventions + lessons for successor` |
| `chore` | `floorbot` | `chore(floorbot): add 100-match test logs as evidence (force-added past .gitignore)` |
| special | `strategy-architect:` prefix | `strategy-architect: ship BOT_STRATEGY.md v1.0 + record D-004/D-005/D-006` (when the author is a persona, it's OK to put their name as the prefix) |

**Scope casing matches the folder/directory name** on disk. `RattleBot` is CamelCase because the folder is; `floorbot` is lowercase because the team treats it that way in prose. Match whatever the teammate writes.

When your subject differs from the teammate's suggestion, that's fine — content preservation matters more than exact wording. ALWAYS note the difference in your reply to them.

---

## 3. Commit body — what goes in, what stays out

**Include:**
- WHY this commit exists (1–2 lines at top is enough if the subject is already concrete).
- Perf numbers if they were in the teammate's ping (e.g. "update 0.032 ms/call over 2000 calls, 15× under 0.5 ms target"). These are evidence for later ELO tuning decisions.
- Cross-references to decisions, using the EXACT ID on origin (e.g. "per D-004", "per D-011 item 3"). Never guess an ID.
- Commit hashes of related prior commits when the new commit logically depends on them (e.g. "STATE row + R-HEUR-001 already in 122467b").
- A **"Scope note:"** section when the working tree had other WIP you deliberately did NOT stage. This is load-bearing for audit — teammates need to know their WIP was seen and left alone. Always name the other files and owners.
- Any mechanical corrections you applied before staging (e.g. "Restored dropped D-006 heading that was eaten during the contrarian-dissent fill-in").

**Cut:**
- "I" language; commits speak in the project voice.
- Running commentary or narrative. Bullets only.
- Re-stating the subject.
- `Co-Authored-By:` — we don't use it on this repo.

**Heredoc pattern** — always use this for multi-line messages so formatting survives:
```bash
git commit -m "$(cat <<'EOF'
<subject>

<body>
EOF
)"
```

---

## 4. Git-safety protocol — NON-NEGOTIABLE

Copy-paste these rules into your working memory:

- NEVER `git push --force` or `--force-with-lease`.
- NEVER `git reset --hard`, `git clean -f`, `git branch -D`, `git checkout --`.
- NEVER commit `.env`, `.pem`, `.key`, credentials, API tokens.
- NEVER `git commit --amend` a commit that's already on origin. Always create a NEW commit on top (even for typo fixes). The team relies on the chain being append-only.
- NEVER edit git config (`git config user.name` et al.) unless the user explicitly asks. Confirm identity before each commit (§7).
- NEVER skip hooks (`--no-verify`).
- NEVER pass `--author=` or `-c user.name=` to override the committer identity.
- If ANY git operation fails unexpectedly, STOP and send a SendMessage to team-lead describing the problem. Do NOT improvise destructive recovery.
- If a file looks sensitive or accidentally-committed, flag the owner and ask before staging.

If `git push` fails (non-fast-forward), do `git pull --rebase origin main` and retry. Never force-push.

---

## 5. Staging discipline — teammates' pings are scoped, trust them

**Default: `git add <explicit paths only>`. Never `git add .` / `git add -A` / `git add -u`.**

Teammates' pings tell you which files are theirs. The working tree may contain:
- Their files (stage).
- Other teammates' in-flight WIP (leave alone — will be staged when those owners ping).
- `.claude/` — harness lockfile, not project content. Never stage.
- `__pycache__/`, `*.log` — already in .gitignore, safely skipped.
- `3600-agents/matches/` — gitignored, match output, never commit.

If a ping is ambiguous or mentions a file you see multiple diffs in, stage only the files matching the ping and mention the leftovers in the commit body under "Scope note:". Then in your reply to the teammate, list what you staged and what you deferred.

**Exception — `tests/` directory is tracked.** It is NOT in .gitignore (only `3600-agents/matches/` is). Test files and even `_batch_smoke.py`-style local runners live there and ARE committed.

---

## 6. Race-condition protocol — pings can arrive out of order

This happened roughly 8 times during the first rotation. It WILL happen to you.

Pattern: teammate A pings you directly. You commit+push. Team-lead separately pings you to do the same commit — their message was already in flight when you pushed.

**Before acting on any ping, ALWAYS run:**
```bash
cd C:/Users/rahil/downloads/3600-bot && git log --oneline -5 && echo "---" && git status --short
```

If the work the ping describes is already on origin:
- Do NOT re-commit or amend. Amending a published commit is forbidden (§4).
- Reply to the pinging teammate with the hash and subject, noting "already on origin".
- Reply to team-lead with the same, referencing your prior report.

Sample response pattern that worked well:
> "Already landed. Hash: `abc1234`, subject: "…". Scope matches exactly: [files]. My subject differs slightly from yours; content identical. Idling."

---

## 7. Identity verification — rjav1 / rahiljav@gmail.com

**Standing user rule:** all commits MUST be authored as `rjav1 <rahiljav@gmail.com>`.

Before each commit, run:
```bash
git config user.name && git config user.email
```

Both should be `rjav1` and `rahiljav@gmail.com` respectively. If either drifts (harness restart, fresh shell), re-apply:
```bash
git config user.name "rjav1" && git config user.email "rahiljav@gmail.com"
```

Never override per-commit with `--author=` or `-c user.name=`. If a commit landed with the wrong author, STOP and ping team-lead — do NOT force-push to rewrite history.

Note: bytefight.org account email is `rjavid3@gatech.edu` (display name "Rjav") — that's a DIFFERENT email. Git commits use `rahiljav@gmail.com`; tournament submission uses `rjavid3@gatech.edu`. See commit `d49877d` and `docs/tests/LIVE_UPLOAD_001.md`.

---

## 8. .gitignore and evidence carve-outs

Current rules that matter:
- `3600-agents/matches/` — engine match-log output. Never commit. Tester-local's paired_runner writes here.
- `__pycache__/` — auto-generated.
- `*.log` — runtime logs, auto-generated.

**One-off evidence carve-out precedent:** commit `1a8d910` used `git add -f` to force `run_A.log` and `run_B.log` into the repo as evidence for FloorBot's 100/100 vs Yolanda smoke-test (cited in `docs/plan/FLOOR_BOT.md`). Rule the team set after:

> Future test logs should remain gitignored by default — only commit them when explicitly labeled as evidence by team-lead. When you do, call out the `.gitignore` override in the commit subject (`"force-added past .gitignore"`) and body.

Never edit `.gitignore` to narrow it unless team-lead explicitly asks.

---

## 9. DECISIONS.md is an append-only ledger with unique IDs

The `docs/DECISIONS.md` format contract: entries are `## D-NNN — YYYY-MM-DD — Title`, numbered ascending, never reused.

**ID-collision incident (this rotation):** strategy-architect submitted a BOT_STRATEGY v1.1 bundle using D-007..D-010, but D-007 was already taken (FloorBot-shipped entry). Fix was a mechanical **+1 renumber** across ALL THREE files that referenced the new IDs:
- `docs/DECISIONS.md` — the new bodies
- `docs/STATE.md` — the summary rows AND the active-agents / open-loops prose that mentioned them
- `docs/plan/BOT_STRATEGY.md` — the §0 arbitration register and v1.1 changelog that listed the IDs

Protocol when you detect a collision:
1. STOP. Do NOT commit the conflicting patch.
2. Ping the submitting teammate (e.g. strategy-architect) proposing the minimal mechanical fix.
3. Ping team-lead in parallel so they can approve or redirect.
4. If approved, apply the renumber by editing the highest ID FIRST and cascading down (D-010→D-011, then D-009→D-010, etc.) to avoid accidentally clobbering your target.
5. Grep for every internal cross-reference and fix it (`grep -n "D-010\|D-011" docs/`).
6. Add a `[IDs bumped +1 from architect's original numbering to avoid collision with D-NNN ...]` footnote in at least one visible place so future readers understand the offset.
7. In the commit body, document the collision and the renumber.
8. After committing, ping the original author so their local notes stay in sync.

Precedent commits: `9ba5967` (the renumber) and `921eb4e` (the follow-up where dev-integrator's code docstrings had to be retargeted from D-010 to D-011 — see §11).

---

## 10. Structural repair pattern — eaten headings etc.

Precedent: during strategy-contrarian's D-004/D-005/D-006 dissent fill-in, the incoming diff accidentally absorbed the `## D-006 — 2026-04-16 — FloorBot is the live-submission baseline...` heading line and its `---` separator into D-005's dissent paragraph. D-006's body was intact but visually merged into D-005.

**Protocol when you detect a structural break:**
1. Before staging, always sanity-check:
   ```
   grep "^## D-0" docs/DECISIONS.md
   ```
   and similar heading-counts on any ledger file. Know the count you expect (6 at that time; 7 after).
2. If a count is off, inspect the diff carefully. The break is usually mechanical (markdown heading lost).
3. Restore the heading+separator with a minimal Edit. Do NOT rewrite surrounding content.
4. Re-run the grep to confirm the count is now correct.
5. In the commit body, explicitly call out the restoration: "NOTE: the D-NNN heading was dropped in teammate's working-tree edit — I restored it as a minimal mechanical fix so the file parses as N discrete decisions. No content changes; only the heading line and its separator were put back."
6. Ping the submitting teammate so they know.

Precedent commit: `c47f45e`.

---

## 11. Code-docstring sync after ledger renumbers

When the DECISIONS.md IDs shift (§9), any source file that cites those IDs in docstrings MUST be updated too. Otherwise future readers see "D-010 item 3" in code but look up D-010 and find a different decision.

Precedent: after `9ba5967` renumbered D-007..D-010 → D-008..D-011, dev-integrator's RattleBot scaffold (`types.py`, `heuristic.py`, `rat_belief.py`, `search.py`, `move_gen.py`, `time_mgr.py`) had 10 references to "D-010" that meant "the five-technical-fixes bundle" (which is now D-011 on origin). I retargeted them mechanically before committing that scaffold (`921eb4e`).

**Protocol when you see this:**
1. `grep -n "D-010\|D-011" <incoming files>` to find every reference.
2. Identify which references are semantic (meaning "the X decision") vs just numeric coincidence.
3. For semantic references, do a targeted search-and-replace using a one-shot Python snippet (be careful with `replace_all` when multiple distinct IDs appear in the same file).
4. Grep again to confirm no stale IDs remain.
5. Call out the retarget in the commit body.
6. Ping the owner with a clear mapping so their follow-up work stays consistent.

---

## 12. STATE.md — the most-modified file, and its traps

Every completion ping touches `docs/STATE.md` (header, active-agents row, decision row, blockers/open-loops). Traps:

1. **Multi-owner STATE patches.** Teammate A's "STATE.md" diff often contains B's already-landed entries too, because they both pulled from the same tree. Commit the diff as-given if it doesn't clobber anything — the cross-owner content is usually already correct. If it does clobber, stop and ping.
2. **Stale open-loop pointers.** Sometimes a new commit's STATE patch re-asserts an out-of-date open-loop (e.g. "FloorBot blocked on team creation" after LIVE-001 had been rewritten). I committed these verbatim and flagged them in my report to team-lead as "pointer-drift" rather than blocking. One-line fix-up commits can clean these up when team-lead approves.
3. **Header line is a tiny summary log.** Every new decision tends to replace the last-updated header. That's fine; treat the header as a rolling pointer, not a history.
4. **The "Recent decisions" section grows forever** and its rows cite DECISIONS.md by ID. When you renumber IDs (§9), these rows must change too.

---

## 13. Task tracking — you do NOT close your task

Task #7 is your persistent task: "Git committer: commit + push on every finished task". It is marked `in_progress` for the life of the project. **Do NOT call TaskUpdate to mark it `completed`** — you stay active until formally rotated out (which is what's happening to me now).

Don't use TaskCreate/TaskUpdate for commit work; commits are implicit state. The task tool is for the teammates doing dev work.

---

## 14. Standard invocation order

When a ping arrives, this is the safe sequence:

```bash
cd C:/Users/rahil/downloads/3600-bot && git config user.name && git config user.email && git log --oneline -5 && git status --short
```

Then inspect diffs for ANY file touched, then `git add` only scoped paths, then `git diff --cached --stat` as a sanity check, then commit with heredoc, then `git push origin main`, then SendMessage both the pinging teammate and team-lead with the hash.

Use `git diff --stat` before reading full diffs — on big files it saves context.

---

## 15. SendMessage hygiene

The SendMessage tool schema requires fetching via ToolSearch once per session. If a fresh session, start with:
```
ToolSearch("select:SendMessage")
```

Pattern for post-commit reporting:
- To the pinging teammate: one short message, one line ideally — "pushed: <hash> — <subject>. [files] on origin/main."
- To team-lead: same hash + subject, plus any FYI about leftover WIP or caveats you noticed.
- Never quote the original message back. Never send structured JSON status.

For protocol messages (shutdown_request, shutdown_response), use the JSON forms in the SendMessage doc. Don't originate `shutdown_request` unless team-lead explicitly asks for rotation (as is happening here).

---

## 16. Untracked `.claude/` and similar harness files

`.claude/scheduled_tasks.lock` is the Claude Code harness's local state. It reliably shows up as `??` in `git status`. Never stage it. Never add it to `.gitignore` either — it's a local-machine concern.

---

## 17. Windows path / line-ending notes

- Always use forward slashes in bash: `C:/Users/rahil/downloads/3600-bot/...`
- `git add` prints "LF will be replaced by CRLF" warnings — IGNORE, they're informational, not errors.
- The repo is on Windows; the tournament runs on Linux. The `tools/paired_runner.py` code has a Windows fallback for `--limit-resources` (commit `0688a02`). Don't be surprised if tests that rely on seccomp skip on Windows.

---

## 18. Final context handoff

At the moment of rotation:
- Origin/main HEAD: `09b182d` — docs(audit): RattleBot v0.1 audit — PASS (amber)
- Next expected pings: T-19 (v0.1 release tagging?), T-20 vs FloorBot paired baseline (task #22 in-progress), LIVE-004 if tester-live runs the next upload experiment.
- Known outstanding small cleanups (not blockers):
  - STATE.md "Open loops" has one stale line saying FloorBot "blocked on LIVE-001 (team creation)" from a tester-local patch that landed before LIVE-001 was rewritten. Harmless but worth fixing whenever STATE gets touched next.
- Latest decision IDs in use: D-011. Next new decision from strategy-architect should be D-012.
- Task list: 18 completed, 3 in_progress, 1 pending. My task #7 remains in_progress as per §13.

Good luck. You're going to do great. When in doubt: check `git log`, check `git status`, and when you can't tell what to do, ASK team-lead before taking an action you can't undo.

— git-committer v1
