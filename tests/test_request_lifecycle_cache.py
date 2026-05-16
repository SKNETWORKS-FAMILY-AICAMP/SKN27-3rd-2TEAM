from fastapi.testclient import TestClient

from app.main import app
from app.services.request_lifecycle_cache import request_lifecycle_cache


def test_main_recommendation_route_rejects_duplicate_inflight_request_id():
    request_id = "req_duplicate_contract_test"
    request_lifecycle_cache.start(request_id)
    try:
        response = TestClient(app).get(
            "/api/recommendations/main",
            params={
                "user_id": "user_1",
                "session_id": "session_1",
                "request_id": request_id,
            },
        )
    finally:
        request_lifecycle_cache.finish(request_id)

    assert response.status_code == 409
