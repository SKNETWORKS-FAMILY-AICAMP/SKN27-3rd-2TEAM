from app.ui.components.recommendation_card_section import render_recommendation_card_section


def render_personalized_recommendation_section(renderer, recommendation_groups):
    render_recommendation_card_section(
        renderer,
        "맞춤 추천",
        recommendation_groups.get("personalized_match", []),
        subtitle="당신의 취향과 최근 활동을 기반으로 추천해요.",
    )
