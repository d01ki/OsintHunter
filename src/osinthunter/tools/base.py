"""Base tool abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..models import Evidence, ProblemInput


@dataclass
class Tool:
    name: str
    description: str
    requires_network: bool = False

    def run(self, problem: ProblemInput) -> List[Evidence]:
        raise NotImplementedError("Tool.run must be implemented by subclasses")
