from __future__ import annotations

from fastapi import FastAPI

from agents.product_description_generator.routes.agent_registry import router as agent_registry_router
from agents.product_description_generator.routes.product_description_generator_api_route import router as pim_router

app = FastAPI(title="Product Description Generator Agent", version="1.0.0")
app.include_router(pim_router)
app.include_router(agent_registry_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "agent": "content"}
