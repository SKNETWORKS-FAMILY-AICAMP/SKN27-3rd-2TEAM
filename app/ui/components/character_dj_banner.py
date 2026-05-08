from app.ui.components.mascot import get_mascot_img_tag


def render_character_dj_banner(renderer, message):
    mascot_svg = get_mascot_img_tag(size=54, expression="singing")
    renderer.markdown(
        f"""
        <div class="rimas-banner">
          {mascot_svg}
          <div class="rimas-banner-body">
            <h3>✨ AI Curator의 오늘의 추천</h3>
            <p>{message}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
