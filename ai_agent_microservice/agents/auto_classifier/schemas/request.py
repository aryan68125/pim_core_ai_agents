from __future__ import annotations

from typing import Literal

from pim_core.schemas.product import Product
from pydantic import BaseModel

TaxonomyType = Literal["gs1", "eclass", "custom"]


class ClassifyRequest(BaseModel):
    product: Product
    taxonomy_type: TaxonomyType = "gs1"
