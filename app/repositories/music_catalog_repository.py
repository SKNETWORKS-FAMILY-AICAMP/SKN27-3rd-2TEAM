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

    def _fetch_all(self, query, params):
        with self._cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
