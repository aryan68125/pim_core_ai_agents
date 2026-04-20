from __future__ import annotations

from pydantic import BaseModel


class ClassifyResult(BaseModel):
    product_id: str
    taxonomy_type: str
    code: str | None
    name: str | None
    confidence: float
    reasoning: str
    model_used: str
    stage: str = ""
    hitl_required: bool = False
