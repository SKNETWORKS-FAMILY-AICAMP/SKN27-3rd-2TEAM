from app.ui.components.mascot import get_mascot_img_tag
from app.ui.styles import theme


def render_personalized_guide_section(renderer, guide_message):
    mascot_svg = get_mascot_img_tag(size=54, expression="happy")
    body = guide_message or "더 세밀한 취향 분석과 음악 정보를 알려드려요."
    renderer.markdown(
        f"""
        <div class="rimas-banner">
          {mascot_svg}
          <div class="rimas-banner-body">
            <h3>큐레이터에게 직접 물어보세요!</h3>
            <p>{body}</p>
          </div>
        </div>
        <div class="rimas-footer-note">
          추천 결과는 KAG/RAG 기반으로 제공되며, 잘못된 추천을 절대 하지 않는 것을 목표로 합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )
