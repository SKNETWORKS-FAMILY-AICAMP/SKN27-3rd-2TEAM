from app.repositories import query_constants

try:
    from psycopg2.extras import Json, RealDictCursor
except ImportError:
    Json = None
    RealDictCursor = None


JSON_FIELDS = (
    "ml_output_json",
    "kag_state_json",
    "rag_state_json",
    "response_state_json",
    "validation_result_json",
)


class InteractionLogRepository:
    def __init__(self, connection):
        self._connection = connection

    def save(self, log):
        self._validate_required_fields(log)
        params = self._prepare_params(log)

        with self._connection.cursor() as cursor:
            cursor.execute(query_constants.INSERT_INTERACTION_LOG, params)

        self._connection.commit()
        return log["log_id"]

    def find_by_user_id(self, user_id):
        if not user_id:
            raise ValueError("user_id is required")

        with self._cursor() as cursor:
            cursor.execute(
                query_constants.SELECT_INTERACTION_LOGS_BY_USER_ID,
                {"user_id": user_id},
            )
            return cursor.fetchall()

    def find_recent(self, limit):
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        with self._cursor() as cursor:
            cursor.execute(
                query_constants.SELECT_RECENT_INTERACTION_LOGS,
                {"limit": limit},
            )
            return cursor.fetchall()

    def _validate_required_fields(self, log):
        required_fields = (
            "log_id",
            "user_id",
            "page_type",
            "status",
            "validation_status",
        )
        missing_fields = [field for field in required_fields if not log.get(field)]
        if missing_fields:
            joined_fields = ", ".join(missing_fields)
            raise ValueError(f"missing required log fields: {joined_fields}")

    def _prepare_params(self, log):
        params = dict(log)
        for field in JSON_FIELDS:
            params[field] = self._json_param(params.get(field))
        return params

    def _json_param(self, value):
        if value is None or Json is None:
            return value
        return Json(value)

    def _cursor(self):
        # psycopg2 사용 시 dict 형태 결과를 반환하고, 테스트 대역에서는 기본 cursor를 사용한다.
        if RealDictCursor is None:
            return self._connection.cursor()
        return self._connection.cursor(cursor_factory=RealDictCursor)
