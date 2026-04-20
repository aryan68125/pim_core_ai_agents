from __future__ import annotations

import json
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from agents.auto_classifier.cache.redis_cache import get_cached, set_cached
from agents.auto_classifier.config import settings
from agents.auto_classifier.db.models import ClassificationAudit, ClassificationResult
from agents.auto_classifier.schemas.response import ClassifyResult
from agents.auto_classifier.workflows.classification_workflow import classification_graph

logger = structlog.get_logger()


async def classify_product(
    product: dict[str, Any],
    taxonomy_type: str,
    session: AsyncSession,
) -> ClassifyResult:
    # 1. Cache check by content hash — same product data = same result
    cached = await get_cached(product, taxonomy_type)
    if cached:
        logger.info("cache_hit")
        return ClassifyResult(**cached)

    # 2. LLM classification — straight to LLM, no embedding search
    state = await classification_graph.ainvoke({
        "product": product,
        "taxonomy_type": taxonomy_type,
        "category_path": None,
        "code": None,
        "confidence": 0.0,
        "reasoning": "",
        "error": None,
    })

    if state.get("error"):
        raise ValueError(state["error"])

    hitl_required = state["confidence"] < settings.confidence_write or state["category_path"] is None

    # 3. Persist result
    db_result = ClassificationResult(
        product_id=str(product.get("productID") or product.get("id") or "unknown"),
        taxonomy_type=taxonomy_type,
        stage="llm",
        code=state["code"],
        name=state["category_path"],
        confidence=state["confidence"],
        reasoning=state["reasoning"],
        model_used=settings.classifier_model,
        hitl_required=hitl_required,
    )
    session.add(db_result)
    await session.commit()
    await session.refresh(db_result)

    # 4. Audit
    session.add(ClassificationAudit.from_dict(
        result_id=db_result.id,
        event="classify",
        payload={
            "taxonomy_type": taxonomy_type,
            "model": settings.classifier_model,
            "confidence": state["confidence"],
            "hitl_required": hitl_required,
        },
    ))
    await session.commit()

    logger.info(
        "classified",
        code=state["code"],
        name=state["name"],
        confidence=state["confidence"],
        hitl_required=hitl_required,
    )

    result = ClassifyResult(
        product_id=db_result.product_id,
        taxonomy_type=taxonomy_type,
        category_path=state["category_path"],
        code=state["code"],
        confidence=state["confidence"],
        reasoning=state["reasoning"],
        model_used=settings.classifier_model,
        hitl_required=hitl_required,
    )

    if not hitl_required:
        await set_cached(product, taxonomy_type, result.model_dump())

    return result
