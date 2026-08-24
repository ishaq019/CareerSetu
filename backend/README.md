# ⚙️ CareerSetu — Backend

FastAPI service powering CareerSetu's analysis, authentication, RAG chat and adaptive interview features. Optimized for **Vercel serverless** (under the 250 MB limit).

## 🧱 Tech stack

- 🚀 **FastAPI** + **Starlette** — async web API
- 🗄️ **SQLAlchemy 2.0** + **Alembic** — ORM & migrations
- 🐘 **psycopg 3** — Neon / PostgreSQL driver (defaults to SQLite for zero-config local dev)
- 🔐 **PyJWT** — signed JWTs; passwords hashed with stdlib **PBKDF2-SHA256**
- 🌐 **OpenAI-compatible LLM gateway** (OpenRouter, free-tier model) over **httpx** — optional, lazy-loaded AI stack (no vendor SDK)
- 🟣 **chromadb-client** — thin Chroma Cloud HTTP client (lexical retrieval, no embeddings)

## 🚀 Quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1

pip install -r requirements-dev.txt   # full local toolchain
cp .env.example .env                  # then edit values

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive API docs.

## 📦 Dependencies

| File | Use |
|---|---|
| `requirements.txt` | 🪶 **Slim runtime** — what Vercel installs (no uvicorn/alembic/pytest) |
| `requirements-dev.txt` | 🛠️ Runtime **+** local tooling (uvicorn, alembic, pytest, psycopg-pool) |

The full `chromadb` package is intentionally **not** used — it pulls in `onnxruntime`, `tokenizers`, `numpy`, `grpcio`, `kubernetes` and `opentelemetry` (~300 MB+). The thin `chromadb-client` keeps the bundle lightweight since retrieval is lexical and Chroma runs in the cloud.

## 🔑 Environment variables

```env
ENVIRONMENT=development
DATABASE_URL=postgresql+psycopg://...     # optional; defaults to SQLite
JWT_SECRET=change-me-to-a-long-random-string
CORS_ORIGINS=http://localhost:5173

# Optional AI stack
LLM_API_KEY=your_openrouter_api_key   # from https://openrouter.ai/keys
LLM_MODEL=google/gemma-4-26b-a4b-it:free   # any free-tier slug (ends in :free)
CHROMA_API_KEY=your_chroma_cloud_key
CHROMA_TENANT=your_tenant_id
CHROMA_DATABASE=careersetu
KNOWLEDGE_ADMIN_EMAILS=admin@example.com
```

See `.env.example` for the complete list. Never commit `.env`.

## 📂 Structure

```text
backend/
├─ api/
│  └─ index.py        ☁️ Vercel ASGI entrypoint (exposes app.main:app)
├─ app/
│  ├─ main.py         FastAPI app + health routes
│  ├─ api/            route router
│  ├─ core/           config & security (JWT, PBKDF2)
│  ├─ modules/        analysis · auth · documents · roadmap
│  └─ ai/             llm (httpx gateway) · rag (lexical knowledge store)
├─ migrations/        Alembic migrations
├─ tests/             pytest suite
├─ requirements.txt   slim runtime deps (Vercel)
├─ requirements-dev.txt
├─ vercel.json        serverless routing
└─ DEPLOYMENT.md      Vercel deploy + size-optimization guide
```

## 🧪 Tests

```bash
pytest -q
```

Covers deterministic analysis, document boundaries, authentication and AI schema/chunking. External LLM/Chroma/Neon calls should be tested separately with disposable credentials.

## ☁️ Deployment

Set the Vercel **Root Directory** to `backend`. Full walkthrough and the exact pip cleanup commands are in [`DEPLOYMENT.md`](DEPLOYMENT.md).
