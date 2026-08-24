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


# --- LaTeX resume builder ---------------------------------------------------
# Structured extraction of a candidate's resume, tailored to a target job. The
# backend renders these fields into a LaTeX document (see documents/latex_resume.py).


class ResumeContact(BaseModel):
    name: str = Field(default="", description="Candidate full name from the resume")
    title: str = Field(default="", description="Professional headline, e.g. 'Backend Engineer'")
    phone: str = ""
    email: str = ""
    location: str = ""
    portfolio: str = Field(default="", description="Portfolio/website URL if present")
    linkedin: str = Field(default="", description="LinkedIn URL or handle if present")
    github: str = Field(default="", description="GitHub URL or handle if present")


class ResumeEducation(BaseModel):
    institution: str = ""
    degree: str = ""
    date: str = Field(default="", description="e.g. '2021 - 2025'")
    detail: str = Field(default="", description="GPA, honors or short note; optional")


class ResumeSkillGroup(BaseModel):
    category: str = Field(description="e.g. 'Languages', 'Frameworks', 'Databases & Tools'")
    items: list[str] = Field(default_factory=list)


class ResumeProject(BaseModel):
    name: str = ""
    tech_stack: str = Field(default="", description="Comma-separated technologies")
    date: str = ""
    github: str = Field(default="", description="Repo URL, optional")
    live: str = Field(default="", description="Live demo URL, optional")
    bullets: list[str] = Field(
        default_factory=list, description="Impact-oriented bullet points, grounded in the resume"
    )


class ResumeExperience(BaseModel):
    company: str = ""
    role: str = ""
    date: str = ""
    location: str = ""
    bullets: list[str] = Field(default_factory=list)


class LatexResumeContent(BaseModel):
    """A resume restructured and tailored to a target job for LaTeX rendering.

    The model must NOT invent employers, dates, degrees, metrics or credentials.
    It may rephrase for ATS alignment and weave in job-description keywords the
    candidate legitimately demonstrates.
    """

    contact: ResumeContact = Field(default_factory=ResumeContact)
    objective: str = Field(default="", description="2-3 sentence summary tailored to the target job")
    education: list[ResumeEducation] = Field(default_factory=list)
    skill_groups: list[ResumeSkillGroup] = Field(default_factory=list)
    experience: list[ResumeExperience] = Field(default_factory=list)
    projects: list[ResumeProject] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    ats_keywords: list[str] = Field(
        default_factory=list, description="Key JD terms surfaced in the tailored resume"
    )
