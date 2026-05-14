import logging
import time

from app.agents.orchestrator_agent import OrchestratorAgent
from app.cache import latest_state_cache, redis_client
from app.services import session_cache_service
from app.services.logging_service import LoggingService

logger = logging.getLogger("rimas.service.chatbot")


class ChatbotService:
    """챗봇 메시지 처리 서비스."""

    def __init__(
        self,
        orchestrator: OrchestratorAgent | None = None,
        logging_service: LoggingService | None = None,
    ):
        self._orchestrator = orchestrator or OrchestratorAgent()
        self._logging_service = logging_service

    def submit_message(self, user_id: str, session_id: str, user_input: str) -> dict:
        start = time.perf_counter()
        session_degraded = not redis_client.is_healthy()

        session_context = session_cache_service.load_context(session_id, user_id=user_id)
        result = self._orchestrator.run_chatbot(
            user_id=user_id,
            session_id=session_id,
            user_input=user_input,
            session_context=session_context,
        )

        meta = result.pop("_meta", {})
        kag_state = meta.get("kag_state", {})
        rag_state = meta.get("rag_state", {})
        latency_ms = meta.get("latency_ms", round((time.perf_counter() - start) * 1000, 1))

        session_cache_service.save_turn_and_update_context(
            session_id=session_id,
            user_input=user_input,
            response_state=result,
            kag_state=kag_state,
            rag_state=rag_state,
        )

        # 응답 생성 직후 latest state를 저장한다.
        latest_state_cache.save_latest_states(
            session_id=session_id,
            kag_state=kag_state,
            rag_state=rag_state,
            response_state=result,
            recommendation_metadata={
                "source_type": "chatbot",
                "user_id": user_id,
                "latency_ms": latency_ms,
            },
        )

        # interaction_log 저장 실패는 응답을 막지 않는다.
        if self._logging_service:
            try:
                self._logging_service.save(
                    user_id=user_id,
                    session_id=session_id,
                    user_input=user_input,
                    session_context=session_context,
                    kag_state=kag_state,
                    rag_state=rag_state,
                    response_state=result,
                    latency_ms=latency_ms,
                )
            except Exception as exc:
                logger.error("log_save_error", extra={"error": str(exc)}, exc_info=True)

        logger.info(
            "chatbot_ok",
            extra={"user_id": user_id, "session_id": session_id, "ms": latency_ms},
        )

        return {
            "status": result.get("status", "error"),
            "session_degraded": session_degraded,
            "response_state": result,
            "latency_ms": latency_ms,
        }
