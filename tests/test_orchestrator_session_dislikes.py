import sys
import types

neo4j_stub = types.ModuleType("neo4j")
neo4j_stub.GraphDatabase = object()
sys.modules.setdefault("neo4j", neo4j_stub)

from app.agents.orchestrator_agent import OrchestratorAgent


INTENT_STATE = {
    "intent_type": "personalized_recommendation",
    "confidence": 0.92,
    "normalized_query": "신나는 음악 듣고 싶다 근데 pop음악은 별로",
    "detected_moods": ["energetic"],
    "detected_genres": [],
    "detected_situations": [],
    "requested_count": None,
    "disliked_artists": ["Sample Artist"],
    "disliked_tracks": ["track_099"],
    "disliked_genres": ["pop"],
    "requires_kag": True,
    "requires_rag": True,
}

KAG_STATE = {
    "status": "success",
    "user_context": {
        "base_preference": {
            "genres": ["dance"],
            "moods": ["energetic"],
        }
    },
    "recommended_content_ids": ["track_001"],
}

RAG_STATE = {
    "status": "success",
    "recommended_content_evidence": [
        {
            "content_id": "track_001",
            "title": "Bright Night",
            "artist": "Catalog Artist",
        }
    ],
    "recommendation_reason": {"summary": "energetic evidence"},
}


class StubInputPlanner:
    def run(self, **kwargs):
        return {
            "intent_state": dict(INTENT_STATE),
            "kag_input_json": {
                "constraints": {
                    "excluded_artists": ["Sample Artist"],
                    "excluded_tracks": ["track_099"],
                    "excluded_genres": ["pop"],
                }
            },
        }


class StubKag:
    def run(self, *args, **kwargs):
        return dict(KAG_STATE)


class StubRag:
    def run(self, *args, **kwargs):
        return dict(RAG_STATE)


class StubIntent:
    def run(self, *args, **kwargs):
        return dict(INTENT_STATE)


class StubRecommendationSuccess:
    def run(self, *args, **kwargs):
        return {
            "selected_recommendations": [
                {
                    "content_id": "track_001",
                    "title": "Bright Night",
                    "artist": "Catalog Artist",
                }
            ]
        }


class StubRecommendationEmpty:
    def run(self, *args, **kwargs):
        return {"selected_recommendations": []}


class StubResponseGenerator:
    def run(self, *args, **kwargs):
        return {
            "status": "success",
            "response_type": "recommendation",
            "chatbot_response": "추천 결과입니다.",
            "display_recommendations": [
                {
                    "content_id": "track_001",
                    "title": "Bright Night",
                    "artist": "Catalog Artist",
                }
            ],
            "used_content_ids": ["track_001"],
        }


class PassingValidator:
    def validate(self, *args, **kwargs):
        return {"passed": True, "errors": []}


def _build_orchestrator(recommendation_agent):
    return OrchestratorAgent(
        input_planner=StubInputPlanner(),
        kag_agent=StubKag(),
        rag_agent=StubRag(),
        intent_agent=StubIntent(),
        recommendation_agent=recommendation_agent,
        response_generator=StubResponseGenerator(),
        contract_validator=PassingValidator(),
        response_validator=PassingValidator(),
        provenance_validator=PassingValidator(),
    )


def test_success_meta_includes_disliked_genres_for_session_cache():
    orchestrator = _build_orchestrator(StubRecommendationSuccess())

    result = orchestrator.run_chatbot(
        user_id="user_1",
        session_id="session_1",
        user_input="신나는 음악 듣고 싶다 근데 pop음악은 별로",
        session_context={"session_id": "session_1"},
    )

    assert result["_meta"]["new_dislikes"] == {
        "disliked_artists": ["Sample Artist"],
        "disliked_tracks": ["track_099"],
        "disliked_genres": ["pop"],
    }


def test_fallback_meta_keeps_disliked_genres_for_session_cache():
    orchestrator = _build_orchestrator(StubRecommendationEmpty())

    result = orchestrator.run_chatbot(
        user_id="user_1",
        session_id="session_1",
        user_input="신나는 음악 듣고 싶다 근데 pop음악은 별로",
        session_context={"session_id": "session_1"},
    )

    assert result["_meta"]["error_type"] == "NO_RECOMMENDATIONS"
    assert result["_meta"]["new_dislikes"] == {
        "disliked_artists": ["Sample Artist"],
        "disliked_tracks": ["track_099"],
        "disliked_genres": ["pop"],
    }
