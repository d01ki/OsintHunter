"""Simple in-memory evidence store."""

from __future__ import annotations

from typing import List, Sequence

from .models import Evidence


class EvidenceStore:
    def __init__(self) -> None:
        self._items: List[Evidence] = []

    def add(self, evidence: Evidence) -> None:
        if evidence.fact and evidence not in self._items:
            self._items.append(evidence)

    def extend(self, evidence_list: Sequence[Evidence]) -> None:
        for ev in evidence_list:
            self.add(ev)

    def all(self) -> List[Evidence]:
        return list(self._items)

    def by_source(self, source: str) -> List[Evidence]:
        return [ev for ev in self._items if ev.source == source]

    def summary(self) -> str:
        parts = [f"- ({ev.confidence:.2f}) {ev.source}: {ev.fact}" for ev in self._items]
        return "\n".join(parts)
