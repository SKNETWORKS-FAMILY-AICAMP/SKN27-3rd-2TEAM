from app.ui.components.recommendation_card_section import render_recommendation_card_section


def render_personalized_recommendation_section(renderer, recommendation_groups):
    render_recommendation_card_section(
        renderer,
        "개인화 추천",
        recommendation_groups.get("personalized_match", []),
    )
