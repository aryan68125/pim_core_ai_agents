import os

# Must be set before any pim_core import so pydantic-settings can validate.
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-placeholder")

import pytest


@pytest.fixture
def sample_product():
    from pim_core.schemas.product import Product, ProductAttributes
    return Product(
        id="prod-001",
        sku="SKU-JACKET-001",
        name="Merino Wool Running Jacket",
        category="Sportswear/Jackets",
        attributes=ProductAttributes(
            brand="TrailPeak",
            color="Navy Blue",
            size="M",
            material="100% Merino Wool",
            weight="350g",
            dimensions="Chest: 96cm, Length: 72cm",
        ),
        existing_description="A jacket for runners.",
    )


@pytest.fixture
def sample_brand_voice():
    from pim_core.schemas.product import BrandVoice
    return BrandVoice(
        tone="professional",
        keywords=["merino wool", "running jacket", "moisture-wicking"],
        avoid_words=["cheap", "discount"],
        max_title_length=80,
        max_description_length=500,
        locale="en-GB",
    )
