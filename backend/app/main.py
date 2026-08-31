"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import models  # noqa: F401  (register ORM models)
from app.api.router import api_router
from app.core.config import settings
from app.db import Base, engine

VERSION = "1.2.0"


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Refuse to boot with a weak/placeholder JWT secret in production — better
    # to crash loud than silently sign every session with a forgeable key.
    settings.validate_for_environment()
    # In development we auto-create tables so the app runs without a manual
    # migration step. Production should run ``alembic upgrade head`` instead.
    if settings.environment == "development":
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            # Persistence is optional for the guest analysis path.
            pass
    yield


app = FastAPI(
    title=settings.app_name,
    version=VERSION,
    description="CareerSetu — AI career intelligence API",
    lifespan=lifespan,
)

# CORS. ``allow_origins`` is the env-overridable explicit list; ``allow_origin_regex``
# is a safety net for the production domain (and any subdomain) so a misconfigured
# or stale ``CORS_ORIGINS`` env var on the host can never silently break sign-in —
# Starlette ORs the regex with the list, so localhost entries still work. A browser
# Origin is scheme://host[:port] with no trailing slash, which is what these match.
# Anchored at both ends so ``syedishaq.me.evil.example`` cannot match.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https://([a-z0-9-]+\.)*syedishaq\.me$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(SQLAlchemyError)
async def _db_error(_: Request, exc: SQLAlchemyError):
    """One place to turn a persistence failure into a clean 500.

    ``get_db`` already closes (and therefore rolls back) the session in its
    ``finally``, so routes don't need their own try/rollback blocks.
    """
    logging.getLogger("careersetu.db").exception("Database error", exc_info=exc)
    return JSONResponse(
        status_code=500, content={"detail": "Database error. Please try again."}
    )


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "careersetu-api", "version": VERSION}


@app.get("/health/db", tags=["health"])
def database_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "sqlite" if settings.is_sqlite else "postgresql",
        }
    except Exception:
        return {
            "status": "degraded",
            "message": "Database unavailable; guest analysis can still run.",
        }


@app.get("/health/ai", tags=["health"])
def ai_health():
    return {
        "provider_configured": settings.llm_configured,
        "provider": settings.llm_provider or None,
        "retrieval_mode": "lexical_chroma",
        "chroma_configured": settings.chroma_configured,
        "chroma_mode": "cloud" if settings.chroma_cloud else "self_hosted",
        "fast_model": settings.llm_fast_model,
        "quality_model": settings.llm_quality_model,
        "rag_collection": "careersetu_knowledge_v2",
    }
