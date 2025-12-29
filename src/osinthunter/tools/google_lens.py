"""Google Lens-style reverse image hints via SerpAPI where possible."""

from __future__ import annotations

from typing import List
from urllib.parse import urlparse

import httpx

from .base import Agent
from ..models import Evidence, ProblemInput


class GoogleLensAgent(Agent):
    def __init__(self, serpapi_api_key: str | None = None, allow_network: bool = False) -> None:
        super().__init__(
            name="google-lens",
            description="Reverse image suggestions using SerpAPI google_lens engine when image URLs are provided",
            requires_network=True,
        )
        self.serpapi_api_key = serpapi_api_key
        self.allow_network = allow_network

    def run(self, problem: ProblemInput) -> List[Evidence]:
        images = problem.image_paths or []
        if not images:
            return [Evidence(source=self.name, fact="No images provided for reverse search", confidence=0.2)]

        if not self.allow_network or not self.serpapi_api_key:
            return [Evidence(source=self.name, fact="Google Lens not executed (network disabled or no SerpAPI key)", confidence=0.25)]

        evidence: List[Evidence] = []
        for img in images:
            parsed = urlparse(img)
            if parsed.scheme not in {"http", "https"}:
                evidence.append(Evidence(source=self.name, fact=f"Image is not a URL: {img}. Upload to a temporary host to use Lens.", confidence=0.3))
                continue
            try:
                resp = httpx.get(
                    "https://serpapi.com/search",
                    params={"engine": "google_lens", "url": img, "api_key": self.serpapi_api_key},
                    timeout=10.0,
                )
                resp.raise_for_status()
                data = resp.json()
                visuals = (data.get("visual_matches") or [])[:3]
                if visuals:
                    for v in visuals:
                        title = v.get("title", "")
                        link = v.get("link", "")
                        fact = f"Lens match: {title} -> {link}"
                        evidence.append(Evidence(source=self.name, fact=fact, confidence=0.55))
                else:
                    evidence.append(Evidence(source=self.name, fact=f"No Lens matches for {img}", confidence=0.3))
            except Exception as exc:
                evidence.append(Evidence(source=self.name, fact=f"Lens query failed for {img}: {exc}", confidence=0.2))

        return evidence if evidence else [Evidence(source=self.name, fact="Lens produced no evidence", confidence=0.2)]
