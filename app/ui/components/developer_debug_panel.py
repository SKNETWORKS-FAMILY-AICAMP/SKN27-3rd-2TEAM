def render_developer_debug_panel(renderer, debug_data, developer_mode):
    if not developer_mode:
        return

    renderer.subheader("Developer Debug Panel")
    renderer.json(debug_data)
