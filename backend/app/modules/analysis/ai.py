"""Optional LLM refinement layer for the deterministic analysis.

If no LLM is configured (or the call fails) the deterministic baseline is
returned unchanged, so the guest path always works.
"""
from __future__ import annotations

from app.ai.llm.schemas import AnalysisEnhancement
from app.ai.llm.service import LLMUnavailable, structured
from app.core.config import settings


def _limit(text: str) -> str:
    return " ".join(text.split())[: settings.llm_context_chars]


async def enhance_analysis(resume: str, jd: str, baseline: dict) -> dict:
    if not settings.llm_configured:
        return baseline

    system = (
        "You improve CareerSetu's resume-to-job analysis using only the supplied "
        "resume, job description, and baseline deterministic result. Do not invent "
        "candidate skills or experience. Keep scores conservative. Return concise, "
        "actionable content for an end user."
    )
    user = (
        f"Resume:\n{_limit(resume)}\n\n"
        f"Job description:\n{_limit(jd)}\n\n"
        f"Baseline result:\n{baseline}"
    )

    try:
        result = await structured("analyze", system, user, AnalysisEnhancement)
    except LLMUnavailable:
        return baseline
    except Exception:
        # Never let an AI failure break the deterministic guest path.
        return baseline

    enhanced = dict(baseline)
    enhanced["match_score"] = result.match_score
    enhanced["ats_coverage"] = result.ats_coverage
    enhanced["recommendation"] = result.recommendation
    enhanced["summary"] = result.summary

    if result.roadmap_steps:
        enhanced["roadmap"] = [
            {
                "skill": "Resume positioning",
                "target_level": "role-ready",
                "priority": "high",
                "steps": result.roadmap_steps[:4],
            },
            *baseline.get("roadmap", []),
        ]
    return enhanced
