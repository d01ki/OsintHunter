"""SNS-focused heuristic tool."""

from __future__ import annotations

import re
from typing import List

from .base import Tool
from ..models import Evidence, ProblemInput


class SNSOSINTTool(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="sns-osint",
            description="Suggest cross-platform checks for discovered handles",
            requires_network=True,
        )

    def run(self, problem: ProblemInput) -> List[Evidence]:
        text = problem.text or ""
        handles = set(re.findall(r"@([A-Za-z0-9_]{3,32})", text))

        evidence: List[Evidence] = []
        for handle in handles:
            fact = f"Check handle '{handle}' on X/Instagram/GitHub/Reddit"
            evidence.append(Evidence(source=self.name, fact=fact, confidence=0.55))

        if not evidence:
            evidence.append(Evidence(source=self.name, fact="No handles found for SNS pivot", confidence=0.2))

        return evidence
