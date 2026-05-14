"""Redis 기반 세션 컨텍스트 관리 서비스.

책임:
  - SESSION_CONTEXT 로드 (Redis hit → 반환, miss → 빈 컨텍스트)
  - 대화 턴 이후 SESSION_CONTEXT 누적 업데이트
  - 세션 히스토리 반환 (최신 50턴, Redis only)
"""
import logging

from app.cache import session_history_cache as cache

logger = logging.getLogger("rimas.service.session_cache")


def load_context(session_id: str, user_id: str | None = None) -> dict:
    return cache.get_context(session_id, user_id=user_id)


def save_turn_and_update_context(
    session_id: str,
    user_input: str,
    response_state: dict,
    kag_state: dict,
    rag_state: dict,
) -> dict:
    """대화 턴을 Redis에 저장하고 SESSION_CONTEXT를 업데이트한다."""
    cache.append_turn(session_id, user_input, response_state)
    updated_ctx = cache.update_context_from_turn(session_id, kag_state, rag_state)
    logger.info("session_updated", extra={"session_id": session_id})
    return updated_ctx


def get_history(session_id: str) -> list[dict]:
    return cache.get_history(session_id)


def clear(session_id: str) -> None:
    cache.clear_session(session_id)
    logger.info("session_cleared", extra={"session_id": session_id})
