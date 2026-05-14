from app.repositories import query_constants
from app.repositories.base_repository import BaseRepository

try:
    from psycopg2.extras import Json
except ImportError:
    Json = None


class NegativePreferenceRepository(BaseRepository):
    def upsert(self, *, user_id: str, disliked_artists: list[str], disliked_tracks: list[str]) -> str:
        if not user_id:
            raise ValueError("user_id is required")
        with self._connection.cursor() as cursor:
            cursor.execute(
                query_constants.UPSERT_USER_NEGATIVE_PREFERENCES,
                {
                    "user_id": user_id,
                    "disliked_artists_json": self._json_param(disliked_artists),
                    "disliked_tracks_json": self._json_param(disliked_tracks),
                },
            )
        self._connection.commit()
        return user_id

    def find_by_user_id(self, user_id: str) -> dict | None:
        if not user_id:
            raise ValueError("user_id is required")
        with self._cursor() as cursor:
            cursor.execute(query_constants.SELECT_USER_NEGATIVE_PREFERENCES, {"user_id": user_id})
            return cursor.fetchone()

    def _json_param(self, value):
        if value is None or Json is None or not self._uses_psycopg2_connection():
            return value
        return Json(value)

    def _uses_psycopg2_connection(self) -> bool:
        return self._connection.__class__.__module__.startswith("psycopg2")
