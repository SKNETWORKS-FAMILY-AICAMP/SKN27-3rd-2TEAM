import pytest

from app.services.main_recommendation_service import MainRecommendationService


class StubOrchestrator:
    def run_recommendation(self, user_id, session_id, session_context):
        return {
            "status": "success",
            "kag_state": {
                "content_requirements": {"must_include": ["personalized_match", "discovery_candidate"]},
            },
            "rag_state": {
                "recommended_content_evidence": [
                    {
                        "content_id": "track_001",
                        "title": "Test Track",
                        "artist": "Test Artist",
                        "album": "Test Album",
                        "genre": ["rnb"],
                        "mood": ["calm"],
                        "recommendation_category": "personalized_match",
                        "evidence_summary": "취향 기반 추천",
                    },
                    {
                        "content_id": "track_002",
                        "title": "Discover Track",
                        "artist": "New Artist",
                        "album": "New Album",
                        "genre": ["indie"],
                        "mood": ["fresh"],
                        "recommendation_category": "discovery_candidate",
                        "evidence_summary": "새로운 취향 탐색",
                    },
                ],
                "recommendation_reason": {"summary": "오늘의 테마"},
                "recommendation_scripts": {"dj_intro": "안녕하세요", "discovery_message": "발견"},
            },
            "latency_ms": 100.0,
        }


class StubSessionCacheService:
    def load_context(self, session_id):
        return {
            "session_id": session_id,
            "recent_genres": ["rnb", "indie"],
            "recent_artists": [],
            "recent_moods": ["calm"],
            "conversation_summary": "",
        }


def test_main_recommendation_service_returns_page_view_model(monkeypatch):
    monkeypatch.setattr(
        "app.services.main_recommendation_service.session_cache_service",
        StubSessionCacheService(),
    )

    view_model = MainRecommendationService(orchestrator=StubOrchestrator()).get_page_view_model(
        "user_001", "session_abc"
    )

    assert view_model["page_type"] == "main_recommendation_page"
    assert view_model["status"] == "success"
    assert view_model["taste_badges"]
    assert view_model["personalized"]
    assert view_model["discovery"]
    assert "new_release" in view_model
    assert "recommendation_groups" not in view_model
    assert "debug" in view_model
