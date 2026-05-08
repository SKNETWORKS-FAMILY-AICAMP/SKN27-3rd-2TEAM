from app.common.constants import ALLOWED_STATUSES, DEFAULT_USER_ID
from app.common.default_state import (
    MOCK_ML_OUTPUT,
    FALLBACK_RESPONSE_STATE,
    SESSION_DEFAULTS,
)
from app.common.labels import CATEGORY_LABELS


def test_common_defaults_match_documented_session_state():
    assert DEFAULT_USER_ID == "user_001"
    assert SESSION_DEFAULTS["selected_user_id"] == DEFAULT_USER_ID
    assert SESSION_DEFAULTS["current_page"] == "main_recommendation_page"
    assert SESSION_DEFAULTS["chat_history"] == []


def test_common_state_constants_keep_contract_values():
    assert "success" in ALLOWED_STATUSES
    assert "error" in ALLOWED_STATUSES
    assert MOCK_ML_OUTPUT["user_id"] == DEFAULT_USER_ID
    assert FALLBACK_RESPONSE_STATE["response_type"] == "fallback"
    assert CATEGORY_LABELS["discovery_candidate"]
