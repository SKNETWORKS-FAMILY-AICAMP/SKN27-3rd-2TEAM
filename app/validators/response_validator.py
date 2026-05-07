from app.validators.base_validator import BaseValidator


class ResponseValidator(BaseValidator):
    REQUIRED_FIELDS = {
        "status",
        "response_type",
        "chatbot_response",
        "display_recommendations",
        "used_content_ids",
        "provenance",
        "validation",
    }

    def validate(self, response_state):
        if not isinstance(response_state, dict):
            return {"passed": False, "errors": ["response_state must be a dict"]}
        missing_fields = [
            field for field in self.REQUIRED_FIELDS if field not in response_state
        ]
        if missing_fields:
            return {"passed": False, "errors": [f"{missing_fields[0]} is required"]}
        if not response_state["chatbot_response"]:
            return {"passed": False, "errors": ["chatbot_response is required"]}
        return {"passed": True, "errors": []}
