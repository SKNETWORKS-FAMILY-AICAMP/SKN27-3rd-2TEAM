from app.ui.components.recommendation_card_section import render_recommendation_card_section


def render_related_recommendation_cards(renderer, recommendations):
    cards = [
        {
            "title": item.get("title", ""),
            "artist": item.get("artist", ""),
            "display_reason": item.get("display_reason", ""),
            "genre": [],
            "mood": [],
        }
        for item in recommendations
    ]
    render_recommendation_card_section(renderer, "관련 추천", cards)
