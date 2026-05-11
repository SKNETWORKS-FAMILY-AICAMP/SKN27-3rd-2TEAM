from app.kag.adapters.mock_kag_adapter import MockKagAdapter
from app.rag.adapters.mock_rag_adapter import MockRagAdapter


def test_mock_rag_adapter_returns_only_docs_allowed_recommendation_categories():
    session_context = {
        "session_id": "session_001",
        "recent_genres": ["rnb"],
        "recent_moods": ["calm"],
        "recent_artists": [],
        "conversation_summary": "",
    }
    kag_state = MockKagAdapter().build_state("user_001", "", session_context)

    rag_state = MockRagAdapter().build_state(
        kag_state,
        rag_input_json={"query_text": "calm rnb recommendation"},
    )

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
    assert rag_state["query"] == "calm rnb recommendation"
    assert rag_state["normalized_query"] == "calm rnb recommendation"
    assert isinstance(rag_state["retrieval_metadata"], dict)
    assert isinstance(rag_state["retrieval_trace"], dict)
