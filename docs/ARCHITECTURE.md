# CareerSetu System Architecture

```text
                           +----------------------+
                           | React / TypeScript UI |
                           +----------+-----------+
                                      |
                               REST / Multipart
                                      |
                           +----------v-----------+
                           |       FastAPI        |
                           +----------+-----------+
                                      |
             +------------------------+-------------------------+
             |                        |                         |
      +------v------+         +-------v------+          +-------v-------+
      | Deterministic|         | Auth / Users |          | AI Services   |
      | Analysis     |         | JWT / OAuth  |          | LangChain     |
      +------+-------+         +-------+------+          | LangGraph     |
             |                         |                 +---+-------+---+
             |                         |                     |       |
             |                 +-------v------+       +------v-+ +--v------+
             |                 | Neon/Postgres|       | Chroma | | LLM/API |
             |                 +--------------+       +--------+ +---------+
             |
             +--> Match score / coverage / gaps / baseline roadmap
```

## Request classes

### Guest, low-cost path

Resume/JD analysis is deterministic and stateless. PostgreSQL is not required for the request to succeed.

### Authenticated application path

Persistent user data belongs in Neon/PostgreSQL. Sensitive resume text should only be stored when the user explicitly requests a saved profile/application feature and the product has a clear retention policy.

### Knowledge path

Trusted interview PDFs are ingested by an administrator or controlled ingestion job. They are embedded and stored in ChromaDB. User documents never directly modify the global knowledge base.

### AI path

Use 2-step RAG for grounded chat because it is predictable. Use LangGraph for adaptive interview state because the workflow needs state, branching and eventual checkpointing.
