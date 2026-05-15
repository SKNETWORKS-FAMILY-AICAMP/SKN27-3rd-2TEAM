import sys
import types

neo4j_stub = types.ModuleType("neo4j")
neo4j_stub.GraphDatabase = object()
sys.modules.setdefault("neo4j", neo4j_stub)

from app.agents.input_planner_agent import InputPlannerAgent
from app.agents.kag_dispatch_agent import KagDispatchAgent
from app.kag.adapters.real_kag_adapter import RealKagAdapter
from app.kag.constant import KagQueryTemplateConstants


def test_input_planner_extracts_korean_artist_alias_for_artist_request():
    result = InputPlannerAgent().run(
        user_id="user_1",
        session_id="session_1",
        request_id="request_1",
        user_input="아리아나 그란데 노래 추천해줘",
        session_context={"session_id": "session_1"},
    )

    assert result["intent_state"]["detected_artists"] == ["Ariana Grande"]
    assert result["kag_input_json"]["query_context"]["artist_candidates"] == ["Ariana Grande"]


def test_kag_dispatch_passes_artist_candidates_to_adapter_context():
    adapter = CapturingKagAdapter()
    agent = KagDispatchAgent(kag_adapter=adapter)

    agent.run(
        user_id="user_1",
        user_input="아리아나 그란데 노래 추천해줘",
        session_context={"session_id": "session_1"},
        kag_input_json={
            "query_context": {
                "normalized_query": "아리아나 그란데 노래 추천해줘",
                "artist_candidates": ["Ariana Grande"],
            },
            "constraints": {
                "max_candidates": 5,
                "excluded_artists": [],
                "excluded_tracks": [],
                "excluded_genres": [],
            },
        },
    )

    assert adapter.session_context["artist_candidates"] == ["Ariana Grande"]
    assert adapter.limit == 5


def test_real_kag_adapter_uses_artist_condition_for_artist_request():
    query_tools = CapturingQueryTools()
    adapter = RealKagAdapter(conn=object(), query_tools=query_tools)

    state = adapter.build_state(
        user_id="user_1",
        user_input="아리아나 그란데 노래 추천해줘",
        session_context={"artist_candidates": ["Ariana Grande"]},
        limit=5,
    )

    assert query_tools.query_key == KagQueryTemplateConstants.Q_REC_006
    assert query_tools.params["artist"] == "Ariana Grande"
    assert state["recommended_content_ids"] == ["ariana_track_1"]
    assert state["candidate_tracks"][0]["artist"] == "Ariana Grande"


class CapturingKagAdapter:
    def __init__(self):
        self.session_context = None
        self.limit = None

    def build_state(self, user_id: str, user_input: str, session_context: dict, limit: int = 10):
        self.session_context = session_context
        self.limit = limit
        return {
            "status": "success",
            "recommendation_goal": {"primary_goal": "personalized_recommendation"},
            "recommended_content_ids": [],
        }


class CapturingQueryTools:
    def __init__(self):
        self.query_key = None
        self.params = None

    def execute(self, query_key, params, conn):
        self.query_key = query_key
        self.params = params
        return [
            {
                "track_id": "ariana_track_1",
                "track_name": "Focus",
                "track_artist": "Ariana Grande",
                "genre": "pop",
                "popularity": 90,
                "recommendation_score": 90,
            }
        ]
