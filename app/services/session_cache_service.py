"""세션 캐시 서비스 경계.

API/서비스 계층은 이 모듈을 통해 Redis 세션 캐시에 접근한다.
"""

from app.cache import session_history_cache


def load_context(session_id: str, user_id: str | None = None) -> dict:
    return session_history_cache.get_context(session_id, user_id=user_id)


def save_turn_and_update_context(
    *,
    session_id: str,
    user_input: str,
    response_state: dict,
    kag_state: dict,
    rag_state: dict,
    new_dislikes: dict | None = None,
) -> dict:
    session_history_cache.append_turn(session_id, user_input, response_state)
    return session_history_cache.update_context_from_turn(
        session_id,
        kag_state,
        rag_state,
        new_dislikes=new_dislikes,
    )


def update_context_from_taste(
    session_id: str,
    *,
    genre: list,
    mood: list,
    artist: str,
    content_id: str,
) -> dict:
    return session_history_cache.update_context_from_taste(
        session_id,
        genre=genre,
        mood=mood,
        artist=artist,
        content_id=content_id,
    )


def append_taste_event(session_id: str, event: dict) -> None:
    session_history_cache.append_taste_event(session_id, event)
