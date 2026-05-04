from app.validators.response_validator import ResponseValidator


def test_response_validator_accepts_docs_response_state():
    response_state = {
        "status": "success",
        "response_type": "curator_recommendation",
        "chatbot_response": "추천 메시지",
        "display_recommendations": [],
        "used_content_ids": [],
        "provenance": {},
        "validation": {},
    }

    result = ResponseValidator().validate(response_state)

    assert result["passed"] is True


def test_response_validator_rejects_missing_chatbot_response():
    result = ResponseValidator().validate(
        {
            "status": "success",
            "response_type": "curator_recommendation",
            "display_recommendations": [],
            "used_content_ids": [],
            "provenance": {},
            "validation": {},
        }
    )

    assert result["passed"] is False
    assert "chatbot_response" in result["errors"][0]
