"""Image OSINT stubs and recommendations."""

from __future__ import annotations

from pathlib import Path
from typing import List

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
