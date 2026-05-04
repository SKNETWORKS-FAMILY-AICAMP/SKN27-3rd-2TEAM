from app.services.chatbot_service import ChatbotService


def test_chatbot_service_returns_response_view_model():
    view_model = ChatbotService().submit_message("user_001", "이 노래 왜 추천했어?")

    assert view_model["page_type"] == "chatbot_page"
    assert view_model["status"] == "success"
    assert view_model["chatbot_response"]
    assert view_model["related_recommendations"]
    assert view_model["debug"]["validation_result"]["passed"] is True
