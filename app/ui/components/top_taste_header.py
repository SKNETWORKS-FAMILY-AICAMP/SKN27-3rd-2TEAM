from app.ui.styles import theme


def render_top_taste_header(renderer, user_id, taste_badges, today_theme):
    badge_html = "".join(
        f'<span class="rimas-badge">{badge}</span>' for badge in taste_badges
    )
    theme_html = (
        f'<div style="font-size:12px;color:{theme.TEXT_MUTED};margin-bottom:8px;">'
        f'🎯 {today_theme}</div>'
        if today_theme else ""
    )
    renderer.markdown(
        f"""
        <div class="rimas-top-header">
          <h1>안녕하세요, {user_id}님 👋</h1>
          <p>오늘도 당신만을 위한 음악을 준비했어요.</p>
          {theme_html}
          <div>{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
