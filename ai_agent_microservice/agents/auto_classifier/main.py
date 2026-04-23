from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from agents.auto_classifier.config import settings
from agents.auto_classifier.db.base import init_db
from agents.auto_classifier.routes.classify import router as classify_router
from agents.auto_classifier.routes.health import router as health_router
from agents.auto_classifier.routes.model_config import router as model_config_router
from pim_core.llm.registry import agent_model_registry

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
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.database_url)
    agent_model_registry.set("auto_classifier", settings.classifier_model)
    logger.info("auto_classifier_startup", model=agent_model_registry.get("auto_classifier"),
                embedding=settings.embedding_model)
    yield
    logger.info("auto_classifier_shutdown")


app = FastAPI(title="Auto Classifier Agent", version="1.0.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(classify_router)
app.include_router(model_config_router)
