from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pim_core.llm.factory import get_provider
from pim_core.llm.registry import agent_model_registry

router = APIRouter(prefix="/config", tags=["configuration"])

AGENT_NAME = "auto_classifier"


class SetModelRequest(BaseModel):
    model: str


class ModelResponse(BaseModel):
    agent: str
    model: str


@router.get("/model", response_model=ModelResponse)
async def get_model() -> ModelResponse:
    """Return the LLM model currently assigned to the auto_classifier agent."""
    return ModelResponse(agent=AGENT_NAME, model=agent_model_registry.get(AGENT_NAME))


@router.post("/model", response_model=ModelResponse)
async def set_model(request: SetModelRequest) -> ModelResponse:
    """Assign an LLM model to the auto_classifier agent.

    Takes effect on the next classify call — no restart required.

    Raises:
        400: If the model prefix is not supported by any provider.
    """
    try:
        get_provider(request.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    agent_model_registry.set(AGENT_NAME, request.model)
    return ModelResponse(agent=AGENT_NAME, model=request.model)
