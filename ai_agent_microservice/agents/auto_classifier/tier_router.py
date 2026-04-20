from __future__ import annotations

from agents.auto_classifier.config import settings
from pim_core.schemas.product import Product

_AMBIGUOUS_CATEGORIES = {"unknown", "other", "general", "misc", ""}


def _complexity_score(product: Product) -> float:
    """Return 0.0–1.0 complexity score. Higher = more complex product."""
    score = 0.0
    attrs = product.attributes

    # Rich attributes → more complex
    filled = sum(
        1
        for f in ("color", "size", "material", "weight", "dimensions", "brand")
        if getattr(attrs, f)
    )
    filled += len(attrs.additional)
    score += min(filled / 10.0, 0.4)

    # Long description → more context to reason about
    if product.existing_description:
        score += min(len(product.existing_description) / 1000.0, 0.3)

    # Ambiguous or missing category hint → harder to classify
    if (product.category or "").strip().lower() in _AMBIGUOUS_CATEGORIES:
        score += 0.3

    return min(score, 1.0)


def get_tier(product: Product) -> tuple[int, str]:
    """Return (tier_number, model_name) for this product.

    Tier 1 (<0.35) → cheap/fast model (Gemini Flash / Llama)
    Tier 2 (0.35–0.70) → standard model (Claude Sonnet / GPT-4o-mini)
    Tier 3 (>0.70) → precision model (Claude Opus / GPT-4o)
    """
    complexity = _complexity_score(product)
    if complexity < 0.35:
        return 1, settings.llm_tier1_model
    elif complexity < 0.70:
        return 2, settings.llm_tier2_model
    else:
        return 3, settings.llm_tier3_model
