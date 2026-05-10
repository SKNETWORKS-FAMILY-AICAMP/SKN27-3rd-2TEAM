import json
import logging
import time
from uuid import uuid4

from app.config.settings import create_database_connection
from app.services.compact_state_builder import CompactStateBuilder

logger = logging.getLogger("rimas.service.logging")


class LoggingService:
    """interaction_logs 테이블에 compact runtime state를 저장한다."""

    def save(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        session_context: dict,
        kag_state: dict,
        rag_state: dict,
        response_state: dict,
        latency_ms: float,
    ) -> None:
        start = time.perf_counter()
        try:
            compact = CompactStateBuilder().build(kag_state, rag_state, response_state)
            conn = create_database_connection()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO interaction_logs
                            (log_id, request_id, user_id, session_id, user_input,
                             page_type, status, response_type, intent_type,
                             compact_kag_state_json, compact_rag_state_json, compact_response_state_json,
                             validation_status, validation_result_json, latency_ms, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s::jsonb, %s::jsonb, %s::jsonb, %s, %s::jsonb, %s, NOW())
                        """,
                        (
                            f"log_{uuid4().hex}",
                            response_state.get("request_id") or f"req_{uuid4().hex}",
                            user_id,
                            session_id,
                            user_input,
                            "chatbot_page",
                            response_state.get("status", "error"),
                            response_state.get("response_type"),
                            response_state.get("intent_type"),
                            json.dumps(compact["kag_state"], ensure_ascii=False),
                            json.dumps(compact["rag_state"], ensure_ascii=False),
                            json.dumps(compact["response_state"], ensure_ascii=False),
                            "success" if response_state.get("status") == "success" else "fallback",
                            json.dumps({"status": response_state.get("status")}, ensure_ascii=False),
                            int(latency_ms),
                        ),
                    )
            conn.close()
            ms = round((time.perf_counter() - start) * 1000, 1)
            logger.info("interaction_log_saved", extra={"user_id": user_id, "ms": ms})
        except Exception as exc:
            logger.error("interaction_log_error", extra={"error": str(exc)}, exc_info=True)
