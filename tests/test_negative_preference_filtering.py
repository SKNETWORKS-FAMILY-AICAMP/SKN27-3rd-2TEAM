import sys
import types

neo4j_stub = types.ModuleType("neo4j")
neo4j_stub.GraphDatabase = object()
sys.modules.setdefault("neo4j", neo4j_stub)

from app.agents.kag_dispatch_agent import KagDispatchAgent
from app.agents.input_planner_agent import InputPlannerAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.kag.adapters.real_kag_adapter import RealKagAdapter
from app.rag.adapters.rag_real_adapter import RealRagAdapter
from app.rag.services.elasticsearch_retriever import ElasticsearchRagHit


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


def test_kag_dispatch_merges_current_turn_excluded_genres_into_adapter_context():
    adapter = CapturingKagAdapter()
    agent = KagDispatchAgent(kag_adapter=adapter)

    agent.run(
        user_id="user_1",
        user_input="신나는 음악 듣고 싶다 근데 pop음악은 별로",
        session_context={"session_id": "session_1", "disliked_genres": []},
        kag_input_json={
            "query_context": {
                "normalized_query": "신나는 음악 듣고 싶다 근데 pop음악은 별로",
            },
            "constraints": {
                "max_candidates": 7,
                "excluded_artists": [],
                "excluded_tracks": [],
                "excluded_genres": ["pop"],
            },
        },
    )

    assert adapter.limit == 7
    assert adapter.session_context["disliked_genres"] == ["pop"]


def test_input_planner_does_not_treat_negative_genre_as_positive_candidate():
    result = InputPlannerAgent().run(
        user_id="user_1",
        session_id="session_1",
        request_id="request_1",
        user_input="안녕 오늘은 신나는 음악 듣고 싶다 근데 pop음악은 별로",
        session_context={"session_id": "session_1"},
    )

    assert result["intent_state"]["disliked_genres"] == ["pop"]
    assert "pop" not in result["intent_state"]["detected_genres"]
    assert "pop" not in result["kag_input_json"]["query_context"]["genre_candidates"]
    assert result["kag_input_json"]["constraints"]["excluded_genres"] == ["pop"]


def test_real_kag_adapter_does_not_use_excluded_genre_as_positive_condition():
    adapter = RealKagAdapter(conn=object())

    conditions = adapter._extract_conditions(
        "신나는 음악 추천 pop 제외",
        {"disliked_genres": ["pop"]},
    )

    assert conditions["genre"] is None


def test_real_kag_adapter_filters_comma_delimited_disliked_candidate_genre():
    candidates = [
        {
            "content_id": "track_pop",
            "genre": "electronic,pop,electropop",
        }
    ]

    filtered = RealKagAdapter._filter_candidate_tracks(
        candidates,
        [{"type": "genre", "value": "pop"}],
    )

    assert filtered == []


def test_real_rag_adapter_filters_comma_delimited_disliked_evidence_genre():
    hit = ElasticsearchRagHit(
        content_id="track_pop",
        title="Pop Track",
        artist="Artist A",
        album=None,
        genre=["electronic,pop,electropop"],
        mood=["energetic"],
        content="evidence",
        score=1.0,
    )

    evidence = RealRagAdapter._build_evidence(
        [hit],
        {"track_pop"},
        {"excluded_nodes": [{"type": "genre", "value": "pop"}]},
        {},
    )

    assert evidence == []


def test_recommendation_agent_filters_disliked_genres_from_final_selection():
    agent = RecommendationAgent()

    result = agent.run(
        intent_result={
            "intent_type": "personalized_recommendation",
            "disliked_artists": [],
            "disliked_tracks": [],
            "disliked_genres": ["pop"],
        },
        rag_state={
            "recommended_content_evidence": [
                {
                    "content_id": "track_pop",
                    "title": "Pop Track",
                    "artist": "Artist A",
                    "genre": ["pop", "dance"],
                    "mood": ["energetic"],
                    "recommendation_category": "personalized_match",
                },
                {
                    "content_id": "track_rock",
                    "title": "Rock Track",
                    "artist": "Artist B",
                    "genre": ["rock"],
                    "mood": ["energetic"],
                    "recommendation_category": "personalized_match",
                },
            ]
        },
    )

    assert [item["content_id"] for item in result["selected_recommendations"]] == ["track_rock"]


def test_recommendation_agent_filters_comma_delimited_disliked_genres():
    agent = RecommendationAgent()

    result = agent.run(
        intent_result={
            "intent_type": "personalized_recommendation",
            "disliked_artists": [],
            "disliked_tracks": [],
            "disliked_genres": ["pop"],
        },
        rag_state={
            "recommended_content_evidence": [
                {
                    "content_id": "track_pop",
                    "title": "Pop Track",
                    "artist": "Artist A",
                    "genre": ["electronic,pop,electropop"],
                    "mood": ["energetic"],
                    "recommendation_category": "personalized_match",
                }
            ]
        },
    )

    assert result["selected_recommendations"] == []
