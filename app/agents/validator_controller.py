from app.common.default_state import FALLBACK_RESPONSE_STATE
from app.validators.provenance_validator import ProvenanceValidator
from app.validators.response_validator import ResponseValidator


class ValidatorController:
    """응답 검증 흐름의 단일 진입점이다."""

    def __init__(
        self,
        response_validator: ResponseValidator | None = None,
        provenance_validator: ProvenanceValidator | None = None,
    ):
        self._response_validator = response_validator or ResponseValidator()
        self._provenance_validator = provenance_validator or ProvenanceValidator()

    def validate_response(self, response_state: dict, rag_state: dict) -> dict:
        response_result = self._response_validator.validate(response_state)
        provenance_result = self._provenance_validator.validate(response_state, rag_state)
        if response_result["passed"] and provenance_result["passed"]:
            return response_state

        return {
            **dict(FALLBACK_RESPONSE_STATE),
            "_meta": {
                "error_type": "RESPONSE_VALIDATION_FAILED",
                "errors": response_result.get("errors", []) + provenance_result.get("errors", []),
            },
        }
