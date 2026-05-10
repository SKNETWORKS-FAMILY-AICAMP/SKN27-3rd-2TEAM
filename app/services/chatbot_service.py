import logging
import time

from app.agents.orchestrator_agent import OrchestratorAgent
from app.services import session_cache_service
from app.services.logging_service import LoggingService

logger = logging.getLogger("rimas.service.chatbot")


class ChatbotService:
    """챗봇 메시지 처리 — 1 API 호출 = 1 turn.

    흐름:
      Redis에서 SESSION_CONTEXT 로드 (DB 조회 없음)
      → OrchestratorAgent (KAG → RAG → Intent → Rec → LLM → Validate)
      → Redis에 turn 저장 + SESSION_CONTEXT 업데이트
      → interaction_log 비동기 저장 (선택)
    """

    def __init__(
        self,
        orchestrator: OrchestratorAgent | None = None,
        logging_service: LoggingService | None = None,
    ):
        self._orchestrator = orchestrator or OrchestratorAgent()
        self._logging_service = logging_service

    def submit_message(self, user_id: str, session_id: str, user_input: str) -> dict:
        start = time.perf_counter()

        # 1. Redis에서 SESSION_CONTEXT 로드 — DB 조회 없음
        session_context = session_cache_service.load_context(session_id)

        # 2. Orchestrator 실행 (KAG → RAG → LLM → Validate)
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

        # 3. Redis에 turn 저장 + SESSION_CONTEXT 업데이트 (1번만)
        session_cache_service.save_turn_and_update_context(
            session_id=session_id,
            user_input=user_input,
            response_state=result,
            kag_state=kag_state,
            rag_state=rag_state,
        )

        # 4. interaction_log 저장 (실패해도 응답은 반환)
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
            "response_state": result,
            "latency_ms": latency_ms,
        }
