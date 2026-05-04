from app.services.chatbot_service import ChatbotService
from app.ui.components.chat_area import render_chat_history, render_curator_response
from app.ui.components.chatbot_header import render_chatbot_header
from app.ui.components.developer_debug_panel import render_developer_debug_panel
from app.ui.components.related_recommendation_cards import (
    render_related_recommendation_cards,
)
from app.ui.styles.css import apply_global_css


def render_chatbot_page(renderer, user_id, developer_mode=False, service=None):
    service = service or ChatbotService()
    renderer.session_state.setdefault("chat_history", [])

    apply_global_css(renderer)
    render_chatbot_header(renderer, user_id)
    render_chat_history(renderer, renderer.session_state["chat_history"])

    user_input = renderer.chat_input("음악이나 추천 이유를 물어보세요")
    view_model = None
    if user_input:
        view_model = service.submit_message(user_id, user_input)
        renderer.session_state["chat_history"].append(
            {"role": "user", "content": user_input}
        )
        renderer.session_state["chat_history"].append(
            {"role": "assistant", "content": view_model["chatbot_response"]}
        )
        render_curator_response(renderer, view_model["chatbot_response"])
        render_related_recommendation_cards(
            renderer, view_model["related_recommendations"]
        )
        render_developer_debug_panel(renderer, view_model["debug"], developer_mode)

    if renderer.button("Main Recommendation Page로 이동"):
        renderer.session_state["current_page"] = "main_recommendation_page"

    return view_model
