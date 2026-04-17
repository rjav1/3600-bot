"""FakeAlbert — local replica of staff reference bot Albert.

Per assignment.pdf §9: "expectiminimax-based bot with a very simple
heuristic and a hidden markov model to track the rat." Best-effort
proxy for local measurement; NOT gold-standard Albert.
"""

from .agent import PlayerAgent

__all__ = ["PlayerAgent"]
