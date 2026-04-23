from __future__ import annotations

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


async def search_categories(
    embedding: list[float],
    session: AsyncSession,
    top_k: int = 5,
) -> list[dict]:
    """Cosine similarity search: returns top_k categories with scores."""
    vector_str = "[" + ",".join(str(v) for v in embedding) + "]"
    sql = text(
        """
        WITH ranked AS (
            SELECT id, category_id, category_path, level1, level2, level3,
                   embedding <=> CAST(:vec AS vector) AS distance
            FROM web_categories
            WHERE embedding IS NOT NULL
            ORDER BY distance
            LIMIT :top_k
        )
        SELECT *, 1 - distance AS score FROM ranked
        """
    )
    result = await session.execute(sql, {"vec": vector_str, "top_k": top_k})
    rows = result.fetchall()
    candidates = [
        {
            "id": r.id,
            "category_id": r.category_id,
            "category_path": r.category_path,
            "level1": r.level1,
            "level2": r.level2,
            "level3": r.level3,
            "score": float(r.score),
        }
        for r in rows
    ]
    if candidates:
        logger.info("category_search", top_score=candidates[0]["score"], count=len(candidates))
    return candidates
