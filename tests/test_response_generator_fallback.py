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


def test_response_generator_uses_llm_refined_display_reason_when_valid():
    class StubLlmClient:
        def generate_json(self, **kwargs):
            return {
                "status": "success",
                "response_type": "curator_recommendation",
                "chatbot_response": "Midnight Loop를 추천할게요.",
                "display_recommendations": [
                    {
                        "content_id": "track_001",
                        "title": "Midnight Loop",
                        "artist": "Nova Lane",
                        "label": "취향 기반 추천",
                        "display_reason": "indie 취향과 calm 분위기가 자연스럽게 이어지는 곡입니다.",
                    }
                ],
                "used_content_ids": ["track_001"],
            }

    result = ResponseGenerator(llm_client=StubLlmClient()).run(
        user_input="추천해줘",
        session_context={"session_id": "session_001"},
        kag_state={"status": "success"},
        rag_state={"recommended_content_evidence": []},
        intent_result={"intent_type": "personalized_recommendation"},
        selected_recommendations={
            "selected_recommendations": [
                {
                    "content_id": "track_001",
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "recommendation_category": "personalized_match",
                    "genre": ["indie"],
                    "mood": ["calm"],
                    "display_reason": "indie 취향과 calm 분위기에 맞춰 고른 곡입니다.",
                    "rank": 1,
                    "score": 100,
                    "source": {"kag": False, "rag": True},
                }
            ]
        },
    )

    assert result["display_recommendations"][0]["display_reason"] == "indie 취향과 calm 분위기가 자연스럽게 이어지는 곡입니다."


def test_response_generator_falls_back_to_deterministic_reason_when_llm_reason_is_invalid():
    raw_lyrics = "raw lyrics line raw lyrics line raw lyrics line"

    class StubLlmClient:
        def generate_json(self, **kwargs):
            return {
                "status": "success",
                "response_type": "curator_recommendation",
                "chatbot_response": "Midnight Loop를 추천할게요.",
                "display_recommendations": [
                    {
                        "content_id": "track_001",
                        "title": "Midnight Loop",
                        "artist": "Nova Lane",
                        "label": "취향 기반 추천",
                        "display_reason": raw_lyrics,
                    }
                ],
                "used_content_ids": ["track_001"],
            }

    result = ResponseGenerator(llm_client=StubLlmClient()).run(
        user_input="추천해줘",
        session_context={"session_id": "session_001"},
        kag_state={"status": "success"},
        rag_state={"recommended_content_evidence": []},
        intent_result={"intent_type": "personalized_recommendation"},
        selected_recommendations={
            "selected_recommendations": [
                {
                    "content_id": "track_001",
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "recommendation_category": "personalized_match",
                    "genre": ["indie"],
                    "mood": ["calm"],
                    "evidence_summary": raw_lyrics,
                    "display_reason": "indie 취향과 calm 분위기에 맞춰 고른 곡입니다.",
                    "rank": 1,
                    "score": 100,
                    "source": {"kag": False, "rag": True},
                }
            ]
        },
    )

    assert result["display_recommendations"][0]["display_reason"] == "indie 취향과 calm 분위기에 맞춰 고른 곡입니다."
