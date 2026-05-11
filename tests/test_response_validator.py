from app.validators.response_validator import ResponseValidator


def test_response_validator_accepts_v3_response_state():
    response_state = {
        "status": "success",
        "response_type": "curator_recommendation",
        "chatbot_response": "추천 메시지",
        "display_recommendations": [
            {
                "content_id": "track_001",
                "title": "Midnight Loop",
                "artist": "Nova Lane",
                "label": "취향 기반 추천",
                "display_reason": "차분한 밤 분위기와 연결되는 곡",
            }
        ],
        "used_content_ids": ["track_001"],
    }

    result = ResponseValidator().validate(response_state)

    assert result["passed"] is True
    assert result["errors"] == []


def test_response_validator_rejects_missing_chatbot_response():
    result = ResponseValidator().validate(
        {
            "status": "success",
            "response_type": "curator_recommendation",
            "display_recommendations": [],
            "used_content_ids": [],
        }
    )

    assert result["passed"] is False
    assert "chatbot_response" in result["errors"][0]


def test_response_validator_rejects_missing_display_recommendations():
    response_state = {
        "status": "success",
        "response_type": "curator_recommendation",
        "chatbot_response": "추천 메시지",
        "used_content_ids": ["track_001"],
    }

    result = ResponseValidator().validate(response_state)

    assert result["passed"] is False
    assert any("display_recommendations" in error for error in result["errors"])


def test_fallback_response_state_uses_v3_public_contract():
    from app.common.default_state import FALLBACK_RESPONSE_STATE

    assert set(FALLBACK_RESPONSE_STATE) == {
        "status",
        "response_type",
        "chatbot_response",
        "display_recommendations",
        "used_content_ids",
    }
