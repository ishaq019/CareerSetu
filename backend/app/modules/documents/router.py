"""Document endpoints: extraction, knowledge ingestion, and AI generation
(resume optimisation + cover letter)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.models import User
from app.modules.auth.router import current_user
from app.modules.documents.service import (
    DOCX_MIME,
    PDF_MIME,
    DocumentParseError,
    extract_pages,
    extract_text,
)

router = APIRouter()
ALLOWED = {PDF_MIME, DOCX_MIME}


class ResumeCreateRequest(BaseModel):
    resume_text: str = Field(min_length=30, max_length=100_000)
    job_description: str = Field(min_length=30, max_length=100_000)


class CoverLetterRequest(BaseModel):
    resume_text: str = Field(min_length=30, max_length=100_000)
    job_description: str = Field(min_length=30, max_length=100_000)
    company: str = Field(default="", max_length=200)
    role: str = Field(default="", max_length=200)
    tone: str = Field(default="professional", max_length=40)


async def read_document(file: UploadFile) -> tuple[bytes, str]:
    if file.content_type not in ALLOWED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only PDF and DOCX files are supported.")
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds the {settings.max_upload_mb} MB limit.",
        )
    try:
        text = extract_text(file.filename or "document", file.content_type, content)
    except DocumentParseError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    if len(text) < 20:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "The document contains too little extractable text.",
        )
    if len(text) > settings.max_text_chars:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "The extracted document is too large to process safely.",
        )
    return content, text


@router.post("/parse")
async def parse_document(file: UploadFile = File(...)):
    _, text = await read_document(file)
    result: dict = {"filename": file.filename, "characters": len(text), "text": text}
    if settings.llm_configured:
        try:
            from app.ai.llm.schemas import DocumentInsight
            from app.ai.llm.service import structured

            insight = await structured(
                "document",
                "Analyze extracted document text for a career platform. Do not add facts not present in the text.",
                f"Filename: {file.filename}\n\nExtracted text:\n{text[: settings.llm_context_chars]}",
                DocumentInsight,
            )
            result["ai_insight"] = insight.model_dump()
        except Exception:
            result["ai_insight"] = None
    return result


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    content, _ = await read_document(file)
    return {"filename": file.filename, "size": len(content), "status": "accepted"}


@router.post("/knowledge/ingest")
async def ingest_knowledge(
    file: UploadFile = File(...), user: User = Depends(current_user)
):
    if user.email.lower() not in settings.knowledge_admin_emails:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Knowledge-base ingestion is restricted to CareerSetu administrators.",
        )
    content, text = await read_document(file)
    try:
        from app.ai.rag.store import KnowledgeStore

        pages = extract_pages(file.filename or "document", file.content_type, content)
        chunks = KnowledgeStore().add_text(text, file.filename or "document", pages=pages)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Knowledge store or embeddings are not configured.",
        ) from exc
    return {
        "filename": file.filename,
        "chunks_indexed": chunks,
        "message": "Document indexed in CareerSetu knowledge base.",
    }


@router.post("/resume/create")
async def create_resume(payload: ResumeCreateRequest, user: User = Depends(current_user)):
    try:
        from app.ai.llm.schemas import ResumeDraft
        from app.ai.llm.service import structured

        draft = await structured(
            "resume",
            "Create ATS-oriented resume content using only the candidate resume and target "
            "job description. Do not invent employers, dates, metrics, degrees, certifications, "
            "or tools. Improve wording and keyword alignment.",
            f"Current resume:\n{payload.resume_text[: settings.llm_context_chars]}\n\n"
            f"Target job:\n{payload.job_description[: settings.llm_context_chars]}",
            ResumeDraft,
        )
        return draft.model_dump()
    except Exception as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI resume generation is not configured. Set LLM_API_KEY on the backend.",
        ) from exc


@router.post("/resume/latex")
async def create_resume_latex(payload: ResumeCreateRequest, user: User = Depends(current_user)):
    """Build a downloadable, ATS-tailored LaTeX resume.

    Combines the deterministic gap analysis (missing skills / ATS keywords from
    the JD) with an LLM restructuring of the candidate's real resume, then
    renders a compilable ``.tex`` document. Returns the LaTeX plus the gap data
    so the SPA can highlight what was optimised.
    """
    from app.modules.analysis.service import analyze

    report = analyze(payload.resume_text, payload.job_description)
    missing_skills = [g["skill"] for g in report.get("gaps", []) if g.get("status") == "missing"]
    partial_skills = [g["skill"] for g in report.get("gaps", []) if g.get("status") == "partial"]
    matched_skills = [s["skill"] for s in report.get("strengths", [])]

    try:
        from app.ai.llm.schemas import LatexResumeContent
        from app.ai.llm.service import structured
        from app.modules.documents.latex_resume import render_latex

        system = (
            "You restructure a candidate's resume into ATS-optimised, structured content "
            "tailored to a target job, for rendering into LaTeX. STRICT RULES: use only facts "
            "present in the candidate's resume — never invent employers, roles, dates, degrees, "
            "metrics, certifications or tools. You MAY rephrase bullets for impact, reorder to "
            "surface the most job-relevant experience first, and naturally incorporate job-"
            "description keywords the candidate genuinely demonstrates. Extract accurate contact "
            "details. Write a 2-3 sentence objective tailored to the target role. Group skills "
            "into sensible categories and ensure legitimately-held skills that match the job "
            "description are represented. Keep bullets concise and results-oriented."
        )
        emphasis = ", ".join((partial_skills + missing_skills)[:15]) or "the job's core requirements"
        keyword_hint = ", ".join(missing_skills[:15]) or "none detected"
        content = await structured(
            "resume",
            system,
            f"Target job's key skills to emphasise where the resume supports them: {emphasis}\n"
            f"ATS keywords from the job the resume currently lacks (only include if truthful): {keyword_hint}\n\n"
            f"Candidate resume:\n{payload.resume_text[: settings.llm_context_chars]}\n\n"
            f"Target job description:\n{payload.job_description[: settings.llm_context_chars]}",
            LatexResumeContent,
        )
        latex = render_latex(content)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI resume generation is not configured or failed. Set a valid "
            f"LLM_API_KEY on the backend. ({exc.__class__.__name__})",
        ) from exc

    safe_name = (content.contact.name or "resume").strip().replace(" ", "_") or "resume"
    return {
        "latex": latex,
        "filename": f"{safe_name}_CareerSetu.tex",
        "content": content.model_dump(),
        "match_score": report.get("match_score", 0),
        "ats_coverage": report.get("ats_coverage", 0),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "partial_skills": partial_skills,
        "ats_keywords": content.ats_keywords,
    }


@router.post("/cover-letter")
async def create_cover_letter(payload: CoverLetterRequest, user: User = Depends(current_user)):
    try:
        from app.ai.llm.schemas import CoverLetterDraft
        from app.ai.llm.service import structured

        target = ", ".join(x for x in [payload.role, payload.company] if x) or "the target role"
        draft = await structured(
            "resume",
            "Write a concise, specific cover letter using only facts present in the candidate's "
            "resume and the job description. Do not invent experience, employers or metrics. "
            f"Match a {payload.tone} tone. Keep it to 3-4 short paragraphs.",
            f"Applying for: {target}\n\n"
            f"Resume:\n{payload.resume_text[: settings.llm_context_chars]}\n\n"
            f"Job description:\n{payload.job_description[: settings.llm_context_chars]}",
            CoverLetterDraft,
        )
        return draft.model_dump()
    except Exception as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI cover-letter generation is not configured. Set LLM_API_KEY on the backend.",
        ) from exc
