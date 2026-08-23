"""LLM access boundary.

Groq is the only supported provider and it is isolated behind this module so the
rest of the app never imports a vendor SDK directly. Fast vs. quality models are
selected per task; all calls run at temperature 0 with bounded timeout, retries
and output tokens.
"""
from __future__ import annotations

from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel

from app.core.config import settings

T = TypeVar("T", bound=BaseModel)

_FAST_TASKS = {"chat", "interview", "evaluate", "question"}


class LLMUnavailable(RuntimeError):
    """Raised when the LLM provider is not configured or cannot be reached."""


@lru_cache(maxsize=8)
def _model(task: str = "default"):
    if not settings.llm_configured:
        raise LLMUnavailable("LLM provider is not configured")
    if settings.llm_provider.lower() != "groq":
        raise LLMUnavailable("Only Groq is supported. Set LLM_PROVIDER=groq.")
    try:
        from langchain_groq import ChatGroq
    except ImportError as exc:  # pragma: no cover - import guard
        raise LLMUnavailable("langchain-groq is not installed") from exc

    model_name = settings.llm_fast_model if task in _FAST_TASKS else settings.llm_quality_model
    return ChatGroq(
        model=model_name,
        api_key=settings.llm_api_key,
        temperature=0,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        max_tokens=settings.llm_max_tokens,
    )


async def structured(task: str, system: str, user: str, schema: type[T]) -> T:
    model = _model(task).with_structured_output(schema)
    result = await model.ainvoke([("system", system), ("human", user)])
    if not isinstance(result, schema):
        raise LLMUnavailable("LLM returned an invalid structured response")
    return result


async def text(task: str, system: str, user: str) -> str:
    result = await _model(task).ainvoke([("system", system), ("human", user)])
    content = getattr(result, "content", "")
    if isinstance(content, list):
        content = "".join(
            str(x.get("text", x)) if isinstance(x, dict) else str(x) for x in content
        )
    return str(content).strip()
