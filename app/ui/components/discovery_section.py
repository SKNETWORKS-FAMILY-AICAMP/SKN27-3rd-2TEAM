from app.ui.components.recommendation_card_section import render_recommendation_card_section


def render_discovery_section(renderer, recommendation_groups):
    render_recommendation_card_section(
        renderer,
        "새로운 취향 탐색",
        recommendation_groups.get("discovery_candidate", []),
        subtitle="당신의 취향을 확장해줄 새로운 음악을 발견해보세요.",
    )
