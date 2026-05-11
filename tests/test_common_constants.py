from app.common.constants import ALLOWED_STATUSES, DEFAULT_USER_ID
from app.common.default_state import FALLBACK_RESPONSE_STATE
from app.common.labels import CATEGORY_LABELS


def test_common_state_constants_keep_contract_values():
    assert DEFAULT_USER_ID == "user_001"
    assert "success" in ALLOWED_STATUSES
    assert "error" in ALLOWED_STATUSES
    assert FALLBACK_RESPONSE_STATE == {
        "status": "error",
        "response_type": "fallback",
        "chatbot_response": "추천 근거를 충분히 확인하지 못해 임시 안내만 제공할게요.",
        "display_recommendations": [],
        "used_content_ids": [],
    }
    assert CATEGORY_LABELS["personalized_match"] == "취향 기반 추천"
    assert CATEGORY_LABELS["discovery_candidate"] == "새로운 취향 탐색"
