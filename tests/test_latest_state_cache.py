from app.cache import latest_state_cache


class FakeRedisClient:
    def __init__(self):
        self.saved = []

    def cache_set(self, key, value, ttl):
        self.saved.append((key, value, ttl))


def test_latest_state_cache_writes_latest_states_to_session_keys(monkeypatch):
    fake_redis = FakeRedisClient()
    monkeypatch.setattr(latest_state_cache, "redis_client", fake_redis)
    monkeypatch.setattr(latest_state_cache, "REDIS_SESSION_TTL", 123)

    latest_state_cache.save_latest_states(
        session_id="session_001",
        kag_state={"status": "success", "kind": "kag"},
        rag_state={"status": "success", "kind": "rag"},
        response_state={"status": "success", "kind": "response"},
        recommendation_metadata={"source_type": "chatbot"},
    )

    assert fake_redis.saved == [
        (
            "rimas:session:session_001:latest:kag_state",
            {"status": "success", "kind": "kag"},
            123,
        ),
        (
            "rimas:session:session_001:latest:rag_state",
            {"status": "success", "kind": "rag"},
            123,
        ),
        (
            "rimas:session:session_001:latest:response_state",
            {"status": "success", "kind": "response"},
            123,
        ),
        (
            "rimas:session:session_001:recommendation:metadata",
            {"source_type": "chatbot"},
            123,
        ),
    ]
