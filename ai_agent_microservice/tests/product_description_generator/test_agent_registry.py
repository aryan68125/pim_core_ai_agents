from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from agents.product_description_generator.routes.agent_registry import AVAILABLE_MODELS
from pim_core.utils.all_agents import AllAgents

AGENT_KEY = AllAgents.PRODUCT_DESCRIPTION_GENERATOR.value


# ---------------------------------------------------------------------------
# Isolation fixture — runs automatically around every test in this file.
#
# Two things it does:
#   1. Patches agent_model_db.upsert / delete so no test touches the real
#      SQLite database (agent_models.db). Without this, running pytest
#      overwrites whatever model the operator set manually via the API.
#   2. Saves the in-memory registry state before each test and restores it
#      afterward, so tests that call the real FastAPI app (which mutates the
#      singleton registry) don't bleed into subsequent tests.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolate_registry(monkeypatch):
    import pim_core.db.agent_model_db as db
    monkeypatch.setattr(db, "upsert", lambda *_: None)
    monkeypatch.setattr(db, "delete", lambda *_: None)

    from pim_core.llm.registry import agent_model_registry
    saved = dict(agent_model_registry._registry)
    yield
    agent_model_registry._registry.clear()
    agent_model_registry._registry.update(saved)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _client():
    from agents.product_description_generator.main import app
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# GET /models/available
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_available_models_returns_200():
    async with await _client() as client:
        response = await client.get("/models/available")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_available_models_includes_all_providers():
    async with await _client() as client:
        response = await client.get("/models/available")
    data = response.json()
    assert "anthropic" in data
    assert "openai" in data
    assert "google" in data


@pytest.mark.asyncio
async def test_list_available_models_anthropic_contains_sonnet():
    async with await _client() as client:
        response = await client.get("/models/available")
    assert "claude-sonnet-4-6" in response.json()["anthropic"]


@pytest.mark.asyncio
async def test_list_available_models_openai_contains_gpt4o():
    async with await _client() as client:
        response = await client.get("/models/available")
    assert "gpt-4o" in response.json()["openai"]


@pytest.mark.asyncio
async def test_list_available_models_google_contains_gemini():
    async with await _client() as client:
        response = await client.get("/models/available")
    assert any("gemini" in m for m in response.json()["google"])


# ---------------------------------------------------------------------------
# POST /agents-settings/{agent_name}/model
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_set_agent_model_returns_200_for_valid_claude_model():
    with patch("agents.product_description_generator.routes.agent_registry.get_provider"):
        async with await _client() as client:
            response = await client.post(
                f"/agents-settings/{AGENT_KEY}/model",
                json={"model": "claude-sonnet-4-6"},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["agent"] == AGENT_KEY
    assert data["model"] == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_set_agent_model_returns_200_for_openai_model():
    with patch("agents.product_description_generator.routes.agent_registry.get_provider"):
        async with await _client() as client:
            response = await client.post(
                "/agents-settings/catalog/model",
                json={"model": "gpt-4o"},
            )
    assert response.status_code == 200
    assert response.json()["agent"] == "catalog"
    assert response.json()["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_set_agent_model_returns_200_for_google_model():
    with patch("agents.product_description_generator.routes.agent_registry.get_provider"):
        async with await _client() as client:
            response = await client.post(
                "/agents-settings/procurement/model",
                json={"model": "gemini-2.0-flash"},
            )
    assert response.status_code == 200
    assert response.json()["model"] == "gemini-2.0-flash"


@pytest.mark.asyncio
async def test_set_agent_model_returns_400_for_unknown_model():
    async with await _client() as client:
        response = await client.post(
            "/agents-settings/content/model",
            json={"model": "unknown-model-xyz"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_set_agent_model_writes_to_registry():
    from pim_core.llm.registry import agent_model_registry
    with patch("agents.product_description_generator.routes.agent_registry.get_provider"):
        async with await _client() as client:
            await client.post(
                "/agents-settings/test-agent/model",
                json={"model": "claude-sonnet-4-6"},
            )
    assert agent_model_registry.get("test-agent") == "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# GET /agents-settings/models
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_all_agent_models_returns_200():
    async with await _client() as client:
        response = await client.get("/agents-settings/models")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_all_agent_models_contains_registry_and_default():
    async with await _client() as client:
        response = await client.get("/agents-settings/models")
    data = response.json()
    assert "registry" in data
    assert "default_model" in data
    assert isinstance(data["registry"], dict)
    assert isinstance(data["default_model"], str)


@pytest.mark.asyncio
async def test_get_all_agent_models_reflects_assignment():
    from pim_core.llm.registry import agent_model_registry
    agent_model_registry.set("visibility-test-agent", "gpt-4o-mini")
    async with await _client() as client:
        response = await client.get("/agents-settings/models")
    assert response.json()["registry"].get("visibility-test-agent") == "gpt-4o-mini"


# ---------------------------------------------------------------------------
# DELETE /agents-settings/{agent_name}/model
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reset_agent_model_returns_200():
    from pim_core.llm.registry import agent_model_registry
    agent_model_registry.set("reset-agent", "gpt-4o")
    async with await _client() as client:
        response = await client.delete("/agents-settings/reset-agent/model")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_reset_agent_model_reverts_to_default():
    from pim_core.llm.registry import agent_model_registry
    agent_model_registry.set("revert-agent", "gpt-4o")
    async with await _client() as client:
        response = await client.delete("/agents-settings/revert-agent/model")
    data = response.json()
    assert data["agent"] == "revert-agent"
    assert data["model"] == response.json()["model"]
    assert "revert-agent" not in agent_model_registry.all()
