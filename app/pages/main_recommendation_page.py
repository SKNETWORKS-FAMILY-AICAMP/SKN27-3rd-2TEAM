from app.services.main_recommendation_service import MainRecommendationService
from app.ui.components.character_dj_banner import render_character_dj_banner
from app.ui.components.developer_debug_panel import render_developer_debug_panel
from app.ui.components.discovery_section import render_discovery_section
from app.ui.components.new_release_section import render_new_release_section
from app.ui.components.personalized_guide_section import render_personalized_guide_section
from app.ui.components.personalized_recommendation_section import (
    render_personalized_recommendation_section,
)
from app.ui.components.top_taste_header import render_top_taste_header
from app.ui.styles.css import apply_global_css


def render_main_recommendation_page(
    renderer,
    user_id,
    developer_mode=False,
    service=None,
):
    service = service or MainRecommendationService()
    view_model = service.get_page_view_model(user_id)

    apply_global_css(renderer)
    render_top_taste_header(
        renderer,
        view_model["user_id"],
        view_model["taste_badges"],
        view_model["today_theme"],
    )
    render_character_dj_banner(renderer, view_model["character_message"])
    render_personalized_recommendation_section(
        renderer, view_model["recommendation_groups"]
    )
    render_new_release_section(renderer, view_model["recommendation_groups"])
    render_discovery_section(renderer, view_model["recommendation_groups"])
    render_personalized_guide_section(renderer, view_model["personalized_guide"])

    if renderer.button("Chatbot Page로 이동"):
        renderer.session_state["current_page"] = "chatbot_page"

    render_developer_debug_panel(renderer, view_model["debug"], developer_mode)
    return view_model
