def render_character_dj_banner(renderer, message):
    renderer.markdown(
        f"""
        <div class="rimas-card">
          <div class="rimas-card-title">DJ Curator</div>
          <div>{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
