"""Pydantic schemas for structured LLM output.

Using structured output (instead of parsing free-form text) keeps model responses
machine-readable and validated before they reach the API layer.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class GroundedAnswer(BaseModel):
    answer: str = Field(description="Answer using only the supplied sources. If unsupported, say so.")
    confidence: str = Field(description="high, medium, or low")
    citations: list[int] = Field(default_factory=list, description="1-based source numbers used")


class InterviewQuestion(BaseModel):
    question: str = Field(description="A single, focused interview question")
    topic: str = Field(default="general")
    difficulty: str = Field(default="intermediate", description="basic, intermediate, or advanced")


class InterviewEvaluation(BaseModel):
    score: float = Field(ge=0, le=10)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    evidence_quality: str = Field(description="strong, moderate, or weak")
    next_difficulty: str = Field(description="basic, intermediate, or advanced")


class AnalysisEnhancement(BaseModel):
    match_score: int = Field(ge=0, le=100)
    ats_coverage: int = Field(ge=0, le=100)
    recommendation: str = Field(description="STRONG_MATCH, MATCH_WITH_IMPROVEMENTS, or LOW_MATCH")
    summary: str
    strengths: list[str] = Field(default_factory=list, description="Concrete matched skills or evidence")
    gaps: list[str] = Field(default_factory=list, description="Concrete missing or weak evidence")
    roadmap_steps: list[str] = Field(default_factory=list, description="High-impact next steps")


class DocumentInsight(BaseModel):
    document_type: str = Field(description="resume, job_description, notes, or unknown")
    summary: str
    detected_skills: list[str] = Field(default_factory=list)
    improvement_notes: list[str] = Field(default_factory=list)


class RoadmapPlan(BaseModel):
    items: list[dict] = Field(default_factory=list)


class ResumeDraft(BaseModel):
    summary: str
    skills: list[str] = Field(default_factory=list)
    experience_bullets: list[str] = Field(default_factory=list)
    project_bullets: list[str] = Field(default_factory=list)
    ats_keywords: list[str] = Field(default_factory=list)


class CoverLetterDraft(BaseModel):
    greeting: str = Field(default="Dear Hiring Manager,")
    opening: str = Field(description="Opening paragraph tailored to the role")
    body: list[str] = Field(default_factory=list, description="Body paragraphs")
    closing: str = Field(description="Closing paragraph")
    signature: str = Field(default="Sincerely,")
