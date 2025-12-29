"""Base agent abstractions (previously called tools)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..models import Evidence, ProblemInput


@dataclass
class Agent:
    """Lightweight agent interface."""

    name: str
    description: str
    requires_network: bool = False

    def run(self, problem: ProblemInput) -> List[Evidence]:
        raise NotImplementedError("Agent.run must be implemented by subclasses")


# Backward compatibility alias
Tool = Agent
