"""Learning-roadmap generation and per-user persistence."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import RoadmapRecord, User
from app.modules.auth.router import current_user

router = APIRouter()
logger = logging.getLogger("careersetu.roadmap")


class RoadmapRequest(BaseModel):
    skills: list[str] = Field(min_length=1, max_length=20)


class RoadmapSaveRequest(BaseModel):
    items: list[dict] = Field(default_factory=list)


def _baseline(skills: list[str]) -> dict:
    return {
        "items": [
            {
                "skill": s,
                "levels": ["basic", "intermediate", "advanced"],
                "status": "not_started",
                "steps": [
                    f"Study {s} fundamentals",
                    f"Build a small project using {s}",
                    f"Add measurable {s} evidence to your resume",
                ],
            }
            for s in skills
        ]
    }


@router.post("/generate")
async def generate(payload: RoadmapRequest, user: User = Depends(current_user)):
    skills = [s.strip() for s in payload.skills if s.strip()]
    if not skills:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "At least one skill is required.")
    try:
        from app.ai.llm.schemas import RoadmapPlan
        from app.ai.llm.service import structured

        result = await structured(
            "roadmap",
            "Build a concise career learning roadmap. Return practical steps, projects, and "
            "milestones for each skill.",
            f"Skills: {skills}",
            RoadmapPlan,
        )
        if result.items:
            return result.model_dump()
    except Exception:
        # Free-tier LLM is best-effort here — the deterministic baseline is
        # always returned so the feature never goes dark, and provider errors
        # are logged for observability.
        logger.exception("Roadmap generation fell back to baseline")
    return _baseline(skills)


@router.get("")
def get_roadmap(db: Session = Depends(get_db), user: User = Depends(current_user)):
    record = db.query(RoadmapRecord).filter(RoadmapRecord.user_id == user.id).first()
    return {"items": record.items if record else []}


@router.post("")
def save_roadmap(
    payload: RoadmapSaveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    # Each user has at most one roadmap, so this is an upsert.
    record = db.query(RoadmapRecord).filter(RoadmapRecord.user_id == user.id).first()
    if record:
        record.items = payload.items
    else:
        record = RoadmapRecord(user_id=user.id, items=payload.items)
        db.add(record)
    db.commit()
    db.refresh(record)
    return {"items": record.items}
