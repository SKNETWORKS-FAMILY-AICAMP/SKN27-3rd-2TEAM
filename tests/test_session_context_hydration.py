def test_hydration_builds_context_from_profile():
    from app.services.session_context_hydration_service import SessionContextHydrationService

    class Repo:
        def find_profile(self, user_id):
            return {
                "user_id": user_id,
                "preferred_genres_json": ["indie"],
                "preferred_moods_json": ["night"],
                "preferred_artists_json": ["Nova Lane"],
                "selected_content_ids_json": ["track_001"],
            }

    ctx = SessionContextHydrationService(repository=Repo()).hydrate(
        user_id="user_001",
        session_id="session_001",
    )

    assert ctx["recent_genres"] == ["indie"]
    assert ctx["recent_moods"] == ["night"]
    assert ctx["recent_artists"] == ["Nova Lane"]
    assert ctx["selected_tracks"] == ["track_001"]


def test_hydration_returns_empty_context_when_no_profile():
    from app.services.session_context_hydration_service import SessionContextHydrationService

    class Repo:
        def find_profile(self, user_id):
            return None

    ctx = SessionContextHydrationService(repository=Repo()).hydrate(
        user_id="user_001",
        session_id="session_001",
    )

    assert ctx["session_id"] == "session_001"
    assert ctx["recent_genres"] == []
    assert ctx["selected_tracks"] == []


def test_hydration_merges_negative_preferences():
    from app.services.session_context_hydration_service import SessionContextHydrationService

    class TasteRepo:
        def find_profile(self, user_id):
            return None

    class NegativeRepo:
        def find_by_user_id(self, user_id):
            return {
                "user_id": user_id,
                "disliked_artists_json": ["Billie Eilish"],
                "disliked_tracks_json": ["track_999"],
            }

    service = SessionContextHydrationService(
        repository=TasteRepo(),
        negative_repository=NegativeRepo(),
    )

    ctx = service.hydrate(user_id="user_001", session_id="session_001")

    assert ctx["disliked_artists"] == ["Billie Eilish"]
    assert ctx["disliked_tracks"] == ["track_999"]


def test_hydration_default_constructor_reads_negative_repository_from_db_connection():
    from app.services.session_context_hydration_service import SessionContextHydrationService

    class FakeCursor:
        def __init__(self):
            self.query = ""

        def execute(self, query, params=None):
            self.query = query

        def fetchone(self):
            if "user_negative_preferences" in self.query:
                return {
                    "user_id": "user_001",
                    "disliked_artists_json": ["Billie Eilish"],
                    "disliked_tracks_json": ["track_999"],
                }
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeConnection:
        def __init__(self):
            self.closed = False
            self.cursor_obj = FakeCursor()

        def cursor(self, *args, **kwargs):
            return self.cursor_obj

        def close(self):
            self.closed = True

    connection = FakeConnection()

    ctx = SessionContextHydrationService(connection_factory=lambda: connection).hydrate(
        user_id="user_001",
        session_id="session_001",
    )

    assert ctx["disliked_artists"] == ["Billie Eilish"]
    assert ctx["disliked_tracks"] == ["track_999"]
    assert connection.closed
