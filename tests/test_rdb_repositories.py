import unittest

from app.repositories.interaction_log_repository import InteractionLogRepository
from app.repositories.ml_output_repository import MlOutputRepository
from app.repositories.music_catalog_repository import MusicCatalogRepository
from app.repositories import query_constants


class FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result


class FakeConnection:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.cursor_instance = FakeCursor(fetchone_result, fetchall_result)
        self.commits = 0

    def cursor(self, *args, **kwargs):
        return self.cursor_instance

    def commit(self):
        self.commits += 1


class RdbRepositoryTest(unittest.TestCase):
    def test_ml_output_repository_fetches_latest_by_user_id(self):
        expected = {"user_id": "user_001", "status": "success"}
        connection = FakeConnection(fetchone_result=expected)
        repository = MlOutputRepository(connection)

        result = repository.get_latest_by_user_id("user_001")

        self.assertEqual(result, expected)
        self.assertEqual(
            connection.cursor_instance.executed,
            [
                (
                    query_constants.SELECT_LATEST_ML_OUTPUT_BY_USER_ID,
                    {"user_id": "user_001"},
                )
            ],
        )

    def test_music_catalog_repository_finds_by_categories(self):
        expected = [{"content_id": "track_001"}]
        connection = FakeConnection(fetchall_result=expected)
        repository = MusicCatalogRepository(connection)

        result = repository.find_by_categories(["personalized_match"])

        self.assertEqual(result, expected)
        self.assertEqual(
            connection.cursor_instance.executed,
            [
                (
                    query_constants.SELECT_MUSIC_BY_CATEGORIES,
                    {"categories": ["personalized_match"]},
                )
            ],
        )

    def test_interaction_log_repository_saves_and_commits(self):
        connection = FakeConnection()
        repository = InteractionLogRepository(connection)
        log = {
            "log_id": "log_20260504_0001",
            "user_id": "user_001",
            "user_input": "hello",
            "page_type": "chatbot_page",
            "status": "success",
            "response_type": "curator_recommendation",
            "primary_goal": "personalized_recommendation",
            "intent_type": "personalized_recommendation",
            "target_page": "chatbot_page",
            "primary_section": "personalized_recommendation_section",
            "validation_status": "success",
            "error_type": None,
            "ml_output_json": {"status": "success"},
            "kag_state_json": {"status": "success"},
            "rag_state_json": {"status": "success"},
            "response_state_json": {"status": "success"},
            "validation_result_json": {"validation_status": "success"},
            "latency_ms": 120,
        }

        result = repository.save(log)

        self.assertEqual(result, "log_20260504_0001")
        self.assertEqual(connection.commits, 1)
        self.assertEqual(
            connection.cursor_instance.executed,
            [(query_constants.INSERT_INTERACTION_LOG, log)],
        )

    def test_interaction_log_repository_finds_by_user_id(self):
        expected = [{"log_id": "log_20260504_0001"}]
        connection = FakeConnection(fetchall_result=expected)
        repository = InteractionLogRepository(connection)

        result = repository.find_by_user_id("user_001")

        self.assertEqual(result, expected)
        self.assertEqual(
            connection.cursor_instance.executed,
            [
                (
                    query_constants.SELECT_INTERACTION_LOGS_BY_USER_ID,
                    {"user_id": "user_001"},
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
