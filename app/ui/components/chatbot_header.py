from app.ui.components.mascot import get_mascot_img_tag
from app.ui.styles import theme


def render_chatbot_header(renderer, user_id):
    mascot_svg = get_mascot_img_tag(size=50, expression="happy")
    renderer.markdown(
        f"""
        <div class="rimas-chat-header">
          {mascot_svg}
          <div class="rimas-chat-header-text">
            <h2>RIMAS Curator</h2>
            <p>
              {user_id}님의 취향을 잘 알고 있어요 &nbsp;·&nbsp;
              <span class="rimas-accent-tag">#indie</span>&nbsp;
              <span class="rimas-accent-tag">#rnb</span>&nbsp;
              <span class="rimas-accent-tag">#calm</span>
            </p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
