"""Quick batch smoke runner for RattleBot v0.1 vs Yolanda.

Runs N games sequentially (limit_resources=False, matching
run_local_agents.py defaults), counts RattleBot wins. Prints summary.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def run_once() -> str:
    t0 = time.perf_counter()
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run(
        [sys.executable, os.path.join(REPO, "engine", "run_local_agents.py"),
         "RattleBot", "Yolanda"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=500,
        encoding="utf-8", errors="replace",
    )
    dt = time.perf_counter() - t0
    out = p.stdout or ""
    result = "UNKNOWN"
    for line in out.splitlines()[-20:]:
        if "wins by" in line or line.startswith("TIE"):
            result = line.strip()
            break
    return f"{dt:6.1f}s  {result}"


def main(n: int = 5) -> None:
    wins = 0
    print(f"Running {n} matches RattleBot vs Yolanda...", flush=True)
    for i in range(n):
        r = run_once()
        if "PLAYER_A wins" in r:
            wins += 1
        print(f"  match {i+1}/{n}: {r}", flush=True)
    print(f"RattleBot wins: {wins}/{n} ({100.0*wins/n:.0f}%)", flush=True)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    main(n)
