"""Image OSINT stubs and LangChain-compatible wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_core.tools import BaseTool

from .base import Tool
from ..models import Evidence, ProblemInput


class ImageOSINTTool(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="image-osint",
            description="Flag next steps for image EXIF/OCR/geolocation",
            requires_network=False,
        )

    def run(self, problem: ProblemInput) -> List[Evidence]:
        evidence: List[Evidence] = []
        for path_str in problem.image_paths:
            path = Path(path_str)
            fact = f"Inspect {path.name} with exiftool and OCR; check for landmarks"
            evidence.append(Evidence(source=self.name, fact=fact, confidence=0.6))

        if not evidence:
            evidence.append(Evidence(source=self.name, fact="No images provided", confidence=0.2))

        return evidence


class ImageInspectTool(BaseTool):
    """LangChain BaseTool wrapper for image OSINT guidance."""

    name = "image-inspect"
    description = "Plan EXIF/OCR/landmark checks for provided image hints"

    def _run(self, query: str) -> str:
        # Deterministic guidance for offline use.
        return "Inspect image with exiftool, run OCR, and check landmarks via reverse image search"

    async def _arun(self, query: str) -> str:  # pragma: no cover - async not used
        return self._run(query)
