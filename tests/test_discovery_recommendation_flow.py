import sys
import types

neo4j_stub = types.ModuleType("neo4j")
neo4j_stub.GraphDatabase = object()
sys.modules.setdefault("neo4j", neo4j_stub)

from app.agents.input_planner_agent import InputPlannerAgent
from app.agents.intent_agent import IntentAgent
from app.kag.adapters.real_kag_adapter import RealKagAdapter
from app.kag.constant import KagQueryTemplateConstants
from app.services.chatbot_service import ChatbotService


DISCOVERY_QUERY = "안녕 오늘은 뭔가 완전 색다른 노래를 찾고 싶은데 추천해봐"


def test_input_planner_classifies_colorful_new_request_as_discovery():
    result = InputPlannerAgent().run(
        user_id="user_1",
        session_id="session_1",
        request_id="request_1",
        user_input=DISCOVERY_QUERY,
        session_context={"session_id": "session_1", "selected_tracks": ["main_track_1"]},
    )

    assert result["intent_state"]["intent_type"] == "discovery_recommendation"
    assert result["kag_input_json"]["intent_type"] == "discovery_recommendation"
    assert result["kag_input_json"]["constraints"]["excluded_tracks"] == ["main_track_1"]


def test_input_planner_classifies_different_from_my_taste_as_discovery():
    result = InputPlannerAgent().run(
        user_id="user_1",
        session_id="session_1",
        request_id="request_1",
        user_input="내 취향과는 완전 다른 노래 없어? 5곡만 추천해봐",
        session_context={"session_id": "session_1", "selected_tracks": ["main_track_1"]},
    )

    assert result["intent_state"]["intent_type"] == "discovery_recommendation"
    assert result["intent_state"]["requested_count"] == 5
    assert result["kag_input_json"]["constraints"]["max_candidates"] == 5
    assert result["kag_input_json"]["constraints"]["excluded_tracks"] == ["main_track_1"]


def test_intent_agent_fallback_classifier_handles_colorful_new_request():
    result = IntentAgent().run(user_input=DISCOVERY_QUERY, intent_state={})

    assert result["intent_type"] == "discovery_recommendation"


def test_real_kag_adapter_routes_discovery_to_diversity_query_and_section():
    adapter = RealKagAdapter(conn=object(), query_tools=CapturingQueryTools())

    state = adapter.build_state(
        user_id="user_1",
        user_input=DISCOVERY_QUERY,
        session_context={"disliked_tracks": ["main_track_1"]},
        limit=10,
    )

    assert CapturingQueryTools.query_key == KagQueryTemplateConstants.Q_REC_007
    assert state["recommendation_goal"]["primary_goal"] == "new_taste_discovery"
    assert state["recommendation_category"] == "discovery_candidate"
    assert state["target_section"] == "discovery_section"
    assert state["recommended_content_ids"] == ["fresh_track_1"]


def test_chatbot_service_adds_latest_displayed_recommendations_to_selected_tracks(monkeypatch):
    orchestrator = CapturingOrchestrator()
    monkeypatch.setattr(
        "app.services.chatbot_service.redis_client.is_healthy",
        lambda: True,
    )
    monkeypatch.setattr(
        "app.services.chatbot_service.session_cache_service.load_context",
        lambda session_id, user_id=None: {"session_id": session_id, "selected_tracks": ["selected_track_1"]},
    )
    monkeypatch.setattr(
        "app.services.chatbot_service.latest_state_cache.get_latest_response_state",
        lambda session_id: {
            "personalized": [{"content_id": "main_track_1"}],
            "new_release": [{"content_id": "main_track_2"}],
            "discovery": [],
        },
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.chatbot_service.session_cache_service.save_turn_and_update_context",
        lambda **kwargs: {},
    )
    monkeypatch.setattr(
        "app.services.chatbot_service.latest_state_cache.save_latest_states",
        lambda **kwargs: None,
    )

    ChatbotService(orchestrator=orchestrator).submit_message(
        user_id="user_1",
        session_id="session_1",
        user_input=DISCOVERY_QUERY,
    )

    assert orchestrator.session_context["selected_tracks"] == [
        "main_track_1",
        "main_track_2",
        "selected_track_1",
    ]


class CapturingQueryTools:
    query_key = None

    @classmethod
    def execute(cls, query_key, params, conn):
        cls.query_key = query_key
        return [
            {
                "track_id": "main_track_1",
                "track_name": "Main Page Track",
                "track_artist": "Artist A",
                "genre": "pop",
                "popularity": 95,
                "recommendation_score": 95,
            },
            {
                "track_id": "fresh_track_1",
                "track_name": "Fresh Track",
                "track_artist": "Artist B",
                "genre": "rnb",
                "popularity": 80,
                "recommendation_score": 80,
            },
        ]


class CapturingOrchestrator:
    def __init__(self):
        self.session_context = None

    def run_chatbot(self, *, user_id, session_id, user_input, session_context):
        self.session_context = session_context
        return {
            "status": "success",
            "response_type": "curator_recommendation",
            "chatbot_response": "ok",
            "display_recommendations": [],
            "used_content_ids": [],
            "_meta": {
                "kag_state": {},
                "rag_state": {},
                "latency_ms": 0,
                "new_dislikes": {
                    "disliked_artists": [],
                    "disliked_tracks": [],
                    "disliked_genres": [],
                },
            },
        }
