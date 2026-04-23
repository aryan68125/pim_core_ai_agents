from __future__ import annotations

from agents.auto_classifier.tools.embedding import get_embedding_provider


async def embed_text(text: str) -> list[float]:
    """Embed any text string using configured provider."""
    provider = get_embedding_provider()
    return await provider.embed(text)
