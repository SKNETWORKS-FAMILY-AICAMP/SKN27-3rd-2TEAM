def render_music_taste_section(renderer, taste_badges):
    badge_html = "".join(
        f'<span class="rimas-badge">{badge}</span>' for badge in taste_badges
    )
    renderer.markdown(badge_html, unsafe_allow_html=True)
