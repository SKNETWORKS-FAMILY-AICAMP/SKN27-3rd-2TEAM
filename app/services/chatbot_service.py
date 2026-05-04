from app.adapters.mock_kag_adapter import MockKagAdapter
from app.adapters.mock_rag_adapter import MockRagAdapter
from app.services.default_state import DEFAULT_ML_OUTPUT, FALLBACK_RESPONSE_STATE
from app.services.view_model_service import ViewModelService
from app.validators.contract_validator import ContractValidator
from app.validators.provenance_validator import ProvenanceValidator
from app.validators.response_validator import ResponseValidator


class ChatbotService:
    def __init__(
        self,
        kag_adapter=None,
        rag_adapter=None,
        contract_validator=None,
        response_validator=None,
        provenance_validator=None,
        view_model_service=None,
        ml_output_repository=None,
    ):
        self._kag_adapter = kag_adapter or MockKagAdapter()
        self._rag_adapter = rag_adapter or MockRagAdapter()
        self._contract_validator = contract_validator or ContractValidator()
        self._response_validator = response_validator or ResponseValidator()
        self._provenance_validator = provenance_validator or ProvenanceValidator()
        self._view_model_service = view_model_service or ViewModelService()
        self._ml_output_repository = ml_output_repository

    def submit_message(self, user_id, user_input):
        ml_output = self._get_ml_output(user_id)
        kag_state = self._kag_adapter.build_state(user_id, user_input, ml_output)
        rag_state = self._rag_adapter.build_state(kag_state)
        contract_result = self._contract_validator.validate_all(
            ml_output, kag_state, rag_state
        )

        response_state = self._build_response_state(user_input, rag_state)
        response_result = self._response_validator.validate(response_state)
        provenance_result = self._provenance_validator.validate(
            response_state, rag_state
        )

        validation_result = self._merge_results(
            contract_result, response_result, provenance_result
        )
        if not validation_result["passed"]:
            response_state = dict(FALLBACK_RESPONSE_STATE)

        return self._view_model_service.build_chatbot_view_model(
            user_id=user_id,
            user_input=user_input,
            response_state=response_state,
            ml_output=ml_output,
            kag_state=kag_state,
            rag_state=rag_state,
            validation_result=validation_result,
        )

    def _build_response_state(self, user_input, rag_state):
        selected = self._select_recommendation(rag_state)
        display_recommendation = {
            "content_id": selected["content_id"],
            "title": selected["title"],
            "artist": selected["artist"],
            "label": self._label_for_category(selected["recommendation_category"]),
            "display_reason": selected["evidence_summary"],
        }
        return {
            "status": "success",
            "response_type": "curator_recommendation",
            "chatbot_response": self._build_chatbot_response(user_input, selected),
            "display_recommendations": [display_recommendation],
            "used_content_ids": [selected["content_id"]],
            "provenance": {
                "used_ml_fields": [
                    "taste_profile.preferred_genres",
                    "taste_profile.preferred_moods",
                ],
                "used_kag_fields": [
                    "recommendation_goal.primary_goal",
                    "curation_intent.intent_type",
                ],
                "used_rag_content_ids": [selected["content_id"]],
                "used_rag_fields": [
                    "recommended_content_evidence.evidence_summary",
                    "recommendation_reason.summary",
                ],
            },
            "validation": {
                "response_validation_passed": True,
                "provenance_validation_passed": True,
            },
        }

    def _select_recommendation(self, rag_state):
        evidence_items = rag_state.get("recommended_content_evidence", [])
        for item in evidence_items:
            if item.get("recommendation_category") == "discovery_candidate":
                return item
        return evidence_items[0]

    def _build_chatbot_response(self, user_input, selected):
        if "왜" in (user_input or "") or "이유" in (user_input or ""):
            return f"{selected['title']}은 {selected['evidence_summary']}"
        return f"{selected['artist']}의 {selected['title']}을 추천할게요. {selected['evidence_summary']}"

    def _label_for_category(self, category):
        labels = {
            "personalized_match": "개인화 추천",
            "new_release": "최신 업데이트",
            "discovery_candidate": "새 취향 탐색",
            "similar_taste": "비슷한 취향",
        }
        return labels.get(category, "추천")

    def _merge_results(self, *results):
        errors = [error for result in results for error in result.get("errors", [])]
        return {"passed": not errors, "errors": errors}

    def _get_ml_output(self, user_id):
        if self._ml_output_repository is None:
            ml_output = dict(DEFAULT_ML_OUTPUT)
            ml_output["user_id"] = user_id
            return ml_output

        found = self._ml_output_repository.get_latest_by_user_id(user_id)
        if found:
            return found

        ml_output = dict(DEFAULT_ML_OUTPUT)
        ml_output["user_id"] = user_id
        return ml_output
