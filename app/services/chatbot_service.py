from app.adapters.mock_kag_adapter import MockKagAdapter
from app.adapters.mock_rag_adapter import MockRagAdapter
from app.common.default_state import FALLBACK_RESPONSE_STATE, resolve_ml_output
from app.services.llm_flow_service import LlmFlowService
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
        llm_flow_service=None,
    ):
        self._kag_adapter = kag_adapter or MockKagAdapter()
        self._rag_adapter = rag_adapter or MockRagAdapter()
        self._contract_validator = contract_validator or ContractValidator()
        self._response_validator = response_validator or ResponseValidator()
        self._provenance_validator = provenance_validator or ProvenanceValidator()
        self._view_model_service = view_model_service or ViewModelService()
        self._ml_output_repository = ml_output_repository
        self._llm_flow_service = llm_flow_service or LlmFlowService()

    def submit_message(self, user_id, user_input):
        ml_output = self._get_ml_output(user_id)
        kag_state, rag_state = self._build_states(user_id, user_input, ml_output)

        contract_result = self._contract_validator.validate(ml_output, kag_state, rag_state)
        if not contract_result["passed"]:
            return self._build_view_model(user_id, user_input, dict(FALLBACK_RESPONSE_STATE), ml_output, kag_state, rag_state, contract_result)

        response_state, llm_result = self._run_llm(user_input, ml_output, kag_state, rag_state)
        validation_result = self._validate_response(contract_result, llm_result, response_state, rag_state)

        if not validation_result["passed"]:
            response_state = dict(FALLBACK_RESPONSE_STATE)

        return self._build_view_model(user_id, user_input, response_state, ml_output, kag_state, rag_state, validation_result)

    def _build_states(self, user_id, user_input, ml_output):
        kag_state = self._kag_adapter.build_state(user_id, user_input, ml_output)
        rag_state = self._rag_adapter.build_state(kag_state)
        return kag_state, rag_state

    def _run_llm(self, user_input, ml_output, kag_state, rag_state):
        try:
            response_state = self._llm_flow_service.run(
                user_input=user_input,
                ml_output=ml_output,
                kag_state=kag_state,
                rag_state=rag_state,
            )
            return response_state, {"passed": True, "errors": []}
        except Exception:
            return dict(FALLBACK_RESPONSE_STATE), {"passed": False, "errors": ["LLM_CALL_FAILED"]}

    def _validate_response(self, contract_result, llm_result, response_state, rag_state):
        return self._merge_results(
            contract_result,
            llm_result,
            self._response_validator.validate(response_state),
            self._provenance_validator.validate(response_state, rag_state),
        )

    def _build_view_model(
        self,
        user_id,
        user_input,
        response_state,
        ml_output,
        kag_state,
        rag_state,
        validation_result,
    ):
        return self._view_model_service.build_chatbot_view_model(
            user_id=user_id,
            user_input=user_input,
            response_state=response_state,
            ml_output=ml_output,
            kag_state=kag_state,
            rag_state=rag_state,
            validation_result=validation_result,
        )

    def _merge_results(self, *results):
        errors = [error for result in results for error in result.get("errors", [])]
        return {"passed": not errors, "errors": errors}

    def _get_ml_output(self, user_id):
        return resolve_ml_output(user_id, self._ml_output_repository)
