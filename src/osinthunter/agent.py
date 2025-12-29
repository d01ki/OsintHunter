"""Single-agent MVP orchestrating the OSINT toolchain."""

from __future__ import annotations

import re
from typing import Iterable, List, Sequence

from .config import OSINTConfig, load_config
from .memory import EvidenceStore
from .models import AgentResult, PlanStep, ProblemInput
from .tools import (
    GeolocationTool,
    ImageOSINTTool,
    SNSOSINTTool,
    TextAnalysisTool,
    URLInvestigationTool,
    WebSearchTool,
)
from .tools.base import Tool


class OSINTAgent:
    def __init__(self, config: OSINTConfig | None = None, tools: Sequence[Tool] | None = None) -> None:
        self.config = config or load_config()
        self.tools: List[Tool] = list(tools) if tools is not None else self._default_tools()

    def _default_tools(self) -> List[Tool]:
        return [
            TextAnalysisTool(),
            URLInvestigationTool(),
            SNSOSINTTool(),
            WebSearchTool(
                serpapi_api_key=self.config.serpapi_api_key,
                bing_api_key=self.config.bing_api_key,
                allow_network=self.config.allow_network,
            ),
            GeolocationTool(),
            ImageOSINTTool(),
        ]

    def plan(self, problem: ProblemInput) -> List[PlanStep]:
        return [
            PlanStep(title="Extract surface entities", tool="text-analysis", rationale="Identify URLs, handles, or coordinates"),
            PlanStep(title="Parse URL anatomy", tool="url-investigation", rationale="Understand domains and pivot points"),
            PlanStep(title="Cross-platform handles", tool="sns-osint", rationale="Search for the same username across SNS"),
            PlanStep(title="Web search", tool="web-search", rationale="Gather open web context"),
            PlanStep(title="Geolocation", tool="geolocation", rationale="Resolve coordinates or location hints"),
            PlanStep(title="Image inspection", tool="image-osint", rationale="Check EXIF/OCR and landmarks"),
        ]

    def run(self, problem: ProblemInput) -> AgentResult:
        plan = self.plan(problem)
        store = EvidenceStore()

        tool_index = {tool.name: tool for tool in self.tools}
        for step in plan:
            tool = tool_index.get(step.tool)
            if not tool:
                continue
            results = tool.run(problem)
            store.extend(results)

        flag_candidates = self._extract_flags(problem.text, [ev.fact for ev in store.all()])

        return AgentResult(
            plan=plan,
            evidence=store.all(),
            flag_candidates=flag_candidates,
            notes="Toggle network/API keys in env to enable live searches.",
        )

    def _extract_flags(self, *sources: Iterable[str]) -> List[str]:
        candidates: List[str] = []
        for source in sources:
            text_block = " ".join(source)
            candidates.extend(re.findall(r"flag\{[^}]+\}", text_block, flags=re.IGNORECASE))
        return sorted(set(candidates))
