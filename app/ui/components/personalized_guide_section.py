def render_personalized_guide_section(renderer, guide_message):
    if not guide_message:
        return
    renderer.markdown(
        f"""
        <div class="rimas-card">
          <div class="rimas-card-title">개인화 안내</div>
          <div>{guide_message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
