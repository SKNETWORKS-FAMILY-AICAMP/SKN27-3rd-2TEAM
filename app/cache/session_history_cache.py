"""Redis 기반 세션 히스토리 및 컨텍스트 캐시.

키 구조:
  rimas:session:{session_id}:history  — lpush 리스트 (최신 항목이 index 0)
  rimas:session:{session_id}:context  — JSON string (SESSION_CONTEXT)
"""
import logging
from datetime import datetime, timezone

from app.cache import redis_client
from app.cache.redis_keys import session_context_key, session_history_key
from app.config.settings import REDIS_SESSION_TTL

logger = logging.getLogger("rimas.session")

_MAX_HISTORY = 50  # Redis에 보관할 최대 턴 수


def get_history(session_id: str) -> list[dict]:
    """최신 순으로 저장된 리스트를 시간순(오래된 것이 앞)으로 반환."""
    key = session_history_key(session_id)
    items = redis_client.cache_lrange(key, 0, _MAX_HISTORY - 1)
    return list(reversed(items))  # lpush → newest first → reverse for chronological


def append_turn(session_id: str, user_input: str, response_state: dict) -> None:
    key = session_history_key(session_id)
    turn = {
        "user_input": user_input,
        "chatbot_response": response_state.get("chatbot_response", ""),
        "display_recommendations": response_state.get("display_recommendations", []),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    redis_client.cache_lpush(key, turn, ttl=REDIS_SESSION_TTL)
    logger.info("session_turn_appended", extra={"session_id": session_id})


def get_context(session_id: str) -> dict:
    key = session_context_key(session_id)
    ctx = redis_client.cache_get(key)
    if ctx is None:
        logger.debug("session_context_cold_start", extra={"session_id": session_id})
        return _empty_context(session_id)
    return ctx


def set_context(session_id: str, context: dict) -> None:
    key = session_context_key(session_id)
    redis_client.cache_set(key, context, ttl=REDIS_SESSION_TTL)


def update_context_from_turn(session_id: str, kag_state: dict, rag_state: dict) -> dict:
    """대화 턴 이후 SESSION_CONTEXT를 누적 업데이트하고 저장한다."""
    ctx = get_context(session_id)

    new_genres = kag_state.get("user_context", {}).get("base_preference", {}).get("genres", [])
    new_moods = kag_state.get("user_context", {}).get("base_preference", {}).get("moods", [])

    ctx["recent_genres"] = _merge_recent(ctx.get("recent_genres", []), new_genres, limit=5)
    ctx["recent_moods"] = _merge_recent(ctx.get("recent_moods", []), new_moods, limit=5)

    reason = rag_state.get("recommendation_reason", {}).get("summary", "")
    if reason:
        ctx["conversation_summary"] = reason

    set_context(session_id, ctx)
    return ctx


def clear_session(session_id: str) -> None:
    redis_client.cache_delete(session_history_key(session_id))
    redis_client.cache_delete(session_context_key(session_id))
    logger.info("session_cleared", extra={"session_id": session_id})


def _empty_context(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "recent_genres": [],
        "recent_artists": [],
        "recent_moods": [],
        "selected_tracks": [],
        "conversation_summary": "",
    }


def _merge_recent(existing: list, new_items: list, limit: int) -> list:
    """새 항목을 앞에 추가하고, 중복 제거 후 limit 개수를 유지한다."""
    merged = new_items + [x for x in existing if x not in new_items]
    return merged[:limit]
