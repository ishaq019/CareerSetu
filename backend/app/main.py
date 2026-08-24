"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import models  # noqa: F401  (register ORM models)
from app.api.router import api_router
from app.core.config import settings
from app.db import Base, engine

VERSION = "1.2.0"


@asynccontextmanager
async def lifespan(_: FastAPI):
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix="/api/v1")


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
