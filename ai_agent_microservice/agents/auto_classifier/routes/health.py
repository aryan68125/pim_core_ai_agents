from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from agents.auto_classifier.db.base import get_session

router = APIRouter(tags=["health"])
logger = structlog.get_logger()


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    db_ok = False
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        logger.warning("health_db_check_failed", error=str(exc))
    return {"status": "ok" if db_ok else "degraded", "agent": "auto_classifier", "db": db_ok}
