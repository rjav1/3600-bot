"""RattleBot_rollout — bold-swing 2-ply + biased Monte Carlo rollout prototype.

Per docs/audit/CONTRARIAN_APR18.md §3: replace alpha-beta with 2-ply
lookahead + biased rollouts that simulate both sides greedily, evolve
the rat belief via T each ply, and score by end-of-rollout point diff.

Insurance fork — does not edit RattleBot/. Promote only if paired scrims
show it beats v0.4.1+ head-to-head.
"""

# Local-dev fallback: if the engine's `game` package isn't already on
# sys.path (e.g. when pytest imports this package from repo root without
# a running engine), add it. Tournament runtime already has it on path,
# so this is a defensive no-op there.
import os as _os
import sys as _sys
try:
    import game  # noqa: F401
except ImportError:
    _engine = _os.path.abspath(
        _os.path.join(_os.path.dirname(__file__), "..", "..", "engine")
    )
    if _os.path.isdir(_engine) and _engine not in _sys.path:
        _sys.path.insert(0, _engine)

from .agent import PlayerAgent
from . import rat_belief, move_gen, rollout, types, zobrist

__all__ = [
    "PlayerAgent",
    "rat_belief",
    "move_gen",
    "rollout",
    "types",
    "zobrist",
]
