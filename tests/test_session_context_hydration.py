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
