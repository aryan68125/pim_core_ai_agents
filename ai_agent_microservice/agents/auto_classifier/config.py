from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class ClassifierSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM tiers (model name determines provider via pim_core factory)
    llm_tier1_model: str = "gemini-1.5-flash"       # simple products
    llm_tier2_model: str = "claude-sonnet-4-6"       # standard products
    llm_tier3_model: str = "claude-opus-4-7"         # complex / regulated

    # Embedding (OpenAI text-embedding-3-small, 1536 dims)
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auto_classifier"

    # Redis
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 86400  # 24 h

    # Confidence thresholds
    confidence_embedding_threshold: float = 0.92   # accept embedding result without LLM
    confidence_auto_accept: float = 0.95            # write immediately, no HITL
    confidence_write: float = 0.75                  # write but flag for sample review

    log_level: str = "INFO"


settings = ClassifierSettings()
