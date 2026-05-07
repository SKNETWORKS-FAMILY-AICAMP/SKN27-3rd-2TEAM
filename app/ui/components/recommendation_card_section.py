def render_recommendation_card_section(renderer, title, cards):
    renderer.subheader(title)
    if not cards:
        renderer.caption("표시할 추천이 없습니다.")
        return

    for card in cards:
        render_recommendation_card(renderer, card)


def render_recommendation_card(renderer, card):
    genres = " · ".join(card.get("genre", []))
    moods = " · ".join(card.get("mood", []))
    tags = " / ".join(value for value in [genres, moods] if value)
    renderer.markdown(
        f"""
        <div class="rimas-card">
          <div class="rimas-card-title">{card.get("title", "")}</div>
          <div class="rimas-card-meta">{card.get("artist", "")}</div>
          <div>{card.get("display_reason", "")}</div>
          <div class="rimas-card-meta">{tags}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
