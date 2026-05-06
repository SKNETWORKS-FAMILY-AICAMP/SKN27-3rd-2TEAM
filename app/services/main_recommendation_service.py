from app.adapters.mock_kag_adapter import MockKagAdapter
from app.adapters.mock_rag_adapter import MockRagAdapter
from app.common.default_state import DEFAULT_ML_OUTPUT
from app.services.view_model_service import ViewModelService
from app.validators.contract_validator import ContractValidator


class MainRecommendationService:
    def __init__(
        self,
        kag_adapter=None,
        rag_adapter=None,
        contract_validator=None,
        view_model_service=None,
        ml_output_repository=None,
    ):
        self._kag_adapter = kag_adapter or MockKagAdapter()
        self._rag_adapter = rag_adapter or MockRagAdapter()
        self._contract_validator = contract_validator or ContractValidator()
        self._view_model_service = view_model_service or ViewModelService()
        self._ml_output_repository = ml_output_repository

    def get_page_view_model(self, user_id):
        ml_output = self._get_ml_output(user_id)
        kag_state = self._kag_adapter.build_state(user_id, "", ml_output)
        rag_state = self._rag_adapter.build_state(kag_state)
        validation_result = self._contract_validator.validate_all(
            ml_output, kag_state, rag_state
        )

        return self._view_model_service.build_main_view_model(
            user_id=user_id,
            ml_output=ml_output,
            kag_state=kag_state,
            rag_state=rag_state,
            validation_result=validation_result,
        )

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
