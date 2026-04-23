from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class ClassifierSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM — swap model name to change provider (pim_core handles routing)
    classifier_model: str = "gpt-4o"

    # Embedding — swap provider/model without changing any other code
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auto_classifier"

    # 3-path confidence thresholds (calibrated for product-description → category-path cross-domain embeddings)
    high_confidence_threshold: float = 0.60   # Path A: top-5 direct to LLM
    low_confidence_threshold: float = 0.35    # Path B: web+top-5; below = Path C

    log_level: str = "INFO"


settings = ClassifierSettings()
