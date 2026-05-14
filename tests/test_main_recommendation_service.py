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
    def load_context(self, session_id, user_id=None):
        return {
            "session_id": session_id,
            "recent_genres": ["rnb", "indie"],
            "recent_artists": [],
            "recent_moods": ["calm"],
            "selected_tracks": [],
            "conversation_summary": "",
        }


class StubLatestStateCache:
    def __init__(self):
        self.saved = []

    def save_latest_states(self, **kwargs):
        self.saved.append(kwargs)


def test_main_recommendation_service_returns_page_view_model(monkeypatch):
    latest_cache = StubLatestStateCache()
    monkeypatch.setattr(
        "app.services.main_recommendation_service.session_cache_service",
        StubSessionCacheService(),
    )
    monkeypatch.setattr(
        "app.services.main_recommendation_service.latest_state_cache",
        latest_cache,
    )

    view_model, session_degraded = MainRecommendationService(orchestrator=StubOrchestrator()).get_page_view_model(
        "user_001", "session_abc"
    )

    assert isinstance(session_degraded, bool)
    assert view_model["page_type"] == "main_recommendation_page"
    assert view_model["status"] == "success"
    assert view_model["taste_badges"]
    assert view_model["personalized"]
    assert view_model["discovery"]
    assert "new_release" in view_model
    assert "recommendation_groups" not in view_model
    assert "debug" in view_model
    assert latest_cache.saved[0]["session_id"] == "session_abc"
    assert latest_cache.saved[0]["kag_state"] == view_model["debug"]["kag_state"]
    assert latest_cache.saved[0]["rag_state"] == view_model["debug"]["rag_state"]
    assert latest_cache.saved[0]["response_state"] == view_model
    assert latest_cache.saved[0]["recommendation_metadata"] == {
        "source_type": "main_recommendation",
        "user_id": "user_001",
        "latency_ms": view_model["debug"]["latency_ms"],
    }


def test_main_recommendation_service_deduplicates_and_fills_sections():
    class StubRepo:
        def find_fallback_new_releases(self, limit, excluded_content_ids, excluded_artists):
            return [
                {
                    "content_id": "new_001",
                    "title": "New",
                    "artist": "Fresh",
                    "album": "",
                    "genres": ["indie"],
                    "moods": ["bright"],
                    "evidence_summary": "new",
                }
            ]

        def find_fallback_discovery(self, limit, preferred_genres, excluded_content_ids, excluded_artists):
            return [
                {
                    "content_id": "disc_001",
                    "title": "Discover",
                    "artist": "Wide",
                    "album": "",
                    "genres": ["ambient"],
                    "moods": ["calm"],
                    "evidence_summary": "discover",
                }
            ]

    view_model = MainRecommendationService._build_view_model(
        user_id="user_001",
        session_context={
            "disliked_artists": [],
            "disliked_tracks": [],
            "recent_genres": ["indie"],
            "recent_moods": [],
        },
        kag_state={},
        rag_state={
            "recommended_content_evidence": [
                {
                    "content_id": "track_001",
                    "title": "Same",
                    "artist": "A",
                    "genre": ["indie"],
                    "mood": ["calm"],
                    "recommendation_category": "personalized_match",
                    "evidence_summary": "raw",
                },
                {
                    "content_id": "track_001",
                    "title": "Same",
                    "artist": "A",
                    "genre": ["indie"],
                    "mood": ["calm"],
                    "recommendation_category": "personalized_match",
                    "evidence_summary": "raw",
                },
            ]
        },
        latency_ms=1.0,
        catalog_repository=StubRepo(),
    )

    assert len(view_model["personalized"]) == 1
    assert view_model["new_release"]
    assert view_model["discovery"]


def test_main_recommendation_service_uses_injected_repository_for_runtime_fallback(monkeypatch):
    class EmptySectionOrchestrator:
        def run_recommendation(self, user_id, session_id, session_context):
            return {
                "status": "success",
                "kag_state": {},
                "rag_state": {
                    "recommended_content_evidence": [
                        {
                            "content_id": "track_001",
                            "title": "Same",
                            "artist": "A",
                            "genre": ["indie"],
                            "mood": ["calm"],
                            "recommendation_category": "personalized_match",
                            "evidence_summary": "raw",
                        }
                    ],
                    "recommendation_reason": {"summary": ""},
                    "recommendation_scripts": {},
                },
            }

    class StubSessionCache:
        def load_context(self, session_id, user_id=None):
            return {
                "session_id": session_id,
                "recent_genres": ["indie"],
                "recent_moods": [],
                "disliked_artists": [],
                "disliked_tracks": [],
            }

    class StubLatestStateCache:
        def save_latest_states(self, **kwargs):
            pass

    class StubRepo:
        def find_fallback_new_releases(self, limit, excluded_content_ids, excluded_artists):
            return [{"content_id": "new_001", "title": "New", "artist": "Fresh", "genres": ["indie"], "moods": ["bright"]}]

        def find_fallback_discovery(self, limit, preferred_genres, excluded_content_ids, excluded_artists):
            return [{"content_id": "disc_001", "title": "Discover", "artist": "Wide", "genres": ["ambient"], "moods": ["calm"]}]

    monkeypatch.setattr("app.services.main_recommendation_service.session_cache_service", StubSessionCache())
    monkeypatch.setattr("app.services.main_recommendation_service.latest_state_cache", StubLatestStateCache())

    view_model, _ = MainRecommendationService(
        orchestrator=EmptySectionOrchestrator(),
        music_catalog_repository=StubRepo(),
    ).get_page_view_model("user_001", "session_001")

    assert view_model["new_release"][0]["content_id"] == "new_001"
    assert view_model["discovery"][0]["content_id"] == "disc_001"
