"""RattleBot — primary bot package.

Entry point: `PlayerAgent` from `.agent`. Submodules re-exported for
convenience and to match BOT_STRATEGY.md v1.1 §3 module layout.
"""

from .agent import PlayerAgent
from . import rat_belief, search, heuristic, move_gen, time_mgr, zobrist, types

__all__ = [
    "PlayerAgent",
    "rat_belief",
    "search",
    "heuristic",
    "move_gen",
    "time_mgr",
    "zobrist",
    "types",
]
