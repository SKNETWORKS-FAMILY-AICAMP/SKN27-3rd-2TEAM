import logging

from app.config.settings import create_database_connection
from app.repositories.negative_preference_repository import NegativePreferenceRepository
from app.repositories.taste_profile_repository import TasteProfileRepository

logger = logging.getLogger("rimas.service.session_context_hydration")


class SessionContextHydrationService:
    def __init__(self, repository=None, negative_repository=None, connection_factory=create_database_connection):
        self._repository = repository
        self._negative_repository = negative_repository
        self._connection_factory = connection_factory

    def hydrate(self, user_id: str, session_id: str) -> dict:
        connection = None
        try:
            repository = self._repository
            negative_repository = self._negative_repository
            if repository is None and negative_repository is None:
                connection = self._connection_factory()
                repository = TasteProfileRepository(connection)
                negative_repository = NegativePreferenceRepository(connection)

            profile = repository.find_profile(user_id) if repository else None
            if not profile:
                context = _empty_context_shape(session_id)
            else:
                context = {
                    "session_id": session_id,
                    "recent_genres": list(profile.get("preferred_genres_json") or [])[:5],
                    "recent_artists": list(profile.get("preferred_artists_json") or [])[:5],
                    "recent_moods": list(profile.get("preferred_moods_json") or [])[:5],
                    "selected_tracks": list(profile.get("selected_content_ids_json") or [])[:20],
                    "conversation_summary": "",
                }

            negative_profile = negative_repository.find_by_user_id(user_id) if negative_repository else None
            context["disliked_artists"] = list((negative_profile or {}).get("disliked_artists_json") or [])[:50]
            context["disliked_tracks"] = list((negative_profile or {}).get("disliked_tracks_json") or [])[:50]
            context["disliked_genres"] = list((negative_profile or {}).get("disliked_genres_json") or [])[:50]
            return context
        except Exception as exc:
            logger.error("session_context_hydration_error", extra={"error": str(exc)}, exc_info=True)
            return _empty_context_shape(session_id)
        finally:
            if connection is not None:
                connection.close()


def _empty_context_shape(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "recent_genres": [],
        "recent_artists": [],
        "recent_moods": [],
        "selected_tracks": [],
        "disliked_artists": [],
        "disliked_tracks": [],
        "disliked_genres": [],
        "conversation_summary": "",
    }
