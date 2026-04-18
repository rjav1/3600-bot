#!/usr/bin/env bash
# archive_replays.sh — catch-up driver for docs/intel/replays/.
#
# Re-run on demand (or from a cron) to pick up any newly-finished
# scrimmages that haven't been archived yet. Idempotent: skips UUIDs
# already on disk. Exits non-zero on auth failure.
#
# Usage:
#   ./tools/archive_replays.sh            # default chunk=40
#   ./tools/archive_replays.sh --chunk 20 # override chunk size

set -eu
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CHUNK="${1:-40}"
if [ "$CHUNK" = "--chunk" ] && [ $# -ge 2 ]; then
  CHUNK="$2"
fi

python tools/scratch/archive_replays_driver.py --chunk "$CHUNK"
