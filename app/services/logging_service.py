import json
import logging
import time
from uuid import uuid4

from app.config.settings import create_database_connection
from app.repositories import query_constants
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
        page_type: str = "chatbot_page",
    ) -> None:
        start = time.perf_counter()
        try:
            compact = CompactStateBuilder().build(kag_state, rag_state, response_state)
            conn = create_database_connection()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        query_constants.INSERT_INTERACTION_LOG,
                        {
                            "log_id": f"log_{uuid4().hex}",
                            "request_id": response_state.get("request_id") or f"req_{uuid4().hex}",
                            "user_id": user_id,
                            "session_id": session_id,
                            "user_input": user_input,
                            "page_type": page_type,
                            "status": response_state.get("status", "error"),
                            "response_type": response_state.get("response_type"),
                            "intent_type": response_state.get("intent_type"),
                            "validation_status": "success"
                            if response_state.get("status") == "success"
                            else "fallback",
                            "error_type": response_state.get("error_type"),
                            "compact_kag_state_json": json.dumps(compact["kag_state"], ensure_ascii=False),
                            "compact_rag_state_json": json.dumps(compact["rag_state"], ensure_ascii=False),
                            "compact_response_state_json": json.dumps(
                                compact["response_state"], ensure_ascii=False
                            ),
                            "validation_result_json": json.dumps(
                                {"status": response_state.get("status")}, ensure_ascii=False
                            ),
                            "latency_ms": int(latency_ms),
                        },
                    )
            conn.close()
            ms = round((time.perf_counter() - start) * 1000, 1)
            logger.info("interaction_log_saved", extra={"user_id": user_id, "ms": ms})
        except Exception as exc:
            logger.error("interaction_log_error", extra={"error": str(exc)}, exc_info=True)
