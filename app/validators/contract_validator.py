ALLOWED_STATUSES = {"success", "partial_match", "empty_result", "timeout", "error"}


class ContractValidator:
    ML_REQUIRED_FIELDS = (
        "status",
        "user_id",
        "taste_profile",
        "behavior_profile",
        "recommendation_profile",
    )
    KAG_REQUIRED_FIELDS = (
        "status",
        "user",
        "recommendation_goal",
        "user_context",
        "curation_intent",
        "curation_strategy",
        "content_requirements",
        "routing",
        "selected_path",
    )
    RAG_REQUIRED_FIELDS = (
        "status",
        "recommendation_context",
        "recommended_content_evidence",
        "recommendation_reason",
        "recommendation_scripts",
    )

    def validate_all(self, ml_output, kag_state, rag_state):
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
