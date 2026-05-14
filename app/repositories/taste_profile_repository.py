from app.repositories import query_constants
from app.repositories.base_repository import BaseRepository

try:
    from psycopg2.extras import Json
except ImportError:
    Json = None

_REQUIRED_EVENT_FIELDS = ("event_id", "user_id", "content_id", "event_type", "source", "title", "artist")
_JSON_EVENT_FIELDS = ("genre_json", "mood_json")


class TasteProfileRepository(BaseRepository):

    def insert_event(self, event: dict) -> str:
        self._validate_event(event)
        params = self._prepare_event_params(event)
        with self._connection.cursor() as cursor:
            cursor.execute(query_constants.INSERT_USER_TASTE_EVENT, params)
        self._connection.commit()
        return event["event_id"]

    def upsert_profile(
        self,
        *,
        user_id: str,
        preferred_genres: list[str],
        preferred_moods: list[str],
        preferred_artists: list[str],
        selected_content_ids: list[str],
    ) -> str:
        if not user_id:
            raise ValueError("user_id is required")
        params = self._prepare_profile_params(
            user_id=user_id,
            preferred_genres=preferred_genres,
            preferred_moods=preferred_moods,
            preferred_artists=preferred_artists,
            selected_content_ids=selected_content_ids,
        )
        with self._connection.cursor() as cursor:
            cursor.execute(query_constants.UPSERT_USER_TASTE_PROFILE, params)
        self._connection.commit()
        return user_id

    def find_profile(self, user_id: str) -> dict | None:
        if not user_id:
            raise ValueError("user_id is required")
        with self._cursor() as cursor:
            cursor.execute(query_constants.SELECT_USER_TASTE_PROFILE, {"user_id": user_id})
            return cursor.fetchone()

    def _validate_event(self, event: dict) -> None:
        missing = [f for f in _REQUIRED_EVENT_FIELDS if not event.get(f)]
        if missing:
            raise ValueError(f"missing required event fields: {', '.join(missing)}")

    def _prepare_event_params(self, event: dict) -> dict:
        params = dict(event)
        params["genre_json"] = self._json_param(event.get("genre", []))
        params["mood_json"] = self._json_param(event.get("mood", []))
        return params

    def _prepare_profile_params(
        self,
        *,
        user_id: str,
        preferred_genres: list[str],
        preferred_moods: list[str],
        preferred_artists: list[str],
        selected_content_ids: list[str],
    ) -> dict:
        return {
            "user_id": user_id,
            "preferred_genres_json": self._json_param(preferred_genres),
            "preferred_moods_json": self._json_param(preferred_moods),
            "preferred_artists_json": self._json_param(preferred_artists),
            "selected_content_ids_json": self._json_param(selected_content_ids),
        }

    def _json_param(self, value):
        if value is None or Json is None or not self._uses_psycopg2_connection():
            return value
        return Json(value)

    def _uses_psycopg2_connection(self) -> bool:
        return self._connection.__class__.__module__.startswith("psycopg2")
