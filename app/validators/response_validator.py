from app.contracts.fields import ResponseStateField
from app.validators.base_validator import BaseValidator


class ResponseValidator(BaseValidator):
    REQUIRED_FIELDS = {field.value for field in ResponseStateField}

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

        if not isinstance(response_state["display_recommendations"], list):
            return {"passed": False, "errors": ["display_recommendations must be a list"]}

        if not isinstance(response_state["used_content_ids"], list):
            return {"passed": False, "errors": ["used_content_ids must be a list"]}

        return {"passed": True, "errors": []}
