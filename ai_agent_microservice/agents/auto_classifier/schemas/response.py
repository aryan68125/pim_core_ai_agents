from __future__ import annotations

from pydantic import BaseModel


class ClassifyResult(BaseModel):
    product_id: str
    taxonomy_type: str
    category_path: str | None    # e.g. "Electronics > Computers > Desktop Computers"
    code: str | None             # GS1/eCl@ss code — null for custom taxonomy
    confidence: float
    reasoning: str
    model_used: str
    hitl_required: bool = False
