from __future__ import annotations

import json

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from agents.auto_classifier.cache.redis_cache import get_cached, set_cached
from agents.auto_classifier.config import settings
from agents.auto_classifier.db.models import ClassificationAudit, ClassificationResult
from agents.auto_classifier.schemas.response import ClassifyResult
from agents.auto_classifier.tier_router import get_tier
from agents.auto_classifier.tools.embed_product import embed_product, search_taxonomy
from agents.auto_classifier.workflows.classification_workflow import classification_graph

logger = structlog.get_logger()


async def classify_product(
    product,
    taxonomy_type: str,
    session: AsyncSession,
) -> ClassifyResult:
    # 1. Redis cache hit → return immediately
    cached = await get_cached(product.id, taxonomy_type)
    if cached:
        logger.info("cache_hit", product_id=product.id)
        return ClassifyResult(**cached)

    # 2. Embed product text → pgvector similarity search (Stage 2)
    candidates: list[dict] = []
    try:
        embedding = await embed_product(product)
        candidates = await search_taxonomy(embedding, taxonomy_type, session)
    except Exception as exc:
        logger.warning("embedding_skipped", error=str(exc))

    # 3. Determine LLM tier from product complexity
    tier, model = get_tier(product)

    # 4. Run LangGraph: embedding-accept or tiered LLM
    state = await classification_graph.ainvoke({
        "product": product,
        "taxonomy_type": taxonomy_type,
        "candidates": candidates,
        "tier": tier,
        "model": model,
        "code": None,
        "name": None,
        "confidence": 0.0,
        "reasoning": "",
        "stage": "",
        "error": None,
    })

    if state.get("error"):
        raise ValueError(state["error"])

    # 5. HITL determination
    hitl_required = state["confidence"] < settings.confidence_write or state["code"] is None

    # 6. Persist classification result
    db_result = ClassificationResult(
        product_id=product.id,
        taxonomy_type=taxonomy_type,
        stage=state["stage"],
        code=state["code"],
        name=state["name"],
        confidence=state["confidence"],
        reasoning=state["reasoning"],
        model_used=model,
        hitl_required=hitl_required,
    )
    session.add(db_result)
    await session.commit()
    await session.refresh(db_result)

    # 7. Append-only audit record
    audit = ClassificationAudit.from_dict(
        result_id=db_result.id,
        event="classify",
        payload={
            "stage": state["stage"],
            "tier": tier,
            "model": model,
            "confidence": state["confidence"],
            "hitl_required": hitl_required,
            "candidates_count": len(candidates),
        },
    )
    session.add(audit)
    await session.commit()

    logger.info(
        "classified",
        product_id=product.id,
        code=state["code"],
        confidence=state["confidence"],
        stage=state["stage"],
        hitl_required=hitl_required,
    )

    result = ClassifyResult(
        product_id=product.id,
        taxonomy_type=taxonomy_type,
        code=state["code"],
        name=state["name"],
        confidence=state["confidence"],
        reasoning=state["reasoning"],
        model_used=model,
        stage=state["stage"],
        hitl_required=hitl_required,
    )

    # 8. Cache only confident results
    if not hitl_required:
        await set_cached(product.id, taxonomy_type, result.model_dump())

    return result
