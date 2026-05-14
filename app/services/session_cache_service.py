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
    new_dislikes: dict | None = None,
) -> dict:
    cache.append_turn(session_id, user_input, response_state)
    updated_ctx = cache.update_context_from_turn(session_id, kag_state, rag_state, new_dislikes=new_dislikes)
    logger.info("session_updated", extra={"session_id": session_id})
    return updated_ctx


def get_history(session_id: str) -> list[dict]:
    return cache.get_history(session_id)


def clear(session_id: str) -> None:
    cache.clear_session(session_id)
    logger.info("session_cleared", extra={"session_id": session_id})
