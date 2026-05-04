from app.repositories import query_constants

try:
    from psycopg2.extras import RealDictCursor
except ImportError:
    RealDictCursor = None


class MusicCatalogRepository:
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

    def _cursor(self):
        # psycopg2 사용 시 dict 형태 결과를 반환하고, 테스트 대역에서는 기본 cursor를 사용한다.
        if RealDictCursor is None:
            return self._connection.cursor()
        return self._connection.cursor(cursor_factory=RealDictCursor)
