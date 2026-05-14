def test_taste_event_service_updates_context_and_appends_event():
    from app.services.taste_event_service import TasteEventService

    class StubSessionCache:
        def __init__(self):
            self.events = []
            self._context = {
                "session_id": "session_001",
                "recent_genres": [],
                "recent_artists": [],
                "recent_moods": [],
                "selected_tracks": [],
                "conversation_summary": "",
            }

        def get_context(self, session_id, user_id=None):
            return dict(self._context)

        def set_context(self, session_id, context):
            self._context = context

        def append_taste_event(self, session_id, event):
            self.events.append(event)

    class StubDetailService:
        def __init__(self, detail):
            self._detail = detail

        def get_detail(self, content_id, recent_rag_state=None):
            return self._detail

    stub_cache = StubSessionCache()
    detail_service = StubDetailService(
        {
            "content_id": "track_001",
            "title": "Midnight Loop",
            "artist": "Nova Lane",
            "genre": ["indie"],
            "mood": ["night"],
            "display_reason": "근거",
            "evidence_summary": "근거",
            "source": "rag",
        }
    )

    result = TasteEventService(
        detail_service=detail_service,
        session_cache=stub_cache,
    ).add_to_taste(
        user_id="user_001",
        session_id="session_001",
        content_id="track_001",
        source="music_detail_modal",
    )

    assert result["status"] == "success"
    assert result["session_context"]["recent_genres"] == ["indie"]
    assert result["session_context"]["selected_tracks"] == ["track_001"]
    assert stub_cache.events[0]["event_type"] == "add_to_taste"


def test_taste_event_service_rejects_missing_user_id():
    from app.services.taste_event_service import TasteEventService
    import pytest

    service = TasteEventService()
    with pytest.raises(ValueError, match="user_id"):
        service.add_to_taste(user_id="", session_id="session_001", content_id="track_001", source="music_detail_modal")


def test_taste_event_service_rejects_missing_content_id():
    from app.services.taste_event_service import TasteEventService
    import pytest

    service = TasteEventService()
    with pytest.raises(ValueError, match="content_id"):
        service.add_to_taste(user_id="user_001", session_id="session_001", content_id="", source="music_detail_modal")


def test_taste_route_factory_injects_music_detail_service(monkeypatch):
    from app.api import taste_routes

    class FakeConnection:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    class FakeRepository:
        def __init__(self, connection):
            self.connection = connection

    connection = FakeConnection()
    monkeypatch.setattr(taste_routes, "create_database_connection", lambda: connection)
    monkeypatch.setattr(taste_routes, "MusicCatalogRepository", FakeRepository)

    dependency = taste_routes.get_taste_event_service()
    service = next(dependency)

    assert service._detail_service is not None
    assert service._detail_service._music_catalog_repository.connection is connection

    try:
        next(dependency)
    except StopIteration:
        pass

    assert connection.closed
