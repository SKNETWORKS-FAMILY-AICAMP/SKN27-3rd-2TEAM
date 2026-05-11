import logging

from app.common.constants import ALLOWED_STATUSES
from app.contracts.fields import KagStateField, RagStateField, SessionContextField
from app.validators.base_validator import BaseValidator

logger = logging.getLogger("rimas.validator.contract")

_KAG_REQUIRED = tuple(f.value for f in KagStateField)
_RAG_REQUIRED = tuple(f.value for f in RagStateField)
_KAG_OPTIONAL_TYPES = {
    "traversal_reason": str,
    "matched_nodes": list,
    "excluded_nodes": list,
    "candidate_tracks": list,
    "diversity_metadata": dict,
}
_RAG_OPTIONAL_TYPES = {
    "query": str,
    "normalized_query": str,
    "retrieval_metadata": dict,
    "retrieval_trace": dict,
}


class ContractValidator(BaseValidator):
    def validate(self, session_context: dict, kag_state: dict, rag_state: dict) -> dict:
        results = [
            self._validate_session_context(session_context),
            self._validate_kag(kag_state),
            self._validate_rag(rag_state),
        ]
        errors = [e for r in results for e in r["errors"]]
        passed = not errors
        if not passed:
            logger.warning("contract_invalid", extra={"errors": errors})
        return {"passed": passed, "errors": errors}

    def _validate_session_context(self, ctx: dict) -> dict:
        if not isinstance(ctx, dict):
            return {"passed": False, "errors": ["session_context must be a dict"]}
        required = (SessionContextField.SESSION_ID,)
        missing = [f for f in required if f not in ctx]
        if missing:
            return {"passed": False, "errors": [f"{missing[0]} is required in session_context"]}
        return {"passed": True, "errors": []}

    def _validate_kag(self, kag_state: dict) -> dict:
        result = self._check_fields(kag_state, _KAG_REQUIRED)
        if not result["passed"]:
            return result
        if not isinstance(kag_state.get("recommended_content_ids"), list):
            return {"passed": False, "errors": ["recommended_content_ids must be a list"]}
        optional_type_error = self._validate_optional_kag_types(kag_state)
        if optional_type_error:
            return {"passed": False, "errors": [optional_type_error]}
        return result

    def _validate_optional_kag_types(self, kag_state: dict) -> str | None:
        for field_name, expected_type in _KAG_OPTIONAL_TYPES.items():
            if field_name not in kag_state:
                continue
            if not isinstance(kag_state[field_name], expected_type):
                return f"{field_name} must be a {expected_type.__name__}"
        return None

    def _validate_rag(self, rag_state: dict) -> dict:
        if not rag_state:
            return {"passed": True, "errors": []}
        result = self._check_fields(rag_state, _RAG_REQUIRED)
        if not result["passed"]:
            return result
        content_ids = [
            item.get("content_id")
            for item in rag_state.get("recommended_content_evidence", [])
        ]
        if len(content_ids) != len(set(content_ids)):
            return {"passed": False, "errors": ["recommended_content_evidence has duplicate content_id"]}
        optional_type_error = self._validate_optional_rag_types(rag_state)
        if optional_type_error:
            return {"passed": False, "errors": [optional_type_error]}
        return result

    def _validate_optional_rag_types(self, rag_state: dict) -> str | None:
        for field_name, expected_type in _RAG_OPTIONAL_TYPES.items():
            if field_name not in rag_state:
                continue
            if not isinstance(rag_state[field_name], expected_type):
                return f"{field_name} must be a {expected_type.__name__}"
        return None

    def _check_fields(self, payload: dict, required_fields: tuple) -> dict:
        if not isinstance(payload, dict):
            return {"passed": False, "errors": ["payload must be a dict"]}
        if payload.get("status") not in ALLOWED_STATUSES:
            return {"passed": False, "errors": [f"status '{payload.get('status')}' is invalid"]}
        missing = [f for f in required_fields if f not in payload]
        if missing:
            return {"passed": False, "errors": [f"{missing[0]} is required"]}
        return {"passed": True, "errors": []}
