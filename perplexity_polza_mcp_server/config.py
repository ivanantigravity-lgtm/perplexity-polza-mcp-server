"""Configuration helpers for the MCP server."""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime settings loaded from environment."""

    polza_api_key: str = Field(alias="POLZA_AI_API_KEY")
    polza_base_url: str = "https://polza.ai/api/v1"
    default_model: str = "perplexity/sonar"
    research_model: str = "perplexity/sonar-deep-research"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        api_key = os.environ.get("POLZA_AI_API_KEY") or os.environ.get("POLZA_API_KEY")
        if not api_key:
            raise KeyError("POLZA_AI_API_KEY")
        return cls(
            POLZA_AI_API_KEY=api_key,
            polza_base_url=os.getenv("POLZA_BASE_URL", "https://polza.ai/api/v1").rstrip("/"),
            default_model=os.getenv("PERPLEXITY_MODEL", "perplexity/sonar"),
            research_model=os.getenv("PERPLEXITY_RESEARCH_MODEL", "perplexity/sonar-deep-research"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
