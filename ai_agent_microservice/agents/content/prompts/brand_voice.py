from __future__ import annotations

from pim_core.schemas.product import BrandVoice, Product


def get_system_prompt(brand_voice: BrandVoice) -> str:
    """Build the Claude system prompt from a BrandVoice configuration."""
    keyword_line = ""
    if brand_voice.keywords:
        keyword_line = (
            f"\n- Include these SEO keywords naturally: {', '.join(brand_voice.keywords)}"
        )

    avoid_line = ""
    if brand_voice.avoid_words:
        avoid_line = f"\n- Avoid these words: {', '.join(brand_voice.avoid_words)}"

    return f"""You are a professional product copywriter specialising in e-commerce content.

Your task is to generate an SEO-optimised product title and description.

Rules:
- Tone: {brand_voice.tone}
- Title: maximum {brand_voice.max_title_length} characters
- Description: maximum {brand_voice.max_description_length} characters
- Locale: {brand_voice.locale}{keyword_line}{avoid_line}

Respond ONLY with valid JSON in this exact format:
{{
  "title": "<product title>",
  "description": "<product description>",
  "seo_keywords": ["keyword1", "keyword2", "keyword3"]
}}"""


def get_user_message(product: Product, channel: str) -> str:
    """Build the Claude user message from a Product and target channel."""
    attr_lines: list[str] = []

    if product.attributes.brand:
        attr_lines.append(f"Brand: {product.attributes.brand}")
    if product.attributes.color:
        attr_lines.append(f"Colour: {product.attributes.color}")
    if product.attributes.size:
        attr_lines.append(f"Size: {product.attributes.size}")
    if product.attributes.material:
        attr_lines.append(f"Material: {product.attributes.material}")
    if product.attributes.weight:
        attr_lines.append(f"Weight: {product.attributes.weight}")
    if product.attributes.dimensions:
        attr_lines.append(f"Dimensions: {product.attributes.dimensions}")
    for key, value in product.attributes.additional.items():
        attr_lines.append(f"{key}: {value}")

    attr_block = "\n".join(attr_lines) if attr_lines else "No additional attributes"

    return f"""Product to describe:
Name: {product.name}
Category: {product.category}
Channel: {channel}

Attributes:
{attr_block}

Existing description (for context, do not copy verbatim):
{product.existing_description or 'None'}"""
