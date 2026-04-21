from __future__ import annotations

import json
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch


SAMPLE_PIM_RECORD = {
    "productID": 705517,
    "shortSku": "969196",
    "productName": "MACSTUDIO E25 M4M/64/1TB",
    "coordGroupDescription": "APPLE DESKTOP SYSTEMS    ",
    "ipManufacturer": "APPLE",
    "productDescription": "MACSTUDIO E25 M4M/64/1TB",
    "warranty": "1 year",
    "asteaWarranty": "1YearVendor",
    "vendorStyle": "15098309",
    "image1": "",
    "image2": "",
    "image3": "",
    "image4": "",
}

MOCK_LLM_RESPONSE = json.dumps({
    "title": "Apple Mac Studio M4 Max — 64GB RAM, 1TB SSD",
    "description": "Experience unparalleled desktop performance with the Apple Mac Studio powered by the M4 Max chip.",
    "seo_keywords": ["mac studio", "apple m4 max", "desktop workstation"],
})


@pytest.mark.asyncio
async def test_product_description_generator_endpoint_returns_200_with_valid_record():
    """POST /agents/generate-description with a valid PIM record returns 200 and DescriptionResult."""
    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new=AsyncMock(return_value=MOCK_LLM_RESPONSE),
    ):
        from agents.product_description_generator.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/agents/generate-description",
                json={"pim_record": SAMPLE_PIM_RECORD, "channel": "ecommerce"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "705517"
    assert data["channel"] == "ecommerce"
    assert "title" in data
    assert "description" in data
    assert "seo_keywords" in data
    assert "word_count" in data


@pytest.mark.asyncio
async def test_product_description_generator_strips_category_trailing_spaces():
    """Adapter strips trailing spaces from coordGroupDescription before passing to the LLM."""
    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new=AsyncMock(return_value=MOCK_LLM_RESPONSE),
    ):
        from agents.product_description_generator.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/agents/generate-description",
                json={"pim_record": SAMPLE_PIM_RECORD, "channel": "ecommerce"},
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_product_description_generator_accepts_optional_brand_voice():
    """POST /agents/generate-description respects an explicit brand_voice payload."""
    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new=AsyncMock(return_value=MOCK_LLM_RESPONSE),
    ):
        from agents.product_description_generator.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/agents/generate-description",
                json={
                    "pim_record": SAMPLE_PIM_RECORD,
                    "channel": "wholesale",
                    "brand_voice": {
                        "tone": "technical",
                        "keywords": ["M4 Max", "workstation"],
                        "avoid_words": ["cheap"],
                        "max_description_length": 400,
                        "locale": "en-US",
                    },
                },
            )

    assert response.status_code == 200
    assert response.json()["channel"] == "wholesale"


@pytest.mark.asyncio
async def test_product_description_generator_returns_422_when_llm_returns_invalid_json():
    """POST /agents/generate-description returns 422 when LLM output cannot be parsed."""
    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new=AsyncMock(return_value="NOT VALID JSON"),
    ):
        from agents.product_description_generator.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/agents/generate-description",
                json={"pim_record": SAMPLE_PIM_RECORD, "channel": "ecommerce"},
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_product_description_generator_uses_real_sample_data_record():
    """End-to-end: POST /agents/generate-description with the first record from the actual sample file."""
    with patch(
        "agents.product_description_generator.workflows.description_workflow.llm_client.complete",
        new=AsyncMock(return_value=json.dumps({
            "title": "UGREEN 2-Bay NAS Enclosure DH2300",
            "description": "Expand your storage with the UGREEN 2-Bay NASSync DH2300 network attached storage enclosure.",
            "seo_keywords": ["nas enclosure", "network storage", "ugreen"],
        })),
    ):
        from agents.product_description_generator.main import app
        nas_record = {
            "productID": 705511,
            "shortSku": "968909",
            "productName": "2-BAY NASYNC DH2300",
            "coordGroupDescription": "SMB NETWORK/NAS DRV ENCL ",
            "ipManufacturer": "UGREEN",
            "productDescription": "2-BAY NASYNC DH2300",
            "warranty": "1 year",
            "asteaWarranty": "1YearVendor",
            "vendorStyle": "95432",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/agents/generate-description",
                json={"pim_record": nas_record, "channel": "ecommerce"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "705511"
