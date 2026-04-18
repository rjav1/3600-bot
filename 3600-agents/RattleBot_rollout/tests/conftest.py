"""Bootstrap sys.path so pytest collection can import `game` and
`RattleBot_rollout` without the caller having to set PYTHONPATH.
"""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
for _p in (
    os.path.join(_REPO_ROOT, "engine"),
    os.path.join(_REPO_ROOT, "3600-agents"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)
