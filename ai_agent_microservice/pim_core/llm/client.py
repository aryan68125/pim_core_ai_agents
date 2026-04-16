from __future__ import annotations

import anthropic

from pim_core.config import settings


class LLMClient:
    """Thin async wrapper around AsyncAnthropic shared across all agents."""

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def complete(
        self,
        system: str,
        messages: list[dict],
        model: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        """Call Claude and return the text of the first content block."""
        response = await self._client.messages.create(
            model=model or settings.claude_model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return response.content[0].text


llm_client = LLMClient()
