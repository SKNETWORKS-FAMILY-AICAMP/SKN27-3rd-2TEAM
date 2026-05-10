import pytest

from app.agents.orchestrator_agent import OrchestratorAgent
from app.services.chatbot_service import ChatbotService


class StubOrchestrator:
    def __init__(self, response_state=None, error=None):
        self._response_state = response_state
        self._error = error
        self.called_with = None

    def run_chatbot(self, user_id, session_id, user_input, session_context):
        self.called_with = (user_id, session_id, user_input)
        if self._error:
            raise self._error
        result = dict(self._response_state)
        result["_meta"] = {"kag_state": {}, "rag_state": {}, "latency_ms": 50.0}
        return result


class StubSessionCacheService:
    def __init__(self):
        self.loaded = []
        self.saved = []

    def load_context(self, session_id):
        self.loaded.append(session_id)
        return {"session_id": session_id, "recent_genres": [], "recent_artists": [], "recent_moods": [], "conversation_summary": ""}

    def save_turn_and_update_context(self, **kwargs):
        self.saved.append(kwargs)


def _valid_response_state():
    return {
        "status": "success",
        "response_type": "curator_recommendation",
        "chatbot_response": "큐레이터 응답",
        "display_recommendations": [],
        "used_content_ids": [],
    }


class PassingValidator:
    def __init__(self):
        self.calls = []

    def validate(self, session_context, kag_state, rag_state):
        self.calls.append((session_context, kag_state, rag_state))
        return {"passed": True, "errors": []}


class StubKagAgent:
    def run(self, user_id, user_input, session_context):
        return {
            "status": "success",
            "recommendation_goal": {"primary_goal": "discovery_recommendation"},
            "recommended_content_ids": ["track_001"],
            "recommendation_category": "discovery_candidate",
            "route": "safe_discovery",
            "target_section": "discovery_section",
        }


class StubRagAgent:
    def run(self, kag_state):
        return {
            "status": "success",
            "recommended_content_evidence": [
                {
                    "content_id": "track_001",
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "recommendation_category": "discovery_candidate",
                    "evidence_summary": "차분한 밤 분위기와 연결되는 곡",
                }
            ],
            "recommendation_reason": {"summary": "근거 요약"},
        }


class StubIntentAgent:
    def run(self, user_input, kag_state=None, rag_state=None):
        return {"status": "success", "intent_type": "discovery_recommendation"}


class StubRecommendationAgent:
    def run(self, intent_result, rag_state):
        return {
            "status": "success",
            "selected_recommendations": [
                {
                    "content_id": "track_001",
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "recommendation_category": "discovery_candidate",
                    "display_reason": "차분한 밤 분위기와 연결되는 곡",
                }
            ],
        }


class StubResponseGenerator:
    def run(
        self,
        user_input,
        session_context,
        kag_state,
        rag_state,
        intent_result,
        selected_recommendations,
    ):
        return {
            "status": "success",
            "response_type": "curator_recommendation",
            "chatbot_response": "Midnight Loop를 추천드릴게요.",
            "display_recommendations": [
                {
                    "content_id": "track_001",
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "label": "취향 기반 추천",
                    "display_reason": "차분한 밤 분위기와 연결되는 곡",
                }
            ],
            "used_content_ids": ["track_001"],
        }


def test_chatbot_service_returns_status_and_response_state(monkeypatch):
    stub_cache = StubSessionCacheService()
    monkeypatch.setattr("app.services.chatbot_service.session_cache_service", stub_cache)

    orchestrator = StubOrchestrator(_valid_response_state())
    result = ChatbotService(orchestrator=orchestrator).submit_message(
        "user_001", "session_abc", "추천해줘"
    )

    assert result["status"] == "success"
    assert result["response_state"]["chatbot_response"] == "큐레이터 응답"
    assert "latency_ms" in result
    assert orchestrator.called_with == ("user_001", "session_abc", "추천해줘")


def test_orchestrator_passes_session_context_to_contract_validator():
    validator = PassingValidator()
    session_context = {"session_id": "session_001"}

    orchestrator = OrchestratorAgent(
        kag_agent=StubKagAgent(),
        rag_agent=StubRagAgent(),
        intent_agent=StubIntentAgent(),
        recommendation_agent=StubRecommendationAgent(),
        response_generator=StubResponseGenerator(),
        contract_validator=validator,
    )

    orchestrator.run_chatbot(
        user_id="user_001",
        session_id="session_001",
        user_input="추천해줘",
        session_context=session_context,
    )

    assert validator.calls[0][0] == session_context


def test_chatbot_service_calls_logging_service_on_success(monkeypatch):
    stub_cache = StubSessionCacheService()
    monkeypatch.setattr("app.services.chatbot_service.session_cache_service", stub_cache)

    log_calls = []

    class StubLoggingService:
        def save(self, **kwargs):
            log_calls.append(kwargs)

    orchestrator = StubOrchestrator(_valid_response_state())
    ChatbotService(orchestrator=orchestrator, logging_service=StubLoggingService()).submit_message(
        "user_001", "session_abc", "추천해줘"
    )

    assert len(log_calls) == 1
    assert log_calls[0]["user_id"] == "user_001"


def test_chatbot_service_logging_failure_does_not_block_response(monkeypatch):
    stub_cache = StubSessionCacheService()
    monkeypatch.setattr("app.services.chatbot_service.session_cache_service", stub_cache)

    class FailingLoggingService:
        def save(self, **kwargs):
            raise RuntimeError("db down")

    orchestrator = StubOrchestrator(_valid_response_state())
    result = ChatbotService(
        orchestrator=orchestrator, logging_service=FailingLoggingService()
    ).submit_message("user_001", "session_abc", "추천해줘")

    assert result["status"] == "success"
