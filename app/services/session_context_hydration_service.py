class SessionContextHydrationService:
    def __init__(self, repository=None):
        self._repository = repository

    def hydrate(self, user_id: str, session_id: str) -> dict:
        profile = self._repository.find_profile(user_id) if self._repository else None
        if not profile:
            return _empty_context_shape(session_id)
        return {
            "session_id": session_id,
            "recent_genres": list(profile.get("preferred_genres_json") or [])[:5],
            "recent_artists": list(profile.get("preferred_artists_json") or [])[:5],
            "recent_moods": list(profile.get("preferred_moods_json") or [])[:5],
            "selected_tracks": list(profile.get("selected_content_ids_json") or [])[:20],
            "conversation_summary": "",
        }


def _empty_context_shape(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "recent_genres": [],
        "recent_artists": [],
        "recent_moods": [],
        "selected_tracks": [],
        "conversation_summary": "",
    }
