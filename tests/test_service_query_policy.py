from app.repositories import query_constants
from app.services import logging_service
from app.services.logging_service import LoggingService
from app.services.session_flush_service import _write_to_db


class FakeCursor:
    def __init__(self):
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.executed.append((query, params))


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return self.cursor_instance

    def close(self):
        self.closed = True


def test_logging_service_uses_interaction_log_query_constant(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(logging_service, "create_database_connection", lambda: connection)

    LoggingService().save(
        user_id="user_001",
        session_id="session_001",
        user_input="추천해줘",
        session_context={"session_id": "session_001"},
        kag_state={"status": "success"},
        rag_state={"status": "success", "recommended_content_evidence": []},
        response_state={
            "status": "success",
            "response_type": "curator_recommendation",
            "intent_type": "personalized_recommendation",
            "chatbot_response": "추천 응답",
            "display_recommendations": [],
            "used_content_ids": [],
        },
        latency_ms=12.4,
    )

    executed_query, params = connection.cursor_instance.executed[0]
    assert executed_query == query_constants.INSERT_INTERACTION_LOG
    assert params["user_id"] == "user_001"
    assert params["validation_status"] == "success"
    assert connection.closed is True


def test_session_flush_uses_session_query_constants():
    connection = FakeConnection()
    history = [
        {
            "user_input": "추천해줘",
            "chatbot_response": "추천 응답",
            "created_at": "2026-05-11T00:00:00+00:00",
        }
    ]

    flushed = _write_to_db(connection, "session_001", "user_001", history)

    assert flushed == 1
    assert connection.cursor_instance.executed == [
        (
            query_constants.UPSERT_CHAT_SESSION,
            {"session_id": "session_001", "user_id": "user_001"},
        ),
        (
            query_constants.INSERT_CHAT_SESSION_TURN,
            {
                "session_id": "session_001",
                "user_input": "추천해줘",
                "chatbot_response": "추천 응답",
                "created_at": "2026-05-11T00:00:00+00:00",
            },
        ),
    ]
