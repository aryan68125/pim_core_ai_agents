from __future__ import annotations

import structlog
from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agents.auto_classifier.config import settings
from pim_core.config import settings as core_settings
from pim_core.schemas.product import Product

logger = structlog.get_logger()

_client: AsyncOpenAI | None = None


def _get_openai() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=core_settings.openai_api_key)
    return _client


def _product_to_text(product: Product) -> str:
    parts = [product.name, product.category]
    attrs = product.attributes
    for field in ("brand", "color", "material", "size", "weight", "dimensions"):
        val = getattr(attrs, field, None)
        if val:
            parts.append(f"{field}: {val}")
    for k, v in attrs.additional.items():
        if v:
            parts.append(f"{k}: {v}")
    if product.existing_description:
        parts.append(product.existing_description[:300])
    return " | ".join(parts)


async def embed_product(product: Product) -> list[float]:
    text_input = _product_to_text(product)
    response = await _get_openai().embeddings.create(
        model=settings.embedding_model,
        input=text_input,
    )
    return response.data[0].embedding


async def search_taxonomy(
    embedding: list[float],
    taxonomy_type: str,
    session: AsyncSession,
    top_k: int = 5,
) -> list[dict]:
    """Cosine similarity search against pre-embedded taxonomy nodes."""
    vector_str = "[" + ",".join(str(v) for v in embedding) + "]"
    sql = text(
        """
        SELECT id, code, name, breadcrumb,
               1 - (embedding <=> :vec::vector) AS score
        FROM taxonomy_nodes
        WHERE taxonomy_type = :ttype
          AND embedding IS NOT NULL
        ORDER BY embedding <=> :vec::vector
        LIMIT :top_k
        """
    )
    try:
        result = await session.execute(
            sql,
            {"vec": vector_str, "ttype": taxonomy_type, "top_k": top_k},
        )
        rows = result.fetchall()
        candidates = [
            {
                "id": r.id,
                "code": r.code,
                "name": r.name,
                "breadcrumb": r.breadcrumb,
                "score": float(r.score),
            }
            for r in rows
        ]
        if candidates:
            logger.info(
                "taxonomy_search",
                taxonomy_type=taxonomy_type,
                count=len(candidates),
                top_score=candidates[0]["score"],
            )
        return candidates
    except Exception as exc:
        logger.warning("taxonomy_search_failed", error=str(exc))
        return []
