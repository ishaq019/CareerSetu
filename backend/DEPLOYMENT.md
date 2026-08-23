# CareerSetu Backend — Vercel Deployment & Dependency Optimization

This backend was slimmed to fit **Vercel's 250 MB unzipped serverless limit**.
The bloat came entirely from the full `chromadb` package, which drags in
`onnxruntime` (~200 MB), plus `tokenizers`, `numpy`, `grpcio`, `kubernetes`,
`opentelemetry`, `huggingface_hub`, and `chromadb_rust_bindings`. None are
needed: retrieval is **lexical** (no embeddings) and Chroma now runs on
**Chroma Cloud** over HTTP.

## What changed

| Package | Before | After | Why |
|---|---|---|---|
| `chromadb` (full) | installed | **removed** → `chromadb-client` (thin HTTP client) | Eliminates onnxruntime, tokenizers, numpy, grpcio, kubernetes, opentelemetry |
| `uvicorn[standard]` | runtime | **dev only** | Vercel provides the ASGI server |
| `alembic` | runtime | **dev only** | Migrations run from your machine/CI, not in the function |
| `pytest` | runtime | **dev only** | Test tooling, not needed at runtime |
| `bcrypt` | installed | **removed** | Auth uses stdlib PBKDF2-SHA256 (`security.py`), never bcrypt |
| `unicorn` | installed | **removed** | Unrelated CPU-emulator package installed by mistake (not `uvicorn`) |
| `psycopg[binary,pool]` | runtime | `psycopg[binary]` | Serverless uses short-lived NullPool; `pool` extra dropped |

Files added/updated:
- `requirements.txt` — slim runtime set (what Vercel installs)
- `requirements-dev.txt` — everything above **plus** uvicorn/alembic/pytest/psycopg-pool for local dev
- `api/index.py` — ASGI entrypoint exposing `app.main:app`
- `vercel.json` — routes all traffic to the function, 60s max duration
- `.vercelignore` — keeps `.venv`, tests, migrations, and secrets out of the bundle

## Expected size

- **Before:** ~450–550 MB unzipped (onnxruntime alone ~200 MB) — over the limit.
- **After:** ~150–200 MB unzipped — comfortably under 250 MB.

## Run these on YOUR machine (the sandbox is offline and can't pip)

From `backend/`, rebuild the virtualenv cleanly so no stale heavy packages leak
into local runs or a `pip freeze`:

**Windows (PowerShell):**
```powershell
cd backend
# Remove the old heavy packages (or just recreate the venv, below)
pip uninstall -y chromadb chromadb-rust-bindings onnxruntime tokenizers `
  huggingface_hub hf_xet kubernetes grpcio bcrypt unicorn `
  opentelemetry-sdk opentelemetry-api opentelemetry-exporter-otlp-proto-grpc

# Then install the slim + dev set
pip install -r requirements-dev.txt
```

**Cleaner — recreate the venv from scratch (recommended):**
```powershell
cd backend
rmdir /s /q .venv          # or: Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements-dev.txt
```

Verify the app still imports and tests pass:
```powershell
python -c "from app.main import app; print('ok')"
pytest -q
```

## Deploy to Vercel

1. Push the repo to GitHub/GitLab.
2. In Vercel → New Project → import the repo.
3. **Set Root Directory to `backend`.** (Critical — so `vercel.json`,
   `requirements.txt`, and `api/index.py` resolve correctly.)
4. Add Environment Variables (Project → Settings → Environment Variables):
   - `ENVIRONMENT=production`
   - `DATABASE_URL` — your Neon Postgres URL (do NOT rely on SQLite; the function filesystem is ephemeral/read-only)
   - `JWT_SECRET` — a long random string
   - `CORS_ORIGINS` — your frontend origin(s)
   - `LLM_API_KEY` (Groq) — optional; AI routes return 503 without it
   - `CHROMA_API_KEY`, `CHROMA_TENANT`, `CHROMA_DATABASE` — for Chroma Cloud (optional)
5. Deploy. The API is served at `https://<project>.vercel.app/api/v1/...`
   and health at `/health`.

## Notes

- Run migrations from your machine/CI against the production DB:
  `alembic upgrade head` (alembic is in `requirements-dev.txt`).
- The slim `chromadb-client` exposes the same `chromadb.CloudClient` /
  `chromadb.HttpClient` API used in `app/ai/rag/store.py`; the store also has a
  fallback that points an `HttpClient` at `api.trychroma.com` if a given thin
  client build lacks the `CloudClient` shortcut.
- If a future `chromadb-client` version bound differs, pin it explicitly, e.g.
  `chromadb-client==1.0.0`.
