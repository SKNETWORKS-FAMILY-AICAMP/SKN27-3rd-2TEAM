def test_flush_writes_taste_events_and_profile_before_clearing_cache(monkeypatch):
    from app.services import session_flush_service

    class StubCache:
        def __init__(self, history, taste_events):
            self._history = history
            self._taste_events = taste_events
            self.cleared = False
            self.taste_cleared = False

        def get_history(self, session_id):
            return self._history

        def get_taste_events(self, session_id):
            return self._taste_events

        def clear_session(self, session_id):
            self.cleared = True

        def clear_taste_events(self, session_id):
            self.taste_cleared = True

    class StubLatestStateCache:
        def clear_latest_states(self, session_id):
            pass

    class StubConn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def cursor(self):
            return StubCursor()

        def close(self):
            pass

        def commit(self):
            pass

    class StubCursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, query, params=None):
            pass

        @property
        def rowcount(self):
            return 0

    stub_cache = StubCache(
        history=[{"user_input": "hi", "chatbot_response": "hello", "created_at": "2026-05-14T00:00:00+00:00"}],
        taste_events=[
            {
                "event_id": "evt_001",
                "user_id": "user_001",
                "session_id": "session_001",
                "content_id": "track_001",
                "event_type": "add_to_taste",
                "source": "music_detail_modal",
                "title": "Midnight Loop",
                "artist": "Nova Lane",
                "genre": ["indie"],
                "mood": ["night"],
                "recommendation_category": "discovery_candidate",
                "created_at": "2026-05-14T00:00:00+00:00",
            }
        ],
    )

    monkeypatch.setattr("app.services.session_flush_service.cache", stub_cache)
    monkeypatch.setattr("app.services.session_flush_service.latest_state_cache", StubLatestStateCache())
    monkeypatch.setattr("app.services.session_flush_service.create_database_connection", lambda: StubConn())

    result = session_flush_service.flush_session("session_001", "user_001")

    assert result["flushed"] == 1
    assert result["taste_events_flushed"] == 1


def test_flush_skips_empty_session():
    from app.services import session_flush_service
    import pytest

    class EmptyCache:
        def get_history(self, session_id):
            return []

    import importlib
    import app.services.session_flush_service as sfs
    original = sfs.cache

    sfs.cache = EmptyCache()
    try:
        result = session_flush_service.flush_session("session_empty", "user_001")
        assert result["flushed"] == 0
    finally:
        sfs.cache = original
