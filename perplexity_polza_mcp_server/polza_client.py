"""HTTP client for Polza.ai."""

from __future__ import annotations

from typing import Any

import httpx

from .config import Settings


class PolzaClient:
    """Thin wrapper around the Polza REST API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call the chat completions endpoint."""
        return await self._request("POST", "/chat/completions", json=payload)

    async def model_catalog(self) -> dict[str, Any]:
        """Fetch model catalog."""
        return await self._request(
            "GET",
            "/models/catalog",
            params={"type": "chat", "search": "perplexity", "limit": 100},
        )

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.settings.polza_api_key}"

        async with httpx.AsyncClient(base_url=self.settings.polza_base_url, timeout=120.0) as client:
            response = await client.request(method, path, headers=headers, **kwargs)

        response.raise_for_status()
        return response.json()
