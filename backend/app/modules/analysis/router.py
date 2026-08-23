"""Resume/JD analysis endpoints.

``POST /analysis`` is a guest, stateless path by default. When the caller is
authenticated *and* passes ``save: true`` the result is stored so it appears in
their history.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AnalysisRecord, User
from app.modules.analysis.ai import enhance_analysis
from app.modules.analysis.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    HistoryDetail,
    HistoryItem,
)
from app.modules.analysis.service import analyze
from app.modules.auth.router import current_user, optional_user

router = APIRouter()


@router.post("", response_model=AnalysisResponse)
async def create_analysis(
    payload: AnalysisRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    baseline = analyze(payload.resume_text, payload.job_description)
    result = await enhance_analysis(payload.resume_text, payload.job_description, baseline)

    record_id: int | None = None
    if user and payload.save:
        record = AnalysisRecord(
            user_id=user.id,
            match_score=result["match_score"],
            ats_coverage=result["ats_coverage"],
            recommendation=result["recommendation"],
            summary=result["summary"],
            result=result,
            resume_text=payload.resume_text,
            job_description=payload.job_description,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        record_id = record.id

    return {"id": record_id, **result}


@router.get("/history", response_model=list[HistoryItem])
def history(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(
        select(AnalysisRecord)
        .where(AnalysisRecord.user_id == user.id)
        .order_by(AnalysisRecord.created_at.desc())
    ).all()
    return rows


@router.get("/history/{record_id}", response_model=HistoryDetail)
def history_detail(
    record_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    record = db.get(AnalysisRecord, record_id)
    if not record or record.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found.")
    return record


@router.delete("/history/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history(
    record_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    record = db.get(AnalysisRecord, record_id)
    if not record or record.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found.")
    db.delete(record)
    db.commit()
