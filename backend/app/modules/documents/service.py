"""PDF / DOCX text extraction with page-aware output."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class DocumentParseError(ValueError):
    """Raised when a document cannot be parsed or is an unsupported type."""


def extract_pages(filename: str, content_type: str | None, data: bytes) -> list[dict]:
    ext = Path(filename or "").suffix.lower()

    if ext == ".pdf" or content_type == PDF_MIME:
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(data))
            return [
                {"page": i + 1, "text": page.extract_text() or ""}
                for i, page in enumerate(reader.pages)
            ]
        except Exception as exc:
            raise DocumentParseError("Unable to parse PDF") from exc

    if ext == ".docx" or content_type == DOCX_MIME:
        try:
            from docx import Document

            doc = Document(BytesIO(data))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return [{"page": None, "text": text}]
        except Exception as exc:
            raise DocumentParseError("Unable to parse DOCX") from exc

    raise DocumentParseError("Only PDF and DOCX files are supported.")


def extract_text(filename: str, content_type: str | None, data: bytes) -> str:
    pages = extract_pages(filename, content_type, data)
    return "\n\n".join(x["text"] for x in pages).strip()
