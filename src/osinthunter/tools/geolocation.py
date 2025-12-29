"""Geolocation helper tool and LangChain-compatible wrapper."""

from __future__ import annotations

import re
from typing import List

from langchain_core.tools import BaseTool

from .base import Agent
from ..models import Evidence, ProblemInput


class GeolocationAgent(Agent):
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


# Backward compatibility
GeolocationTool = GeolocationAgent


class GeolocationLookupTool(BaseTool):
    """LangChain BaseTool wrapper for geolocation hints."""

    name: str = "geolocation"
    description: str = "Suggest location pivots from coordinates or text"

    def _run(self, query: str) -> str:
        # Simple deterministic guidance; this is safe for offline use.
        coords = re.findall(r"(-?\d{1,3}\.\d{3,}),\s*(-?\d{1,3}\.\d{3,})", query)
        if coords:
            parts = [f"Map lookup for coordinates {lat}, {lon}" for lat, lon in coords]
            return " | ".join(parts)
        return "No coordinates detected; pivot on landmarks or language cues"

    async def _arun(self, query: str) -> str:  # pragma: no cover - async not used
        return self._run(query)
