from __future__ import annotations

from pim_core.schemas.product import Product

_SYSTEM_PROMPT = """\
You are a product taxonomy classifier for a PIM system.
Given a product and a taxonomy standard, return the single best matching category code and name.

Respond ONLY with valid JSON in this exact format:
{"code": "<category_code>", "name": "<category_name>", "confidence": <0.0-1.0>, "reasoning": "<brief reason>"}

If no suitable category exists, respond:
{"code": null, "name": null, "confidence": 0.0, "reasoning": "<why no match>"}

Do not include any text outside the JSON object.\
"""


def get_system_prompt() -> str:
    return _SYSTEM_PROMPT


def get_user_message(
    product: Product,
    taxonomy_type: str,
    candidates: list[dict] | None = None,
) -> str:
    attrs = product.attributes
    attr_lines = "\n".join(
        f"  {k}: {v}"
        for k, v in {
            "Color": attrs.color,
            "Size": attrs.size,
            "Material": attrs.material,
            "Weight": attrs.weight,
            "Dimensions": attrs.dimensions,
            "Brand": attrs.brand,
            **attrs.additional,
        }.items()
        if v
    )

    msg = (
        f"Product:\n"
        f"  ID: {product.id}\n"
        f"  SKU: {product.sku}\n"
        f"  Name: {product.name}\n"
        f"  Category hint: {product.category}\n"
        + (f"  Attributes:\n{attr_lines}\n" if attr_lines else "")
        + (f"  Description: {product.existing_description}\n" if product.existing_description else "")
        + f"\nTaxonomy standard: {taxonomy_type.upper()}\n"
    )

    if candidates:
        candidate_lines = "\n".join(
            f"  {i+1}. [{c['code']}] {c['name']} (similarity: {c['score']:.3f})"
            + (f" — {c['breadcrumb']}" if c.get("breadcrumb") else "")
            for i, c in enumerate(candidates[:5])
        )
        msg += f"\nTop candidate categories from taxonomy search:\n{candidate_lines}\n"
        msg += f"\nSelect the best match from the candidates above, or choose a different category if none fit."
    else:
        msg += f"\nClassify this product into the most appropriate {taxonomy_type.upper()} category."

    return msg
