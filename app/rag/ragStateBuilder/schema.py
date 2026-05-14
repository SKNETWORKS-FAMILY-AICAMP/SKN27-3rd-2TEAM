"""
RAG state schema definitions.

This module defines:
1. The request payload shape that enters the RAG layer
2. The shared RAG state shape used across workflow nodes
3. The final output payload returned from the RAG layer
"""

from typing import Literal, TypedDict


class KagUser(TypedDict):
    user_id: str


class RecommendationGoal(TypedDict):
    primary_goal: str
    secondary_goal: str
    goal_reason: str


class CurationIntent(TypedDict):
    intent_type: str
    intent_confidence: float
    allowed_modes: list[str]


class ContentRequirements(TypedDict):
    must_include: list[str]
    optional_include: list[str]
    avoid: list[str]


class RoutingInfo(TypedDict):
    target_page: str
    primary_section: str


class PreferenceTags(TypedDict, total=False):
    genres: list[str]
    artists: list[str]
    moods: list[str]
    energy: str
    tempo: str


class KagState(TypedDict):
    status: Literal["success", "fallback", "failed"]
    user: KagUser
    recommendation_goal: RecommendationGoal
    curation_intent: CurationIntent
    content_requirements: ContentRequirements
    preference_tags: PreferenceTags
    routing: RoutingInfo


class RetrievalConstraints(TypedDict):
    max_candidates: int
    max_display_recommendations: int
    allowed_source_types: list[str]
    require_evidence_summary: bool
    require_content_id: bool


class RagRequest(TypedDict):
    request_id: str
    user_id: str
    page_type: str
    user_input: str
    kag_state: KagState
    retrieval_constraints: RetrievalConstraints


class RecommendationContext(TypedDict):
    context_type: str
    base_context: str
    source_type: str


class MatchReason(TypedDict):
    genre_match: bool
    mood_match: bool
    tempo_match: bool
    new_taste_expansion: bool


class RecommendedContentEvidence(TypedDict, total=False):
    content_id: str
    title: str
    artist: str
    album: str
    genre: list[str]
    mood: list[str]
    tempo: str
    release_type: str
    recommendation_category: str
    evidence_summary: str
    match_reason: MatchReason
    score: float


class RecommendationReason(TypedDict):
    summary: str
    reason_items: list[str]


class InformationEvidence(TypedDict):
    info_id: str
    info_type: str
    title: str
    summary: str


class RecommendationScripts(TypedDict):
    dj_intro: str
    personalized_message: str
    new_release_message: str
    discovery_message: str
    fallback_message: str


class RetrievalTrace(TypedDict):
    retrieval_strategy: str
    retrieval_filters: list[str]
    matched_fields: list[str]
    candidate_count: int


class RagOutput(TypedDict):
    status: Literal["success", "fallback", "failed"]
    recommendation_context: RecommendationContext
    recommended_content_evidence: list[RecommendedContentEvidence]
    recommendation_reason: RecommendationReason
    information_evidence: list[InformationEvidence]
    recommendation_scripts: RecommendationScripts
    retrieval_trace: RetrievalTrace


class RagState(TypedDict, total=False):
    """
    Shared state across the RAG workflow.

    `request` holds the original input contract.
    The remaining fields can be filled progressively by retrieval,
    grading, validation, and state-building nodes.
    """

    request: RagRequest

    request_id: str
    user_id: str
    page_type: str
    user_input: str
    kag_state: KagState
    retrieval_constraints: RetrievalConstraints

    transformed_query: str
    retrieved_candidates: list[RecommendedContentEvidence]
    filtered_candidates: list[RecommendedContentEvidence]
    validation_errors: list[str]
    warnings: list[str]

    status: Literal["success", "fallback", "failed"]
    recommendation_context: RecommendationContext
    recommended_content_evidence: list[RecommendedContentEvidence]
    recommendation_reason: RecommendationReason
    information_evidence: list[InformationEvidence]
    recommendation_scripts: RecommendationScripts
    retrieval_trace: RetrievalTrace
    output: RagOutput
