from app.repositories import query_constants

try:
    from psycopg2.extras import RealDictCursor
except ImportError:
    RealDictCursor = None


class MlOutputRepository:
    def __init__(self, connection):
        self._connection = connection

    def get_latest_by_user_id(self, user_id):
        if not user_id:
            raise ValueError("user_id is required")

        with self._cursor() as cursor:
            cursor.execute(
                query_constants.SELECT_LATEST_ML_OUTPUT_BY_USER_ID,
                {"user_id": user_id},
            )
            return cursor.fetchone()

    def _cursor(self):
        # psycopg2 사용 시 dict 형태 결과를 반환하고, 테스트 대역에서는 기본 cursor를 사용한다.
        if RealDictCursor is None:
            return self._connection.cursor()
        return self._connection.cursor(cursor_factory=RealDictCursor)
