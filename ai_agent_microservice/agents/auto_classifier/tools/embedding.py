from __future__ import annotations

from abc import ABC, abstractmethod

import structlog

logger = structlog.get_logger()

_provider: "EmbeddingProvider | None" = None


class EmbeddingProvider(ABC):
    """Swap implementations by changing config.embedding_provider."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        ...


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def embed(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(model=self._model, input=text)
        return response.data[0].embedding

    @property
    def dimensions(self) -> int:
        return 1536


def get_embedding_provider() -> EmbeddingProvider:
    """Returns singleton provider. Change config.embedding_provider to swap."""
    global _provider
    if _provider is None:
        from agents.auto_classifier.config import settings
        from pim_core.config import settings as core_settings

        if settings.embedding_provider == "openai":
            _provider = OpenAIEmbeddingProvider(
                api_key=core_settings.openai_api_key,
                model=settings.embedding_model,
            )
        else:
            raise ValueError(f"Unknown embedding_provider: {settings.embedding_provider}")
        logger.info("embedding_provider_init", provider=settings.embedding_provider,
                    model=settings.embedding_model)
    return _provider
