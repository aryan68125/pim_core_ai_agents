from __future__ import annotations

import json
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agents.auto_classifier.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaxonomyNode(Base):
    """Pre-embedded taxonomy categories — GS1 / eCl@ss / custom (loaded in v2)."""

    __tablename__ = "taxonomy_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    taxonomy_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    breadcrumb: Mapped[str | None] = mapped_column(Text, nullable=True)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[list | None] = mapped_column(Vector(1536), nullable=True)


class ClassificationResult(Base):
    """Every classification decision — one row per request."""

    __tablename__ = "classification_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    taxonomy_type: Mapped[str] = mapped_column(String(32), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)  # embedding_accept | llm_tier1/2/3
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    model_used: Mapped[str] = mapped_column(String(64), nullable=False)
    hitl_required: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    corrections: Mapped[list[Correction]] = relationship("Correction", back_populates="result")


class Correction(Base):
    """Human override — feeds the accuracy improvement loop."""

    __tablename__ = "corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    result_id: Mapped[int] = mapped_column(
        ForeignKey("classification_results.id"), nullable=False, index=True
    )
    correct_code: Mapped[str] = mapped_column(String(64), nullable=False)
    correct_name: Mapped[str] = mapped_column(String(256), nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    result: Mapped[ClassificationResult] = relationship(
        "ClassificationResult", back_populates="corrections"
    )


class ClassificationAudit(Base):
    """Append-only audit log — every decision is traceable."""

    __tablename__ = "classification_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    result_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    event: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    @classmethod
    def from_dict(cls, result_id: int | None, event: str, payload: dict) -> "ClassificationAudit":
        return cls(result_id=result_id, event=event, payload=json.dumps(payload))
