def test_system_prompt_includes_tone(sample_brand_voice):
    from agents.content.prompts.brand_voice import get_system_prompt
    prompt = get_system_prompt(sample_brand_voice)
    assert "professional" in prompt


def test_system_prompt_includes_seo_keywords(sample_brand_voice):
    from agents.content.prompts.brand_voice import get_system_prompt
    prompt = get_system_prompt(sample_brand_voice)
    assert "merino wool" in prompt
    assert "running jacket" in prompt


def test_system_prompt_includes_avoid_words(sample_brand_voice):
    from agents.content.prompts.brand_voice import get_system_prompt
    prompt = get_system_prompt(sample_brand_voice)
    assert "cheap" in prompt


def test_system_prompt_contains_json_format_instruction(sample_brand_voice):
    from agents.content.prompts.brand_voice import get_system_prompt
    prompt = get_system_prompt(sample_brand_voice)
    assert "JSON" in prompt
    assert '"title"' in prompt
    assert '"description"' in prompt
    assert '"seo_keywords"' in prompt


def test_system_prompt_no_keyword_section_when_empty():
    from pim_core.schemas.product import BrandVoice
    from agents.content.prompts.brand_voice import get_system_prompt
    bv = BrandVoice(tone="friendly", keywords=[], avoid_words=[])
    prompt = get_system_prompt(bv)
    assert "Include these SEO keywords" not in prompt
    assert "Avoid these words" not in prompt


def test_user_message_includes_product_name(sample_product):
    from agents.content.prompts.brand_voice import get_user_message
    msg = get_user_message(sample_product, "ecommerce")
    assert "Merino Wool Running Jacket" in msg


def test_user_message_includes_category(sample_product):
    from agents.content.prompts.brand_voice import get_user_message
    msg = get_user_message(sample_product, "ecommerce")
    assert "Sportswear/Jackets" in msg


def test_user_message_includes_channel(sample_product):
    from agents.content.prompts.brand_voice import get_user_message
    msg = get_user_message(sample_product, "wholesale")
    assert "wholesale" in msg


def test_user_message_includes_brand_attribute(sample_product):
    from agents.content.prompts.brand_voice import get_user_message
    msg = get_user_message(sample_product, "ecommerce")
    assert "TrailPeak" in msg


def test_user_message_handles_product_with_no_attributes():
    from pim_core.schemas.product import Product
    from agents.content.prompts.brand_voice import get_user_message
    p = Product(id="2", sku="SKU-2", name="Basic Widget", category="Tools")
    msg = get_user_message(p, "ecommerce")
    assert "Basic Widget" in msg
    assert "No additional attributes" in msg
