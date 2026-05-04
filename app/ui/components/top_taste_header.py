def render_top_taste_header(renderer, user_id, taste_badges, today_theme):
    renderer.title("RIMAS")
    renderer.caption(f"User: {user_id}")
    if today_theme:
        renderer.markdown(f"**오늘의 추천 방향**  \n{today_theme}")

    badge_html = "".join(
        f'<span class="rimas-badge">{badge}</span>' for badge in taste_badges
    )
    renderer.markdown(badge_html, unsafe_allow_html=True)
