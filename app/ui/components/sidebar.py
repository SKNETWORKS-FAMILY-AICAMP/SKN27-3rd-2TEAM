from app.ui.components.mascot import get_mascot_img_tag
from app.ui.styles import theme


def render_sidebar(renderer):
    sidebar = getattr(renderer, "sidebar", renderer)

    mascot_svg = get_mascot_img_tag(size=42, expression="happy")
    sidebar.markdown(
        f"""
        <div class="rimas-sidebar-logo">
          <div class="rimas-logo-row">
            {mascot_svg}
            <div>
              <div class="rimas-logo-name">RIMAS</div>
              <div class="rimas-logo-sub">AI Music Curator</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page_labels = {
        "🏠  홈 (추천)": "main_recommendation_page",
        "💬  채팅 (Curator)": "chatbot_page",
    }
    current_page = getattr(renderer, "session_state", {}).get(
        "current_page", "main_recommendation_page"
    )
    default_label = next(
        (k for k, v in page_labels.items() if v == current_page),
        "🏠  홈 (추천)",
    )
    selected_label = sidebar.radio(
        "Navigation",
        list(page_labels.keys()),
        index=list(page_labels.keys()).index(default_label),
        label_visibility="collapsed",
    )
    page = page_labels[selected_label]

    sidebar.markdown(
        f'<div style="margin:10px 0 4px;font-size:11px;color:{theme.TEXT_MUTED};font-weight:600;letter-spacing:.5px;">USER</div>',
        unsafe_allow_html=True,
    )
    user_id = sidebar.text_input("User ID", value="user_001", label_visibility="collapsed")

    sidebar.markdown(
        f'<div style="margin-top:4px;font-size:10px;color:{theme.TEXT_MUTED};opacity:.7;">@{user_id}</div>',
        unsafe_allow_html=True,
    )

    sidebar.markdown(f'<div style="border-top:1px solid {theme.BORDER};margin:12px 0 8px;"></div>', unsafe_allow_html=True)

    developer_mode = sidebar.checkbox("Developer Mode", value=False)

    sidebar.markdown(
        f'<div style="margin-top:16px;font-size:9.5px;color:{theme.TEXT_MUTED};opacity:.5;line-height:1.5;">RIMAS v2.0.0<br/>© 2024 RIMAS Team</div>',
        unsafe_allow_html=True,
    )

    return {
        "developer_mode": developer_mode,
        "current_page": page,
        "selected_user_id": user_id,
    }
