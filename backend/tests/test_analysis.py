from app.modules.analysis.service import analyze
from app.modules.analysis.ai import enhance_analysis

def test_analysis_runs():
    result = analyze(
        "Built React and Node.js applications with PostgreSQL and Docker.",
        "Looking for React Node.js PostgreSQL developer. Docker experience preferred."
    )
    assert 0 <= result["match_score"] <= 100
    assert 0 <= result["ats_coverage"] <= 100

def test_missing_skill():
    result = analyze("Built React applications.", "Requires React, Docker and AWS.")
    names = {x["skill"] for x in result["gaps"]}
    assert "Docker" in names
    assert "AWS" in names

def test_ai_enhancement_falls_back_without_key(monkeypatch):
    baseline = analyze("Built React applications.", "Requires React and Docker.")
    monkeypatch.setattr("app.modules.analysis.ai.settings.llm_api_key", "")
    import asyncio
    result = asyncio.run(enhance_analysis("Built React applications.", "Requires React and Docker.", baseline))
    assert result == baseline
