"""LLM access boundary.

CareerSetu talks to an OpenAI-compatible LLM gateway (OpenRouter) over plain
HTTP with ``httpx`` — no vendor SDK, no langchain. A single API key
(``LLM_API_KEY``) and one model (``LLM_MODEL``, default a free-tier OpenRouter
slug) are used for every task. Calls run at temperature 0 with bounded timeout,
retries and output tokens. ``structured`` coerces the reply into a Pydantic
schema; ``text`` returns the raw assistant message.
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMUnavailable(RuntimeError):
    """Raised when the LLM provider is not configured or cannot be reached."""


class LLMCallFailed(RuntimeError):
    """Raised when the provider IS configured but the call failed (bad model,
    rate limit, malformed reply, or upstream error). Distinct from
    ``LLMUnavailable`` so callers can show an accurate message."""


def _endpoint() -> str:
    base = (settings.llm_base_url or "https://openrouter.ai/api/v1").rstrip("/")
    # Accept either a bare gateway root or a full ``/v1`` base URL.
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _headers() -> dict[str, str]:
    key = settings.llm_api_key
    scheme = (settings.llm_auth_scheme or "bearer").lower()
    auth = key if scheme == "raw" else f"Bearer {key}"
    headers = {"Authorization": auth, "Content-Type": "application/json"}
    # Optional OpenRouter attribution headers (used for their dashboard/rankings
    # only). Harmless for any other OpenAI-compatible gateway.
    if settings.llm_referer:
        headers["HTTP-Referer"] = settings.llm_referer
    if settings.llm_app_title:
        headers["X-Title"] = settings.llm_app_title
    return headers


async def _chat(messages: list[dict[str, str]], *, json_mode: bool) -> str:
    """POST to the gateway and return the assistant message content."""
    if not settings.llm_configured:
        raise LLMUnavailable("LLM provider is not configured. Set LLM_API_KEY.")

    payload: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": settings.llm_max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    url = _endpoint()
    headers = _headers()
    last_exc: Exception | None = None
    attempts = max(1, settings.llm_max_retries + 1)
    json_fallback_tried = False

    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        for attempt in range(attempts):
            try:
                resp = await client.post(url, headers=headers, json=payload)
            except httpx.HTTPError as exc:
                last_exc = exc
            else:
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        return str(data["choices"][0]["message"]["content"] or "")
                    except (KeyError, IndexError, ValueError) as exc:
                        raise LLMCallFailed(
                            "LLM gateway returned an unexpected response shape"
                        ) from exc
                # Some free models reject ``response_format`` with a 4xx. Since
                # ``structured()`` also embeds the schema in the prompt, drop the
                # JSON-mode hint once and retry rather than failing outright.
                if (
                    json_mode
                    and not json_fallback_tried
                    and "response_format" in payload
                    and resp.status_code in (400, 404, 415, 422)
                ):
                    payload.pop("response_format", None)
                    json_fallback_tried = True
                    continue
                # 429 / 5xx are worth retrying; other 4xx are terminal.
                if resp.status_code in (408, 409, 425, 429) or resp.status_code >= 500:
                    last_exc = LLMCallFailed(
                        f"gateway returned HTTP {resp.status_code}"
                    )
                else:
                    detail = resp.text[:300]
                    raise LLMCallFailed(
                        f"gateway returned HTTP {resp.status_code}: {detail}"
                    )
            if attempt < attempts - 1:
                await asyncio.sleep(0.5 * (attempt + 1))

    raise LLMCallFailed(str(last_exc) if last_exc else "LLM call failed")


def _extract_json(raw: str) -> str:
    """Pull a JSON object out of a model reply that may be fenced or chatty."""
    s = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", s, re.DOTALL)
    if fence:
        s = fence.group(1).strip()
    if s.startswith("{") and s.endswith("}"):
        return s
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return s[start : end + 1]
    return s


async def structured(task: str, system: str, user: str, schema: type[T]) -> T:
    """Call the LLM and coerce the reply into ``schema``.

    ``task`` is accepted for call-site clarity (all tasks share one model).
    """
    json_schema = json.dumps(schema.model_json_schema(), separators=(",", ":"))
    system_json = (
        f"{system}\n\nRespond with a SINGLE JSON object that strictly matches this "
        f"JSON schema. Output only the JSON, no prose, no code fences.\n"
        f"JSON schema:\n{json_schema}"
    )
    raw = await _chat(
        [{"role": "system", "content": system_json}, {"role": "user", "content": user}],
        json_mode=True,
    )
    candidate = _extract_json(raw)
    try:
        return schema.model_validate_json(candidate)
    except ValidationError as exc:
        raise LLMCallFailed(
            f"LLM returned JSON that does not match {schema.__name__}: {exc}"
        ) from exc
    except ValueError as exc:
        raise LLMCallFailed("LLM did not return valid JSON") from exc


async def text(task: str, system: str, user: str) -> str:
    raw = await _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        json_mode=False,
    )
    return raw.strip()
