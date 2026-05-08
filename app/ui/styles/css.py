from app.ui.styles import theme


def build_global_css():
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800;900&family=Nunito:wght@700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');

    /* ── Animations ── */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes cardIn {{
        from {{ opacity: 0; transform: translateY(12px) scale(.97); }}
        to   {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}
    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); opacity: .7; }}
        50%       {{ transform: scale(1.15); opacity: 1; }}
    }}
    @keyframes mascotBob {{
        from {{ transform: translateY(0); }}
        to   {{ transform: translateY(-4px); }}
    }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
    ::-webkit-scrollbar-track {{ background: {theme.BG}; }}
    ::-webkit-scrollbar-thumb {{ background: {theme.BORDER}; border-radius: 2px; }}

    /* ── Global dark background ── */
    .stApp {{
        background: {theme.BG} !important;
        font-family: 'Noto Sans KR', sans-serif !important;
    }}
    [data-testid="stAppViewContainer"] {{
        background: {theme.BG} !important;
    }}
    [data-testid="stMain"] {{
        background: {theme.BG} !important;
    }}
    [data-testid="block-container"] {{
        background: {theme.BG} !important;
        padding-top: 24px !important;
    }}
    section.main > div {{
        background: {theme.BG} !important;
    }}

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer {{ visibility: hidden !important; }}
    [data-testid="stHeader"] {{ visibility: hidden !important; min-height: 0 !important; }}
    [data-testid="stDecoration"] {{ display: none !important; }}
    [data-testid="stToolbar"] {{ display: none !important; }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: {theme.SIDEBAR_BG} !important;
        border-right: 1px solid {theme.BORDER} !important;
    }}
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {{
        font-family: 'Noto Sans KR', sans-serif !important;
        color: {theme.TEXT_MUTED} !important;
    }}
    [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {{
        color: {theme.TAG_TEXT} !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }}
    [data-testid="stSidebar"] input[type="text"] {{
        background: {theme.INPUT_BG} !important;
        border: 1px solid {theme.INPUT_BORDER} !important;
        color: {theme.TEXT} !important;
        border-radius: 8px !important;
    }}

    /* ── Overflow visible so horizontal card rows work ── */
    .element-container, .stMarkdown {{
        overflow: visible !important;
    }}

    /* ── rimas-page ── */
    .rimas-page {{
        color: {theme.TEXT};
        animation: fadeIn .4s ease;
    }}

    /* ── Section container ── */
    .rimas-section {{
        background: {theme.SECTION_BG};
        border: 1px solid {theme.SECTION_BORDER};
        border-radius: 16px;
        padding: 18px 20px;
        margin-bottom: 18px;
        animation: fadeIn .4s ease;
    }}
    .rimas-section-title {{
        font-size: 17px;
        font-weight: 800;
        color: {theme.TEXT};
        margin: 0 0 3px 0;
        font-family: 'Noto Sans KR', sans-serif;
    }}
    .rimas-section-subtitle {{
        font-size: 12px;
        color: {theme.TEXT_MUTED};
        margin: 0 0 14px 0;
    }}

    /* ── Horizontal card row ── */
    .rimas-cards-row {{
        display: flex;
        gap: 12px;
        overflow-x: auto;
        padding-bottom: 8px;
        scrollbar-width: thin;
        scrollbar-color: {theme.BORDER} transparent;
    }}
    .rimas-cards-row::-webkit-scrollbar {{ height: 4px; }}
    .rimas-cards-row::-webkit-scrollbar-thumb {{ background: {theme.BORDER}; border-radius: 2px; }}

    /* ── Music card ── */
    .rimas-music-card {{
        width: 152px;
        flex-shrink: 0;
        background: {theme.CARD_BG};
        border: 1px solid {theme.BORDER};
        border-radius: 14px;
        overflow: hidden;
        cursor: pointer;
        transition: all .22s ease;
        animation: cardIn .3s ease;
    }}
    .rimas-music-card:hover {{
        border-color: rgba(124,77,255,.53);
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 8px 20px rgba(124,77,255,.15);
    }}
    .rimas-album-art {{
        position: relative;
        height: 130px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }}
    .rimas-album-note {{
        font-size: 32px;
        opacity: .18;
        color: white;
        pointer-events: none;
    }}
    .rimas-new-badge {{
        position: absolute;
        top: 8px; right: 8px;
        background: {theme.PINK};
        color: white;
        border-radius: 6px;
        padding: 2px 7px;
        font-size: 9px;
        font-weight: 800;
        letter-spacing: .8px;
    }}
    .rimas-card-info {{ padding: 10px 10px 12px; }}
    .rimas-card-title {{
        font-size: 12.5px;
        font-weight: 700;
        color: {theme.TEXT};
        margin: 0 0 2px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .rimas-card-artist {{
        font-size: 11px;
        color: {theme.TEXT_MUTED};
        margin: 0 0 4px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .rimas-card-reason {{
        font-size: 10px;
        color: {theme.TEXT_MUTED};
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }}

    /* ── Tag ── */
    .rimas-tag {{
        display: inline-block;
        background: {theme.TAG_BG};
        color: {theme.TAG_TEXT};
        border-radius: 999px;
        padding: 2px 8px;
        font-size: 10px;
        font-weight: 600;
        margin-right: 4px;
        margin-top: 3px;
    }}

    /* ── Badge (taste) ── */
    .rimas-badge {{
        display: inline-block;
        background: {theme.ACCENT_SOFT};
        color: {theme.ACCENT};
        border-radius: 999px;
        padding: 4px 12px;
        margin: 3px 5px 3px 0;
        font-size: 13px;
        font-weight: 600;
    }}

    /* ── Banners (DJ / guide) ── */
    .rimas-banner {{
        background: {theme.ACCENT_SOFT};
        border: 1px solid rgba(124,77,255,.27);
        border-radius: 16px;
        padding: 18px 20px;
        display: flex;
        align-items: flex-start;
        gap: 16px;
        margin-bottom: 18px;
        animation: fadeIn .4s ease;
    }}
    .rimas-banner-body h3 {{
        font-size: 14px;
        font-weight: 800;
        color: {theme.TEXT};
        margin: 0 0 4px 0;
        font-family: 'Noto Sans KR', sans-serif;
    }}
    .rimas-banner-body p {{
        font-size: 12px;
        color: {theme.TEXT_MUTED};
        line-height: 1.6;
        margin: 0;
    }}
    .rimas-banner-btn {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: {theme.ACCENT};
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 8px 18px;
        font-size: 12.5px;
        font-weight: 700;
        cursor: pointer;
        margin-top: 10px;
        font-family: 'Noto Sans KR', sans-serif;
        text-decoration: none;
    }}

    /* ── Top header ── */
    .rimas-top-header {{
        padding: 18px 0 14px;
        border-bottom: 1px solid {theme.BORDER};
        margin-bottom: 20px;
        animation: fadeIn .3s ease;
    }}
    .rimas-top-header h1 {{
        font-size: 20px;
        font-weight: 800;
        color: {theme.TEXT};
        margin: 0 0 2px 0;
        font-family: 'Noto Sans KR', sans-serif;
    }}
    .rimas-top-header p {{
        font-size: 12.5px;
        color: {theme.TEXT_MUTED};
        margin: 0 0 10px 0;
    }}

    /* ── Chat page header ── */
    .rimas-chat-header {{
        background: {theme.SIDEBAR_BG};
        border: 1px solid {theme.BORDER};
        border-radius: 14px;
        padding: 14px 18px;
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 16px;
        animation: fadeIn .3s ease;
    }}
    .rimas-chat-header-text h2 {{
        font-size: 15.5px;
        font-weight: 800;
        color: {theme.TEXT};
        margin: 0 0 3px 0;
        font-family: 'Noto Sans KR', sans-serif;
    }}
    .rimas-chat-header-text p {{
        font-size: 11.5px;
        color: {theme.TEXT_MUTED};
        margin: 0;
    }}
    .rimas-accent-tag {{ color: {theme.ACCENT}; font-weight: 600; }}

    /* ── Small play card ── */
    .rimas-small-card {{
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 8px 10px;
        background: {theme.CARD_BG};
        border: 1px solid {theme.BORDER};
        border-radius: 10px;
        margin-bottom: 7px;
        transition: all .18s;
        animation: fadeIn .3s ease;
    }}
    .rimas-small-card:hover {{ border-color: rgba(124,77,255,.4); }}
    .rimas-small-art {{
        width: 44px; height: 44px;
        border-radius: 8px;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        color: white;
        opacity: .85;
    }}
    .rimas-small-info {{ flex: 1; overflow: hidden; }}
    .rimas-small-title {{ font-size: 12.5px; font-weight: 700; color: {theme.TEXT}; margin: 0 0 1px 0; }}
    .rimas-small-artist {{ font-size: 11px; color: {theme.TEXT_MUTED}; margin: 0 0 2px 0; }}
    .rimas-small-desc {{ font-size: 11px; color: {theme.TEXT_MUTED}; line-height: 1.45; margin: 0; }}

    /* ── Streamlit chat message overrides ── */
    [data-testid="stChatMessage"] {{
        background: transparent !important;
        padding: 4px 0 !important;
    }}
    [data-testid="stChatMessageContent"] > div {{
        background: {theme.CHAT_BOT} !important;
        border: 1px solid {theme.BORDER} !important;
        border-radius: 4px 14px 14px 14px !important;
        color: {theme.TEXT} !important;
        padding: 10px 14px !important;
    }}
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] > div {{
        background: {theme.CHAT_USER} !important;
        border: none !important;
        border-radius: 14px 14px 4px 14px !important;
        color: white !important;
    }}

    /* ── Chat input overrides ── */
    [data-testid="stChatInput"] > div {{
        background: {theme.INPUT_BG} !important;
        border: 1px solid {theme.INPUT_BORDER} !important;
        border-radius: 12px !important;
    }}
    [data-testid="stChatInput"] textarea {{
        background: transparent !important;
        color: {theme.TEXT} !important;
        font-family: 'Noto Sans KR', sans-serif !important;
    }}
    [data-testid="stChatInput"] button {{
        background: {theme.ACCENT} !important;
        border-radius: 8px !important;
    }}

    /* ── Button overrides ── */
    .stButton > button {{
        background: {theme.ACCENT} !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-family: 'Noto Sans KR', sans-serif !important;
        transition: opacity .18s !important;
    }}
    .stButton > button:hover {{
        opacity: .85 !important;
        border: none !important;
        color: white !important;
    }}

    /* ── Text input ── */
    .stTextInput input {{
        background: {theme.INPUT_BG} !important;
        border: 1px solid {theme.INPUT_BORDER} !important;
        border-radius: 10px !important;
        color: {theme.TEXT} !important;
        font-family: 'Noto Sans KR', sans-serif !important;
    }}

    /* ── Text color overrides ── */
    p, .stMarkdown p, [data-testid="stMarkdownContainer"] p {{
        color: {theme.TEXT} !important;
    }}

    /* ── Footer note ── */
    .rimas-footer-note {{
        font-size: 10.5px;
        color: {theme.TEXT_MUTED};
        text-align: center;
        opacity: .6;
        line-height: 1.6;
        margin-top: 20px;
        padding-bottom: 20px;
    }}

    /* ── Prevent Streamlit from resizing mascot images ── */
    .rimas-banner img, .rimas-chat-header img, .rimas-sidebar-logo img {{
        max-width: none !important;
        max-height: none !important;
    }}

    /* ── Hide Streamlit auto-detected multipage nav ── */
    [data-testid="stSidebarNav"] {{ display: none !important; }}
    [data-testid="stSidebarNavItems"] {{ display: none !important; }}
    [data-testid="stSidebarNavSeparator"] {{ display: none !important; }}

    /* ── Sidebar logo ── */
    .rimas-sidebar-logo {{
        padding: 8px 0 14px;
        border-bottom: 1px solid {theme.BORDER};
        margin-bottom: 4px;
    }}
    .rimas-logo-row {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .rimas-logo-name {{
        font-family: 'Nunito', sans-serif;
        font-size: 22px;
        font-weight: 900;
        color: {theme.ACCENT};
        letter-spacing: -0.5px;
        line-height: 1;
    }}
    .rimas-logo-sub {{
        font-size: 9.5px;
        color: {theme.TEXT_MUTED};
        font-weight: 500;
        margin-top: 2px;
    }}
    </style>
    """


def apply_global_css(renderer):
    renderer.markdown(build_global_css(), unsafe_allow_html=True)
