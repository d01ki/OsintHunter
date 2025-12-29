"""Lightweight text analysis for OSINT hints."""

from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import List

from .base import Tool
from ..models import Evidence, ProblemInput


class TextAnalysisTool(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="text-analysis",
            description="Extract entities (urls, emails, usernames, coordinates) from text",
            requires_network=False,
        )

    def run(self, problem: ProblemInput) -> List[Evidence]:
        text = problem.text or ""
        if not text.strip():
            return []

        evidence: List[Evidence] = []

        url_matches = set(re.findall(r"https?://[^\s]+", text))
        for raw_url in url_matches:
            parsed = urlparse(raw_url)
            fact = f"URL found: {raw_url} (domain={parsed.netloc})"
            evidence.append(Evidence(source=self.name, fact=fact, confidence=0.7))

        email_matches = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))
        for email in email_matches:
            evidence.append(Evidence(source=self.name, fact=f"Email found: {email}", confidence=0.6))

        username_matches = set(re.findall(r"@([A-Za-z0-9_]{3,32})", text))
        for username in username_matches:
            evidence.append(
                Evidence(
                    source=self.name,
                    fact=f"Possible handle: {username}",
                    confidence=0.55,
                    metadata={"username": username},
                )
            )

        coord_matches = set(re.findall(r"(-?\d{1,3}\.\d{3,}),\s*(-?\d{1,3}\.\d{3,})", text))
        for lat, lon in coord_matches:
            evidence.append(
                Evidence(
                    source=self.name,
                    fact=f"Possible coordinates: {lat}, {lon}",
                    confidence=0.65,
                    metadata={"lat": lat, "lon": lon},
                )
            )

        return evidence
