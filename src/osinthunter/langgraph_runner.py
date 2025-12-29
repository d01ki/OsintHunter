"""LangGraph-based multi-agent orchestration (planner, tools, validator, flagger).

Note: This graph is intentionally LLM-light; it keeps deterministic heuristics so it
can run offline. Replace the planner/validator with real LLM calls when keys are
available.
"""

from __future__ import annotations

import re
from typing import Dict, List, TypedDict

from langgraph.graph import StateGraph

from .config import OSINTConfig
from .models import Evidence, PlanStep, ProblemInput
from .tools import (
    GeolocationTool,
    ImageOSINTTool,
    SNSOSINTTool,
    TextAnalysisTool,
    URLInvestigationTool,
    WebSearchTool,
)


class AgentState(TypedDict):
    input: str
    plan: List[str]
    evidence: List[Dict]
    flags: List[str]
    loop: int
    stop: bool


def _evidence_to_dict(items: List[Evidence]) -> List[Dict]:
    out: List[Dict] = []
    for ev in items:
        out.append({
            "source": ev.source,
            "fact": ev.fact,
            "confidence": ev.confidence,
            "metadata": ev.metadata,
        })
    return out


def _extract_flags_from_text(text: str) -> List[str]:
    return re.findall(r"flag\{[^}]+\}", text, flags=re.IGNORECASE)


def build_langgraph_app(config: OSINTConfig) -> StateGraph:
    tools = [
        TextAnalysisTool(),
        URLInvestigationTool(),
        SNSOSINTTool(),
        WebSearchTool(
            serpapi_api_key=config.serpapi_api_key,
            bing_api_key=config.bing_api_key,
            allow_network=config.allow_network,
        ),
        GeolocationTool(),
        ImageOSINTTool(),
    ]

    graph = StateGraph(AgentState)

    def planner_node(state: AgentState) -> AgentState:
        """Planner handles plan, task split, and retry/stop hints.

        - If evidence is sparse, prioritize entity extraction and URL parsing.
        - If images are present, include image/geo branches early.
        - Loop count is used for simple stop control.
        """
        base_plan = [
            "extract entities",
            "parse urls",
            "sns pivot",
            "web search",
            "geolocation",
            "image review",
        ]
        # Simple heuristic: keep existing plan if provided, else use base.
        plan_steps = state.get("plan") or base_plan
        loop = state.get("loop", 0) + 1
        return {**state, "plan": plan_steps, "loop": loop, "stop": False}

    def tools_node(state: AgentState) -> AgentState:
        problem = ProblemInput(text=state.get("input", ""))
        evs: List[Evidence] = []
        for tool in tools:
            evs.extend(tool.run(problem))
        ev_dicts = _evidence_to_dict(evs)
        all_ev = (state.get("evidence") or []) + ev_dicts
        return {**state, "evidence": all_ev}

    def validator_node(state: AgentState) -> AgentState:
        flags = list(state.get("flags") or [])
        text_blob = " ".join(ev.get("fact", "") for ev in state.get("evidence", []))
        flags.extend(_extract_flags_from_text(text_blob))
        stop = bool(flags) or state.get("loop", 0) >= config.max_iterations
        return {**state, "flags": list(dict.fromkeys(flags)), "stop": stop}

    def flagger_node(state: AgentState) -> AgentState:
        # Final formatting; no-op beyond dedupe here.
        flags = list(dict.fromkeys(state.get("flags") or []))
        return {**state, "flags": flags, "stop": True}

    graph.add_node("planner", planner_node)
    graph.add_node("tools", tools_node)
    graph.add_node("validator", validator_node)
    graph.add_node("flagger", flagger_node)

    graph.add_edge("planner", "tools")
    graph.add_edge("tools", "validator")

    def route_after_validator(state: AgentState):
        return "flagger" if state.get("stop") else "planner"

    graph.add_conditional_edges("validator", route_after_validator, {
        "flagger": "flagger",
        "planner": "planner",
    })

    graph.set_entry_point("planner")
    graph.set_finish_point("flagger")
    return graph
*** End of File