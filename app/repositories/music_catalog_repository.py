from app.repositories import query_constants
from app.repositories.base_repository import BaseRepository


class MusicCatalogRepository(BaseRepository):
    def __init__(self, connection):
        self._connection = connection

    def find_by_categories(self, categories):
        if not categories:
            return []
        return self._fetch_all(
            query_constants.SELECT_MUSIC_BY_CATEGORIES,
            {"categories": categories},
        )

    def find_by_release_type(self, release_type):
        if not release_type:
            raise ValueError("release_type is required")
        return self._fetch_all(
            query_constants.SELECT_MUSIC_BY_RELEASE_TYPE,
            {"release_type": release_type},
        )

    def find_by_genres(self, genres):
        if not genres:
            return []
        return self._fetch_all(
            query_constants.SELECT_MUSIC_BY_GENRES,
            {"genres": genres},
        )

    def find_by_moods(self, moods):
        if not moods:
            return []
        return self._fetch_all(
            query_constants.SELECT_MUSIC_BY_MOODS,
            {"moods": moods},
        )

    def find_by_content_id(self, content_id):
        if not content_id:
            raise ValueError("content_id is required")
        with self._cursor() as cursor:
            cursor.execute(
                query_constants.SELECT_MUSIC_BY_CONTENT_ID,
                {"content_id": content_id},
            )
            return cursor.fetchone()

    def find_identity_matches(self, text):
        if not text:
            return []
        return self._fetch_all(
            query_constants.SELECT_MUSIC_IDENTITY_MATCHES,
            {"text": text},
        )

    def find_fallback_new_releases(self, limit, excluded_content_ids, excluded_artists, excluded_genres=None):
        return self._fetch_all(
            query_constants.SELECT_FALLBACK_NEW_RELEASES,
            {
                "limit": limit,
                "excluded_content_ids": excluded_content_ids or [],
                "excluded_artists": excluded_artists or [],
                "excluded_genres": excluded_genres or [],
            },
        )

    def find_fallback_discovery(self, limit, preferred_genres, excluded_content_ids, excluded_artists, excluded_genres=None):
        return self._fetch_all(
            query_constants.SELECT_FALLBACK_DISCOVERY,
            {
                "limit": limit,
                "preferred_genres": preferred_genres or [],
                "excluded_content_ids": excluded_content_ids or [],
                "excluded_artists": excluded_artists or [],
                "excluded_genres": excluded_genres or [],
            },
        )

    def _fetch_all(self, query, params):
        with self._cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
