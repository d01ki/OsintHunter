"""Web search planner stub (API-agnostic)."""

from __future__ import annotations

from typing import List

from .base import Tool
from ..models import Evidence, ProblemInput


class WebSearchTool(Tool):
    def __init__(self, serpapi_api_key: str | None = None, bing_api_key: str | None = None, allow_network: bool = False) -> None:
        super().__init__(
            name="web-search",
            description="Propose or execute web searches for OSINT leads",
            requires_network=True,
        )
        self.serpapi_api_key = serpapi_api_key
        self.bing_api_key = bing_api_key
        self.allow_network = allow_network

    def run(self, problem: ProblemInput) -> List[Evidence]:
        keywords = problem.text.split()[:8]
        base_query = " ".join(keywords) if keywords else "osint ctf"

        if not self.allow_network or not (self.serpapi_api_key or self.bing_api_key):
            fact = f"Search not executed (network disabled). Suggested query: '{base_query}'"
            return [Evidence(source=self.name, fact=fact, confidence=0.25)]

        # Placeholder for actual search integration to keep the skeleton offline-friendly.
        fact = f"Search executed with query: '{base_query}'. Integrate API client to fetch results."
        return [Evidence(source=self.name, fact=fact, confidence=0.4)]
