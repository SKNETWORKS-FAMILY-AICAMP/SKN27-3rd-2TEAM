from app.agents.input_planner_agent import InputPlannerAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.validator_controller import ValidatorController
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
