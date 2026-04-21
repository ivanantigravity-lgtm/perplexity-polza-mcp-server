"""FastMCP server for Perplexity through Polza.ai."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from fastmcp import FastMCP

from .config import Settings
from .polza_client import PolzaClient


LOGGER = logging.getLogger(__name__)
MODEL_GUIDE = """Perplexity model guide:

1. Sonar
Use for fast search + answer. Best for quick facts, current events, short summaries, and simple Q&A.

2. Sonar Pro
Use when Sonar is too shallow. Better for richer synthesis, comparisons, and more structured answers.

3. Sonar Pro Search
Use when the task needs deeper search behavior, multiple search hops, and broader source collection.

4. Sonar Reasoning Pro
Use when logic matters more than breadth of search. Best for careful comparison, synthesis, and multi-step conclusions.

5. Sonar Deep Research
Use for full research jobs, long reports, market scans, and deep topic overviews with many sources.
"""


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif isinstance(item, dict) and item.get("type"):
                parts.append(f"[{item['type']}]")
        return "\n".join(part for part in parts if part)

    if content is None:
        return ""

    return json.dumps(content, ensure_ascii=False, indent=2)


def _format_response(response: dict[str, Any]) -> str:
    choice = (response.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    answer = _normalize_content(message.get("content")) or "(empty response)"

    lines = [answer]

    annotations = message.get("annotations") or []
    if annotations:
        lines.append("")
        lines.append("Sources:")
        for index, annotation in enumerate(annotations, start=1):
            citation = annotation.get("url_citation") if isinstance(annotation, dict) else None
            title = (
                (annotation.get("title") if isinstance(annotation, dict) else None)
                or (annotation.get("name") if isinstance(annotation, dict) else None)
                or (citation.get("title") if isinstance(citation, dict) else None)
                or f"Source {index}"
            )
            url = (
                (annotation.get("url") if isinstance(annotation, dict) else None)
                or (annotation.get("uri") if isinstance(annotation, dict) else None)
                or (annotation.get("source") if isinstance(annotation, dict) else None)
                or (citation.get("url") if isinstance(citation, dict) else None)
            )
            lines.append(f"{index}. {title}" + (f" — {url}" if url else ""))

    usage = response.get("usage") or {}
    usage_parts = []
    for key in ("prompt_tokens", "completion_tokens", "total_tokens", "cost_rub"):
        if usage.get(key) is not None:
            usage_parts.append(f"{key}={usage[key]}")
    web_search_requests = ((usage.get("server_tool_use") or {}).get("web_search_requests"))
    if web_search_requests is not None:
        usage_parts.append(f"web_search_requests={web_search_requests}")
    if usage_parts:
        lines.append("")
        lines.append("Usage: " + ", ".join(usage_parts))

    if message.get("reasoning") is not None:
        lines.append("")
        lines.append("Reasoning:")
        lines.append(_normalize_content(message["reasoning"]))

    if message.get("tool_calls"):
        lines.append("")
        lines.append("Tool calls:")
        lines.append(json.dumps(message["tool_calls"], ensure_ascii=False, indent=2))

    return "\n".join(lines)


def create_app() -> FastMCP:
    """Application factory for FastMCP."""
    settings = Settings.from_env()
    _setup_logging(settings.log_level)

    client = PolzaClient(settings)
    app = FastMCP(
        name="perplexity-polza-mcp-server",
        instructions=(
            "This server exposes Perplexity models through the Polza.ai API. "
            "Use it for web-backed answers, research, model discovery, and choosing the right "
            "Perplexity model for the task."
        ),
    )

    @app.tool
    async def perplexity_model_guide() -> str:
        """Return a practical guide for choosing between Sonar, Sonar Pro, Pro Search, Reasoning Pro, and Deep Research."""
        return MODEL_GUIDE

    @app.tool
    async def perplexity_ask(
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        search_context_size: str | None = None,
        reasoning_effort: str | None = None,
        include_reasoning: bool | None = None,
    ) -> str:
        """Send a regular Perplexity request through Polza. Default: Sonar for fast search-backed answers."""
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body: dict[str, Any] = {
            "model": model or settings.default_model,
            "messages": messages,
        }
        if temperature is not None:
            body["temperature"] = temperature
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if search_context_size:
            body["web_search_options"] = {"search_context_size": search_context_size}
        if reasoning_effort or include_reasoning is not None:
            reasoning: dict[str, Any] = {}
            if reasoning_effort:
                reasoning["effort"] = reasoning_effort
            if include_reasoning is not None:
                reasoning["exclude"] = not include_reasoning
            body["reasoning"] = reasoning

        response = await client.chat_completions(body)
        return _format_response(response)

    @app.tool
    async def perplexity_research(
        topic: str,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        search_context_size: str = "high",
    ) -> str:
        """Run a deeper research pass with web search turned on. Default: Sonar Deep Research."""
        prompt = (
            "Conduct a thorough research pass on the following topic.\n\n"
            f"Topic: {topic}\n\n"
            "Return a synthesis with key facts, caveats, and direct source references."
        )
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body: dict[str, Any] = {
            "model": model or settings.research_model,
            "messages": messages,
            "web_search_options": {"search_context_size": search_context_size},
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens

        response = await client.chat_completions(body)
        return _format_response(response)

    @app.tool
    async def list_perplexity_models(include_providers: bool = True) -> str:
        """List Perplexity models from the Polza catalog available through Polza."""
        response = await client.model_catalog()
        models = []
        for model in response.get("data", []):
            model_id = str(model.get("id", ""))
            if not model_id.startswith("perplexity/"):
                continue
            models.append(
                {
                    "id": model_id,
                    "name": model.get("name"),
                    "description": model.get("short_description"),
                    "context_length": ((model.get("top_provider") or {}).get("context_length")),
                    "max_completion_tokens": (
                        (model.get("top_provider") or {}).get("max_completion_tokens")
                    ),
                    "pricing": ((model.get("top_provider") or {}).get("pricing")),
                    "supported_parameters": (
                        (model.get("top_provider") or {}).get("supported_parameters") or []
                    ),
                    "providers": model.get("providers") if include_providers else None,
                }
            )
        return json.dumps(models, ensure_ascii=False, indent=2)

    return app


def main() -> None:
    """Main entrypoint for direct execution."""
    try:
        app = create_app()
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as error:
        LOGGER.error("Server failed to start: %s", error, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
