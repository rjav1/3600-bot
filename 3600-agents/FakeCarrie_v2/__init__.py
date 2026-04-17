"""FakeCarrie_v2 — harder proxy for the staff Carrie reference bot.

See `docs/plan/FAKE_CARRIE_V2.md` for design + smoke-test results.
"""

from .agent import PlayerAgent
from . import rat_belief, search, heuristic, time_mgr, zobrist

__all__ = [
    "PlayerAgent",
    "rat_belief",
    "search",
    "heuristic",
    "time_mgr",
    "zobrist",
]
