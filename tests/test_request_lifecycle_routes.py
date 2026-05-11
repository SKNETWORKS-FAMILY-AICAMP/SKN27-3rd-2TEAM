from fastapi.testclient import TestClient

from app.api import chatbot_routes, recommendation_routes
from app.main import app
from app.services.request_lifecycle_cache import request_lifecycle_cache


class StubRecommendationService:
    def __init__(self):
        self.calls = []

    def get_page_view_model(self, user_id, session_id):
        self.calls.append((user_id, session_id))
        return {"personalized": [], "new_release": [], "discovery": []}


class StubChatbotService:
    def __init__(self):
        self.calls = []

    def submit_message(self, user_id, session_id, user_input):
        self.calls.append((user_id, session_id, user_input))
        return {
            "status": "success",
            "response_state": {
                "status": "success",
                "response_type": "curator_recommendation",
                "chatbot_response": "응답",
                "display_recommendations": [],
                "used_content_ids": [],
            },
            "latency_ms": 1,
        }


def test_recommendation_route_rejects_duplicate_inflight_request_id(monkeypatch):
    request_id = "req_route_duplicate_main"
    service = StubRecommendationService()
    monkeypatch.setattr(recommendation_routes, "_service", service)
    request_lifecycle_cache.start(request_id)

    try:
        response = TestClient(app).get(
            "/api/recommendations/main",
            params={
                "user_id": "user_001",
                "session_id": "session_001",
                "request_id": request_id,
            },
        )
    finally:
        request_lifecycle_cache.finish(request_id)

    assert response.status_code == 409
    assert service.calls == []


def test_recommendation_route_finishes_request_id_after_success(monkeypatch):
    request_id = "req_route_finish_main"
    monkeypatch.setattr(recommendation_routes, "_service", StubRecommendationService())

    response = TestClient(app).get(
        "/api/recommendations/main",
        params={
            "user_id": "user_001",
            "session_id": "session_001",
            "request_id": request_id,
        },
    )

    assert response.status_code == 200
    request_lifecycle_cache.start(request_id)
    request_lifecycle_cache.finish(request_id)


def test_chatbot_route_rejects_duplicate_inflight_request_id(monkeypatch):
    request_id = "req_route_duplicate_chat"
    service = StubChatbotService()
    monkeypatch.setattr(chatbot_routes, "_service", service)
    request_lifecycle_cache.start(request_id)

    try:
        response = TestClient(app).post(
            "/api/chatbot/respond",
            json={
                "user_id": "user_001",
                "session_id": "session_001",
                "user_input": "추천해줘",
                "request_id": request_id,
            },
        )
    finally:
        request_lifecycle_cache.finish(request_id)

    assert response.status_code == 409
    assert service.calls == []


def test_chatbot_route_finishes_request_id_after_success(monkeypatch):
    request_id = "req_route_finish_chat"
    monkeypatch.setattr(chatbot_routes, "_service", StubChatbotService())

    response = TestClient(app).post(
        "/api/chatbot/respond",
        json={
            "user_id": "user_001",
            "session_id": "session_001",
            "user_input": "추천해줘",
            "request_id": request_id,
        },
    )

    assert response.status_code == 200
    request_lifecycle_cache.start(request_id)
    request_lifecycle_cache.finish(request_id)
