def test_product_minimal_construction():
    """Product can be created with only required fields."""
    from pim_core.schemas.product import Product, ProductAttributes
    p = Product(id="1", sku="SKU-1", name="Widget", category="Tools")
    assert p.attributes == ProductAttributes()
    assert p.image_urls == []
    assert p.existing_description is None


def test_product_full_construction(sample_product):
    """sample_product fixture constructs a valid Product."""
    assert sample_product.id == "prod-001"
    assert sample_product.attributes.brand == "TrailPeak"
    assert sample_product.attributes.color == "Navy Blue"


def test_brand_voice_defaults():
    """BrandVoice uses sensible defaults."""
    from pim_core.schemas.product import BrandVoice
    bv = BrandVoice()
    assert bv.tone == "professional"
    assert bv.locale == "en-GB"
    assert bv.max_title_length == 80
    assert bv.max_description_length == 500
    assert bv.keywords == []
    assert bv.avoid_words == []


def test_brand_voice_with_keywords(sample_brand_voice):
    """sample_brand_voice fixture sets keywords and avoid_words correctly."""
    assert "merino wool" in sample_brand_voice.keywords
    assert "cheap" in sample_brand_voice.avoid_words


def test_description_result_construction():
    """DescriptionResult stores all generated fields."""
    from pim_core.schemas.product import DescriptionResult
    r = DescriptionResult(
        product_id="prod-001",
        channel="ecommerce",
        title="TrailPeak Jacket",
        description="A professional running jacket for serious athletes.",
        seo_keywords=["running", "jacket", "merino"],
        word_count=8,
        model_used="claude-sonnet-4-6",
    )
    assert r.product_id == "prod-001"
    assert r.word_count == 8
    assert "running" in r.seo_keywords


def test_product_attributes_additional_fields():
    """ProductAttributes.additional stores arbitrary key-value pairs."""
    from pim_core.schemas.product import ProductAttributes
    attrs = ProductAttributes(additional={"waterproof_rating": "IPX4", "pockets": "4"})
    assert attrs.additional["waterproof_rating"] == "IPX4"
