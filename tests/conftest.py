import pytest

from app.adapters.mock_kag_adapter import MockKagAdapter
from app.adapters.mock_rag_adapter import MockRagAdapter
from app.common.default_state import DEFAULT_ML_OUTPUT


@pytest.fixture
def sample_payloads():
    ml_output = dict(DEFAULT_ML_OUTPUT)
    ml_output["user_id"] = "user_001"
    kag_state = MockKagAdapter().build_state(
        "user_001",
        "내 취향이랑 다른 것도 추천해줘",
        ml_output,
    )
    rag_state = MockRagAdapter().build_state(kag_state)
    return {
        "ml_output": ml_output,
        "kag_state": kag_state,
        "rag_state": rag_state,
    }
