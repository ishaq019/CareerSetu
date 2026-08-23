import pytest

from app.ai.llm.service import LLMUnavailable, _model

def test_groq_provider_requires_api_key(monkeypatch):
    _model.cache_clear()
    monkeypatch.setattr("app.ai.llm.service.settings.llm_provider", "groq")
    monkeypatch.setattr("app.ai.llm.service.settings.llm_api_key", "")
    with pytest.raises(LLMUnavailable):
        _model("chat")
    _model.cache_clear()
