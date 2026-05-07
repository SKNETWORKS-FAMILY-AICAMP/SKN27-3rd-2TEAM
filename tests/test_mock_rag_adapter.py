from app.adapters.mock_kag_adapter import MockKagAdapter
from app.adapters.mock_rag_adapter import MockRagAdapter


def test_mock_rag_adapter_returns_only_docs_allowed_recommendation_categories():
    kag_state = MockKagAdapter().build_state(
        "user_001",
        "",
        {
            "status": "success",
            "user_id": "user_001",
            "taste_profile": {
                "preferred_genres": ["rnb"],
                "preferred_moods": ["calm"],
                "preferred_tempo": "medium",
            },
            "behavior_profile": {},
            "recommendation_profile": {},
        },
    )

    rag_state = MockRagAdapter().build_state(kag_state)

    categories = {
        evidence["recommendation_category"]
        for evidence in rag_state["recommended_content_evidence"]
    }
    assert rag_state["status"] == "success"
    assert categories <= {
        "personalized_match",
        "similar_taste",
        "new_release",
        "discovery_candidate",
        "information_related",
    }
    assert {"content_id", "title", "artist", "evidence_summary"} <= set(
        rag_state["recommended_content_evidence"][0]
    )
