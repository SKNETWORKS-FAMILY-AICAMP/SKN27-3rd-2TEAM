from app.ui.styles import theme


def _get_gradient(title: str, index: int) -> str:
    return theme.CARD_GRADIENTS[(hash(title) + index) % len(theme.CARD_GRADIENTS)]


def render_related_recommendation_cards(renderer, recommendations):
    if not recommendations:
        return

    cards_html = ""
    for i, item in enumerate(recommendations):
        gradient = _get_gradient(item.get("title", ""), i)
        title = item.get("title", "")
        artist = item.get("artist", "")
        desc = item.get("display_reason", "")
        desc_html = f'<p class="rimas-small-desc">{desc}</p>' if desc else ""
        cards_html += f"""
        <div class="rimas-small-card">
          <div class="rimas-small-art" style="background:{gradient};">♫</div>
          <div class="rimas-small-info">
            <p class="rimas-small-title">{title}</p>
            <p class="rimas-small-artist">{artist}</p>
            {desc_html}
          </div>
        </div>
        """

    renderer.markdown(
        f"""
        <div style="margin-top:12px;">
          <div style="font-size:13px;font-weight:700;color:{theme.TEXT_MUTED};
                      margin-bottom:10px;letter-spacing:.3px;">관련 추천</div>
          {cards_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
