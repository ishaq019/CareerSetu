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


def _recursive_split(text: str, size: int, overlap: int) -> list[str]:
    """Split on the largest natural boundary that keeps chunks under ``size``.

    Mirrors LangChain's RecursiveCharacterTextSplitter behaviour with zero
    third-party dependencies: try paragraph, then line, then sentence, then
    word, then character boundaries, packing pieces greedily with overlap.
    """
    separators = ["\n\n", "\n", ". ", " ", ""]

    def split(chunk: str, seps: list[str]) -> list[str]:
        if len(chunk) <= size:
            return [chunk] if chunk else []
        sep = seps[0] if seps else ""
        rest = seps[1:] if len(seps) > 1 else [""]
        pieces = chunk.split(sep) if sep else list(chunk)
        out: list[str] = []
        for piece in pieces:
            unit = piece + sep if sep else piece
            if len(unit) > size:
                out.extend(split(unit, rest))
            else:
                out.append(unit)
        return out

    pieces = [p for p in split(text, separators) if p]
    # Greedily pack pieces into chunks of roughly ``size`` with ``overlap``.
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if current and len(current) + len(piece) > size:
            chunks.append(current.strip())
            tail = current[-overlap:] if overlap else ""
            current = tail + piece
        else:
            current += piece
    if current.strip():
        chunks.append(current.strip())
    return chunks or ([text] if text else [])


def chunk_document(
    text: str,
    source: str,
    chunk_size: int = 900,
    overlap: int = 120,
    pages: list[dict] | None = None,
) -> list[DocumentChunk]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    units = pages or [{"text": text, "page": None}]
    result: list[DocumentChunk] = []
    index = 0
    for unit in units:
        raw = " ".join((unit.get("text") or "").split())
        if not raw:
            continue
        parts = _recursive_split(raw, chunk_size, overlap)
        for part in parts:
            result.append(DocumentChunk(part, source, unit.get("page"), _topic(part), index))
            index += 1
    return result
