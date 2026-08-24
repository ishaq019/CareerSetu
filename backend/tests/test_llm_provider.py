import asyncio

import pytest

from app.ai.llm.service import (
    LLMUnavailable,
    _chat,
    _endpoint,
    _extract_json,
    _headers,
)


def test_gateway_requires_api_key(monkeypatch):
    monkeypatch.setattr("app.ai.llm.service.settings.llm_api_key", "")
    with pytest.raises(LLMUnavailable):
        asyncio.run(
            _chat([{"role": "user", "content": "hi"}], json_mode=False)
        )


def test_endpoint_builds_openrouter_url(monkeypatch):
    # A full ``/v1`` base URL only gets ``/chat/completions`` appended.
    monkeypatch.setattr(
        "app.ai.llm.service.settings.llm_base_url", "https://openrouter.ai/api/v1"
    )
    assert _endpoint() == "https://openrouter.ai/api/v1/chat/completions"
    # A bare root gets the full ``/v1/chat/completions`` suffix.
    monkeypatch.setattr(
        "app.ai.llm.service.settings.llm_base_url", "https://example.com/"
    )
    assert _endpoint() == "https://example.com/v1/chat/completions"


def test_headers_include_openrouter_attribution(monkeypatch):
    monkeypatch.setattr("app.ai.llm.service.settings.llm_api_key", "sk-test")
    monkeypatch.setattr("app.ai.llm.service.settings.llm_auth_scheme", "bearer")
    monkeypatch.setattr(
        "app.ai.llm.service.settings.llm_referer", "https://careersetu.app"
    )
    monkeypatch.setattr("app.ai.llm.service.settings.llm_app_title", "CareerSetu")
    headers = _headers()
    assert headers["Authorization"] == "Bearer sk-test"
    assert headers["HTTP-Referer"] == "https://careersetu.app"
    assert headers["X-Title"] == "CareerSetu"


def test_headers_omit_attribution_when_unset(monkeypatch):
    monkeypatch.setattr("app.ai.llm.service.settings.llm_api_key", "sk-test")
    monkeypatch.setattr("app.ai.llm.service.settings.llm_referer", "")
    monkeypatch.setattr("app.ai.llm.service.settings.llm_app_title", "")
    headers = _headers()
    assert "HTTP-Referer" not in headers
    assert "X-Title" not in headers


def test_extract_json_handles_fences_and_chatter():
    assert _extract_json('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert _extract_json('Sure! {"a": 1} done') == '{"a": 1}'
    assert _extract_json('{"a": 1}') == '{"a": 1}'
