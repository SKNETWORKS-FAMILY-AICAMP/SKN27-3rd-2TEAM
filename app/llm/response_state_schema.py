RESPONSE_STATE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "partial_match", "empty_result", "timeout", "error"],
        },
        "response_type": {
            "type": "string",
            "enum": [
                "curator_recommendation",
                "curator_information",
                "recommendation_reason",
                "fallback",
            ],
        },
        "chatbot_response": {"type": "string"},
        "display_recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "content_id": {"type": "string"},
                    "title": {"type": "string"},
                    "artist": {"type": "string"},
                    "label": {"type": "string"},
                    "display_reason": {"type": "string"},
                },
                "required": [
                    "content_id",
                    "title",
                    "artist",
                    "label",
                    "display_reason",
                ],
                "additionalProperties": False,
            },
        },
        "used_content_ids": {
            "type": "array",
            "items": {"type": "string"},
        },
        "provenance": {
            "type": "object",
            "properties": {
                "used_ml_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "used_kag_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "used_rag_content_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "used_rag_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "used_ml_fields",
                "used_kag_fields",
                "used_rag_content_ids",
                "used_rag_fields",
            ],
            "additionalProperties": False,
        },
        "validation": {
            "type": "object",
            "properties": {
                "response_validation_passed": {"type": "boolean"},
                "provenance_validation_passed": {"type": "boolean"},
            },
            "required": [
                "response_validation_passed",
                "provenance_validation_passed",
            ],
            "additionalProperties": False,
        },
    },
    "required": [
        "status",
        "response_type",
        "chatbot_response",
        "display_recommendations",
        "used_content_ids",
        "provenance",
        "validation",
    ],
    "additionalProperties": False,
}
