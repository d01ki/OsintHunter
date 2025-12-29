"""SOCMINT-style helper agents."""

from __future__ import annotations

from typing import List

from .base import Agent
from ..models import Evidence, ProblemInput


class SocialSearchAgent(Agent):
    def __init__(self) -> None:
        super().__init__(name="social-searcher", description="Cross-SNS keyword/hashtag guidance", requires_network=False)

    def run(self, problem: ProblemInput) -> List[Evidence]:
        query = (problem.text or "").strip()[:80]
        if not query:
            return [Evidence(source=self.name, fact="No keywords provided for social search", confidence=0.2)]
        fact = f"Use Social Searcher or native SNS search for: {query}"
        return [Evidence(source=self.name, fact=fact, confidence=0.3)]


class SherlockAgent(Agent):
    def __init__(self) -> None:
        super().__init__(name="sherlock", description="Username presence across sites", requires_network=False)

    def run(self, problem: ProblemInput) -> List[Evidence]:
        handles = []
        # Handles are already extracted by text-analysis; here we just guide usage.
        fact = "Run: sherlock <username> --print-found (requires local tool install)"
        return [Evidence(source=self.name, fact=fact, confidence=0.35)]
