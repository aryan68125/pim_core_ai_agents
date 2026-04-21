from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from agents.auto_classifier.db.base import get_session
from agents.auto_classifier.schemas.request import ClassifyRequest
from agents.auto_classifier.schemas.response import ClassifyResponse
from agents.auto_classifier.tools.classify_product import classify_product

router = APIRouter(prefix="/classify", tags=["classify"])


@router.post("", response_model=ClassifyResponse)
async def classify(
    body: ClassifyRequest,
    session: AsyncSession = Depends(get_session),
) -> ClassifyResponse:
    try:
        return await classify_product(
            product_description=body.product_description,
            product_manufacturer=body.product_manufacturer,
            session=session,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
