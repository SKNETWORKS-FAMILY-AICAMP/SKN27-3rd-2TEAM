from app.services.llm_flow_service import LlmFlowService


class CapturingResponseGenerator:
    def __init__(self):
        self.received = None

    def run(
        self,
        user_input,
        ml_output,
        kag_state,
        rag_state,
        curation_plan,
        selected_recommendations,
    ):
        self.received = {
            "user_input": user_input,
            "ml_output": ml_output,
            "kag_state": kag_state,
            "rag_state": rag_state,
            "curation_plan": curation_plan,
            "selected_recommendations": selected_recommendations,
        }
        selected = selected_recommendations["selected_recommendations"][0]
        return {
            "status": "success",
            "response_type": "curator_recommendation",
            "chatbot_response": "LLM response",
            "display_recommendations": [
                {
                    "content_id": selected["content_id"],
                    "title": selected["title"],
                    "artist": selected["artist"],
                    "label": "새로운 취향 시도",
                    "display_reason": selected["display_reason"],
                }
            ],
            "used_content_ids": [selected["content_id"]],
            "provenance": {
                "used_ml_fields": [],
                "used_kag_fields": [],
                "used_rag_content_ids": [selected["content_id"]],
                "used_rag_fields": [],
            },
            "validation": {
                "response_validation_passed": False,
                "provenance_validation_passed": False,
            },
        }


def test_llm_flow_service_runs_agents_in_documented_order(sample_payloads):
    response_generator = CapturingResponseGenerator()
    service = LlmFlowService(response_generator=response_generator)

    response_state = service.run(
        user_input="내 취향이랑 다른 것도 추천해줘",
        ml_output=sample_payloads["ml_output"],
        kag_state=sample_payloads["kag_state"],
        rag_state=sample_payloads["rag_state"],
    )

    assert response_state["status"] == "success"
    assert response_state["used_content_ids"] == ["track_002"]
    assert response_generator.received["curation_plan"]["curation_mode"] == "recommend_discovery"
    assert response_generator.received["selected_recommendations"]["selected_recommendations"][0]["content_id"] == "track_002"


def test_llm_flow_service_returns_empty_recommendations_when_rag_has_no_evidence(sample_payloads):
    response_generator = CapturingResponseGenerator()
    rag_state = dict(sample_payloads["rag_state"])
    rag_state["recommended_content_evidence"] = []
    service = LlmFlowService(response_generator=response_generator)

    response_state = service.run(
        user_input="추천해줘",
        ml_output=sample_payloads["ml_output"],
        kag_state=sample_payloads["kag_state"],
        rag_state=rag_state,
    )

    assert response_state["status"] == "error"
    assert response_state["response_type"] == "fallback"
