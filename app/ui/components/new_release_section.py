from app.ui.components.recommendation_card_section import render_recommendation_card_section


def render_new_release_section(renderer, recommendation_groups):
    render_recommendation_card_section(
        renderer,
        "최신 업데이트",
        recommendation_groups.get("new_release", []),
    )
