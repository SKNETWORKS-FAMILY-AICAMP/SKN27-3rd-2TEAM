"""
Builder utilities for the RAG state workflow.

This module provides:
- A simple graph description for the MVP flow
- A lightweight compiled workflow object with an invoke method

The structure is intentionally simple so it can be replaced later with
LangGraph without changing the higher-level service interface.
"""

from dataclasses import dataclass
from typing import Callable

from app.rag.ragStateBuilder.edges import check_hallucination, decide_to_generate
from app.rag.ragStateBuilder.nodes import (
    generate_answer,
    grade_documents,
    retrieve_documents,
    transform_query,
)
from app.rag.ragStateBuilder.schema import RagState


NodeFunction = Callable[[RagState], RagState]


@dataclass(frozen=True)
class RagGraph:
    entrypoint: str
    nodes: dict[str, NodeFunction]


class CompiledRagGraph:
    """
    Lightweight executable workflow wrapper.
    """

    def __init__(self, graph: RagGraph):
        self.graph = graph

    def invoke(self, state: RagState) -> RagState:
        """
        Execute the MVP workflow in a fixed order with edge decisions.
        """
        current_state = state

        current_state = self.graph.nodes["transform_query"](current_state)
        current_state = self.graph.nodes["retrieve_documents"](current_state)
        current_state = self.graph.nodes["grade_documents"](current_state)

        next_step = decide_to_generate(current_state)
        if next_step == "transform_query":
            current_state = self.graph.nodes["transform_query"](current_state)
            current_state = self.graph.nodes["retrieve_documents"](current_state)
            current_state = self.graph.nodes["grade_documents"](current_state)
            next_step = decide_to_generate(current_state)

        if next_step == "generate_answer":
            current_state = self.graph.nodes["generate_answer"](current_state)
        else:
            current_state = _build_fallback_state(current_state)
            return current_state

        hallucination_check = check_hallucination(current_state)
        if hallucination_check == "fallback":
            current_state = _build_fallback_state(current_state)

        return current_state


def build_rag_graph() -> RagGraph:
    """
    Build the MVP workflow node map.
    """
    return RagGraph(
        entrypoint="transform_query",
        nodes={
            "transform_query": transform_query,
            "retrieve_documents": retrieve_documents,
            "grade_documents": grade_documents,
            "generate_answer": generate_answer,
        },
    )


def compile_graph(graph: RagGraph) -> CompiledRagGraph:
    """
    Wrap the graph in an executable workflow object.
    """
    return CompiledRagGraph(graph)


def _build_fallback_state(state: RagState) -> RagState:
    fallback_state = dict(state)
    fallback_state["status"] = "fallback"
    fallback_state["recommendation_context"] = {
        "context_type": "fallback",
        "base_context": "Only fallback guidance is available.",
        "source_type": "fallback",
    }
    fallback_state["recommended_content_evidence"] = []
    fallback_state["recommendation_reason"] = {
        "summary": "The workflow could not build a grounded recommendation result.",
        "reason_items": [
            "The candidate set was empty or failed the final evidence check."
        ],
    }
    fallback_state["information_evidence"] = []
    fallback_state["recommendation_scripts"] = {
        "dj_intro": "",
        "personalized_message": "",
        "new_release_message": "",
        "discovery_message": "",
        "fallback_message": "Recommendation evidence is limited, so fallback guidance is returned.",
    }
    fallback_state["retrieval_trace"] = fallback_state.get(
        "retrieval_trace",
        {
            "retrieval_strategy": "fallback",
            "retrieval_filters": [],
            "matched_fields": [],
            "candidate_count": 0,
        },
    )
    fallback_state["output"] = {
        "status": fallback_state["status"],
        "recommendation_context": fallback_state["recommendation_context"],
        "recommended_content_evidence": fallback_state["recommended_content_evidence"],
        "recommendation_reason": fallback_state["recommendation_reason"],
        "information_evidence": fallback_state["information_evidence"],
        "recommendation_scripts": fallback_state["recommendation_scripts"],
        "retrieval_trace": fallback_state["retrieval_trace"],
    }
    return fallback_state
