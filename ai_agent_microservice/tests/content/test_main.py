import json
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok():
    """GET /health returns status ok and agent name."""
    from agents.content.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "agent": "content"}


@pytest.mark.asyncio
async def test_generate_description_endpoint_success(sample_product, sample_brand_voice):
    """POST /generate-description returns 200 with a valid DescriptionResult body."""
    mock_response = json.dumps({
        "title": "TrailPeak Merino Wool Running Jacket — Navy Blue, M",
        "description": "Crafted from 100% merino wool, this jacket keeps you comfortable on every run.",
        "seo_keywords": ["merino wool", "running jacket", "moisture-wicking"],
    })

    with patch(
        "agents.content.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = mock_response

        from agents.content.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/generate-description",
                json={
                    "product": sample_product.model_dump(),
                    "channel": "ecommerce",
                    "brand_voice": sample_brand_voice.model_dump(),
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "prod-001"
    assert data["channel"] == "ecommerce"
    assert data["title"] == "TrailPeak Merino Wool Running Jacket — Navy Blue, M"
    assert data["word_count"] > 0
    assert data["model_used"] == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_generate_description_endpoint_without_brand_voice(sample_product):
    """POST /generate-description works when brand_voice field is omitted."""
    mock_response = json.dumps({
        "title": "Merino Wool Running Jacket",
        "description": "A professional-grade jacket for runners.",
        "seo_keywords": ["running jacket"],
    })

    with patch(
        "agents.content.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = mock_response

        from agents.content.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/generate-description",
                json={
                    "product": sample_product.model_dump(),
                    "channel": "marketplace",
                },
            )

    assert response.status_code == 200
    assert response.json()["channel"] == "marketplace"


@pytest.mark.asyncio
async def test_generate_description_endpoint_llm_error_returns_422(
    sample_product, sample_brand_voice
):
    """POST /generate-description returns 422 when LLM response is invalid JSON."""
    with patch(
        "agents.content.workflows.description_workflow.llm_client.complete",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = "not valid json"

        from agents.content.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/generate-description",
                json={
                    "product": sample_product.model_dump(),
                    "channel": "ecommerce",
                    "brand_voice": sample_brand_voice.model_dump(),
                },
            )

    assert response.status_code == 422
