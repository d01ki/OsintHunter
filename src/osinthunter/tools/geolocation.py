"""Geolocation helper tool."""

from __future__ import annotations

import re
from typing import List

from .base import Tool
from ..models import Evidence, ProblemInput


class GeolocationTool(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="geolocation",
            description="Suggest location pivots from text or coordinates",
            requires_network=True,
        )

    def run(self, problem: ProblemInput) -> List[Evidence]:
        text = problem.text or ""
        coords = set(re.findall(r"(-?\d{1,3}\.\d{3,}),\s*(-?\d{1,3}\.\d{3,})", text))

        evidence: List[Evidence] = []
        for lat, lon in coords:
            fact = f"Map lookup for coordinates {lat}, {lon}"
            evidence.append(Evidence(source=self.name, fact=fact, confidence=0.65))

        if not evidence:
            evidence.append(Evidence(source=self.name, fact="No coordinates detected; use landmarks or language cues", confidence=0.3))

        return evidence
