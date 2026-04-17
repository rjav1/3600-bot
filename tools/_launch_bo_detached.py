"""One-shot detached launcher for tools/bo_tune.py.

Spawns bo_tune.py as a process fully detached from this Python process
and its console, so it survives the parent shell exiting. Used when the
orchestrating agent's bash shell may terminate (Claude background-task
lifetime < BO wall-clock).

Writes the launched PID to `<log-dir>/bo_pid.txt` for later monitoring
or targeted kill. stdout/stderr go to `<log-dir>/bo_stdout.log`.

Usage: `python tools/_launch_bo_detached.py -- <bo_tune args...>`
(anything after the `--` is passed through to bo_tune.py verbatim.)

The script exits immediately after spawning (returns the child PID on
stdout), so it's safe to call synchronously from any shell.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000


def main():
    # Forward everything after a literal "--" to bo_tune.py.
    argv = sys.argv[1:]
    if "--" in argv:
        i = argv.index("--")
        bo_args = argv[i + 1:]
    else:
        bo_args = argv
    # Extract log-dir so we can park the stdout/pid alongside.
    log_dir = None
    for j, tok in enumerate(bo_args):
        if tok == "--log-dir" and j + 1 < len(bo_args):
            log_dir = bo_args[j + 1]
            break
    if log_dir is None:
        log_dir = str(REPO_ROOT / "3600-agents" / "matches" / "bo_detached")
    log_path = pathlib.Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    stdout_path = log_path / "bo_stdout.log"
    pid_path = log_path / "bo_pid.txt"

    cmd = [
        sys.executable,
        "-u",
        str(REPO_ROOT / "tools" / "bo_tune.py"),
    ] + bo_args

    log_fh = open(stdout_path, "a", buffering=1, encoding="utf-8")
    log_fh.write(
        f"\n=== bo_tune detached launch ===\ncwd={REPO_ROOT}\n"
        f"argv={cmd}\n===\n"
    )
    log_fh.flush()

    # Windows-specific: DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP so
    # the child survives parent death. CREATE_NO_WINDOW to suppress any
    # console popup under cmd/powershell.
    flags = 0
    if os.name == "nt":
        flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        cwd=str(REPO_ROOT),
        creationflags=flags,
        close_fds=True,
    )

    pid_path.write_text(str(proc.pid), encoding="utf-8")
    print(proc.pid)


if __name__ == "__main__":
    main()
