from app.ui.styles import theme


def _get_gradient(title: str, index: int) -> str:
    return theme.CARD_GRADIENTS[(hash(title) + index) % len(theme.CARD_GRADIENTS)]


def render_recommendation_card_section(
    renderer, title: str, cards: list, subtitle: str = "", show_date: bool = False
):
    if not cards:
        subtitle_html = f'<div class="rimas-section-subtitle">{subtitle}</div>' if subtitle else ""
        renderer.markdown(
            f"""
            <div class="rimas-section">
              <div class="rimas-section-title">{title}</div>
              {subtitle_html}
              <div style="color:{theme.TEXT_MUTED};font-size:13px;padding:8px 0;">
                표시할 추천이 없습니다.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    cards_html = ""
    for i, card in enumerate(cards):
        gradient = _get_gradient(card.get("title", ""), i)
        new_badge = f'<div class="rimas-new-badge">NEW</div>' if show_date else ""

        genres = card.get("genre", [])
        moods = card.get("mood", [])
        tags = (genres + moods)[:2]
        if show_date:
            bottom_html = f'<span class="rimas-tag" style="background:{theme.ACCENT};color:white;">NEW</span>'
        elif tags:
            tags_html = "".join(f'<span class="rimas-tag">#{t}</span>' for t in tags)
            bottom_html = f'<div style="margin-top:2px;">{tags_html}</div>'
        else:
            bottom_html = ""

        reason = card.get("display_reason", "")
        reason_html = f'<div class="rimas-card-reason">{reason}</div>' if reason else ""

        cards_html += f"""
        <div class="rimas-music-card">
          <div class="rimas-album-art" style="background:{gradient};">
            <span class="rimas-album-note">♫</span>
            {new_badge}
          </div>
          <div class="rimas-card-info">
            <div class="rimas-card-title">{card.get("title", "")}</div>
            <div class="rimas-card-artist">{card.get("artist", "")}</div>
            {bottom_html}
            {reason_html}
          </div>
        </div>
        """

    subtitle_html = f'<div class="rimas-section-subtitle">{subtitle}</div>' if subtitle else ""
    renderer.markdown(
        f"""
        <div class="rimas-section">
          <div class="rimas-section-title">{title}</div>
          {subtitle_html}
          <div class="rimas-cards-row">
            {cards_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
