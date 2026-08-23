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
            "AI resume generation is not configured. Set LLM_PROVIDER=groq and LLM_API_KEY.",
        ) from exc


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
            "AI cover-letter generation is not configured. Set LLM_PROVIDER=groq and LLM_API_KEY.",
        ) from exc
