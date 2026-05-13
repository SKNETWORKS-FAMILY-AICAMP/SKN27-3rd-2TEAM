"""
Edge and decision helpers for the RAG state workflow.

These functions decide which node should run next based on the current state.
"""

from typing import Literal

from app.rag.ragStateBuilder.schema import RagState


DecisionToGenerate = Literal["generate_answer", "transform_query", "fallback"]
HallucinationDecision = Literal["complete", "fallback"]


def decide_to_generate(state: RagState) -> DecisionToGenerate:
    """
    Decide whether the workflow can move to answer assembly.

    Rules:
    - If graded candidates exist, continue to `generate_answer`
    - If retrieval has not produced candidates yet, retry through `transform_query`
    - If validation has already failed or fallback status is set, stop with fallback
    """
    status = state.get("status")
    if status == "fallback":
        return "fallback"

    if state.get("validation_errors"):
        return "fallback"

    filtered_candidates = state.get("filtered_candidates", [])
    if filtered_candidates:
        return "generate_answer"

    retrieved_candidates = state.get("retrieved_candidates", [])
    if not retrieved_candidates:
        return "transform_query"

    return "fallback"


def check_hallucination(state: RagState) -> HallucinationDecision:
    """
    Perform a lightweight post-generation gate.

    MVP behavior:
    - Success requires at least one recommendation evidence item
    - Every recommendation must include content_id and evidence_summary
    """
    evidence_items = state.get("recommended_content_evidence", [])
    if not evidence_items:
        return "fallback"

    for item in evidence_items:
        if not item.get("content_id"):
            return "fallback"
        if not item.get("evidence_summary"):
            return "fallback"

    return "complete"
