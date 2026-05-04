from app.ui.styles import theme


def build_global_css():
    return f"""
    <style>
      .rimas-page {{
        color: {theme.COLOR_TEXT};
      }}
      .rimas-card {{
        background: {theme.COLOR_SURFACE};
        border: 1px solid {theme.COLOR_BORDER};
        border-radius: {theme.CARD_RADIUS_PX}px;
        padding: 14px 16px;
        margin: 8px 0;
      }}
      .rimas-card-title {{
        font-weight: 700;
        color: {theme.COLOR_TEXT};
        margin-bottom: 4px;
      }}
      .rimas-card-meta {{
        color: {theme.COLOR_MUTED};
        font-size: 14px;
        margin-bottom: 8px;
      }}
      .rimas-badge {{
        display: inline-block;
        background: {theme.COLOR_ACCENT_SOFT};
        color: {theme.COLOR_ACCENT};
        border-radius: 999px;
        padding: 3px 9px;
        margin: 2px 4px 2px 0;
        font-size: 13px;
      }}
    </style>
    """


def apply_global_css(renderer):
    renderer.markdown(build_global_css(), unsafe_allow_html=True)
