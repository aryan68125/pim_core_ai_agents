import json
import pytest
from unittest.mock import AsyncMock, patch

from pim_core.utils.all_agents import AllAgents

AGENT_KEY = AllAgents.PRODUCT_DESCRIPTION_GENERATOR.value


@pytest.mark.asyncio
async def test_generate_description_returns_result(sample_product, sample_brand_voice):
    """generate_description returns a valid DescriptionResult."""
    mock_response = json.dumps({
        "title": "TrailPeak Merino Wool Running Jacket — Navy Blue, M",
        "description": "Stay warm on every run with the TrailPeak 100% merino wool jacket.",
        "seo_keywords": ["merino wool", "running jacket", "moisture-wicking"],
    })

    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm, patch(
        "agents.product_description_generator.tools.generate_description.agent_model_registry.get",
        return_value="claude-sonnet-4-6",
    ):
        mock_llm.return_value = mock_response

        from agents.product_description_generator.tools.generate_description import generate_description
        result = await generate_description(
            product=sample_product,
            channel="ecommerce",
            brand_voice=sample_brand_voice,
        )

    assert result.product_id == "prod-001"
    assert result.channel == "ecommerce"
    assert result.title == "TrailPeak Merino Wool Running Jacket — Navy Blue, M"
    assert len(result.description) > 0
    assert "merino wool" in result.seo_keywords
    assert result.word_count > 0
    assert result.model_used == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_generate_description_uses_default_brand_voice(sample_product):
    """generate_description applies default BrandVoice when none supplied."""
    mock_response = json.dumps({
        "title": "Merino Wool Running Jacket",
        "description": "High-quality jacket for all conditions.",
        "seo_keywords": ["running jacket"],
    })

    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = mock_response

        from agents.product_description_generator.tools.generate_description import generate_description
        result = await generate_description(product=sample_product, channel="wholesale")

    assert result.channel == "wholesale"
    assert result.title == "Merino Wool Running Jacket"


@pytest.mark.asyncio
async def test_generate_description_raises_on_llm_error(sample_product, sample_brand_voice):
    """generate_description raises ValueError when the workflow returns an error."""
    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = "not valid json"

        from agents.product_description_generator.tools.generate_description import generate_description
        with pytest.raises(ValueError, match="Failed to parse LLM response"):
            await generate_description(
                product=sample_product,
                channel="ecommerce",
                brand_voice=sample_brand_voice,
            )


@pytest.mark.asyncio
async def test_generate_description_word_count_matches_description(
    sample_product, sample_brand_voice
):
    """word_count equals the number of whitespace-separated words in description."""
    description_text = "Stay warm and dry on every run with this jacket."
    mock_response = json.dumps({
        "title": "Test Title",
        "description": description_text,
        "seo_keywords": [],
    })

    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = mock_response

        from agents.product_description_generator.tools.generate_description import generate_description
        result = await generate_description(
            product=sample_product,
            channel="ecommerce",
            brand_voice=sample_brand_voice,
        )

    assert result.word_count == len(description_text.split())
