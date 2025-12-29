"""Configuration helpers for the OSINT Hunter agent."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class OSINTConfig:
    openai_api_key: Optional[str]
    openrouter_api_key: Optional[str]
    openrouter_base_url: Optional[str]
    serpapi_api_key: Optional[str]
    bing_api_key: Optional[str]
    tavily_api_key: Optional[str]
    shodan_api_key: Optional[str]
    censys_api_id: Optional[str]
    censys_api_secret: Optional[str]
    hunter_api_key: Optional[str]
    builtwith_api_key: Optional[str]
    allow_network: bool = False
    max_iterations: int = 6
    model_name: str = "gpt-4o-mini"


def load_config() -> OSINTConfig:
    """Load configuration from environment variables."""

    return OSINTConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        serpapi_api_key=os.getenv("SERPAPI_API_KEY"),
        bing_api_key=os.getenv("BING_API_KEY"),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        shodan_api_key=os.getenv("SHODAN_API_KEY"),
        censys_api_id=os.getenv("CENSYS_API_ID"),
        censys_api_secret=os.getenv("CENSYS_API_SECRET"),
        hunter_api_key=os.getenv("HUNTER_API_KEY"),
        builtwith_api_key=os.getenv("BUILTWITH_API_KEY"),
        allow_network=os.getenv("OSINTHUNTER_ALLOW_NETWORK", "false").lower() == "true",
        max_iterations=int(os.getenv("OSINTHUNTER_MAX_ITERATIONS", "6")),
        model_name=os.getenv("OSINTHUNTER_MODEL", "gpt-4o-mini"),
    )
