import asyncio

import pytest

from app.ai.llm.service import LLMUnavailable, _chat


def test_gateway_requires_api_key(monkeypatch):
    monkeypatch.setattr("app.ai.llm.service.settings.llm_api_key", "")
    with pytest.raises(LLMUnavailable):
        asyncio.run(
            _chat([{"role": "user", "content": "hi"}], json_mode=False)
        )
