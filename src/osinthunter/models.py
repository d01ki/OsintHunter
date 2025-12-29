"""Core data models for the OSINT Hunter agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProblemInput:
    """Normalized problem input for the agent."""

    text: str = ""
    urls: List[str] = field(default_factory=list)
    image_paths: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence:
    """Structured finding captured by the agent."""

    source: str
    fact: str
    confidence: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanStep:
    """Represents a planned action for the agent."""

    title: str
    tool: str
    rationale: str


@dataclass
class AgentResult:
    """Final output bundle returned by the agent."""

    plan: List[PlanStep]
    evidence: List[Evidence]
    flag_candidates: List[str] = field(default_factory=list)
    notes: Optional[str] = None
