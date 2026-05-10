import logging

from app.common.constants import ALLOWED_STATUSES
from app.contracts.fields import KagStateField, RagStateField, SessionContextField
from app.validators.base_validator import BaseValidator

logger = logging.getLogger("rimas.validator.contract")

_KAG_REQUIRED = tuple(f.value for f in KagStateField)
_RAG_REQUIRED = tuple(f.value for f in RagStateField)


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
        # content_ids는 리스트여야 한다
        if not isinstance(kag_state.get("recommended_content_ids"), list):
            return {"passed": False, "errors": ["recommended_content_ids must be a list"]}
        return result

    def _validate_rag(self, rag_state: dict) -> dict:
        if not rag_state:
            return {"passed": True, "errors": []}  # RAG가 아직 없을 경우 허용
        result = self._check_fields(rag_state, _RAG_REQUIRED)
        if not result["passed"]:
            return result
        content_ids = [
            item.get("content_id")
            for item in rag_state.get("recommended_content_evidence", [])
        ]
        if len(content_ids) != len(set(content_ids)):
            return {"passed": False, "errors": ["recommended_content_evidence has duplicate content_id"]}
        return result

    def _check_fields(self, payload: dict, required_fields: tuple) -> dict:
        if not isinstance(payload, dict):
            return {"passed": False, "errors": ["payload must be a dict"]}
        if payload.get("status") not in ALLOWED_STATUSES:
            return {"passed": False, "errors": [f"status '{payload.get('status')}' is invalid"]}
        missing = [f for f in required_fields if f not in payload]
        if missing:
            return {"passed": False, "errors": [f"{missing[0]} is required"]}
        return {"passed": True, "errors": []}
