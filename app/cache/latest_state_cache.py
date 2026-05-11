import logging

from app.cache import redis_client
from app.cache.redis_keys import (
    latest_kag_state_key,
    latest_rag_state_key,
    latest_response_state_key,
    recommendation_metadata_key,
)
from app.config.settings import REDIS_SESSION_TTL

logger = logging.getLogger("rimas.cache.latest_state")


def save_latest_states(
    session_id: str,
    kag_state: dict,
    rag_state: dict,
    response_state: dict | None = None,
    recommendation_metadata: dict | None = None,
) -> None:
    redis_client.cache_set(latest_kag_state_key(session_id), kag_state, ttl=REDIS_SESSION_TTL)
    redis_client.cache_set(latest_rag_state_key(session_id), rag_state, ttl=REDIS_SESSION_TTL)
    if response_state is not None:
        redis_client.cache_set(
            latest_response_state_key(session_id),
            response_state,
            ttl=REDIS_SESSION_TTL,
        )
    if recommendation_metadata is not None:
        redis_client.cache_set(
            recommendation_metadata_key(session_id),
            recommendation_metadata,
            ttl=REDIS_SESSION_TTL,
        )
    logger.info("latest_states_saved", extra={"session_id": session_id})


def get_latest_rag_state(session_id: str) -> dict | None:
    cached = redis_client.cache_get(latest_rag_state_key(session_id))
    if isinstance(cached, dict):
        return cached
    return None


def clear_latest_states(session_id: str) -> None:
    redis_client.cache_delete(latest_kag_state_key(session_id))
    redis_client.cache_delete(latest_rag_state_key(session_id))
    redis_client.cache_delete(latest_response_state_key(session_id))
    redis_client.cache_delete(recommendation_metadata_key(session_id))
    logger.info("latest_states_cleared", extra={"session_id": session_id})
