"""LangGraph interview-evaluation graph.

Kept intentionally small: a single evaluation node with clean state boundaries.
More nodes (question selection, difficulty adjustment) can be added as each gains
a meaningful retry/checkpoint boundary. For production, compile with a PostgreSQL
checkpointer so an interrupted interview can resume.
"""
from __future__ import annotations

from typing import TypedDict


class InterviewState(TypedDict, total=False):
    question: str
    answer: str
    score: float
    strengths: list[str]
    improvements: list[str]
    evidence_quality: str
    next_difficulty: str
    llm_calls: int


async def _evaluate(state: InterviewState) -> dict:
    from app.ai.llm.schemas import InterviewEvaluation
    from app.ai.llm.service import structured

    result = await structured(
        "evaluate",
        "You evaluate interview answers. Score only the answer shown. Do not invent experience. "
        "Prefer evidence, reasoning, correctness and clarity. Choose next difficulty based on "
        "demonstrated performance.",
        f"Question:\n{state.get('question', '')}\n\nCandidate answer:\n{state.get('answer', '')}",
        InterviewEvaluation,
    )
    return {**result.model_dump(), "llm_calls": state.get("llm_calls", 0) + 1}


def build_interview_graph(checkpointer=None):
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        return None
    graph = StateGraph(InterviewState)
    graph.add_node("evaluate", _evaluate)
    graph.add_edge(START, "evaluate")
    graph.add_edge("evaluate", END)
    return graph.compile(checkpointer=checkpointer)
