from app.common.constants import ALLOWED_STATUSES
from app.contracts.fields import KagStateField, MlOutputField, RagStateField
from app.validators.base_validator import BaseValidator


class ContractValidator(BaseValidator):
    ML_REQUIRED_FIELDS = tuple(f.value for f in MlOutputField)
    KAG_REQUIRED_FIELDS = tuple(f.value for f in KagStateField)
    RAG_REQUIRED_FIELDS = (
        RagStateField.STATUS,
        RagStateField.RECOMMENDATION_CONTEXT,
        RagStateField.RECOMMENDED_CONTENT_EVIDENCE,
        RagStateField.RECOMMENDATION_REASON,
        RagStateField.RECOMMENDATION_SCRIPTS,
    )

    def validate(self, ml_output, kag_state, rag_state):
        results = [
            self.validate_ml_output(ml_output),
            self.validate_kag(kag_state),
            self.validate_rag(rag_state),
        ]
        errors = [error for result in results for error in result["errors"]]
        return {"passed": not errors, "errors": errors}

    def validate_ml_output(self, ml_output):
        return self._validate_required_fields(ml_output, self.ML_REQUIRED_FIELDS)

    def validate_kag(self, kag_state):
        return self._validate_required_fields(kag_state, self.KAG_REQUIRED_FIELDS)

    def validate_rag(self, rag_state):
        result = self._validate_required_fields(rag_state, self.RAG_REQUIRED_FIELDS)
        if not result["passed"]:
            return result
        content_ids = [
            item.get("content_id")
            for item in rag_state.get("recommended_content_evidence", [])
        ]
        if len(content_ids) != len(set(content_ids)):
            return {"passed": False, "errors": ["recommended_content_evidence has duplicate content_id"]}
        return result

    def _validate_required_fields(self, payload, required_fields):
        if not isinstance(payload, dict):
            return {"passed": False, "errors": ["payload must be a dict"]}
        if payload.get("status") not in ALLOWED_STATUSES:
            return {"passed": False, "errors": ["status is invalid"]}
        missing_fields = [field for field in required_fields if field not in payload]
        if missing_fields:
            return {
                "passed": False,
                "errors": [f"{missing_fields[0]} is required"],
            }
        return {"passed": True, "errors": []}
