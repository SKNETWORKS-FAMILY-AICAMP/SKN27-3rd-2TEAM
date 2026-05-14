def test_stream_service_chunks_validated_response_after_service_result():
    from app.services.chatbot_stream_service import ChatbotStreamService

    class StubChatbotService:
        def submit_message(self, user_id, session_id, user_input):
            return {
                "status": "success",
                "response_state": {
                    "status": "success",
                    "response_type": "curator_recommendation",
                    "chatbot_response": "안녕하세요 추천입니다.",
                    "display_recommendations": [],
                    "used_content_ids": [],
                },
                "latency_ms": 12.3,
            }

    service = ChatbotStreamService(chatbot_service=StubChatbotService())
    events = list(service.stream_response("user_001", "session_001", "추천해줘"))

    delta_events = [e for e in events if e["event"] == "delta"]
    assert len(delta_events) > 0
    assembled = "".join(e["data"]["text"] for e in delta_events)
    assert assembled == "안녕하세요 추천입니다."

    assert events[-2]["event"] == "final"
    assert events[-1]["event"] == "done"


def test_stream_service_emits_error_event_on_service_failure():
    from app.services.chatbot_stream_service import ChatbotStreamService

    class FailingChatbotService:
        def submit_message(self, user_id, session_id, user_input):
            raise RuntimeError("downstream failure")

    service = ChatbotStreamService(chatbot_service=FailingChatbotService())
    events = list(service.stream_response("user_001", "session_001", "추천해줘"))

    assert events[-1]["event"] == "error"
