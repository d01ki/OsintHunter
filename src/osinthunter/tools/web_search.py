"""Web search planner stub (API-agnostic)."""

from __future__ import annotations

from typing import List

import httpx

from .base import Agent
from ..models import Evidence, ProblemInput


class WebSearchAgent(Agent):
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

        evidence: List[Evidence] = []

        if self.serpapi_api_key:
            try:
                resp = httpx.get(
                    "https://serpapi.com/search",
                    params={"engine": "google", "q": base_query, "api_key": self.serpapi_api_key, "num": 3},
                    timeout=8.0,
                )
                resp.raise_for_status()
                data = resp.json()
                for item in (data.get("organic_results") or [])[:3]:
                    title = item.get("title", "")
                    link = item.get("link", "")
                    snippet = item.get("snippet", "")
                    fact = f"SERP: {title} -> {link} | {snippet}"
                    evidence.append(Evidence(source=self.name, fact=fact, confidence=0.55))
            except Exception as exc:
                evidence.append(Evidence(source=self.name, fact=f"SerpAPI search failed: {exc}", confidence=0.2))

        elif self.bing_api_key:
            try:
                resp = httpx.get(
                    "https://api.bing.microsoft.com/v7.0/search",
                    params={"q": base_query, "count": 3},
                    headers={"Ocp-Apim-Subscription-Key": self.bing_api_key},
                    timeout=8.0,
                )
                resp.raise_for_status()
                data = resp.json()
                for item in (data.get("webPages", {}).get("value", []) or [])[:3]:
                    title = item.get("name", "")
                    link = item.get("url", "")
                    snippet = item.get("snippet", "")
                    fact = f"Bing: {title} -> {link} | {snippet}"
                    evidence.append(Evidence(source=self.name, fact=fact, confidence=0.55))
            except Exception as exc:
                evidence.append(Evidence(source=self.name, fact=f"Bing search failed: {exc}", confidence=0.2))

        if not evidence:
            return [Evidence(source=self.name, fact=f"Search attempted but no results. Query: '{base_query}'", confidence=0.3)]

        return evidence


# Backward compatibility
WebSearchTool = WebSearchAgent
