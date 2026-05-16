import sys
import types

neo4j_stub = types.ModuleType("neo4j")
neo4j_stub.GraphDatabase = object()
sys.modules.setdefault("neo4j", neo4j_stub)

from app.agents.orchestrator_agent import OrchestratorAgent
from app.validators.contract_validator import ContractValidator
from app.validators.provenance_validator import ProvenanceValidator


INTENT_STATE = {
    "intent_type": "personalized_recommendation",
    "confidence": 0.92,
    "normalized_query": "신나는 음악 듣고 싶다 근데 pop음악은 별로",
    "detected_moods": ["energetic"],
    "detected_genres": [],
    "detected_situations": [],
    "requested_count": None,
    "disliked_artists": ["Sample Artist"],
    "disliked_tracks": ["track_099"],
    "disliked_genres": ["pop"],
    "requires_kag": True,
    "requires_rag": True,
}

KAG_STATE = {
    "status": "success",
    "user_context": {
        "base_preference": {
            "genres": ["dance"],
            "moods": ["energetic"],
        }
    },
    "recommended_content_ids": ["track_001"],
}

RAG_STATE = {
    "status": "success",
    "recommended_content_evidence": [
        {
            "content_id": "track_001",
            "title": "Bright Night",
            "artist": "Catalog Artist",
        }
    ],
    "recommendation_reason": {"summary": "energetic evidence"},
}


class StubInputPlanner:
    def run(self, **kwargs):
        return {
            "intent_state": dict(INTENT_STATE),
            "kag_input_json": {
                "constraints": {
                    "excluded_artists": ["Sample Artist"],
                    "excluded_tracks": ["track_099"],
                    "excluded_genres": ["pop"],
                }
            },
        }


class ValidInputPlanner(StubInputPlanner):
    def run(self, **kwargs):
        return {
            "intent_state": dict(INTENT_STATE),
            "kag_input_json": {
                "request_id": "request_1",
                "user_id": "user_1",
                "session_id": "session_1",
                "intent_type": "personalized_recommendation",
                "query_context": {
                    "normalized_query": "?좊굹???뚯븙 異붿쿇",
                    "mood_candidates": [],
                    "genre_candidates": [],
                    "artist_candidates": [],
                    "situation_candidates": [],
                },
                "constraints": {
                    "allow_discovery": True,
                    "allow_new_release": True,
                    "max_candidates": 5,
                    "excluded_artists": [],
                    "excluded_tracks": [],
                    "excluded_genres": [],
                },
            },
        }


class StubKag:
    def run(self, *args, **kwargs):
        return dict(KAG_STATE)


class StubRag:
    def run(self, *args, **kwargs):
        return dict(RAG_STATE)


class ValidContractKag(StubKag):
    def run(self, *args, **kwargs):
        return {
            "status": "success",
            "recommendation_goal": {"primary_goal": "personalized_recommendation"},
            "recommended_content_ids": ["track_001"],
            "recommendation_category": "personalized_match",
            "route": "personalized",
            "target_section": "personalized_section",
        }


class InvalidRagMissingReason(StubRag):
    def run(self, *args, **kwargs):
        return {
            "status": "success",
            "recommended_content_evidence": [
                {
                    "content_id": "track_001",
                    "title": "Bright Night",
                    "artist": "Catalog Artist",
                }
            ],
        }


class StubIntent:
    def run(self, *args, **kwargs):
        return dict(INTENT_STATE)


class StubRecommendationSuccess:
    def run(self, *args, **kwargs):
        return {
            "selected_recommendations": [
                {
                    "content_id": "track_001",
                    "title": "Bright Night",
                    "artist": "Catalog Artist",
                }
            ]
        }


class StubRecommendationEmpty:
    def run(self, *args, **kwargs):
        return {"selected_recommendations": []}


class RecordingRecommendation(StubRecommendationSuccess):
    def __init__(self, calls):
        self.calls = calls

    def run(self, *args, **kwargs):
        self.calls.append("recommendation")
        return super().run(*args, **kwargs)


class StubResponseGenerator:
    def run(self, *args, **kwargs):
        return {
            "status": "success",
            "response_type": "recommendation",
            "chatbot_response": "추천 결과입니다.",
            "display_recommendations": [
                {
                    "content_id": "track_001",
                    "title": "Bright Night",
                    "artist": "Catalog Artist",
                }
            ],
            "used_content_ids": ["track_001"],
        }


class HallucinatedResponseGenerator:
    def run(self, *args, **kwargs):
        return {
            "status": "success",
            "response_type": "recommendation",
            "chatbot_response": "없는 곡을 추천했습니다.",
            "display_recommendations": [
                {
                    "content_id": "missing_track",
                    "title": "Missing Track",
                    "artist": "Missing Artist",
                }
            ],
            "used_content_ids": ["missing_track"],
        }


class PassingValidator:
    def validate(self, *args, **kwargs):
        return {"passed": True, "errors": []}

    def validate_kag_input(self, *args, **kwargs):
        return {"passed": True, "errors": []}

    def validate_rag_state(self, *args, **kwargs):
        return {"passed": True, "errors": []}


class RecordingInputPlanner(StubInputPlanner):
    def __init__(self, calls):
        self.calls = calls

    def run(self, **kwargs):
        self.calls.append("input_planner")
        return super().run(**kwargs)


class RecordingIntent(StubIntent):
    def __init__(self, calls):
        self.calls = calls

    def run(self, *args, **kwargs):
        self.calls.append("intent")
        return super().run(*args, **kwargs)


class RecordingKag(StubKag):
    def __init__(self, calls):
        self.calls = calls

    def run(self, *args, **kwargs):
        self.calls.append("kag")
        return super().run(*args, **kwargs)


class InvalidKagInputPlanner(StubInputPlanner):
    def run(self, **kwargs):
        return {
            "intent_state": dict(INTENT_STATE),
            "kag_input_json": {},
        }


def _build_orchestrator(recommendation_agent):
    return OrchestratorAgent(
        input_planner=StubInputPlanner(),
        kag_agent=StubKag(),
        rag_agent=StubRag(),
        intent_agent=StubIntent(),
        recommendation_agent=recommendation_agent,
        response_generator=StubResponseGenerator(),
        contract_validator=PassingValidator(),
        response_validator=PassingValidator(),
        provenance_validator=PassingValidator(),
    )


def test_success_meta_includes_disliked_genres_for_session_cache():
    orchestrator = _build_orchestrator(StubRecommendationSuccess())

    result = orchestrator.run_chatbot(
        user_id="user_1",
        session_id="session_1",
        user_input="신나는 음악 듣고 싶다 근데 pop음악은 별로",
        session_context={"session_id": "session_1"},
    )

    assert result["_meta"]["new_dislikes"] == {
        "disliked_artists": ["Sample Artist"],
        "disliked_tracks": ["track_099"],
        "disliked_genres": ["pop"],
    }


def test_chatbot_flow_confirms_intent_before_kag_dispatch():
    calls = []
    orchestrator = OrchestratorAgent(
        input_planner=RecordingInputPlanner(calls),
        kag_agent=RecordingKag(calls),
        rag_agent=StubRag(),
        intent_agent=RecordingIntent(calls),
        recommendation_agent=StubRecommendationSuccess(),
        response_generator=StubResponseGenerator(),
        contract_validator=PassingValidator(),
        response_validator=PassingValidator(),
        provenance_validator=PassingValidator(),
    )

    orchestrator.run_chatbot(
        user_id="user_1",
        session_id="session_1",
        user_input="?좊굹???뚯븙 異붿쿇",
        session_context={"session_id": "session_1"},
    )

    assert calls[:3] == ["input_planner", "intent", "kag"]


def test_main_recommendation_flow_confirms_intent_before_kag_dispatch():
    calls = []
    orchestrator = OrchestratorAgent(
        input_planner=RecordingInputPlanner(calls),
        kag_agent=RecordingKag(calls),
        rag_agent=StubRag(),
        intent_agent=RecordingIntent(calls),
        recommendation_agent=StubRecommendationSuccess(),
        response_generator=StubResponseGenerator(),
        contract_validator=PassingValidator(),
        response_validator=PassingValidator(),
        provenance_validator=PassingValidator(),
    )

    orchestrator.run_recommendation(
        user_id="user_1",
        session_id="session_1",
        session_context={"session_id": "session_1"},
    )

    assert calls[:3] == ["input_planner", "intent", "kag"]


def test_chatbot_flow_blocks_kag_when_kag_input_contract_is_invalid():
    calls = []
    orchestrator = OrchestratorAgent(
        input_planner=InvalidKagInputPlanner(),
        kag_agent=RecordingKag(calls),
        rag_agent=StubRag(),
        intent_agent=StubIntent(),
        recommendation_agent=StubRecommendationSuccess(),
        response_generator=StubResponseGenerator(),
        contract_validator=ContractValidator(),
        response_validator=PassingValidator(),
        provenance_validator=PassingValidator(),
    )

    result = orchestrator.run_chatbot(
        user_id="user_1",
        session_id="session_1",
        user_input="?좊굹???뚯븙 異붿쿇",
        session_context={"session_id": "session_1"},
    )

    assert calls == []
    assert result["_meta"]["error_type"] == "CONTRACT_VALIDATION_FAILED"


def test_chatbot_flow_blocks_recommendation_when_rag_state_contract_is_invalid():
    calls = []
    orchestrator = OrchestratorAgent(
        input_planner=ValidInputPlanner(),
        kag_agent=ValidContractKag(),
        rag_agent=InvalidRagMissingReason(),
        intent_agent=StubIntent(),
        recommendation_agent=RecordingRecommendation(calls),
        response_generator=StubResponseGenerator(),
        contract_validator=ContractValidator(),
        response_validator=PassingValidator(),
        provenance_validator=PassingValidator(),
    )

    result = orchestrator.run_chatbot(
        user_id="user_1",
        session_id="session_1",
        user_input="?좊굹???뚯븙 異붿쿇",
        session_context={"session_id": "session_1"},
    )

    assert calls == []
    assert result["_meta"]["error_type"] == "CONTRACT_VALIDATION_FAILED"


def test_chatbot_flow_falls_back_when_response_uses_content_id_outside_rag_state():
    orchestrator = OrchestratorAgent(
        input_planner=ValidInputPlanner(),
        kag_agent=ValidContractKag(),
        rag_agent=StubRag(),
        intent_agent=StubIntent(),
        recommendation_agent=StubRecommendationSuccess(),
        response_generator=HallucinatedResponseGenerator(),
        contract_validator=ContractValidator(),
        response_validator=PassingValidator(),
        provenance_validator=ProvenanceValidator(),
    )

    result = orchestrator.run_chatbot(
        user_id="user_1",
        session_id="session_1",
        user_input="?좊굹???뚯븙 異붿쿇",
        session_context={"session_id": "session_1"},
    )

    assert result["_meta"]["error_type"] == "RESPONSE_VALIDATION_FAILED"


def test_fallback_meta_keeps_disliked_genres_for_session_cache():
    orchestrator = _build_orchestrator(StubRecommendationEmpty())

    result = orchestrator.run_chatbot(
        user_id="user_1",
        session_id="session_1",
        user_input="신나는 음악 듣고 싶다 근데 pop음악은 별로",
        session_context={"session_id": "session_1"},
    )

    assert result["_meta"]["error_type"] == "NO_RECOMMENDATIONS"
    assert result["_meta"]["new_dislikes"] == {
        "disliked_artists": ["Sample Artist"],
        "disliked_tracks": ["track_099"],
        "disliked_genres": ["pop"],
    }
