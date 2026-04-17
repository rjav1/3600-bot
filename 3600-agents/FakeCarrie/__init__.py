"""FakeCarrie — local replica of staff reference bot Carrie.

Per assignment.pdf §9: same expectiminimax+HMM structure as Albert,
but with a more advanced heuristic that estimates cell potential ×
distance from the bot. Best-effort proxy for local measurement;
NOT gold-standard Carrie.
"""

from .agent import PlayerAgent

__all__ = ["PlayerAgent"]
