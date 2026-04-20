from __future__ import annotations

import json
from typing import Any

# Fields that are never useful for classification — internal system fields
_SKIP_FIELDS = {
    "productID", "id", "shortSku", "sku", "vendorStyle", "upc", "isbnEan",
    "reclassToSKU", "reclassToProductID", "ipVendorID", "ipVendorNumber",
    "ipStyle", "ipSize", "ipColor", "brandID", "prodManufacturerID",
    "coordGroupID", "coordGroup", "deckID", "deck", "filler", "buyerID",
    "buyerFirstName", "buyerLastName", "buyerIPUser", "buyerAssociateID",
    "dateCreated", "lastModifiedOn", "firstShipDate", "firstActivityDate",
    "streetDate", "adEmbargo", "asteaWarranty", "accountCode",
    "isActive", "isAnItemSet", "pageCount",
}

_SYSTEM_PROMPT = """\
You are a product category classifier for a PIM system.

Given a product in JSON format, identify what the product is and classify it into the most accurate category.

Return ONLY this JSON — no other text:
{
  "category_path": "<top level> > <mid level> > <specific category>",
  "code": "<taxonomy code or null>",
  "confidence": <0.0 to 1.0>,
  "reasoning": "<one sentence why>"
}

Notes:
- category_path must always be a hierarchical path using " > " as separator
- For GS1 and eCl@ss: fill code from your knowledge of that standard
- For custom taxonomy: set code to null, focus on a clear descriptive category_path
- confidence reflects how clearly the product data identifies the category\
"""


def get_system_prompt() -> str:
    return _SYSTEM_PROMPT


def _clean_product(product: dict[str, Any]) -> dict[str, Any]:
    """Remove empty, zero, internal-system fields. Keep only what describes the product."""
    cleaned = {}
    for k, v in product.items():
        if k in _SKIP_FIELDS:
            continue
        if v is None or v == "" or v == 0 or v == 0.0 or v is False:
            continue
        # Skip attribute fields that are empty (attribute1..attribute99)
        if k.startswith("attribute") and k[9:].isdigit():
            continue
        # Skip image/copy fields with no value
        if k.startswith(("image", "copy")) and not v:
            continue
        cleaned[k] = v
    return cleaned


def get_user_message(product: dict[str, Any], taxonomy_type: str) -> str:
    cleaned = _clean_product(product)
    product_json = json.dumps(cleaned, indent=2, default=str)

    return (
        f"Taxonomy: {taxonomy_type.upper()}\n\n"
        f"Product:\n{product_json}"
    )
