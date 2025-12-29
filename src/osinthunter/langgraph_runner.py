"""LangGraph-based multi-agent orchestration (planner, tools, validator, flagger).

Planner/Validator can call LLMs (OpenAI or OpenRouter). If no keys are available,
the graph falls back to deterministic heuristics.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI

from .config import OSINTConfig
from .models import Evidence, PlanStep, ProblemInput
from .tools import (
    GeolocationAgent,
    ImageOSINTAgent,
    SNSOSINTAgent,
    TavilySearchAgent,
    TextAnalysisAgent,
    URLInvestigationAgent,
    WebSearchAgent,
    GoogleLensAgent,
    ShodanAgent,
    CensysAgent,
    WhoisAgent,
    BuiltWithAgent,
    HunterAgent,
    PhonebookAgent,
    WaybackAgent,
    SocialSearchAgent,
    SherlockAgent,
    EarthViewAgent,
    YandexReverseImageAgent,
)
from .tools.geolocation import GeolocationLookupTool
from .tools.image_osint import ImageInspectTool


class AgentState(TypedDict):
    input: str
    urls: List[str]
    images: List[str]
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


def _dedupe_evidence_dicts(items: List[Dict]) -> List[Dict]:
    seen = set()
    deduped: List[Dict] = []
    for ev in items:
        key = (ev.get("source", ""), ev.get("fact", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ev)
    return deduped


def _make_llm(config: OSINTConfig) -> Optional[ChatOpenAI]:
    if config.openrouter_api_key:
        return ChatOpenAI(
            api_key=config.openrouter_api_key,
            base_url=config.openrouter_base_url,
            model=config.model_name,
            temperature=0,
        )
    if config.openai_api_key:
        return ChatOpenAI(
            api_key=config.openai_api_key,
            model=config.model_name,
            temperature=0,
        )
    return None


def _log_jsonl(payload: Dict) -> None:
    path = Path(os.getenv("OSINTHUNTER_LOG_PATH", ".cache/logs/agent_runs.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**payload, "ts": datetime.now(timezone.utc).isoformat()}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def build_langgraph_app(config: OSINTConfig) -> StateGraph:
    tools = [
        TextAnalysisAgent(),
        URLInvestigationAgent(),
        SNSOSINTAgent(),
        WebSearchAgent(
            serpapi_api_key=config.serpapi_api_key,
            bing_api_key=config.bing_api_key,
            allow_network=config.allow_network,
        ),
        TavilySearchAgent(api_key=config.tavily_api_key, allow_network=config.allow_network),
        ShodanAgent(api_key=config.shodan_api_key, allow_network=config.allow_network),
        CensysAgent(api_id=config.censys_api_id, api_secret=config.censys_api_secret, allow_network=config.allow_network),
        WhoisAgent(),
        BuiltWithAgent(api_key=config.builtwith_api_key, allow_network=config.allow_network),
        HunterAgent(api_key=config.hunter_api_key, allow_network=config.allow_network),
        PhonebookAgent(),
        WaybackAgent(allow_network=config.allow_network),
        SocialSearchAgent(),
        SherlockAgent(),
        GeolocationAgent(),
        ImageOSINTAgent(),
        EarthViewAgent(),
        YandexReverseImageAgent(),
        GoogleLensAgent(serpapi_api_key=config.serpapi_api_key, allow_network=config.allow_network),
    ]

    lc_tools = [GeolocationLookupTool(), ImageInspectTool()]
    llm = _make_llm(config)
    graph = StateGraph(AgentState)

    def planner_node(state: AgentState) -> AgentState:
        """Planner handles plan, task split, and retry/stop hints."""
        base_plan = ["extract entities", "parse urls"]
        if state.get("urls"):
            base_plan.append("url enrichment")
        base_plan.append("sns pivot")
        base_plan.append("web search")
        if state.get("images"):
            base_plan.append("image review")
        base_plan.append("geolocation")

        if llm:
            prompt = (
                "You are an OSINT planner for CTF. Given the problem text, propose a concise plan "
                "(<=6 steps) including image/geolocation branches when images or coordinates appear. "
                "Return bullet points only.\n\n"
                f"Problem: {state.get('input','')}\n"
                f"Evidence so far: {len(state.get('evidence', []))} items"
            )
            resp = llm.invoke(prompt)
            text = resp.content if hasattr(resp, "content") else str(resp)
            plan_lines = [line.strip("- ") for line in text.splitlines() if line.strip()]
            plan_steps = plan_lines[:6] if plan_lines else base_plan
        else:
            plan_steps = state.get("plan") or base_plan

        loop = state.get("loop", 0) + 1
        return {**state, "plan": plan_steps, "loop": loop, "stop": False}

    def tools_node(state: AgentState) -> AgentState:
        problem = ProblemInput(
            text=state.get("input", ""),
            urls=state.get("urls", []),
            image_paths=state.get("images", []),
        )
        evs: List[Evidence] = []
        for tool in tools:
            evs.extend(tool.run(problem))

        # Also run LC BaseTools via ToolNode-style call (deterministic usage)
        for lc_tool in lc_tools:
            result = lc_tool.run(state.get("input", ""))
            if isinstance(result, str):
                evs.append(Evidence(source=lc_tool.name, fact=result, confidence=0.4))

        ev_dicts = _evidence_to_dict(evs)
        all_ev = (state.get("evidence") or []) + ev_dicts
        return {**state, "evidence": _dedupe_evidence_dicts(all_ev)}

    def validator_node(state: AgentState) -> AgentState:
        flags = list(state.get("flags") or [])
        text_blob = " ".join(ev.get("fact", "") for ev in state.get("evidence", []))
        flags.extend(_extract_flags_from_text(text_blob))

        if llm:
            prompt = (
                "You are a validator. Given evidence text, list any flag{...} candidates and decide whether to stop.\n"
                "Answer in JSON: {\"flags\": [], \"stop\": bool}"
            )
            resp = llm.invoke(f"{prompt}\nEvidence:\n{text_blob}\n")
            content = resp.content if hasattr(resp, "content") else str(resp)
            try:
                parsed = json.loads(content)
                flags.extend(parsed.get("flags", []))
                stop = bool(parsed.get("stop"))
            except Exception:
                stop = False
        else:
            stop = False

        stop = stop or bool(flags) or state.get("loop", 0) >= config.max_iterations
        return {**state, "flags": list(dict.fromkeys(flags)), "stop": stop}

    def flagger_node(state: AgentState) -> AgentState:
        # Final formatting; no-op beyond dedupe here.
        flags = list(dict.fromkeys(state.get("flags") or []))
        _log_jsonl({
            "input": state.get("input", ""),
            "evidence": state.get("evidence", []),
            "flags": flags,
            "plan": state.get("plan", []),
            "loop": state.get("loop", 0),
        })
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