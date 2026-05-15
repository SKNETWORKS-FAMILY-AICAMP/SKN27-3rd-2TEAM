import logging
import time

from app.agents.orchestrator_agent import OrchestratorAgent
from app.cache import latest_state_cache, redis_client
from app.config.settings import create_database_connection
from app.repositories.negative_preference_repository import NegativePreferenceRepository
from app.services.logging_service import LoggingService
from app.services.negative_preference_service import NegativePreferenceService
from app.services import session_cache_service

logger = logging.getLogger("rimas.service.chatbot")


class ChatbotService:
    """챗봇 메시지 처리 서비스."""

    def __init__(
        self,
        orchestrator: OrchestratorAgent | None = None,
        logging_service: LoggingService | None = None,
        negative_preference_service: NegativePreferenceService | None = None,
    ):
        self._orchestrator = orchestrator or OrchestratorAgent()
        self._logging_service = logging_service
        self._negative_preference_service = negative_preference_service

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
        new_dislikes = meta.get("new_dislikes", {"disliked_artists": [], "disliked_tracks": []})
        self._save_negative_preferences(user_id, session_context, new_dislikes)

        session_cache_service.save_turn_and_update_context(
            session_id=session_id,
            user_input=user_input,
            response_state=result,
            kag_state=kag_state,
            rag_state=rag_state,
            new_dislikes=new_dislikes,
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

    def _save_negative_preferences(self, user_id: str, session_context: dict, new_dislikes: dict) -> None:
        new_artists = new_dislikes.get("disliked_artists", []) or []
        new_tracks = new_dislikes.get("disliked_tracks", []) or []
        new_genres = new_dislikes.get("disliked_genres", []) or []
        if not new_artists and not new_tracks and not new_genres:
            return

        try:
            service = self._negative_preference_service or self._build_negative_preference_service()
            service.merge_and_save(
                user_id=user_id,
                existing_artists=session_context.get("disliked_artists", []),
                existing_tracks=session_context.get("disliked_tracks", []),
                existing_genres=session_context.get("disliked_genres", []),
                new_artists=new_artists,
                new_tracks=new_tracks,
                new_genres=new_genres,
            )
        except Exception as exc:
            logger.error("negative_preference_save_error", extra={"error": str(exc)}, exc_info=True)

    @staticmethod
    def _build_negative_preference_service() -> NegativePreferenceService:
        conn = create_database_connection()
        return NegativePreferenceService(repository=NegativePreferenceRepository(conn))
