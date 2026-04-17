#!/usr/bin/env bash
# Tournament-sandbox simulator — shell path (Linux / WSL).
#
# Wraps a command under resource limits that approximate bytefight.org's
# sandbox: virtual-memory cap, wall-clock timeout, a network namespace
# (when unshare is available, effectively drops the network), and the
# working directory held constant.
#
# Usage:
#   tools/sandbox_sim.sh -- <command...>
#
# Example — verify RattleBot imports cleanly in Python 3.12 Linux
# (the actual tournament Python):
#   tools/sandbox_sim.sh -- python3 -c \
#       'import sys; sys.path[0:0]=["engine","3600-agents"]; import RattleBot'
#
# Caveats
# -------
# - We rely on WSL's ulimit + timeout + unshare. No seccomp (would need
#   root + libseccomp tooling).
# - Full engine matches require `jax`, `psutil`, `scikit-learn`, etc.
#   WSL typically ships none of those. Use this script for import
#   sanity checks and pure-logic unit tests; use `tools/sandbox_sim.py`
#   on Windows for full engine matches.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MEM_KB=$((1536 * 1024))   # 1.5 GB virtual memory (GAME_SPEC §7)
WALL_S=300                # 5 min hard cap (4 min play + headroom)
NET=1                     # try to drop network via unshare

show_help() {
    cat <<EOF
Usage: $(basename "$0") [--no-net] [--mem-kb N] [--timeout S] -- <cmd> [args...]

Options
  --no-net        Skip network-namespace drop (fallback if unshare fails).
  --mem-kb N      Override virtual-memory cap (default $MEM_KB KB = 1.5 GB).
  --timeout S     Wall-clock timeout in seconds (default $WALL_S).
  --help          Show this message.

The command is run with CWD = repo root ($REPO_ROOT).
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-net)    NET=0 ; shift ;;
        --mem-kb)    MEM_KB="$2" ; shift 2 ;;
        --timeout)   WALL_S="$2" ; shift 2 ;;
        -h|--help)   show_help ; exit 0 ;;
        --)          shift ; break ;;
        *)           echo "Unknown flag: $1" >&2 ; exit 2 ;;
    esac
done

if [[ $# -lt 1 ]]; then
    echo "No command supplied. Use --help." >&2
    exit 2
fi

cd "$REPO_ROOT"

# Log sandbox setup to stderr.
>&2 echo "[sandbox_sim.sh] cwd=$REPO_ROOT mem_kb=$MEM_KB wall_s=$WALL_S net=$NET"
>&2 echo "[sandbox_sim.sh] cmd=$*"

# Build the inner command that executes under resource limits.
# ulimit -v sets virtual memory; this is the Linux-equivalent of
# limit_resources=True's RLIMIT_RSS cap. Some kernels enforce this more
# aggressively than others but it's a reasonable ceiling.
inner_cmd='ulimit -v '"$MEM_KB"' ; ulimit -c 0 ; ulimit -f 524288 ; exec "$@"'

rc=0
use_unshare=0
if [[ "$NET" -eq 1 ]] && command -v unshare >/dev/null 2>&1; then
    if unshare -r -n true 2>/dev/null; then
        use_unshare=1
    fi
fi

if [[ "$use_unshare" -eq 1 ]]; then
    >&2 echo "[sandbox_sim.sh] using unshare -r -n (network disabled)"
    unshare -r -n -- \
        timeout --signal=TERM --kill-after=5s "${WALL_S}s" \
        bash -c "$inner_cmd" _ "$@" || rc=$?
else
    >&2 echo "[sandbox_sim.sh] no netns — running under ulimit+timeout only"
    timeout --signal=TERM --kill-after=5s "${WALL_S}s" \
        bash -c "$inner_cmd" _ "$@" || rc=$?
fi

>&2 echo "[sandbox_sim.sh] exit=$rc"
exit "$rc"
