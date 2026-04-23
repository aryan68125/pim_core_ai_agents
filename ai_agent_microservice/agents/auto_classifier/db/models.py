from __future__ import annotations

from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from agents.auto_classifier.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WebCategory(Base):
    """Master category table — loaded from Web Category Hierarchy Excel."""

    __tablename__ = "web_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    level1: Mapped[str] = mapped_column(String(256), nullable=False)
    level2: Mapped[str | None] = mapped_column(String(256), nullable=True)
    level3: Mapped[str | None] = mapped_column(String(256), nullable=True)
    category_path: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)


class ClassificationResult(Base):
    """One row per classification request."""

    __tablename__ = "classification_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_description: Mapped[str] = mapped_column(Text, nullable=False)
    category_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(1), nullable=False)
    model_used: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
