from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pim_core.llm.factory import get_provider
from pim_core.llm.registry import agent_model_registry
from pim_core.config import settings
from pim_core.utils.all_available_models import (
    AllAvailableModelsAnthropic,
    AllAvailableModelsGoogle,
    AllAvailableModelsOpenAI,
)

router = APIRouter(tags=["agent-settings"])

# ---------------------------------------------------------------------------
# Model catalogue — derived entirely from enums, no hardcoded strings.
# To add a new model: add it to the enum in pim_core/utils/all_available_models.py.
# ---------------------------------------------------------------------------

AVAILABLE_MODELS: dict[str, list[str]] = {
    "anthropic": [m.value for m in AllAvailableModelsAnthropic],
    "openai": [m.value for m in AllAvailableModelsOpenAI],
    "google": [m.value for m in AllAvailableModelsGoogle],
}


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class AvailableModelsResponse(BaseModel):
    anthropic: list[str]
    openai: list[str]
    google: list[str]


class SetAgentModelRequest(BaseModel):
    model: str


class AgentModelResponse(BaseModel):
    agent: str
    model: str


class AllAgentModelsResponse(BaseModel):
    registry: dict[str, str]
    default_model: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/models/available", response_model=AvailableModelsResponse)
async def list_available_models() -> AvailableModelsResponse:
    """Return all LLM models available for assignment, grouped by provider.

    These models are sourced from the AllAvailableModels* enums in
    pim_core/utils/all_available_models.py. To add a new model, update the
    relevant enum — this endpoint reflects the change automatically.
    """
    return AvailableModelsResponse(**AVAILABLE_MODELS)


@router.post("/agents-settings/{agent_name}/model", response_model=AgentModelResponse)
async def set_agent_model(
    agent_name: str,
    request: SetAgentModelRequest,
) -> AgentModelResponse:
    """Assign an LLM model to a named agent.

    The change takes effect immediately and is persisted to SQLite — it
    survives server restarts. Any subsequent call that goes through
    agent_model_registry.get(agent_name) will use the new model.

    Args:
        agent_name: Logical agent identifier from AllAgents enum
                    (e.g. "product_description_generator").
        request.model: Model name to assign. Must be listed in
            GET /models/available.

    Raises:
        400: When the model name is not in any AllAvailableModels* enum.
    """
    try:
        get_provider(request.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    agent_model_registry.set(agent_name, request.model)
    return AgentModelResponse(agent=agent_name, model=request.model)


@router.get("/agents-settings/models", response_model=AllAgentModelsResponse)
async def get_all_agent_models() -> AllAgentModelsResponse:
    """Return every agent's current model assignment and the global default.

    Data is read from the in-memory registry, which is loaded from SQLite
    on server startup. Agents not listed fall back to default_model.
    """
    return AllAgentModelsResponse(
        registry=agent_model_registry.all(),
        default_model=settings.claude_model,
    )


@router.delete("/agents-settings/{agent_name}/model", response_model=AgentModelResponse)
async def reset_agent_model(agent_name: str) -> AgentModelResponse:
    """Remove the explicit model assignment for an agent, reverting to the default.

    The deletion is persisted to SQLite — the agent uses default_model
    on all subsequent calls and after restarts.
    """
    agent_model_registry.remove(agent_name)
    return AgentModelResponse(agent=agent_name, model=settings.claude_model)
