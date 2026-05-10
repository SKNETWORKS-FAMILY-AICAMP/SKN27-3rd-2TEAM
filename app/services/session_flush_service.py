"""Redis → PostgreSQL 세션 플러시 서비스.

세션 종료, TTL 만료 전, 또는 API 호출 시 Redis 히스토리를
chat_sessions / chat_session_turns / interaction_logs 테이블에 저장한다.
"""
import logging
import time

from app.cache import session_history_cache as cache
from app.config.settings import create_database_connection

logger = logging.getLogger("rimas.service.session_flush")


def flush_session(session_id: str, user_id: str) -> dict:
    start = time.perf_counter()
    history = cache.get_history(session_id)

    if not history:
        logger.info("flush_skipped_empty", extra={"session_id": session_id})
        return {"flushed": 0}

    try:
        conn = create_database_connection()
        flushed = _write_to_db(conn, session_id, user_id, history)
        conn.close()
        cache.clear_session(session_id)
        ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info("flush_ok", extra={"session_id": session_id, "turns": flushed, "ms": ms})
        return {"flushed": flushed}
    except Exception as exc:
        ms = round((time.perf_counter() - start) * 1000, 1)
        logger.error("flush_error", extra={"session_id": session_id, "error": str(exc), "ms": ms}, exc_info=True)
        raise


def _write_to_db(conn, session_id: str, user_id: str, history: list[dict]) -> int:
    with conn:
        with conn.cursor() as cur:
            # 1. chat_sessions upsert
            cur.execute(
                """
                INSERT INTO chat_sessions (session_id, user_id, started_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (session_id) DO NOTHING
                """,
                (session_id, user_id),
            )
            # 2. chat_session_turns insert
            for turn in history:
                cur.execute(
                    """
                    INSERT INTO chat_session_turns
                        (session_id, user_input, chatbot_response, created_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        session_id,
                        turn.get("user_input", ""),
                        turn.get("chatbot_response", ""),
                        turn.get("created_at"),
                    ),
                )
    return len(history)
