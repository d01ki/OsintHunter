"""URL structure inspection and lightweight enrichment."""

from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import List

from .base import Agent
from ..models import Evidence, ProblemInput


class URLInvestigationAgent(Agent):
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
            parts = []
            hostname = parsed.netloc or ""
            if hostname:
                parts.append(f"domain={hostname}")
                if re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", hostname):
                    parts.append("host_is_ipv4")
            if parsed.path and parsed.path != "/":
                parts.append(f"path={parsed.path}")
                path_lower = parsed.path.lower()
                for ext in (".zip", ".rar", ".7z", ".gz", ".tar", ".bak"):
                    if path_lower.endswith(ext):
                        parts.append(f"archive_extension={ext}")
                        break
            if parsed.query:
                parts.append("query parameters present")
            if not parts:
                parts.append("no notable components")

            fact = f"URL analysis: {url} | " + ", ".join(parts)
            confidence = 0.65 if len(parts) > 1 else 0.55
            evidence.append(Evidence(source=self.name, fact=fact, confidence=confidence))

        return evidence


# Backward compatibility
URLInvestigationTool = URLInvestigationAgent
