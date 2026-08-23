"""Vercel serverless entrypoint.

Vercel's @vercel/python runtime auto-detects a module-level ``app`` that is an
ASGI application and serves it directly — no uvicorn needed. All routing is
handled by ``vercel.json`` rewriting every request to this function.

Set the Vercel Project "Root Directory" to ``backend`` so that this file lives
at ``api/index.py`` and ``requirements.txt`` is picked up from the backend root.
"""
from app.main import app  # noqa: F401  (ASGI app exposed for Vercel)
