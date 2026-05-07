from app.adapters.mock_kag_adapter import MockKagAdapter


def test_mock_kag_adapter_returns_docs_defined_kag_state():
    adapter = MockKagAdapter()
    ml_output = {
        "status": "success",
        "user_id": "user_001",
        "taste_profile": {
            "preferred_genres": ["rnb", "indie"],
            "preferred_moods": ["calm", "night"],
            "preferred_tempo": "medium",
        },
        "behavior_profile": {
            "recent_listening_level": "medium",
            "recent_discovery_level": "low",
            "repeat_listening_ratio": 0.72,
            "new_artist_acceptance": 0.34,
        },
        "recommendation_profile": {
            "personalization_strength": "high",
            "discovery_readiness": "medium",
            "new_release_affinity": "medium",
        },
    }

    kag_state = adapter.build_state("user_001", "새로운 취향도 추천해줘", ml_output)

    assert kag_state["status"] == "success"
    assert kag_state["user"]["user_id"] == "user_001"
    assert kag_state["recommendation_goal"]["primary_goal"] == "new_taste_discovery"
    assert kag_state["routing"]["target_page"] == "main_recommendation_page"
    assert "personalized_match" in kag_state["content_requirements"]["must_include"]
