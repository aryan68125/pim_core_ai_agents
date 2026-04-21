import json
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_workflow_returns_title_and_description(sample_product, sample_brand_voice):
    """Workflow populates title and description from LLM JSON response."""
    mock_response = json.dumps({
        "title": "TrailPeak Merino Wool Running Jacket — Navy, M",
        "description": "Stay comfortable on every run with TrailPeak's merino wool jacket.",
        "seo_keywords": ["merino wool", "running jacket", "moisture-wicking"],
    })

    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = mock_response

        from agents.product_description_generator.workflows.description_workflow import description_graph
        result = await description_graph.ainvoke({
            "product": sample_product,
            "channel": "ecommerce",
            "brand_voice": sample_brand_voice,
            "title": "",
            "description": "",
            "seo_keywords": [],
            "error": None,
        })

    assert result["title"] == "TrailPeak Merino Wool Running Jacket — Navy, M"
    assert "merino wool" in result["description"]
    assert result["error"] is None


@pytest.mark.asyncio
async def test_workflow_returns_seo_keywords(sample_product, sample_brand_voice):
    """Workflow extracts seo_keywords list from LLM JSON response."""
    mock_response = json.dumps({
        "title": "Any Title",
        "description": "Any description.",
        "seo_keywords": ["keyword-a", "keyword-b", "keyword-c"],
    })

    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = mock_response

        from agents.product_description_generator.workflows.description_workflow import description_graph
        result = await description_graph.ainvoke({
            "product": sample_product,
            "channel": "ecommerce",
            "brand_voice": sample_brand_voice,
            "title": "",
            "description": "",
            "seo_keywords": [],
            "error": None,
        })

    assert result["seo_keywords"] == ["keyword-a", "keyword-b", "keyword-c"]


@pytest.mark.asyncio
async def test_workflow_handles_json_wrapped_in_code_fences(sample_product, sample_brand_voice):
    """Workflow correctly parses JSON even when Claude wraps it in markdown code fences."""
    inner = json.dumps({
        "title": "Fenced Title",
        "description": "Fenced description.",
        "seo_keywords": ["a", "b"],
    })
    fenced_response = f"```json\n{inner}\n```"

    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = fenced_response

        from agents.product_description_generator.workflows.description_workflow import description_graph
        result = await description_graph.ainvoke({
            "product": sample_product,
            "channel": "ecommerce",
            "brand_voice": sample_brand_voice,
            "title": "",
            "description": "",
            "seo_keywords": [],
            "error": None,
        })

    assert result["title"] == "Fenced Title"
    assert result["error"] is None


@pytest.mark.asyncio
async def test_workflow_sets_error_on_invalid_json(sample_product, sample_brand_voice):
    """Workflow sets error key when LLM returns unparseable text."""
    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = "Sorry, I cannot help with that."

        from agents.product_description_generator.workflows.description_workflow import description_graph
        result = await description_graph.ainvoke({
            "product": sample_product,
            "channel": "ecommerce",
            "brand_voice": sample_brand_voice,
            "title": "",
            "description": "",
            "seo_keywords": [],
            "error": None,
        })

    assert result["error"] is not None
    assert "Failed to parse" in result["error"]


@pytest.mark.asyncio
async def test_workflow_sets_error_on_missing_title_key(sample_product, sample_brand_voice):
    """Workflow sets error when JSON response is missing required 'title' key."""
    mock_response = json.dumps({"description": "ok", "seo_keywords": []})

    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = mock_response

        from agents.product_description_generator.workflows.description_workflow import description_graph
        result = await description_graph.ainvoke({
            "product": sample_product,
            "channel": "ecommerce",
            "brand_voice": sample_brand_voice,
            "title": "",
            "description": "",
            "seo_keywords": [],
            "error": None,
        })

    assert result["error"] is not None
