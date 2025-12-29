"""Image OSINT stubs and LangChain-compatible wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_core.tools import BaseTool
from PIL import Image, ExifTags

from .base import Agent
from ..models import Evidence, ProblemInput


class ImageOSINTAgent(Agent):
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
            if not path.exists():
                evidence.append(Evidence(source=self.name, fact=f"File not found: {path}", confidence=0.2))
                continue

            try:
                size = path.stat().st_size
                evidence.append(
                    Evidence(
                        source=self.name,
                        fact=f"Inspect {path.name} (size={size} bytes) with EXIF/OCR/reverse image search",
                        confidence=0.62,
                        metadata={"path": str(path)},
                    )
                )
            except OSError:
                evidence.append(Evidence(source=self.name, fact=f"Inspect {path.name}", confidence=0.55))

            evidence.extend(self._extract_exif(path))

        if not evidence:
            evidence.append(Evidence(source=self.name, fact="No images provided", confidence=0.2))

        return evidence

    def _extract_exif(self, path: Path) -> List[Evidence]:
        facts: List[Evidence] = []
        try:
            with Image.open(path) as img:
                info = img._getexif() or {}
                if not info:
                    return facts
                tag_map = {ExifTags.TAGS.get(k, k): v for k, v in info.items()}
                if dt := tag_map.get("DateTimeOriginal"):
                    facts.append(Evidence(source=self.name, fact=f"EXIF DateTimeOriginal: {dt}", confidence=0.55))
                if cam := tag_map.get("Model"):
                    facts.append(Evidence(source=self.name, fact=f"Camera model: {cam}", confidence=0.45))
                if gps := tag_map.get("GPSInfo"):
                    gps_data = self._gps_to_degrees(gps)
                    if gps_data:
                        lat, lon = gps_data
                        facts.append(
                            Evidence(
                                source=self.name,
                                fact=f"GPS from EXIF: {lat:.6f}, {lon:.6f}",
                                confidence=0.7,
                                metadata={"lat": lat, "lon": lon},
                            )
                        )
        except Exception:
            facts.append(Evidence(source=self.name, fact=f"EXIF parsing failed for {path.name}", confidence=0.2))
        return facts

    def _gps_to_degrees(self, gps_info) -> tuple | None:
        try:
            gps_tags = {}
            for key, val in gps_info.items():
                name = ExifTags.GPSTAGS.get(key, key)
                gps_tags[name] = val

            def _to_deg(value):
                d = value[0][0] / value[0][1]
                m = value[1][0] / value[1][1]
                s = value[2][0] / value[2][1]
                return d + (m / 60.0) + (s / 3600.0)

            lat_ref = gps_tags.get("GPSLatitudeRef")
            lon_ref = gps_tags.get("GPSLongitudeRef")
            lat = gps_tags.get("GPSLatitude")
            lon = gps_tags.get("GPSLongitude")
            if lat and lon and lat_ref and lon_ref:
                lat_val = _to_deg(lat) * (1 if lat_ref in ["N", "n"] else -1)
                lon_val = _to_deg(lon) * (1 if lon_ref in ["E", "e"] else -1)
                return (lat_val, lon_val)
        except Exception:
            return None
        return None


# Backward compatibility
ImageOSINTTool = ImageOSINTAgent


class ImageInspectTool(BaseTool):
    """LangChain BaseTool wrapper for image OSINT guidance."""

    name: str = "image-inspect"
    description: str = "Plan EXIF/OCR/landmark checks for provided image hints"

    def _run(self, query: str) -> str:
        # Deterministic guidance for offline use.
        return "Inspect image with exiftool, run OCR, and check landmarks via reverse image search"

    async def _arun(self, query: str) -> str:  # pragma: no cover - async not used
        return self._run(query)
