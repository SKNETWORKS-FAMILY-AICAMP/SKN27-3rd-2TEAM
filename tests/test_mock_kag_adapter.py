from app.kag.adapters.mock_kag_adapter import MockKagAdapter


def test_mock_kag_adapter_returns_kag_state():
    adapter = MockKagAdapter()
    session_context = {
        "session_id": "session_001",
        "recent_genres": ["rnb", "indie"],
        "recent_moods": ["calm", "night"],
        "recent_artists": [],
        "conversation_summary": "",
    }

    kag_state = adapter.build_state("user_001", "새로운 취향도 추천해줘", session_context)

    assert kag_state["status"] == "success"
    assert kag_state["recommendation_goal"]["primary_goal"] == "new_taste_discovery"
    assert kag_state["recommendation_category"] == "discovery_candidate"
    assert kag_state["route"] == "safe_discovery"
    assert kag_state["target_section"] == "discovery_section"
    assert isinstance(kag_state["recommended_content_ids"], list)
    assert isinstance(kag_state["traversal_reason"], str)
    assert isinstance(kag_state["matched_nodes"], list)
    assert isinstance(kag_state["excluded_nodes"], list)
    assert isinstance(kag_state["candidate_tracks"], list)
    assert isinstance(kag_state["diversity_metadata"], dict)
