from app.agents.response_generator import ResponseGenerator


def test_response_generator_uses_local_response_when_openai_key_is_missing(monkeypatch):
    monkeypatch.setattr("app.config.settings.OPENAI_API_KEY", "")

    result = ResponseGenerator().run(
        user_input="추천해줘",
        session_context={"session_id": "session_001"},
        kag_state={"status": "success"},
        rag_state={
            "recommended_content_evidence": [
                {
                    "content_id": "track_001",
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "evidence_summary": "차분한 밤 분위기와 연결되는 곡",
                }
            ]
        },
        intent_result={"intent_type": "personalized_recommendation"},
        selected_recommendations={
            "selected_recommendations": [
                {
                    "content_id": "track_001",
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "recommendation_category": "personalized_match",
                    "display_reason": "차분한 밤 분위기와 연결되는 곡",
                }
            ]
        },
    )

    assert result["status"] == "success"
    assert result["response_type"] == "curator_recommendation"
    assert result["used_content_ids"] == ["track_001"]
    assert result["display_recommendations"][0]["title"] == "Midnight Loop"
