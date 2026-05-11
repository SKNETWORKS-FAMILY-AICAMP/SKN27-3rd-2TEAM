"""Redis → PostgreSQL 세션 플러시 서비스.

세션 종료, TTL 만료 전, 또는 API 호출 시 Redis 히스토리를
chat_sessions / chat_session_turns / interaction_logs 테이블에 저장한다.
"""
import logging
import os
import time

from app.cache import latest_state_cache, session_history_cache as cache
from app.config.settings import create_database_connection
from app.repositories import query_constants

logger = logging.getLogger("rimas.service.session_flush")

_ALLOW_FLUSH_LOGS_ENVS = {"local", "dev", "development"}


def flush_session(session_id: str, user_id: str, flush_logs: bool = False) -> dict:
    start = time.perf_counter()
    history = cache.get_history(session_id)

    if not history:
        logger.info("flush_skipped_empty", extra={"session_id": session_id})
        return {"flushed": 0, "logs_deleted": 0}

    try:
        conn = create_database_connection()
        flushed = _write_to_db(conn, session_id, user_id, history)
        logs_deleted = 0
        if flush_logs:
            logs_deleted = _delete_interaction_logs(conn, session_id)
        conn.close()
        cache.clear_session(session_id)
        latest_state_cache.clear_latest_states(session_id)
        ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info("flush_ok", extra={"session_id": session_id, "turns": flushed, "logs_deleted": logs_deleted, "ms": ms})
        return {"flushed": flushed, "logs_deleted": logs_deleted}
    except Exception as exc:
        ms = round((time.perf_counter() - start) * 1000, 1)
        logger.error("flush_error", extra={"session_id": session_id, "error": str(exc), "ms": ms}, exc_info=True)
        raise


def _delete_interaction_logs(conn, session_id: str) -> int:
    env = os.environ.get("APP_ENV", "local").lower()
    if env not in _ALLOW_FLUSH_LOGS_ENVS:
        logger.warning("flush_logs_denied_env", extra={"env": env, "session_id": session_id})
        return 0
    with conn:
        with conn.cursor() as cur:
            cur.execute(query_constants.DELETE_INTERACTION_LOGS_BY_SESSION_ID, {"session_id": session_id})
            return cur.rowcount


def _write_to_db(conn, session_id: str, user_id: str, history: list[dict]) -> int:
    with conn:
        with conn.cursor() as cur:
            # 1. chat_sessions upsert
            cur.execute(
                query_constants.UPSERT_CHAT_SESSION,
                {"session_id": session_id, "user_id": user_id},
            )
            # 2. chat_session_turns insert
            for turn in history:
                cur.execute(
                    query_constants.INSERT_CHAT_SESSION_TURN,
                    {
                        "session_id": session_id,
                        "user_input": turn.get("user_input", ""),
                        "chatbot_response": turn.get("chatbot_response", ""),
                        "created_at": turn.get("created_at"),
                    },
                )
    return len(history)
