from __future__ import annotations

from pydantic import BaseModel


class ClassifyRequest(BaseModel):
    product_description: str
    product_manufacturer: str | None = None
