"""Structure-aware, page-aware document chunking for the RAG knowledge base."""
from __future__ import annotations

from dataclasses import dataclass

_TOPIC_KEYWORDS = {
    "coding": ["algorithm", "leetcode", "code", "data structure", "complexity"],
    "behavioral": ["behavioral", "strength", "conflict", "leadership", "situation"],
    "resume": ["resume", "cv", "experience", "project"],
    "interview": ["interview", "question", "answer"],
}


@dataclass
class DocumentChunk:
    text: str
    source: str
    page: int | None = None
    topic: str | None = None
    index: int = 0


def _topic(text: str) -> str:
    lowered = text.lower()
    for topic, words in _TOPIC_KEYWORDS.items():
        if any(w in lowered for w in words):
            return topic
    return "general"


def _fallback_split(text: str, size: int, overlap: int) -> list[str]:
    out, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        out.append(text[start:end])
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return out


def chunk_document(
    text: str,
    source: str,
    chunk_size: int = 900,
    overlap: int = 120,
    pages: list[dict] | None = None,
) -> list[DocumentChunk]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    except ImportError:
        splitter = None

    units = pages or [{"text": text, "page": None}]
    result: list[DocumentChunk] = []
    index = 0
    for unit in units:
        raw = " ".join((unit.get("text") or "").split())
        if not raw:
            continue
        parts = splitter.split_text(raw) if splitter else _fallback_split(raw, chunk_size, overlap)
        for part in parts:
            result.append(DocumentChunk(part, source, unit.get("page"), _topic(part), index))
            index += 1
    return result
