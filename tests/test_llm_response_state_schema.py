from app.llm.response_state_schema import RESPONSE_STATE_JSON_SCHEMA


def test_response_state_json_schema_requires_only_v3_public_fields():
    assert RESPONSE_STATE_JSON_SCHEMA["required"] == [
        "status",
        "response_type",
        "chatbot_response",
        "display_recommendations",
        "used_content_ids",
    ]
    assert "provenance" not in RESPONSE_STATE_JSON_SCHEMA["properties"]
    assert "validation" not in RESPONSE_STATE_JSON_SCHEMA["properties"]
