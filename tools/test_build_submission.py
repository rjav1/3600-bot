"""Tests for tools/build_submission.py (T-40d).

Run via pytest:
    python3 -m pytest tools/test_build_submission.py -v
"""

from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "tools"))

from build_submission import (  # noqa: E402
    build_submission,
    _strip_numba,
    _NUMBA_FALSE_LINE,
)


# --- Fixtures -----------------------------------------------------------


@pytest.fixture
def fake_agent_dir(tmp_path: Path) -> Path:
    """Build a minimal agent package mirroring RattleBot shape so we can
    test the zip pipeline without depending on live source files.
    """
    agent = tmp_path / "FakeAgent"
    agent.mkdir()
    (agent / "__init__.py").write_text("from .agent import PlayerAgent\n")
    (agent / "agent.py").write_text(
        "class PlayerAgent:\n"
        "    def __init__(self, *a, **k): pass\n"
        "    def play(self, *a, **k): return None\n"
        "    def commentate(self): return 'fake'\n"
    )
    (agent / "heuristic.py").write_text(
        "import os\n"
        "\n"
        "# comment preceding the toggle\n"
        '_USE_NUMBA: bool = os.environ.get("FAKE_NUMBA", "0") == "1"\n'
        "\n"
        "def evaluate():\n"
        "    return 0.0\n"
    )
    (agent / "time_mgr.py").write_text("# time mgr placeholder\n")
    # excluded paths
    (agent / "__pycache__").mkdir()
    (agent / "__pycache__" / "agent.cpython-313.pyc").write_bytes(b"\x00\x01")
    tests_dir = agent / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_agent.py").write_text("def test_ok(): assert True\n")
    (agent / "agent.pyc").write_bytes(b"\x00\x01")
    return agent


@pytest.fixture
def weights_file(tmp_path: Path) -> Path:
    w = tmp_path / "weights_test.json"
    w.write_text(json.dumps([1.0, 2.0, 3.0]))
    return w


# --- Tests --------------------------------------------------------------


def test_build_without_weights_excludes_weights_json(
    fake_agent_dir: Path, tmp_path: Path
):
    out = tmp_path / "out"
    result = build_submission(
        name="FakeBot",
        source_dir=fake_agent_dir,
        out_dir=out,
        weights=None,
        strip_numba=False,
        candidates_md=None,
        now="20260101_000000",
    )
    assert result.zip_path.exists()
    with zipfile.ZipFile(result.zip_path) as zf:
        names = set(zf.namelist())
    assert "FakeAgent/weights.json" not in names
    assert "FakeAgent/agent.py" in names
    assert "FakeAgent/__init__.py" in names


def test_build_with_weights_places_sibling_at_depth_1(
    fake_agent_dir: Path, weights_file: Path, tmp_path: Path
):
    out = tmp_path / "out"
    result = build_submission(
        name="FakeBot",
        source_dir=fake_agent_dir,
        out_dir=out,
        weights=weights_file,
        strip_numba=False,
        candidates_md=None,
        now="20260101_000000",
    )
    with zipfile.ZipFile(result.zip_path) as zf:
        names = set(zf.namelist())
        raw = zf.read("FakeAgent/weights.json")
    assert "FakeAgent/weights.json" in names
    assert json.loads(raw.decode("utf-8")) == [1.0, 2.0, 3.0]
    assert result.weights_path == weights_file.resolve()


def test_strip_numba_forces_false_in_heuristic(
    fake_agent_dir: Path, tmp_path: Path
):
    out = tmp_path / "out"
    result = build_submission(
        name="FakeBot",
        source_dir=fake_agent_dir,
        out_dir=out,
        weights=None,
        strip_numba=True,
        candidates_md=None,
        now="20260101_000000",
    )
    with zipfile.ZipFile(result.zip_path) as zf:
        body = zf.read("FakeAgent/heuristic.py").decode("utf-8")
    assert _NUMBA_FALSE_LINE in body, body
    assert "os.environ.get" not in body.splitlines()[3], (
        "numba toggle was not replaced on the declaration line"
    )
    assert result.numba_stripped is True


def test_sha256_and_size_recorded(
    fake_agent_dir: Path, tmp_path: Path
):
    out = tmp_path / "out"
    result = build_submission(
        name="FakeBot",
        source_dir=fake_agent_dir,
        out_dir=out,
        weights=None,
        strip_numba=False,
        candidates_md=None,
        now="20260101_000000",
    )
    disk_bytes = result.zip_path.read_bytes()
    assert result.size_bytes == len(disk_bytes)
    import hashlib
    assert result.sha256 == hashlib.sha256(disk_bytes).hexdigest()
    assert len(result.sha256) == 64


def test_tests_and_pycache_excluded(
    fake_agent_dir: Path, tmp_path: Path
):
    out = tmp_path / "out"
    result = build_submission(
        name="FakeBot",
        source_dir=fake_agent_dir,
        out_dir=out,
        weights=None,
        strip_numba=False,
        candidates_md=None,
        now="20260101_000000",
    )
    with zipfile.ZipFile(result.zip_path) as zf:
        names = zf.namelist()
    # nothing from tests/, __pycache__/, or *.pyc should be present
    for n in names:
        assert "tests/" not in n, f"tests leaked: {n}"
        assert "__pycache__" not in n, f"__pycache__ leaked: {n}"
        assert not n.endswith(".pyc"), f".pyc leaked: {n}"


def test_candidates_md_append(
    fake_agent_dir: Path, tmp_path: Path, weights_file: Path
):
    out = tmp_path / "out"
    md = tmp_path / "SUBMISSION_CANDIDATES.md"
    md.write_text("# SUBMISSION_CANDIDATES\n")
    result = build_submission(
        name="FakeBot_v03",
        source_dir=fake_agent_dir,
        out_dir=out,
        weights=weights_file,
        strip_numba=True,
        candidates_md=md,
        now="20260101_000000",
    )
    text = md.read_text(encoding="utf-8")
    assert "Auto-build log" in text
    assert "FakeBot_v03" in text
    assert result.sha256 in text
    assert "numba_stripped=True" in text
    assert "weights=weights_test.json" in text


def test_strip_numba_idempotent_on_already_false_line(tmp_path: Path):
    body = (
        "import os\n\n"
        "_USE_NUMBA: bool = False\n"
        "def f(): pass\n"
    )
    rewritten = _strip_numba(body)
    assert rewritten.count(_NUMBA_FALSE_LINE) == 1


def test_strip_numba_raises_when_declaration_missing(tmp_path: Path):
    body = "print('no numba toggle here')\n"
    with pytest.raises(RuntimeError, match="no `_USE_NUMBA"):
        _strip_numba(body)


def test_zip_layout_depth_one(fake_agent_dir: Path, tmp_path: Path):
    """Every arcname must be `<agent_dir>/<file>` — no deeper paths."""
    out = tmp_path / "out"
    result = build_submission(
        name="FakeBot",
        source_dir=fake_agent_dir,
        out_dir=out,
        weights=None,
        strip_numba=False,
        candidates_md=None,
        now="20260101_000000",
    )
    with zipfile.ZipFile(result.zip_path) as zf:
        for name in zf.namelist():
            parts = name.split("/")
            assert len(parts) == 2, f"bad depth: {name}"
            assert parts[0] == "FakeAgent"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
