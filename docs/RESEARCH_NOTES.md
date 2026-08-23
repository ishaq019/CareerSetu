# CareerSetu Architecture Research Notes

Research checked on 18 Aug 2026 against current official/primary documentation and package release information.

## LangChain

- 2-step RAG is recommended when retrieval is a clear prerequisite because it is simple and predictable.
- Hybrid RAG adds query enhancement, retrieval validation and answer validation when the domain needs stronger quality control.
- Structured output with Pydantic gives machine-readable model responses instead of fragile natural-language parsing.

## LangGraph

- LangGraph is an orchestration/runtime layer for durable, stateful workflows.
- PostgreSQL checkpointers are the production persistence option for long-running stateful workflows.
- Smaller nodes provide better checkpoint/retry boundaries.

## Neon

- Neon is PostgreSQL and provides built-in connection pooling.
- Pooled endpoints use a `-pooler` hostname.
- CareerSetu avoids stacking a long-lived SQLAlchemy pool on top of a Neon pooler URL.

## ChromaDB

- Chroma supports explicit/custom embedding functions.
- CareerSetu uses explicit embeddings so the embedding model is controlled and reproducible.
- The knowledge collection is versioned to avoid mixing incompatible embedding/schema versions.

## Design conclusions

1. Deterministic score first; LLM second.
2. 2-step RAG for normal grounded chat.
3. LangGraph for adaptive interview state, not every request.
4. Structured LLM outputs for data consumed by the frontend/backend.
5. Explicit embeddings instead of implicit defaults.
6. Stable chunk IDs for idempotent ingestion.
7. Page metadata for evidence.
8. Strict context/token budgets for cost and latency control.
9. Treat retrieved/user content as untrusted data.
10. Persist long-running agent state only when the product actually needs resume/recovery.
