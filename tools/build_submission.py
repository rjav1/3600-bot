"""Automated submission-zip builder for RattleBot (T-40d).

Problem: every submission to bytefight.org has been hand-built. We've had
bugs (forgot `tests/` exclusion, had to manually flip `_USE_NUMBA`,
forgot to rename `weights_v03.json` -> `weights.json`). This tool
eliminates all of those.

Usage:
  python tools/build_submission.py \\
    --name RattleBot_v03_tuned \\
    --source-dir 3600-agents/RattleBot \\
    --weights 3600-agents/RattleBot/weights_v03.json \\
    --strip-numba \\
    --out C:/Users/rahil/AppData/Local/Temp/submissions

Behavior:
- Reads `--source-dir`. Excludes `tests/`, `__pycache__/`, and `*.pyc`.
  Keeps every `.py` at the top level of the agent directory.
- If `--weights` is given: copies the JSON into the zip as
  `weights.json` at depth 1 (sibling of `agent.py`) so the agent's
  `_load_tuned_weights()` sibling-file lookup fires.
- If `--strip-numba` is given: rewrites `heuristic.py` in a temp copy,
  replacing the `_USE_NUMBA: bool = ...` declaration line with
  `_USE_NUMBA: bool = False`. Then adds the stripped copy to the zip.
- Zip layout: `<name>/*.py` + optional `<name>/weights.json` at depth 1.
  `<name>` is the agent directory basename (so `PlayerAgent` imports
  as `<name>.agent:PlayerAgent` on the tournament machine).
- Computes SHA256 + size of the final zip.
- Writes to `<out>/<name>_<YYYYMMDD_HHMMSS>.zip`.
- Prints `python -m zipfile -l` equivalent for quick visual verification.
- Appends a row to `docs/plan/SUBMISSION_CANDIDATES.md` §1 with
  name / timestamp / SHA256 / size / weights path / numba-stripped flag.

Testing: `tools/test_build_submission.py`.

Deliverable scope:
- NEW: tools/build_submission.py (this file)
- NEW: tools/test_build_submission.py
- MOD (at runtime): docs/plan/SUBMISSION_CANDIDATES.md (a single row appended
  to §1 per invocation)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Paths / constants

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBMISSION_CANDIDATES_MD = REPO_ROOT / "docs" / "plan" / "SUBMISSION_CANDIDATES.md"

_EXCLUDE_DIRS = {"tests", "__pycache__", ".pytest_cache"}
_EXCLUDE_SUFFIXES = (".pyc", ".pyo")

_NUMBA_DECL_RE = re.compile(
    r"^(\s*)_USE_NUMBA\s*:\s*bool\s*=\s*.*$", re.MULTILINE
)
_NUMBA_FALSE_LINE = "_USE_NUMBA: bool = False"


# ---------------------------------------------------------------------------
# Build result

@dataclass(frozen=True)
class BuildResult:
    name: str
    zip_path: Path
    sha256: str
    size_bytes: int
    weights_path: Optional[Path]
    numba_stripped: bool
    timestamp: str  # YYYYMMDD_HHMMSS
    entries: List[str]  # sorted list of zip entry names


# ---------------------------------------------------------------------------
# Core build

def _collect_source_files(source_dir: Path) -> List[Path]:
    """Return the list of .py files in `source_dir` that should ship.

    Top-level .py files only (no recursion into `tests/` / `__pycache__`).
    `__init__.py` is included. Files are returned sorted by name for
    reproducible zip ordering.
    """
    if not source_dir.is_dir():
        raise FileNotFoundError(f"source_dir not found: {source_dir}")
    out: List[Path] = []
    for entry in sorted(source_dir.iterdir(), key=lambda p: p.name):
        if entry.is_dir():
            # Skip excluded dirs silently; nothing else ships from subdirs.
            continue
        if entry.suffix in _EXCLUDE_SUFFIXES:
            continue
        if entry.suffix == ".py":
            out.append(entry)
    if not out:
        raise RuntimeError(f"no .py files found in {source_dir}")
    return out


def _strip_numba(heuristic_source: str) -> str:
    """Rewrite the `_USE_NUMBA: bool = ...` declaration line to False.

    Idempotent: already-False files pass through unchanged (matches the
    regex but the substitution produces the same line).
    """
    new_source, n_subs = _NUMBA_DECL_RE.subn(
        lambda m: f"{m.group(1)}{_NUMBA_FALSE_LINE}", heuristic_source
    )
    if n_subs == 0:
        raise RuntimeError(
            "--strip-numba specified but no `_USE_NUMBA: bool = ...` "
            "declaration found in heuristic.py"
        )
    return new_source


def _load_weights(path: Path) -> bytes:
    """Load + validate a weights JSON file, return its bytes verbatim.

    Supports either a bare list or `{"weights": [...]}`. Only validates
    shape/parse; doesn't touch numeric contents (BO owns those).
    """
    raw = path.read_bytes()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"weights JSON parse error: {path}: {e}") from e
    if isinstance(parsed, dict) and "weights" in parsed:
        vec = parsed["weights"]
    else:
        vec = parsed
    if not isinstance(vec, list) or not vec:
        raise RuntimeError(
            f"weights JSON must be a non-empty list or {{'weights': [...]}}"
        )
    if not all(isinstance(x, (int, float)) for x in vec):
        raise RuntimeError("weights JSON list must contain only numbers")
    return raw


def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _timestamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _candidate_row(result: BuildResult, source_dir: Path) -> str:
    """Build a single pipe-row for SUBMISSION_CANDIDATES.md §1."""
    weights_cell = (
        result.weights_path.name if result.weights_path else "—"
    )
    return (
        f"| auto | {result.name} | `{result.zip_path.name}` | "
        f"{result.timestamp} | `{source_dir.name}/*.py` | "
        f"{result.size_bytes} | `{result.sha256}` | "
        f"weights={weights_cell}, numba_stripped={result.numba_stripped} "
        f"| auto-built |"
    )


def _append_candidate_row(
    result: BuildResult, source_dir: Path, md_path: Path = SUBMISSION_CANDIDATES_MD
) -> None:
    """Append a row to SUBMISSION_CANDIDATES.md under a `## Auto-build log`
    heading (created on first write). Left as an append rather than
    table-row insert to avoid mangling the hand-curated §1 table.
    """
    line = _candidate_row(result, source_dir)
    heading = "## Auto-build log (tools/build_submission.py)"
    try:
        existing = md_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        existing = "# SUBMISSION_CANDIDATES\n\n"
    if heading not in existing:
        existing = existing.rstrip() + f"\n\n{heading}\n\n{line}\n"
    else:
        existing = existing.rstrip() + f"\n{line}\n"
    md_path.write_text(existing, encoding="utf-8")


def build_submission(
    name: str,
    source_dir: Path,
    out_dir: Path,
    weights: Optional[Path] = None,
    strip_numba: bool = False,
    candidates_md: Optional[Path] = SUBMISSION_CANDIDATES_MD,
    now: Optional[str] = None,
) -> BuildResult:
    """Build a submission zip and return the BuildResult.

    `now` — optional timestamp override for reproducible tests.
    `candidates_md` — set to None to skip the log append (tests pass this).
    """
    source_dir = Path(source_dir).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = _collect_source_files(source_dir)
    ts = now or _timestamp()
    zip_name = f"{name}_{ts}.zip"
    zip_path = out_dir / zip_name

    agent_dir_name = source_dir.name

    # Stage payload bytes in memory first so we can compute SHA256 of the
    # final file exactly once.
    buf = io.BytesIO()
    entries: List[str] = []
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src in files:
            arcname = f"{agent_dir_name}/{src.name}"
            if strip_numba and src.name == "heuristic.py":
                body = _strip_numba(src.read_text(encoding="utf-8"))
                zf.writestr(arcname, body)
            else:
                zf.writestr(arcname, src.read_bytes())
            entries.append(arcname)
        if weights is not None:
            weights_path = Path(weights).resolve()
            weights_bytes = _load_weights(weights_path)
            arcname = f"{agent_dir_name}/weights.json"
            zf.writestr(arcname, weights_bytes)
            entries.append(arcname)
        else:
            weights_path = None

    raw = buf.getvalue()
    zip_path.write_bytes(raw)
    sha256 = _sha256_bytes(raw)
    size = len(raw)

    result = BuildResult(
        name=name,
        zip_path=zip_path,
        sha256=sha256,
        size_bytes=size,
        weights_path=weights_path,
        numba_stripped=bool(strip_numba),
        timestamp=ts,
        entries=sorted(entries),
    )

    if candidates_md is not None:
        _append_candidate_row(result, source_dir, md_path=candidates_md)

    return result


# ---------------------------------------------------------------------------
# CLI

def _print_listing(zip_path: Path) -> None:
    """Analog of `python -m zipfile -l <zip>` for verification."""
    print(f"\nZip listing ({zip_path}):")
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            print(
                f"  {info.file_size:>8} B  {info.filename}"
            )


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build a bytefight.org submission zip for a RattleBot "
                    "agent. See module docstring for full behavior."
    )
    p.add_argument("--name", required=True,
                   help="Zip base name (e.g. RattleBot_v03_tuned).")
    p.add_argument("--source-dir", required=True,
                   help="Path to the agent directory (contains agent.py).")
    p.add_argument("--out", required=True,
                   help="Output directory for the zip.")
    p.add_argument("--weights", default=None,
                   help="Optional path to a weights JSON file to bundle "
                        "as sibling `weights.json`.")
    p.add_argument("--strip-numba", action="store_true",
                   help="Force `_USE_NUMBA: bool = False` in heuristic.py.")
    p.add_argument("--no-candidates-log", action="store_true",
                   help="Skip appending to docs/plan/SUBMISSION_CANDIDATES.md.")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    weights = Path(args.weights) if args.weights else None
    md_path: Optional[Path] = (
        None if args.no_candidates_log else SUBMISSION_CANDIDATES_MD
    )
    result = build_submission(
        name=args.name,
        source_dir=Path(args.source_dir),
        out_dir=Path(args.out),
        weights=weights,
        strip_numba=args.strip_numba,
        candidates_md=md_path,
    )
    print(f"Built: {result.zip_path}")
    print(f"  size   : {result.size_bytes} bytes")
    print(f"  sha256 : {result.sha256}")
    print(f"  weights: {result.weights_path or '(none)'}")
    print(f"  numba  : stripped={result.numba_stripped}")
    _print_listing(result.zip_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
