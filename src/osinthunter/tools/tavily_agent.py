"""Tavily-powered web search agent."""

from __future__ import annotations

from typing import List

from tavily import TavilyClient

from .base import Agent
from ..models import Evidence, ProblemInput


class TavilySearchAgent(Agent):
    def __init__(self, api_key: str | None = None, allow_network: bool = False) -> None:
        super().__init__(
            name="tavily-search",
            description="High-signal web search using Tavily",
            requires_network=True,
        )
        self.api_key = api_key
        self.allow_network = allow_network
        self.client = TavilyClient(api_key=api_key) if api_key and allow_network else None

    def run(self, problem: ProblemInput) -> List[Evidence]:
        query = (problem.text or "").strip()
        if not query:
            return [Evidence(source=self.name, fact="No query provided", confidence=0.2)]

        if not self.allow_network or not self.client:
            return [Evidence(source=self.name, fact=f"Tavily not executed (network disabled). Suggested query: '{query[:80]}'", confidence=0.25)]

        try:
            resp = self.client.search(query=query, max_results=3)
            results = resp.get("results", []) or []
            evidence: List[Evidence] = []
            for item in results[:3]:
                title = item.get("title", "")
                url = item.get("url", "")
                snippet = item.get("content", "")
                fact = f"Tavily: {title} -> {url} | {snippet}"
                evidence.append(Evidence(source=self.name, fact=fact, confidence=0.6))
            if evidence:
                return evidence
            return [Evidence(source=self.name, fact=f"Tavily returned no results for '{query[:80]}'", confidence=0.3)]
        except Exception as exc:
            return [Evidence(source=self.name, fact=f"Tavily search failed: {exc}", confidence=0.2)]
