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
    },
    "required": [
        "status",
        "response_type",
        "chatbot_response",
        "display_recommendations",
        "used_content_ids",
    ],
    "additionalProperties": False,
}
