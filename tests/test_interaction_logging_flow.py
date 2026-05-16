from app.services.chatbot_service import ChatbotService
from app.services.main_recommendation_service import MainRecommendationService


class StubOrchestrator:
    def run_chatbot(self, *, user_id, session_id, user_input, session_context):
        return {
            "status": "success",
            "response_type": "curator_recommendation",
            "chatbot_response": "ok",
            "display_recommendations": [],
            "used_content_ids": [],
            "_meta": {
                "kag_state": {
                    "status": "success",
                    "recommendation_goal": {"primary_goal": "personalized_recommendation"},
                    "recommended_content_ids": [],
                    "recommendation_category": "personalized_match",
                    "route": "personalized",
                    "target_section": "personalized_section",
                },
                "rag_state": {
                    "status": "success",
                    "recommended_content_evidence": [],
                    "recommendation_reason": {"summary": "empty"},
                },
                "latency_ms": 12,
                "new_dislikes": {
                    "disliked_artists": [],
                    "disliked_tracks": [],
                    "disliked_genres": [],
                },
            },
        }


class RecordingLoggingService:
    def __init__(self):
        self.calls = []

    def save(self, **kwargs):
        self.calls.append(kwargs)


class StubMainOrchestrator:
    def run_recommendation(self, *, user_id, session_id, session_context):
        return {
            "status": "success",
            "kag_state": {
                "status": "success",
                "recommendation_goal": {"primary_goal": "personalized_recommendation"},
                "recommended_content_ids": ["track_001"],
                "recommendation_category": "personalized_match",
                "route": "personalized",
                "target_section": "personalized_section",
            },
            "rag_state": {
                "status": "success",
                "recommended_content_evidence": [
                    {
                        "content_id": "track_001",
                        "title": "Bright Night",
                        "artist": "Catalog Artist",
                        "genre": [],
                        "mood": [],
                        "recommendation_category": "personalized_match",
                    }
                ],
                "recommendation_reason": {"summary": "summary"},
            },
            "latency_ms": 7,
        }


class EmptyCatalogRepository:
    def find_fallback_new_releases(self, **kwargs):
        return []

    def find_fallback_discovery(self, **kwargs):
        return []


def test_default_chatbot_service_saves_interaction_log(monkeypatch):
    logger = RecordingLoggingService()
    monkeypatch.setattr("app.services.chatbot_service.LoggingService", lambda: logger)
    monkeypatch.setattr("app.services.chatbot_service.redis_client.is_healthy", lambda: True)
    monkeypatch.setattr(
        "app.services.chatbot_service.session_cache_service.load_context",
        lambda session_id, user_id=None: {"session_id": session_id},
    )
    monkeypatch.setattr(
        "app.services.chatbot_service.session_cache_service.save_turn_and_update_context",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "app.services.chatbot_service.latest_state_cache.save_latest_states",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "app.services.chatbot_service.latest_state_cache.get_latest_response_state",
        lambda session_id: None,
    )

    ChatbotService(orchestrator=StubOrchestrator()).submit_message(
        user_id="user_1",
        session_id="session_1",
        user_input="music please",
    )

    assert len(logger.calls) == 1
    assert logger.calls[0]["user_id"] == "user_1"
    assert logger.calls[0]["session_id"] == "session_1"
    assert logger.calls[0]["response_state"]["status"] == "success"


def test_main_recommendation_service_saves_interaction_log(monkeypatch):
    logger = RecordingLoggingService()
    monkeypatch.setattr("app.services.main_recommendation_service.redis_client.is_healthy", lambda: True)
    monkeypatch.setattr(
        "app.services.main_recommendation_service.session_cache_service.load_context",
        lambda session_id, user_id=None: {"session_id": session_id},
    )
    monkeypatch.setattr(
        "app.services.main_recommendation_service.latest_state_cache.save_latest_states",
        lambda **kwargs: None,
    )

    MainRecommendationService(
        orchestrator=StubMainOrchestrator(),
        music_catalog_repository=EmptyCatalogRepository(),
        logging_service=logger,
    ).get_page_view_model(user_id="user_1", session_id="session_1")

    assert len(logger.calls) == 1
    assert logger.calls[0]["page_type"] == "main_recommendation_page"
    assert logger.calls[0]["user_input"] == ""
    assert logger.calls[0]["response_state"]["page_type"] == "main_recommendation_page"
