from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from agents.auto_classifier.config import settings as classifier_settings
from agents.auto_classifier.db.base import init_db
from agents.auto_classifier.routes.classify import router as classify_router
from agents.product_description_generator.routes.agent_registry import router as agent_registry_router
from agents.product_description_generator.routes.product_description_generator_api_route import router as pim_router
from pim_core.llm.registry import agent_model_registry
from pim_core.utils.all_agents import AllAgents

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logging.basicConfig(
    level=getattr(logging, classifier_settings.log_level.upper(), logging.INFO)
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(classifier_settings.database_url)
    logger.info(
        "startup_complete",
        agents=[a.value for a in AllAgents],
        embedding=classifier_settings.embedding_model,
    )
    yield
    logger.info("shutdown_complete")


app = FastAPI(
    title="PIM AI Agents",
    version="1.0.0",
    description="Unified gateway for all PIM AI agents. Each agent's routes are grouped by tag.",
    lifespan=lifespan,
)

# ── Product Description Generator ────────────────────────────────────────────
app.include_router(pim_router)
app.include_router(agent_registry_router)

# ── Auto Classifier ───────────────────────────────────────────────────────────
app.include_router(classify_router, prefix="/agents")


# ── Platform health ───────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health() -> dict:
    return {
        "status": "ok",
        "agents": [a.value for a in AllAgents],
    }
