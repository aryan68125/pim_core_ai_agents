from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.product_description_generator.tools.generate_description import (
    generate_description,
)
from pim_core.adapters.pim_adapter import pim_record_to_product
from pim_core.schemas.pim_product import PIMProductRecord
from pim_core.schemas.product import BrandVoice, DescriptionResult

router = APIRouter(prefix="/agents", tags=["agents"])


class GenerateFromPIMRequest(BaseModel):
    """Request body for generating a description directly from a raw PIM record."""

    pim_record: PIMProductRecord
    channel: str
    brand_voice: BrandVoice | None = None


@router.post("/generate-description", response_model=DescriptionResult)
async def generate_description_from_pim(
    request: GenerateFromPIMRequest,
) -> DescriptionResult:
    """Generate an SEO-optimised description from a raw PIM product record.

    Accepts a product record exactly as exported from the PIM system — no
    pre-processing required by the caller. The adapter layer handles field
    mapping internally before invoking the same generation pipeline used by
    POST /generate-description.

    Args:
        request.pim_record: Raw PIM product record (productID, productName,
            coordGroupDescription, ipManufacturer, etc.)
        request.channel: Target distribution channel (ecommerce, wholesale,
            marketplace, …)
        request.brand_voice: Optional brand voice configuration. Uses defaults
            when omitted.

    Returns:
        DescriptionResult with title, description, SEO keywords, and word count.

    Raises:
        422: When the LLM returns a response that cannot be parsed as JSON.
        400: When the PIM record cannot be adapted (e.g. missing productName).
    """
    try:
        product = pim_record_to_product(request.pim_record)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to adapt PIM record: {exc}",
        ) from exc

    try:
        return await generate_description(
            product=product,
            channel=request.channel,
            brand_voice=request.brand_voice,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
