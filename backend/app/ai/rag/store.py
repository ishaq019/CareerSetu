"""ChromaDB-backed knowledge store with idempotent ingestion and hybrid-friendly
lexical retrieval.

Chunk IDs are derived from source/page/content hashes so re-ingesting the same
document is idempotent. Retrieval currently uses lexical overlap scoring, which
requires no paid embeddings API while still handling exact technical terms well.
"""
from __future__ import annotations

import hashlib
import re

from app.ai.rag.ingestion import chunk_document
from app.core.config import settings

_TOKEN_RE = re.compile(r"[a-z0-9+#.]{2,}")


class KnowledgeStore:
    COLLECTION = "careersetu_knowledge_v2"

    def __init__(self):
        import chromadb

        if settings.chroma_cloud:
            # Chroma Cloud — managed, no local server required. Works with both
            # the full `chromadb` package and the slim `chromadb-client`.
            cloud_client = getattr(chromadb, "CloudClient", None)
            if cloud_client is not None:
                self.client = cloud_client(
                    api_key=settings.chroma_api_key,
                    tenant=settings.chroma_tenant,
                    database=settings.chroma_database,
                )
            else:
                # Older thin clients without the CloudClient shortcut: point an
                # HttpClient at the Chroma Cloud API endpoint with auth headers.
                self.client = chromadb.HttpClient(
                    host="api.trychroma.com",
                    port=8000,
                    ssl=True,
                    tenant=settings.chroma_tenant,
                    database=settings.chroma_database,
                    headers={"x-chroma-token": settings.chroma_api_key},
                )
        else:
            # Self-hosted Chroma server fallback.
            self.client = chromadb.HttpClient(
                host=settings.chroma_host, port=settings.chroma_port
            )
        self.collection = self.client.get_or_create_collection(
            self.COLLECTION,
            metadata={
                "description": "Trusted CareerSetu interview and career knowledge",
                "schema_version": "2",
            },
        )

    @staticmethod
    def _lexical_score(query: str, text: str) -> float:
        q = set(_TOKEN_RE.findall(query.lower()))
        t = set(_TOKEN_RE.findall(text.lower()))
        return len(q & t) / max(len(q), 1)

    def add_text(self, text: str, source: str, pages: list[dict] | None = None) -> int:
        chunks = chunk_document(text, source, pages=pages)
        if not chunks:
            return 0
        source_key = hashlib.sha256(source.encode()).hexdigest()[:16]
        ids, docs, metas = [], [], []
        for chunk in chunks:
            chunk_key = hashlib.sha256(
                f"{source}|{chunk.page}|{chunk.text}".encode()
            ).hexdigest()[:32]
            ids.append(f"{source_key}:{chunk_key}")
            docs.append(chunk.text)
            metas.append(
                {
                    "source": chunk.source,
                    "page": chunk.page or 0,
                    "chunk_index": chunk.index,
                    "topic": chunk.topic or "general",
                }
            )
        self.collection.upsert(ids=ids, documents=docs, metadatas=metas)
        return len(chunks)

    def search(self, query: str, top_k: int = 8, where: dict | None = None) -> list[dict]:
        query = query.strip()
        if not query:
            return []
        result = self.collection.get(where=where, limit=200, include=["documents", "metadatas"])
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []

        candidates: list[dict] = []
        for i, doc in enumerate(docs):
            score = self._lexical_score(query, doc)
            if score <= 0:
                continue
            meta = metas[i] or {}
            candidates.append(
                {
                    "text": doc,
                    "source": meta.get("source", "unknown"),
                    "page": meta.get("page") or None,
                    "score": round(score, 4),
                }
            )
        candidates.sort(key=lambda x: x["score"], reverse=True)

        # Deduplicate near-identical chunks before sending context to an LLM.
        seen: set = set()
        output: list[dict] = []
        for item in candidates:
            key = (item["source"], item["page"], item["text"][:120])
            if key in seen:
                continue
            seen.add(key)
            output.append(item)
            if len(output) >= top_k:
                break
        return output
