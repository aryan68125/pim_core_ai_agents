from __future__ import annotations

from pydantic import BaseModel, Field


class ProductAttributes(BaseModel):
    """Structured product attributes. Only populate fields that are known."""
    color: str | None = None
    size: str | None = None
    material: str | None = None
    weight: str | None = None
    dimensions: str | None = None
    brand: str | None = None
    additional: dict[str, str] = Field(default_factory=dict)


class Product(BaseModel):
    """A product record from the PIM system."""
    id: str
    sku: str
    name: str
    category: str
    attributes: ProductAttributes = Field(default_factory=ProductAttributes)
    existing_description: str | None = None
    image_urls: list[str] = Field(default_factory=list)


class BrandVoice(BaseModel):
    """Brand voice configuration for description generation."""
    tone: str = "professional"  # professional | friendly | technical | luxury
    keywords: list[str] = Field(default_factory=list)
    avoid_words: list[str] = Field(default_factory=list)
    max_title_length: int = 80
    max_description_length: int = 500
    locale: str = "en-GB"


class DescriptionResult(BaseModel):
    """Output from the generate_description tool."""
    product_id: str
    channel: str
    title: str
    description: str
    seo_keywords: list[str]
    word_count: int
    model_used: str
