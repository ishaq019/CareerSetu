"""Thin typed wrapper around :class:`KnowledgeStore` search results."""
from __future__ import annotations

from dataclasses import dataclass

from app.ai.rag.store import KnowledgeStore


@dataclass
class RetrievedChunk:
    text: str
    source: str
    page: int | None
    score: float


class RAGRetriever:
    def __init__(self):
        self.store = KnowledgeStore()

    def retrieve(self, query: str, top_k: int = 8, where: dict | None = None) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(x["text"], x["source"], x["page"], x["score"])
            for x in self.store.search(query, top_k, where)
        ]
