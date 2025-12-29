"""Configuration helpers for the OSINT Hunter agent."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class OSINTConfig:
    openai_api_key: Optional[str]
    serpapi_api_key: Optional[str]
    bing_api_key: Optional[str]
    allow_network: bool = False
    max_iterations: int = 6
    model_name: str = "gpt-4o-mini"


def load_config() -> OSINTConfig:
    """Load configuration from environment variables."""

    return OSINTConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        serpapi_api_key=os.getenv("SERPAPI_API_KEY"),
        bing_api_key=os.getenv("BING_API_KEY"),
        allow_network=os.getenv("OSINTHUNTER_ALLOW_NETWORK", "false").lower() == "true",
        max_iterations=int(os.getenv("OSINTHUNTER_MAX_ITERATIONS", "6")),
        model_name=os.getenv("OSINTHUNTER_MODEL", "gpt-4o-mini"),
    )
