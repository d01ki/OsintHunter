"""URL structure inspection and lightweight enrichment."""

from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import List

from .base import Tool
from ..models import Evidence, ProblemInput


class URLInvestigationTool(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="url-investigation",
            description="Parse URLs and highlight domains, paths, and potential pivots",
            requires_network=False,
        )

    def run(self, problem: ProblemInput) -> List[Evidence]:
        urls = set(problem.urls)
        urls.update(re.findall(r"https?://[^\s]+", problem.text or ""))

        evidence: List[Evidence] = []
        for url in urls:
            parsed = urlparse(url)
            parts = [f"domain={parsed.netloc}"]
            if parsed.path and parsed.path != "/":
                parts.append(f"path={parsed.path}")
            if parsed.query:
                parts.append("query parameters present")
            fact = f"URL analysis: {url} | " + ", ".join(parts)
            evidence.append(Evidence(source=self.name, fact=fact, confidence=0.6))

        return evidence
