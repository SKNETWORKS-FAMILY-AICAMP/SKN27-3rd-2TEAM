import pytest

from app.kag.adapters.mock_kag_adapter import MockKagAdapter
from app.rag.adapters.mock_rag_adapter import MockRagAdapter


@pytest.fixture
def sample_session_context():
    return {
        "session_id": "session_001",
        "recent_genres": ["rnb", "indie"],
        "recent_artists": [],
        "recent_moods": ["calm", "night"],
        "conversation_summary": "",
    }


@pytest.fixture
def sample_payloads(sample_session_context):
    kag_state = MockKagAdapter().build_state(
        "user_001",
        "내 취향이랑 다른 것도 추천해줘",
        sample_session_context,
    )
    rag_state = MockRagAdapter().build_state(kag_state)
    return {
        "session_context": sample_session_context,
        "kag_state": kag_state,
        "rag_state": rag_state,
    }
