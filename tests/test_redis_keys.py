from app.cache import redis_keys


def test_session_redis_keys_are_centralized_and_namespaced():
    session_id = "session_001"

    assert redis_keys.session_history_key(session_id) == "rimas:session:session_001:history"
    assert redis_keys.session_context_key(session_id) == "rimas:session:session_001:context"
    assert redis_keys.latest_kag_state_key(session_id) == "rimas:session:session_001:latest:kag_state"
    assert redis_keys.latest_rag_state_key(session_id) == "rimas:session:session_001:latest:rag_state"
    assert redis_keys.latest_response_state_key(session_id) == "rimas:session:session_001:latest:response_state"
    assert redis_keys.recommendation_metadata_key(session_id) == "rimas:session:session_001:recommendation:metadata"


def test_session_redis_keys_reject_empty_session_id():
    for build_key in (
        redis_keys.session_history_key,
        redis_keys.session_context_key,
        redis_keys.latest_kag_state_key,
        redis_keys.latest_rag_state_key,
        redis_keys.latest_response_state_key,
        redis_keys.recommendation_metadata_key,
    ):
        try:
            build_key("")
        except ValueError as exc:
            assert str(exc) == "session_id is required"
        else:
            raise AssertionError(f"{build_key.__name__} accepted an empty session_id")
