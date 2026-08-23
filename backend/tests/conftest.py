"""Pytest configuration.

Forces an in-memory SQLite database and a deterministic JWT secret *before* the
application (and its settings singleton) are imported, so the whole suite runs
without any external services.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "sqlite://")  # in-memory
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-only-do-not-use")
os.environ.setdefault("LLM_API_KEY", "")  # keep AI paths disabled during tests

import pytest  # noqa: E402


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.db import Base, engine
    from app.main import app

    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
