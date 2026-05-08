from app.ui.components.recommendation_card_section import render_recommendation_card_section


def render_new_release_section(renderer, recommendation_groups):
    render_recommendation_card_section(
        renderer,
        "최신 업데이트",
        recommendation_groups.get("new_release", []),
        subtitle="최근 발매되었거나 업데이트된 음악을 확인해보세요.",
        show_date=True,
    )
