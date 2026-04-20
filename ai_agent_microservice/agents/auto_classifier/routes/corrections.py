from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from agents.auto_classifier.db.base import get_session
from agents.auto_classifier.db.models import ClassificationAudit, Correction

router = APIRouter(prefix="/corrections", tags=["corrections"])


class CorrectionRequest(BaseModel):
    result_id: int
    correct_code: str
    correct_name: str
    reviewer_note: str | None = None


class CorrectionResponse(BaseModel):
    id: int
    result_id: int
    correct_code: str
    correct_name: str


@router.post("", response_model=CorrectionResponse, status_code=201)
async def submit_correction(
    body: CorrectionRequest,
    session: AsyncSession = Depends(get_session),
) -> CorrectionResponse:
    correction = Correction(
        result_id=body.result_id,
        correct_code=body.correct_code,
        correct_name=body.correct_name,
        reviewer_note=body.reviewer_note,
    )
    session.add(correction)

    audit = ClassificationAudit.from_dict(
        result_id=body.result_id,
        event="correction",
        payload={
            "correct_code": body.correct_code,
            "correct_name": body.correct_name,
            "reviewer_note": body.reviewer_note,
        },
    )
    session.add(audit)

    try:
        await session.commit()
        await session.refresh(correction)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return CorrectionResponse(
        id=correction.id,
        result_id=correction.result_id,
        correct_code=correction.correct_code,
        correct_name=correction.correct_name,
    )
