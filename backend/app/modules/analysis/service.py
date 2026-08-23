"""Deterministic resume-to-job analysis.

The Match Score is computed with plain Python — no LLM — so it is cheap,
repeatable and explainable. An optional LLM pass (see ``ai.py``) can refine the
wording afterwards but must never invent skills or change the method.
"""
from __future__ import annotations

import re

SKILLS: dict[str, list[str]] = {
    "React": [r"\breact(?:\.js)?\b"],
    "Node.js": [r"\bnode(?:\.js)?\b", r"\bnodejs\b"],
    "Python": [r"\bpython\b"],
    "FastAPI": [r"\bfastapi\b"],
    "PostgreSQL": [r"\bpostgres(?:ql)?\b"],
    "MongoDB": [r"\bmongodb\b", r"\bmongo\b"],
    "Docker": [r"\bdocker\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "Redis": [r"\bredis\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
    "TypeScript": [r"\btypescript\b", r"\bts\b"],
    "Git": [r"\bgit\b"],
    "GraphQL": [r"\bgraphql\b"],
    "REST APIs": [r"\brest(?:ful)?\b", r"\brest api(?:s)?\b"],
    "SQL": [r"\bsql\b"],
    "CI/CD": [r"\bci/cd\b", r"\bgithub actions\b", r"\bjenkins\b", r"\bgitlab ci\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "Testing": [r"\bpytest\b", r"\bjest\b", r"\bunit tests?\b", r"\btesting\b", r"\bvitest\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b", r"\bdeep learning\b"],
    "LangChain": [r"\blangchain\b"],
    "LangGraph": [r"\blanggraph\b"],
    "Java": [r"\bjava\b"],
    "Go": [r"\bgolang\b", r"\bgo lang\b"],
    "Kafka": [r"\bkafka\b"],
    "Tailwind CSS": [r"\btailwind\b"],
}

LEVEL = {"none": 0, "basic": 1, "intermediate": 2, "advanced": 3}
_ADVANCED = ("architect", "led", "lead", "expert", "optimized", "optimised", "scale", "production")
_INTERMEDIATE = ("built", "developed", "implemented", "deployed", "experience", "project", "shipped")
_BASIC = ("basic", "fundamental", "familiar", "beginner", "exposure", "learning")


def _has(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def _level(text: str, skill: str) -> str:
    pos = text.lower().find(skill.lower())
    if pos < 0:
        return "none"
    window = text[max(0, pos - 220): pos + 420].lower()
    if any(w in window for w in _ADVANCED):
        return "advanced"
    if any(w in window for w in _INTERMEDIATE):
        return "intermediate"
    if any(w in window for w in _BASIC):
        return "basic"
    return "basic"


def analyze(resume: str, jd: str) -> dict:
    resume = " ".join(resume.split())
    jd = " ".join(jd.split())
    r, j = resume.lower(), jd.lower()

    required = [s for s, p in SKILLS.items() if _has(j, p)]
    if not required:
        # No recognised requirements in the JD — fall back to the resume's own skills.
        required = [s for s, p in SKILLS.items() if _has(r, p)][:8]

    strengths: list[dict] = []
    gaps: list[dict] = []
    for skill in required:
        present = _has(r, SKILLS[skill])
        req = _level(j, skill) if _has(j, SKILLS[skill]) else "intermediate"
        got = _level(r, skill) if present else "none"
        ratio = LEVEL[got] / max(LEVEL[req], 1)
        status = "strong" if ratio >= 1 else ("partial" if ratio > 0 else "missing")
        evidence = (
            f"Resume shows {got} evidence for {skill}; the job appears to expect {req}."
            if present
            else f"The job description asks for {skill}, but the resume does not clearly mention it."
        )
        item = {
            "skill": skill,
            "required_level": req,
            "detected_level": got,
            "status": status,
            "evidence": evidence,
        }
        (strengths if status == "strong" else gaps).append(item)

    total = max(len(required), 1)
    weighted = sum(
        1.0 if x["status"] == "strong" else 0.5
        for x in strengths + gaps
        if x["status"] != "missing"
    )
    coverage = round(weighted / total * 100)
    evidence_bonus = min(
        10, len(re.findall(r"\b(built|developed|implemented|deployed|led|optimized|optimised)\b", r)) * 1.5
    )
    score = max(0, min(100, round(coverage * 0.9 + evidence_bonus)))

    if score >= 80:
        recommendation = "STRONG_MATCH"
        summary = (
            "Your resume already shows strong alignment. Apply now and prepare "
            "examples for the strongest matched skills."
        )
    elif score >= 60:
        recommendation = "MATCH_WITH_IMPROVEMENTS"
        summary = (
            "You are close enough to consider applying, but your resume should be "
            "updated to show clearer evidence for the top gaps."
        )
    else:
        recommendation = "LOW_MATCH"
        summary = (
            "This role has several visible gaps. Focus on the high-priority skills "
            "first, then re-analyze before applying."
        )

    roadmap = [
        {
            "skill": x["skill"],
            "target_level": x["required_level"],
            "priority": "high" if x["status"] == "missing" else "medium",
            "steps": [
                f"Learn the {x['skill']} concepts listed in the job description",
                f"Practice {x['skill']} with role-specific exercises",
                f"Add one resume bullet with measurable {x['skill']} evidence",
                "Re-analyze the updated resume",
            ],
        }
        for x in gaps[:6]
    ]

    return {
        "match_score": score,
        "ats_coverage": coverage,
        "recommendation": recommendation,
        "summary": summary,
        "strengths": strengths,
        "gaps": gaps,
        "roadmap": roadmap,
    }
