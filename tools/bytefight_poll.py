"""
Anonymous match-status poller for bytefight.org.

Runs in a loop, hitting the public game-match endpoint every N seconds, and
appends any NEW match events (scheduled -> running -> completed) to
`docs/tests/LIVE_SCRIMMAGE_LOG.md` under a "Poller observations" section.

No auth needed — uses only public endpoints. Safe to leave running 24/7.

Usage:
    python tools/bytefight_poll.py                       # runs forever, 30s interval
    python tools/bytefight_poll.py --interval 15         # faster poll
    python tools/bytefight_poll.py --once                # one-shot (for cron/test)
    python tools/bytefight_poll.py --pid-file bytefight_poll_pid.txt
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.bytefight_client import BytefightClient, BytefightError  # noqa: E402


LOG_PATH_DEFAULT = REPO_ROOT / "docs" / "tests" / "LIVE_SCRIMMAGE_LOG.md"
STATE_PATH_DEFAULT = REPO_ROOT / "tools" / "bytefight_poll_state.json"  # gitignored via tmp/scratch pattern? ensure in gitignore
PID_PATH_DEFAULT = REPO_ROOT / "bytefight_poll_pid.txt"
POLLER_SECTION_HEADER = "## Poller observations (bytefight_poll.py)"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def _load_state(path: Path) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"seen": {}}  # match_uuid -> last_status_seen


def _save_state(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)


def _ensure_section(log_path: Path) -> None:
    """Ensure the 'Poller observations' section exists at the end of the log."""
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(f"# LIVE_SCRIMMAGE_LOG\n\n{POLLER_SECTION_HEADER}\n\n", encoding="utf-8")
        return
    content = log_path.read_text(encoding="utf-8")
    if POLLER_SECTION_HEADER not in content:
        with open(log_path, "a", encoding="utf-8") as f:
            if not content.endswith("\n"):
                f.write("\n")
            f.write(f"\n{POLLER_SECTION_HEADER}\n\n")
            f.write("_Auto-appended by `tools/bytefight_poll.py`. Each line = one status transition observed via `GET /api/v1/public/game-match`._\n\n")


def _append_event(log_path: Path, line: str) -> None:
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _fmt_event(match: dict) -> str:
    status = match.get("status", "?")
    result_map = {
        "waiting": "queued",
        "running": "RUNNING",
        "in_progress": "RUNNING",
        "team_a_win": "A_WIN",
        "team_b_win": "B_WIN",
        "draw": "DRAW",
        "error": "ERROR",
        "submission_valid": "VAL_OK",
        "submission_invalid": "VAL_BAD",
    }
    result = result_map.get(status, status.upper())
    opp_name = match.get("teamBName", "?")
    opp_uuid = match.get("teamBUuid", "")
    my_sub = match.get("submissionAName", "?")
    opp_sub = match.get("submissionBName", "?")
    finished = match.get("finishedAt") or ""
    scheduled = match.get("scheduledAt") or ""
    reason = match.get("reason") or "?"
    uuid = match.get("uuid", "?")
    return (
        f"- [{_now_iso()}] {result:<8} match=`{uuid[:8]}` "
        f"vs `{opp_name}` ({opp_uuid[:8]}) "
        f"sub=`{my_sub}` opp_sub=`{opp_sub}` "
        f"reason={reason} sched={scheduled[:16]} finished={finished[:16]}"
    )


def _poll_once(client: BytefightClient, state: dict, log_path: Path, pages: int = 1, size: int = 20, verbose: bool = True) -> int:
    """One sweep. Returns number of new events appended."""
    new_events = 0
    for page in range(pages):
        try:
            resp = client.list_matches(page=page, size=size)
        except BytefightError as e:
            print(f"[{_now_iso()}] poll error: {e}", file=sys.stderr)
            return new_events
        content = resp.get("content") or []
        for m in content:
            uuid = m.get("uuid")
            status = m.get("status")
            if not uuid or not status:
                continue
            prev = state["seen"].get(uuid)
            if prev == status:
                continue
            line = _fmt_event(m)
            _append_event(log_path, line)
            if verbose:
                print(line)
            state["seen"][uuid] = status
            new_events += 1
        # No more pages to fetch if this was short
        if len(content) < size:
            break
    return new_events


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Anonymous bytefight match poller")
    p.add_argument("--interval", type=float, default=30.0, help="seconds between polls (default 30)")
    p.add_argument("--pages", type=int, default=1, help="number of 20-item pages to scan per sweep")
    p.add_argument("--size", type=int, default=20, help="page size")
    p.add_argument("--log-path", default=str(LOG_PATH_DEFAULT))
    p.add_argument("--state-path", default=str(STATE_PATH_DEFAULT))
    p.add_argument("--pid-file", default=str(PID_PATH_DEFAULT))
    p.add_argument("--team-uuid", help="override team UUID")
    p.add_argument("--once", action="store_true", help="single sweep then exit")
    p.add_argument("--quiet", action="store_true", help="suppress per-event stdout (still writes log)")
    args = p.parse_args(argv)

    log_path = Path(args.log_path)
    state_path = Path(args.state_path)
    pid_path = Path(args.pid_file)

    client = BytefightClient(team_uuid=args.team_uuid)
    state = _load_state(state_path)
    _ensure_section(log_path)

    if not args.once:
        pid_path.write_text(str(os.getpid()), encoding="utf-8")
        print(f"[{_now_iso()}] bytefight_poll started pid={os.getpid()} interval={args.interval}s log={log_path}", flush=True)

    stop = {"flag": False}

    def _handle_sig(signum, frame):  # noqa: ARG001
        stop["flag"] = True
        print(f"[{_now_iso()}] signal {signum} received, shutting down after current sweep", flush=True)

    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, _handle_sig)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_sig)

    try:
        while not stop["flag"]:
            added = _poll_once(client, state, log_path, pages=args.pages, size=args.size, verbose=not args.quiet)
            _save_state(state_path, state)
            if added:
                print(f"[{_now_iso()}] appended {added} event(s)", flush=True)
            if args.once:
                break
            # Sleep in short increments so Ctrl+C is responsive
            remaining = args.interval
            while remaining > 0 and not stop["flag"]:
                step = min(1.0, remaining)
                time.sleep(step)
                remaining -= step
    finally:
        if pid_path.exists() and not args.once:
            try:
                pid_path.unlink()
            except OSError:
                pass
        print(f"[{_now_iso()}] bytefight_poll exited cleanly", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
