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
        result["_meta"] = {
            "kag_state": {"status": "success", "kind": "kag"},
            "rag_state": {"status": "success", "kind": "rag"},
            "latency_ms": 50.0,
        }
        return result


class StubSessionCacheService:
    def __init__(self):
        self.loaded = []
        self.saved = []

    def load_context(self, session_id, user_id=None):
        self.loaded.append(session_id)
        return {"session_id": session_id, "recent_genres": [], "recent_artists": [], "recent_moods": [], "selected_tracks": [], "conversation_summary": ""}

    def save_turn_and_update_context(self, **kwargs):
        self.saved.append(kwargs)


class StubLatestStateCache:
    def __init__(self):
        self.saved = []

    def save_latest_states(self, **kwargs):
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


class StubInputPlanner:
    def __init__(self, calls):
        self.calls = calls

    def run(self, user_id, session_id, request_id, user_input, session_context):
        self.calls.append("input_planner")
        return {
            "intent_state": {
                "intent_type": "discovery_recommendation",
                "confidence": 0.82,
                "normalized_query": user_input,
                "detected_moods": ["night"],
                "detected_genres": ["indie"],
                "detected_situations": [],
                "requires_kag": True,
                "requires_rag": True,
            },
            "kag_input_json": {
                "request_id": request_id,
                "user_id": user_id,
                "session_id": session_id,
                "intent_type": "discovery_recommendation",
                "query_context": {
                    "normalized_query": user_input,
                    "mood_candidates": ["night"],
                    "genre_candidates": ["indie"],
                    "situation_candidates": [],
                },
                "constraints": {
                    "allow_discovery": True,
                    "allow_new_release": True,
                    "max_candidates": 10,
                },
            },
        }


class StubKagAgent:
    def __init__(self, calls=None):
        self.calls = calls
        self.received_kag_input_json = None

    def run(self, user_id, user_input, session_context, kag_input_json=None):
        if self.calls is not None:
            self.calls.append("kag")
        self.received_kag_input_json = kag_input_json
        return {
            "status": "success",
            "recommendation_goal": {"primary_goal": "discovery_recommendation"},
            "recommended_content_ids": ["track_001"],
            "recommendation_category": "discovery_candidate",
            "route": "safe_discovery",
            "target_section": "discovery_section",
        }


class StubRagAgent:
    def __init__(self):
        self.received_rag_input_json = None
        self.received_kag_input_json = None

    def run(
        self,
        kag_state,
        user_id=None,
        session_id=None,
        request_id=None,
        intent_state=None,
        kag_input_json=None,
    ):
        self.received_kag_input_json = kag_input_json
        self.received_rag_input_json = {
            "user_id": user_id,
            "session_id": session_id,
            "request_id": request_id,
            "intent_type": (intent_state or {}).get("intent_type"),
            "query_text": (kag_input_json or {}).get("query_context", {}).get("normalized_query"),
        }
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
    def __init__(self):
        self.received_intent_state = None

    def run(self, user_input, kag_state=None, rag_state=None, intent_state=None):
        self.received_intent_state = intent_state
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
    latest_cache = StubLatestStateCache()
    monkeypatch.setattr("app.services.chatbot_service.session_cache_service", stub_cache)
    monkeypatch.setattr("app.services.chatbot_service.latest_state_cache", latest_cache)

    orchestrator = StubOrchestrator(_valid_response_state())
    result = ChatbotService(orchestrator=orchestrator).submit_message(
        "user_001", "session_abc", "추천해줘"
    )

    assert result["status"] == "success"
    assert result["response_state"]["chatbot_response"] == "큐레이터 응답"
    assert "latency_ms" in result
    assert latest_cache.saved[0]["session_id"] == "session_abc"
    assert latest_cache.saved[0]["kag_state"] == {"status": "success", "kind": "kag"}
    assert latest_cache.saved[0]["rag_state"] == {"status": "success", "kind": "rag"}
    assert latest_cache.saved[0]["response_state"] == result["response_state"]
    assert latest_cache.saved[0]["recommendation_metadata"] == {
        "source_type": "chatbot",
        "user_id": "user_001",
        "latency_ms": 50.0,
    }
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


def test_orchestrator_runs_input_planner_before_kag_and_passes_kag_input_json():
    calls = []
    kag_agent = StubKagAgent(calls)
    rag_agent = StubRagAgent()
    intent_agent = StubIntentAgent()

    orchestrator = OrchestratorAgent(
        input_planner=StubInputPlanner(calls),
        kag_agent=kag_agent,
        rag_agent=rag_agent,
        intent_agent=intent_agent,
        recommendation_agent=StubRecommendationAgent(),
        response_generator=StubResponseGenerator(),
        contract_validator=PassingValidator(),
    )

    orchestrator.run_chatbot(
        user_id="user_001",
        session_id="session_001",
        user_input="새로운 밤 인디 음악 추천해줘",
        session_context={"session_id": "session_001"},
    )

    assert calls[:2] == ["input_planner", "kag"]
    assert kag_agent.received_kag_input_json["intent_type"] == "discovery_recommendation"
    assert kag_agent.received_kag_input_json["query_context"]["genre_candidates"] == ["indie"]
    assert rag_agent.received_kag_input_json["intent_type"] == "discovery_recommendation"
    assert rag_agent.received_rag_input_json["query_text"] == "새로운 밤 인디 음악 추천해줘"
    assert intent_agent.received_intent_state["intent_type"] == "discovery_recommendation"


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


def test_chatbot_service_saves_new_negative_preferences_to_context(monkeypatch):
    saved = {}
    persisted = {}

    class NegativeOrchestrator:
        def run_chatbot(self, user_id, session_id, user_input, session_context):
            return {
                "status": "success",
                "response_type": "curator_recommendation",
                "chatbot_response": "반영했습니다.",
                "display_recommendations": [],
                "used_content_ids": [],
                "_meta": {
                    "kag_state": {},
                    "rag_state": {},
                    "latency_ms": 1.0,
                    "new_dislikes": {"disliked_artists": ["Billie Eilish"], "disliked_tracks": [], "disliked_genres": ["pop"]},
                },
            }

    def fake_save_turn_and_update_context(**kwargs):
        saved.update(kwargs)
        return {}

    class StubNegativePreferenceService:
        def merge_and_save(self, **kwargs):
            persisted.update(kwargs)
            return {}

    monkeypatch.setattr(
        "app.services.chatbot_service.session_cache_service.save_turn_and_update_context",
        fake_save_turn_and_update_context,
    )

    ChatbotService(
        orchestrator=NegativeOrchestrator(),
        negative_preference_service=StubNegativePreferenceService(),
    ).submit_message(
        "user_001",
        "session_001",
        "Billie Eilish 싫어",
    )

    assert saved["new_dislikes"]["disliked_artists"] == ["Billie Eilish"]
    assert persisted["new_artists"] == ["Billie Eilish"]
    assert persisted["new_genres"] == ["pop"]
