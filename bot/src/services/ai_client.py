"""Shared AsyncOpenAI client for AI services."""

from __future__ import annotations

from openai import AsyncOpenAI

from config.settings import settings

_client: AsyncOpenAI | None = None


def get_ai_client() -> AsyncOpenAI:
    """Return a reusable AsyncOpenAI client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=60.0,
        )
    return _client
