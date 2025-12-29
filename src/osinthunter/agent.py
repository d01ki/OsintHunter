"""Single-agent MVP orchestrating the OSINT toolchain.

LangGraph 版の多段エージェントは langgraph_runner.build_langgraph_app() を参照。
"""

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
from .langgraph_runner import build_langgraph_app


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
        # デフォルトは LangGraph を使う（鍵が無くてもオフライン動作）
        app = build_langgraph_app(self.config).compile()
        state = {
            "input": problem.text,
            "urls": problem.urls,
            "images": problem.image_paths,
            "plan": [step.title for step in self.plan(problem)],
            "evidence": [],
            "flags": [],
            "loop": 0,
            "stop": False,
        }
        final_state = app.invoke(state)

        evidence = [
            Evidence(source=ev.get("source", ""), fact=ev.get("fact", ""), confidence=ev.get("confidence", 0.0), metadata=ev.get("metadata", {}))
            for ev in final_state.get("evidence", [])
        ]
        flag_candidates = final_state.get("flags", []) or self._extract_flags(problem.text)

        return AgentResult(
            plan=self.plan(problem),
            evidence=evidence,
            flag_candidates=flag_candidates,
            notes="LangGraph pipeline executed (planner/tools/validator/flagger).",
        )

    def _extract_flags(self, *sources: Iterable[str]) -> List[str]:
        candidates: List[str] = []
        for source in sources:
            text_block = " ".join(source)
            candidates.extend(re.findall(r"flag\{[^}]+\}", text_block, flags=re.IGNORECASE))
        return sorted(set(candidates))
