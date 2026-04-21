from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from agents.auto_classifier.config import settings
from agents.auto_classifier.db.models import ClassificationResult
from agents.auto_classifier.schemas.response import ClassifyResponse
from agents.auto_classifier.workflows.classification_workflow import classification_graph

logger = structlog.get_logger()


async def classify_product(
    product_description: str,
    product_manufacturer: str | None,
    session: AsyncSession,
) -> ClassifyResponse:
    product_text = product_description
    if product_manufacturer:
        product_text = f"{product_manufacturer} {product_description}"

    state = await classification_graph.ainvoke({
        "product_text": product_text,
        "session": session,
        "embedding": None,
        "candidates": [],
        "top_score": 0.0,
        "web_context": None,
        "path": None,
        "category_path": None,
        "category_id": None,
        "confidence": 0.0,
        "method": "",
        "error": None,
    })

    if state.get("error"):
        raise ValueError(state["error"])

    db_result = ClassificationResult(
        product_description=product_description[:500],
        category_path=state["category_path"],
        category_id=state.get("category_id"),
        confidence=state["confidence"],
        method=state["method"],
        model_used=settings.classifier_model,
    )
    session.add(db_result)
    await session.commit()

    logger.info(
        "classified",
        method=state["method"],
        category_path=state["category_path"],
        confidence=state["confidence"],
    )

    parts = [p.strip() for p in (state["category_path"] or "").split(">")]
    return ClassifyResponse(
        category_path=state["category_path"] or "",
        level1=parts[0] if len(parts) > 0 else None,
        level2=parts[1] if len(parts) > 1 else None,
        level3=parts[2] if len(parts) > 2 else None,
        confidence=state["confidence"],
        method=state["method"],
        model_used=settings.classifier_model,
    )
