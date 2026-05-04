from app.services.chatbot_service import ChatbotService


class StubLlmFlowService:
    def __init__(self, response_state=None, error=None):
        self.response_state = response_state
        self.error = error
        self.called = False

    def run(self, user_input, ml_output, kag_state, rag_state):
        self.called = True
        if self.error:
            raise self.error
        return self.response_state


def _valid_response_state():
    return {
        "status": "success",
        "response_type": "curator_recommendation",
        "chatbot_response": "LLM이 생성한 큐레이터 응답",
        "display_recommendations": [
            {
                "content_id": "track_002",
                "title": "Soft Orbit",
                "artist": "Luna Field",
                "label": "새로운 취향 시도",
                "display_reason": "calm/night 분위기를 유지하면서 확장 가능한 곡입니다.",
            }
        ],
        "used_content_ids": ["track_002"],
        "provenance": {
            "used_ml_fields": [],
            "used_kag_fields": [],
            "used_rag_content_ids": ["track_002"],
            "used_rag_fields": [],
        },
        "validation": {
            "response_validation_passed": False,
            "provenance_validation_passed": False,
        },
    }


def test_chatbot_service_returns_response_view_model():
    llm_flow_service = StubLlmFlowService(_valid_response_state())

    view_model = ChatbotService(llm_flow_service=llm_flow_service).submit_message(
        "user_001",
        "이 노래 왜 추천했어?",
    )

    assert view_model["page_type"] == "chatbot_page"
    assert view_model["status"] == "success"
    assert view_model["chatbot_response"] == "LLM이 생성한 큐레이터 응답"
    assert view_model["related_recommendations"]
    assert view_model["debug"]["validation_result"]["passed"] is True
    assert llm_flow_service.called is True


def test_chatbot_service_returns_fallback_when_llm_flow_fails():
    llm_flow_service = StubLlmFlowService(error=RuntimeError("llm failed"))

    view_model = ChatbotService(llm_flow_service=llm_flow_service).submit_message(
        "user_001",
        "추천해줘",
    )

    assert view_model["status"] == "error"
    assert view_model["related_recommendations"] == []
    assert view_model["debug"]["validation_result"]["passed"] is False
    assert "LLM_CALL_FAILED" in view_model["debug"]["validation_result"]["errors"]
