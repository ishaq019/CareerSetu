"""Database engine, session factory and declarative base.

Supports SQLite (default, zero-config local dev) and PostgreSQL/Neon. When a Neon
*pooler* URL is detected we avoid stacking a long-lived SQLAlchemy pool on top of
Neon's server-side PgBouncer by using ``NullPool``.

Engine construction is defensive: if the database driver cannot be imported (e.g.
a serverless cold start where ``psycopg`` failed to load), we degrade gracefully
to ``engine = None`` instead of crashing the whole app at import time. The guest
analysis path and health checks keep working; DB-backed routes return a clean
error.
"""
from __future__ import annotations

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _is_neon_pooler(url: str) -> bool:
    return "-pooler." in url or ".pooler." in url


def _build_engine():
    url = settings.database_url

    if settings.is_sqlite:
        # check_same_thread=False lets the FastAPI thread pool share the connection.
        connect_args = {"check_same_thread": False}
        # An in-memory SQLite DB must use StaticPool so every session sees the
        # same underlying connection (used by the test-suite).
        if ":memory:" in url or url.endswith("://"):
            return create_engine(
                url, connect_args=connect_args, poolclass=StaticPool, future=True
            )
        return create_engine(url, connect_args=connect_args, future=True)

    pool_mode = settings.database_pool_mode.lower()
    use_null_pool = pool_mode == "null" or (
        pool_mode == "auto" and _is_neon_pooler(url)
    )
    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if use_null_pool:
        kwargs["poolclass"] = NullPool
    else:
        kwargs.update(pool_size=5, max_overflow=5, pool_recycle=1800)
    return create_engine(url, **kwargs)


engine = None
try:
    engine = _build_engine()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
except Exception:  # pragma: no cover - driver/connect-arg failure at cold start
    logger.exception("Database engine could not be created; DB routes will 503")
    SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        from fastapi import HTTPException, status

        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Database is unavailable. Check DATABASE_URL and the psycopg driver.",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
