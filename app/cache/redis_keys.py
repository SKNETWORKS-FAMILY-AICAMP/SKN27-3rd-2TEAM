"""Redis key naming contract."""

_SESSION_PREFIX = "rimas:session:{session_id}"


def session_history_key(session_id: str) -> str:
    return f"{_session_prefix(session_id)}:history"


def session_context_key(session_id: str) -> str:
    return f"{_session_prefix(session_id)}:context"


def latest_kag_state_key(session_id: str) -> str:
    return f"{_session_prefix(session_id)}:latest:kag_state"


def latest_rag_state_key(session_id: str) -> str:
    return f"{_session_prefix(session_id)}:latest:rag_state"


def latest_response_state_key(session_id: str) -> str:
    return f"{_session_prefix(session_id)}:latest:response_state"


def recommendation_metadata_key(session_id: str) -> str:
    return f"{_session_prefix(session_id)}:recommendation:metadata"


def _session_prefix(session_id: str) -> str:
    if not session_id:
        raise ValueError("session_id is required")
    return _SESSION_PREFIX.format(session_id=session_id)
