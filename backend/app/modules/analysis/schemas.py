from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    resume_text: str = Field(min_length=30, max_length=100_000)
    job_description: str = Field(min_length=30, max_length=100_000)
    save: bool = Field(
        default=False,
        description="If true and the caller is authenticated, persist this analysis to history.",
    )


class SkillResult(BaseModel):
    skill: str
    required_level: str
    detected_level: str
    status: str
    evidence: str


class RoadmapStep(BaseModel):
    skill: str
    target_level: str
    priority: str
    steps: list[str]


class AnalysisResponse(BaseModel):
    id: int | None = None
    match_score: int
    ats_coverage: int
    recommendation: str
    summary: str
    strengths: list[SkillResult]
    gaps: list[SkillResult]
    roadmap: list[dict]


class HistoryItem(BaseModel):
    id: int
    title: str
    match_score: int
    ats_coverage: int
    recommendation: str
    summary: str
    created_at: datetime


class HistoryDetail(HistoryItem):
    result: dict
    resume_text: str
    job_description: str
