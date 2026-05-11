from app.agents.input_planner_agent import InputPlannerAgent
from app.agents.intent_agent import IntentAgent
from app.agents.rag_dispatch_agent import RagDispatchAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.validator_controller import ValidatorController
from app.common.constants import ALLOWED_INTENT_TYPES
from app.policies.recommendation_policy import (
    CATEGORY_SECTION_MAP,
    INTENT_CATEGORY_PRIORITY,
    MAX_SELECTED_RECOMMENDATIONS,
)
from app.policies.ranking_policy import score_for_rank
from app.services.music_detail_service import MusicDetailService


def test_input_planner_agent_builds_intent_and_kag_input_without_track_identity():
    result = InputPlannerAgent().run(
        user_id="user_001",
        session_id="session_001",
        request_id="req_001",
        user_input="차분한 밤 인디 음악 추천해줘",
        session_context={"session_id": "session_001", "recent_genres": ["indie"]},
    )

    assert result["intent_state"]["intent_type"] == "personalized_recommendation"
    assert result["kag_input_json"]["request_id"] == "req_001"
    assert "content_id" not in result["kag_input_json"]
    assert "title" not in result["kag_input_json"]
    assert "artist" not in result["kag_input_json"]


def test_intent_agent_returns_only_v4_allowed_intent_types():
    agent = IntentAgent()

    samples = [
        ("이 노래 왜 추천했어?", "recommendation_reason"),
        ("최신 신곡 추천해줘", "new_release_recommendation"),
        ("이 곡 정보 알려줘", "music_information"),
        ("새로운 취향 발견하고 싶어", "discovery_recommendation"),
        ("내 취향에 맞는 노래 추천해줘", "personalized_recommendation"),
        ("안녕", "general_chat"),
    ]

    for user_input, expected_intent in samples:
        result = agent.run(user_input=user_input)
        assert result["intent_type"] == expected_intent
        assert result["intent_type"] in ALLOWED_INTENT_TYPES


def test_rag_dispatch_agent_builds_rag_input_json_from_kag_and_planner_input():
    class CapturingRagAdapter:
        def __init__(self):
            self.received_rag_input_json = None

        def build_state(self, kag_state, rag_input_json=None):
            self.received_rag_input_json = rag_input_json
            return {
                "status": "success",
                "recommended_content_evidence": [],
                "recommendation_reason": {"summary": ""},
            }

    adapter = CapturingRagAdapter()
    kag_state = {
        "status": "success",
        "recommendation_goal": {"primary_goal": "discovery_recommendation"},
        "recommended_content_ids": ["track_001", "track_002"],
        "target_section": "discovery_section",
    }
    kag_input_json = {
        "request_id": "req_001",
        "user_id": "user_001",
        "session_id": "session_001",
        "intent_type": "discovery_recommendation",
        "query_context": {
            "normalized_query": "새로운 밤 인디 음악 추천해줘",
            "mood_candidates": ["night"],
            "genre_candidates": ["indie"],
            "situation_candidates": [],
        },
        "constraints": {
            "allow_discovery": True,
            "allow_new_release": True,
            "max_candidates": 10,
        },
    }

    result = RagDispatchAgent(rag_adapter=adapter).run(
        kag_state=kag_state,
        user_id="user_001",
        session_id="session_001",
        request_id="req_001",
        intent_state={"intent_type": "discovery_recommendation"},
        kag_input_json=kag_input_json,
    )

    assert result["status"] == "success"
    assert adapter.received_rag_input_json["request_id"] == "req_001"
    assert adapter.received_rag_input_json["intent_type"] == "discovery_recommendation"
    assert adapter.received_rag_input_json["kag_recommended_content_ids"] == ["track_001", "track_002"]
    assert adapter.received_rag_input_json["target_section"] == "discovery_section"
    assert adapter.received_rag_input_json["query_text"] == "새로운 밤 인디 음악 추천해줘"
    assert adapter.received_rag_input_json["retrieval_constraints"]["require_content_id_match"] is True


def test_recommendation_agent_outputs_v4_selected_recommendation_contract():
    result = RecommendationAgent().run(
        intent_result={"intent_type": "personalized_recommendation"},
        rag_state={
            "recommended_content_evidence": [
                {
                    "content_id": "track_001",
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "recommendation_category": "personalized_match",
                    "evidence_summary": "차분한 밤 분위기와 연결되는 곡",
                }
            ]
        },
    )

    selected = result["selected_recommendations"][0]
    assert selected["section"] == "personalized"
    assert selected["rank"] == 1
    assert selected["score"] > 0
    assert selected["source"] == {"kag": False, "rag": True}


def test_recommendation_agent_uses_policy_modules_for_selection_and_score():
    result = RecommendationAgent().run(
        intent_result={"intent_type": "discovery_recommendation"},
        rag_state={
            "recommended_content_evidence": [
                {
                    "content_id": "track_personal",
                    "title": "Personal",
                    "artist": "Artist A",
                    "recommendation_category": "personalized_match",
                    "evidence_summary": "개인화 후보",
                },
                {
                    "content_id": "track_discovery",
                    "title": "Discovery",
                    "artist": "Artist B",
                    "recommendation_category": "discovery_candidate",
                    "evidence_summary": "탐색 후보",
                },
            ]
        },
    )

    selected = result["selected_recommendations"]

    assert INTENT_CATEGORY_PRIORITY["discovery_recommendation"][0] == "discovery_candidate"
    assert selected[0]["content_id"] == "track_discovery"
    assert selected[0]["section"] == CATEGORY_SECTION_MAP["discovery_candidate"]
    assert selected[0]["score"] == score_for_rank(1)
    assert len(selected) <= MAX_SELECTED_RECOMMENDATIONS


def test_validator_controller_returns_fallback_when_response_fails_provenance():
    controller = ValidatorController()
    response_state = {
        "status": "success",
        "response_type": "curator_recommendation",
        "chatbot_response": "존재하지 않는 곡을 추천합니다.",
        "display_recommendations": [
            {
                "content_id": "track_missing",
                "title": "Missing",
                "artist": "Ghost",
                "label": "추천",
                "display_reason": "없는 근거",
            }
        ],
        "used_content_ids": ["track_missing"],
    }

    result = controller.validate_response(response_state=response_state, rag_state={"recommended_content_evidence": []})

    assert result["status"] == "error"
    assert result["_meta"]["error_type"] == "RESPONSE_VALIDATION_FAILED"


def test_music_detail_service_prefers_recent_rag_evidence():
    service = MusicDetailService()
    result = service.get_detail(
        content_id="track_001",
        recent_rag_state={
            "recommended_content_evidence": [
                {
                    "content_id": "track_001",
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "album": "Night Sketch",
                    "genre": ["indie"],
                    "mood": ["night"],
                    "evidence_summary": "차분한 밤 분위기와 연결되는 곡",
                }
            ]
        },
    )

    assert result["content_id"] == "track_001"
    assert result["source"] == "rag_state"


def test_music_detail_service_falls_back_to_music_catalog_when_rag_evidence_missing():
    class StubMusicCatalogRepository:
        def __init__(self):
            self.requested_content_id = None

        def find_by_content_id(self, content_id):
            self.requested_content_id = content_id
            return {
                "content_id": content_id,
                "title": "Midnight Loop",
                "artist": "Nova Lane",
                "album": "Night Sketch",
                "genres": ["rnb", "indie"],
                "moods": ["calm", "night"],
                "evidence_summary": "rnb/indie 취향과 calm/night 분위기에 직접 연결되는 곡",
            }

    repository = StubMusicCatalogRepository()
    service = MusicDetailService(music_catalog_repository=repository)

    result = service.get_detail(content_id="track_001", recent_rag_state={"recommended_content_evidence": []})

    assert repository.requested_content_id == "track_001"
    assert result["content_id"] == "track_001"
    assert result["title"] == "Midnight Loop"
    assert result["artist"] == "Nova Lane"
    assert result["genre"] == ["rnb", "indie"]
    assert result["mood"] == ["calm", "night"]
    assert result["source"] == "music_catalog"
