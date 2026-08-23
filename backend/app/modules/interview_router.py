"""Adaptive interview preparation.

- ``POST /interview/question`` generates a question for a role/topic/difficulty.
- ``POST /interview/evaluate`` scores a candidate answer via the LangGraph graph
  and stores the attempt so difficulty can adapt over time.
- ``GET /interview/history`` returns past attempts.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import InterviewAttempt, User
from app.modules.auth.router import current_user

router = APIRouter()

# Small offline fallback bank so the interview screen is usable without an LLM.
_FALLBACK_QUESTIONS = {
    "basic": [
        "Explain the difference between a list and a tuple in Python.",
        "What is the purpose of an index in a relational database?",
    ],
    "intermediate": [
        "Describe how you would design a REST API for a job-application service.",
        "How does React reconciliation decide what to re-render, and why does it matter?",
    ],
    "advanced": [
        "Design a rate limiter for a multi-tenant API. Discuss trade-offs.",
        "How would you make a stateful LLM interview workflow resumable after a crash?",
    ],
}


class QuestionRequest(BaseModel):
    role: str = Field(default="Software Engineer", max_length=200)
    topic: str = Field(default="general", max_length=100)
    difficulty: str = Field(default="intermediate", max_length=32)


class EvaluationRequest(BaseModel):
    question: str = Field(min_length=5, max_length=2000)
    answer: str = Field(min_length=5, max_length=6000)


class EvaluationResponse(BaseModel):
    id: int | None = None
    score: float
    strengths: list[str] = []
    improvements: list[str] = []
    evidence_quality: str = ""
    next_difficulty: str = ""


@router.post("/question")
async def question(payload: QuestionRequest, user: User = Depends(current_user)):
    difficulty = payload.difficulty if payload.difficulty in _FALLBACK_QUESTIONS else "intermediate"
    if settings.llm_configured:
        try:
            from app.ai.llm.schemas import InterviewQuestion
            from app.ai.llm.service import structured

            result = await structured(
                "question",
                "You are an interviewer. Produce exactly one focused interview question "
                "appropriate for the given role, topic and difficulty. Do not include the answer.",
                f"Role: {payload.role}\nTopic: {payload.topic}\nDifficulty: {difficulty}",
                InterviewQuestion,
            )
            return result.model_dump()
        except Exception:
            pass
    bank = _FALLBACK_QUESTIONS[difficulty]
    # Rotate through the small bank using the user's attempt count.
    return {"question": bank[user.id % len(bank)], "topic": payload.topic, "difficulty": difficulty}


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    try:
        from app.ai.agents.interview_graph import build_interview_graph

        graph = build_interview_graph()
        if graph is None:
            raise RuntimeError("LangGraph is unavailable")
        result = await graph.ainvoke({"question": payload.question, "answer": payload.answer})
    except Exception as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Interview evaluation is temporarily unavailable. Configure the LLM provider.",
        ) from exc

    attempt = InterviewAttempt(
        user_id=user.id,
        question=payload.question,
        answer=payload.answer,
        score=float(result.get("score", 0.0)),
        evidence_quality=result.get("evidence_quality", ""),
        next_difficulty=result.get("next_difficulty", ""),
        strengths=result.get("strengths", []),
        improvements=result.get("improvements", []),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return {
        "id": attempt.id,
        "score": attempt.score,
        "strengths": attempt.strengths,
        "improvements": attempt.improvements,
        "evidence_quality": attempt.evidence_quality,
        "next_difficulty": attempt.next_difficulty,
    }


@router.get("/history")
def history(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(
        select(InterviewAttempt)
        .where(InterviewAttempt.user_id == user.id)
        .order_by(InterviewAttempt.created_at.desc())
        .limit(50)
    ).all()
    return [
        {
            "id": r.id,
            "question": r.question,
            "score": r.score,
            "evidence_quality": r.evidence_quality,
            "next_difficulty": r.next_difficulty,
            "strengths": r.strengths,
            "improvements": r.improvements,
            "created_at": r.created_at,
        }
        for r in rows
    ]
