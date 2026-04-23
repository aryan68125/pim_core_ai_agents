from __future__ import annotations

from pydantic import BaseModel


class ClassifyResponse(BaseModel):
    category_path: str
    level1: str | None = None
    level2: str | None = None
    level3: str | None = None
    confidence: float
    method: str
    model_used: str
