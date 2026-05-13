import pytest

from app.kag.adapters.real_kag_adapter import RealKagAdapter
from app.kag.constant import KagQueryTemplateConstants


class StubQueryTools:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, query_key, params, conn):
        self.calls.append((query_key, params, conn))
        return self.rows


class StubConnection:
    pass


def test_real_kag_adapter_maps_neo4j_rows_to_kag_state():
    rows = [
        {
            "track_id": "track_001",
            "track_name": "Night Drive",
            "track_artist": "Nova Lane",
            "genre": "indie",
            "subgenre": "dream pop",
            "popularity": 82,
            "recommendation_score": 91,
            "matched_mood": "night",
        },
        {
            "track_id": "track_001",
            "track_name": "Night Drive",
            "track_artist": "Nova Lane",
        },
        {
            "track_id": "track_002",
            "track_name": "Soft Orbit",
            "track_artist": "Luna Field",
            "matched_count": 2,
        },
    ]
    query_tools = StubQueryTools(rows)
    conn = StubConnection()

    state = RealKagAdapter(conn=conn, query_tools=query_tools).build_state(
        user_id="user_001",
        user_input="인디 밤 감성 추천",
        session_context={"recent_genres": ["indie"], "recent_moods": ["night"]},
    )

    assert state["status"] == "success"
    assert state["recommended_content_ids"] == ["track_001", "track_002"]
    assert state["recommendation_goal"]["primary_goal"] == "personalized_recommendation"
    assert state["recommendation_category"] == "personalized_match"
    assert state["route"] == "personalized"
    assert state["target_section"] == "personalized_section"
    assert state["candidate_tracks"][0]["content_id"] == "track_001"
    assert state["candidate_tracks"][0]["title"] == "Night Drive"
    assert state["candidate_tracks"][0]["artist"] == "Nova Lane"
    assert state["candidate_tracks"][0]["matched_mood"] == "night"
    assert state["matched_nodes"] == [
        {"type": "genre", "value": "indie"},
        {"type": "mood", "value": "night"},
    ]
    assert state["diversity_metadata"]["source"] == "neo4j"
    assert query_tools.calls[0][0] == KagQueryTemplateConstants.Q_REC_008
    assert query_tools.calls[0][1]["limit"] == 10


def test_real_kag_adapter_returns_degraded_success_when_neo4j_has_no_rows():
    query_tools = StubQueryTools([])

    state = RealKagAdapter(conn=StubConnection(), query_tools=query_tools).build_state(
        user_id="user_001",
        user_input="추천해줘",
        session_context={},
    )

    assert state["status"] == "success"
    assert state["recommended_content_ids"] == []
    assert state["candidate_tracks"] == []
    assert state["traversal_reason"] == "neo4j traversal returned no candidates"
    assert state["diversity_metadata"] == {"source": "neo4j", "degraded": True}
    assert query_tools.calls[0][0] == KagQueryTemplateConstants.Q_REC_006


def test_real_kag_adapter_caps_limit_to_fifty():
    query_tools = StubQueryTools([])

    RealKagAdapter(conn=StubConnection(), query_tools=query_tools).build_state(
        user_id="user_001",
        user_input="추천해줘",
        session_context={},
        limit=200,
    )

    assert query_tools.calls[0][1]["limit"] == 50


def test_real_kag_adapter_requires_user_id():
    with pytest.raises(ValueError, match="user_id is required"):
        RealKagAdapter(conn=StubConnection(), query_tools=StubQueryTools([])).build_state(
            user_id="",
            user_input="추천해줘",
            session_context={},
        )
