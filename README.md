<div align="center">

# 🎯 CareerSetu

**AI-powered career intelligence — know if a job fits, close your skill gaps, and prepare to win the interview.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Deploy](https://img.shields.io/badge/Deploy-Vercel-000000?logo=vercel&logoColor=white)](https://vercel.com/)

</div>

---

## 📖 Overview

**CareerSetu** helps a candidate decide whether a job is a good fit, understand their skill gaps, build a learning roadmap, prepare for interviews, optimize application documents, and ask grounded questions about career and interview material.

> ⚠️ **Note:** CareerSetu's Match Score is an **internal compatibility score**. It is *not* an official ATS score and must not be presented as a probability of getting shortlisted.

## ✨ Features

- 🧮 **Deterministic job-fit analysis** — Match Score, ATS-style coverage, strengths with evidence, skill gaps, and an application recommendation, all computed *without* an LLM so results are cheap, repeatable and explainable.
- 📄 **Document parsing** — page-aware PDF and DOCX extraction for resumes and job descriptions.
- 🗺️ **Learning roadmap** — turns skill gaps into a saved, per-user learning plan.
- 💬 **Grounded chat (RAG)** — answers questions from trusted interview/career knowledge with citation validation.
- 🎙️ **Adaptive interview** — a stateful LangGraph workflow that evaluates answers and adjusts difficulty.
- ✍️ **Application documents** — resume optimization and tailored cover-letter generation.
- 🔐 **Auth & accounts** — email/password with salted PBKDF2-SHA256 hashing and signed JWTs.

## 🧭 Product workflow

```text
Guest
  ├─ Resume (paste / PDF / DOCX)
  └─ Job description
        │
        ▼
Deterministic analysis
  ├─ Match Score
  ├─ ATS-oriented coverage
  ├─ Strengths / evidence
  ├─ Skill gaps
  ├─ Application recommendation
  └─ Baseline skill roadmap
        │
        ▼
Sign in / Sign up  ──►  Advanced features
                          ├─ Interview preparation & adaptive evaluation
                          ├─ Resume optimization
                          ├─ Cover-letter generation
                          ├─ Grounded CareerSetu chat
                          └─ Saved roadmap / progress
```

## 🧠 Why the AI architecture is optimized

The project deliberately does **not** send every request to an LLM.

### 🧮 Job-fit analysis — no LLM required

```text
Resume + JD → requirement extraction → evidence matching
            → deterministic score → gaps → roadmap
```

This makes the score cheap, repeatable and explainable. When `LLM_API_KEY` is present, Groq is used only to *improve* wording, gap prioritization and roadmap steps — never to replace the deterministic score.

### 💬 Grounded chat — 2-step RAG

```text
Question → Chroma retrieval → lexical rerank → deduplication
         → context budget → structured LLM answer → citation validation
```

Retrieval uses **lexical (token-overlap) scoring**, so it needs **no paid embeddings API**. Groq produces the final grounded answer, and invalid citations are stripped before they reach the frontend.

### 🎙️ Interview — LangGraph

```text
Candidate profile → retrieve material → question → candidate answer
   → structured evaluation → difficulty adjustment → next question
```

LangGraph is used because interview preparation needs state, branching and eventual persistence. For production, enable PostgreSQL checkpoint persistence so an interrupted interview can resume.

## 🏗️ Architecture

```text
React + TypeScript + Vite
        │  REST / multipart
        ▼
     FastAPI
        ├─ deterministic analysis
        ├─ authentication (JWT)
        ├─ document extraction
        ├─ roadmap
        ├─ RAG ingestion / retrieval
        ├─ grounded chat
        └─ interview graph
             │
             ├─ 🐘 Neon PostgreSQL   users / application data / checkpoints
             ├─ 🟣 Chroma Cloud       trusted interview knowledge (lexical)
             ├─ 🦜 LangChain          chunking / structured LLM integration
             ├─ 🕸️ LangGraph          adaptive interview workflow
             └─ ⚡ Groq (LLM)         generation / evaluation
```

## 🚀 Quick start

### 1️⃣ Backend

> Python 3.10+ recommended.

```bash
cd backend
python -m venv .venv

# Linux / macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Local dev installs the full toolchain (uvicorn, alembic, pytest)
pip install -r requirements-dev.txt

cp .env.example .env        # then edit values
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 2️⃣ Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

```env
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 🐘 Neon PostgreSQL

Neon is standard PostgreSQL with built-in connection pooling. Use the **pooled** connection string (its hostname contains `-pooler`).

```env
# backend/.env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@YOUR-HOST-POOLER.REGION.aws.neon.tech/neondb?sslmode=require
DATABASE_POOL_MODE=auto
```

`DATABASE_POOL_MODE=auto` detects Neon pooler URLs and avoids stacking an extra long-lived SQLAlchemy pool on top of Neon's PgBouncer. Direct PostgreSQL URLs use a small application pool with `pool_pre_ping`. Verify with `curl http://localhost:8000/health/db`.

## 🟣 Chroma Cloud (RAG knowledge store)

Trusted interview-preparation material is stored in **Chroma Cloud** and retrieved with lexical scoring — no local Chroma server and no embeddings required.

```env
# backend/.env
CHROMA_API_KEY=your_chroma_cloud_key
CHROMA_TENANT=your_tenant_id
CHROMA_DATABASE=careersetu
```

The backend uses the thin `chromadb-client` package (`chromadb.CloudClient`), keeping the deployment lightweight. Ingestion is restricted to `KNOWLEDGE_ADMIN_EMAILS` — user-uploaded resumes are untrusted data and must never poison the global knowledge base.

## ⚡ LLM configuration (Groq)

CareerSetu uses **Groq** as its only LLM provider, isolated behind `app/ai/llm/service.py`.

```env
LLM_PROVIDER=groq
LLM_API_KEY=your_groq_api_key
LLM_FAST_MODEL=llama-3.1-8b-instant
LLM_QUALITY_MODEL=llama-3.3-70b-versatile
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_MAX_TOKENS=1200
LLM_CONTEXT_CHARS=12000
```

If `LLM_API_KEY` is unset, AI routes return `503` and the deterministic analysis path still works.

## 🔌 API map

| Endpoint | Access | Purpose |
|---|---|---|
| `GET /health` | 🌐 Public | API health |
| `GET /health/db` | 🌐 Public | PostgreSQL connectivity |
| `GET /health/ai` | 🌐 Public | AI configuration status |
| `POST /api/v1/analysis` | 👤 Guest | Resume/JD analysis |
| `POST /api/v1/documents/parse` | 👤 Guest | PDF/DOCX extraction |
| `POST /api/v1/auth/signup` | 🌐 Public | Create account |
| `POST /api/v1/auth/login` | 🌐 Public | Sign in |
| `GET /api/v1/auth/me` | 🔐 Auth | Current user |
| `POST /api/v1/roadmap/generate` | 🔐 Auth | Roadmap generation |
| `POST /api/v1/chat` | 🔐 Auth | Grounded knowledge chat |
| `POST /api/v1/interview/evaluate` | 🔐 Auth | LangGraph interview evaluation |
| `POST /api/v1/documents/knowledge/ingest` | 🛡️ Admin | Trusted RAG ingestion |

## ☁️ Deploy to Vercel

The backend is optimized to stay under Vercel's **250 MB** serverless limit. Full instructions live in [`backend/DEPLOYMENT.md`](backend/DEPLOYMENT.md).

1. Push the repo to GitHub.
2. Import it in Vercel and **set the Root Directory to `backend`**.
3. Add environment variables (`DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, and optionally `LLM_API_KEY`, `CHROMA_*`).
4. Deploy — the API is served at `https://<project>.vercel.app/api/v1/...`.

## 🧪 Tests

```bash
cd backend
pytest -q
```

Tests cover deterministic analysis, document boundaries, authentication and AI schema/chunking. External LLM/Chroma/Neon tests should run separately with disposable test credentials.

## 📂 Repository structure

```text
CareerSetu/
├─ backend/     FastAPI API, AI stack, migrations, Vercel config
├─ frontend/    React 19 + Vite SPA
├─ docs/        Architecture, product spec, research notes
└─ README.md
```

## 🗺️ Implementation status

**✅ Implemented:** React UI · FastAPI API · Neon/PostgreSQL config · Alembic migrations · email/password auth · JWT protection · guest resume/JD analysis · PDF/DOCX extraction · page-aware processing · Chroma Cloud knowledge store · lexical hybrid retrieval · grounded structured chat · LangGraph interview evaluation · roadmap endpoint · security boundaries.

**🚧 Roadmap:** full Google OAuth callback/session flow · persistent LangGraph checkpoints · resume-optimization PDF delivery · background ingestion workers · object storage · production rate limiting and observability.

## 📄 License

Released for educational and portfolio use. Add a license file before public distribution.

<div align="center">

Made with ❤️ for job seekers.

</div>

"# CareerSetu" 
