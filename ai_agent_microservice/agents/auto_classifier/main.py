from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from agents.auto_classifier.config import settings
from agents.auto_classifier.db.base import init_db
from agents.auto_classifier.routes.classify import router as classify_router
from agents.auto_classifier.routes.health import router as health_router

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
    logger.info("auto_classifier_startup", model=settings.classifier_model,
                embedding=settings.embedding_model)
    yield
    logger.info("auto_classifier_shutdown")


app = FastAPI(title="Auto Classifier Agent", version="1.0.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(classify_router)
