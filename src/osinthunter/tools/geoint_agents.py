"""GEOINT/reverse image helper agents."""

from __future__ import annotations

from typing import List

from .base import Agent
from ..models import Evidence, ProblemInput


class EarthViewAgent(Agent):
    def __init__(self) -> None:
        super().__init__(name="earth-view", description="Google Earth/Street View guidance", requires_network=False)

    def run(self, problem: ProblemInput) -> List[Evidence]:
        return [Evidence(source=self.name, fact="Pivot to Google Earth/Street View for landmarks and building shapes", confidence=0.3)]


class YandexReverseImageAgent(Agent):
    def __init__(self) -> None:
        super().__init__(name="yandex-images", description="Reverse image search guidance via Yandex", requires_network=False)

    def run(self, problem: ProblemInput) -> List[Evidence]:
        if not problem.image_paths:
            return [Evidence(source=self.name, fact="No images provided for Yandex reverse search", confidence=0.2)]
        facts: List[Evidence] = []
        for img in problem.image_paths[:3]:
            facts.append(Evidence(source=self.name, fact=f"Upload {img} to https://yandex.com/images for reverse search", confidence=0.3))
        return facts
