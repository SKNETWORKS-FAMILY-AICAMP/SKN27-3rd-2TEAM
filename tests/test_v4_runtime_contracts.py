import pytest
from pydantic import ValidationError

from app.schemas.intent_state_schema import IntentStateSchema
from app.schemas.kag_input_schema import KagInputSchema
from app.schemas.music_detail_schema import MusicDetailViewModelSchema
from app.schemas.rag_input_schema import RagInputSchema
from app.services.compact_state_builder import CompactStateBuilder
from app.services.request_lifecycle_cache import DuplicateRequestError, RequestLifecycleCache


def test_intent_state_rejects_unknown_intent_type():
    with pytest.raises(ValidationError):
        IntentStateSchema(
            intent_type="unsupported",
            confidence=0.9,
            normalized_query="사용자 취향 기반 음악 추천",
            detected_moods=[],
            detected_genres=[],
            detected_situations=[],
            requires_kag=True,
            requires_rag=True,
        )


def test_kag_input_json_does_not_accept_generated_track_identity_fields():
    with pytest.raises(ValidationError):
        KagInputSchema(
            request_id="req_001",
            user_id="user_001",
            session_id="session_001",
            intent_type="personalized_recommendation",
            query_context={
                "normalized_query": "사용자 취향 기반 음악 추천",
                "mood_candidates": ["calm"],
                "genre_candidates": ["indie"],
                "situation_candidates": [],
            },
            constraints={"allow_discovery": True, "allow_new_release": True, "max_candidates": 10},
            content_id="track_999",
        )


def test_rag_input_json_requires_content_id_match_constraint():
    rag_input = RagInputSchema(
        request_id="req_001",
        user_id="user_001",
        session_id="session_001",
        intent_type="personalized_recommendation",
        kag_recommended_content_ids=["track_001"],
        target_section="personalized_section",
        query_text="차분한 밤 분위기의 인디 음악 추천 이유",
        evidence_need=["track_description"],
        retrieval_constraints={"max_evidence_per_track": 3, "require_content_id_match": True},
    )

    assert rag_input.retrieval_constraints.require_content_id_match is True


def test_compact_state_builder_removes_internal_trace_fields():
    compact = CompactStateBuilder().build(
        kag_state={
            "status": "success",
            "recommendation_goal": {"primary_goal": "new_taste_discovery"},
            "curation_strategy": {"strategy_code": "SAFE_DISCOVERY_FROM_PERSONAL_TASTE"},
            "routing": {"target_page": "chatbot_page"},
            "target_section": "discovery_section",
        },
        rag_state={
            "status": "success",
            "recommended_content_evidence": [
                {
                    "content_id": "track_001",
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "evidence_summary": "차분한 밤 분위기와 연결되는 곡",
                }
            ],
            "retrieval_trace": {"retrieval_strategy": "hybrid_search"},
        },
        response_state={
            "status": "success",
            "response_type": "curator_recommendation",
            "chatbot_response": "추천 응답",
            "display_recommendations": [],
            "used_content_ids": [],
            "validator_trace": {"passed": True},
        },
    )

    assert compact["kag_state"] == {
        "status": "success",
        "recommendation_goal": {"primary_goal": "new_taste_discovery"},
        "target_section": "discovery_section",
    }
    assert "retrieval_trace" not in compact["rag_state"]
    assert "validator_trace" not in compact["response_state"]


def test_request_lifecycle_cache_blocks_duplicate_inflight_request():
    cache = RequestLifecycleCache()
    cache.start("req_001")

    with pytest.raises(DuplicateRequestError):
        cache.start("req_001")

    cache.finish("req_001")
    cache.start("req_001")


def test_music_detail_view_model_contract():
    detail = MusicDetailViewModelSchema(
        content_id="track_001",
        title="Midnight Loop",
        artist="Nova Lane",
        display_reason="차분한 밤 분위기와 연결되는 곡",
        evidence_summary="RAG 근거 요약",
        source="rag_state",
    )

    assert detail.content_id == "track_001"
