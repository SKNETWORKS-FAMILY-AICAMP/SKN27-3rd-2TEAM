from app.repositories import query_constants
from app.repositories.base_repository import BaseRepository


class MlOutputRepository(BaseRepository):
    def get_latest_by_user_id(self, user_id):
        if not user_id:
            raise ValueError("user_id is required")

        with self._cursor() as cursor:
            cursor.execute(
                query_constants.SELECT_LATEST_ML_OUTPUT_BY_USER_ID,
                {"user_id": user_id},
            )
            return cursor.fetchone()
