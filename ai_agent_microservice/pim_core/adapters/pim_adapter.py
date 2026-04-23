from __future__ import annotations

import json

from pim_core.schemas.pim_product import PIMProductRecord
from pim_core.schemas.product import Product, ProductAttributes


def pim_record_to_product(record: PIMProductRecord) -> Product:
    """Convert a raw PIM product record into the normalised Product schema.

    Field mapping:
        productID               → id  (cast to str)
        productName             → name
        coordGroupDescription   → category  (trailing spaces stripped)
        ipManufacturer          → attributes.brand
        copy1                   → existing_description (preferred)
        productDescription      → existing_description fallback
        posDescription          → existing_description final fallback
        warranty                → attributes.additional["warranty"]
        vendorStyle             → attributes.additional["vendor_part_number"]
        webManufacturer         → attributes.additional["web_manufacturer"]
        suggestedWebcategory    → attributes.additional["web_category"]
        productType             → attributes.additional["product_type"]
        categorySpecificAttributes → attributes.additional["category_attributes"]
                                     (only when non-empty; serialised as JSON)
    """
    # --- existing description: pick the most informative non-empty value ---
    existing_description: str | None = None
    for candidate in (
        record.copy1,
        record.productDescription,
        record.posDescription,
    ):
        stripped = candidate.strip()
        # Skip values that are just repetitions of the product name (adds no value)
        if stripped and stripped.upper() != record.productName.strip().upper():
            existing_description = stripped
            break

    # --- additional attributes: only include non-empty values ---
    additional: dict[str, str] = {}

    _add_if_set(additional, "warranty", record.warranty)
    _add_if_set(additional, "vendor_part_number", record.vendorStyle)
    _add_if_set(additional, "web_manufacturer", record.webManufacturer)
    _add_if_set(additional, "web_category", record.suggestedWebcategory)
    _add_if_set(additional, "product_type", record.productType)

    if record.categorySpecificAttributes:
        additional["category_attributes"] = json.dumps(record.categorySpecificAttributes)

    return Product(
        id=str(record.productID),
        sku="",
        name=record.productName.strip(),
        category=record.coordGroupDescription.strip(),
        attributes=ProductAttributes(
            brand=record.ipManufacturer.strip() or None,
            additional=additional,
        ),
        existing_description=existing_description,
        image_urls=[],
    )


def _add_if_set(target: dict[str, str], key: str, value: str) -> None:
    """Add value to dict only when it is a non-empty, non-whitespace string."""
    stripped = value.strip()
    if stripped:
        target[key] = stripped
