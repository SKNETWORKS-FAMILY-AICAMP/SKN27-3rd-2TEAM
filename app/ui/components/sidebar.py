def render_sidebar(renderer):
    sidebar = getattr(renderer, "sidebar", renderer)
    developer_mode = sidebar.checkbox("Developer mode", value=False)
    pages = ["main_recommendation_page", "chatbot_page"]
    current_page = getattr(renderer, "session_state", {}).get(
        "current_page", "main_recommendation_page"
    )
    page_index = pages.index(current_page) if current_page in pages else 0
    page = sidebar.radio("Page", pages, index=page_index)
    user_id = sidebar.text_input("User ID", value="user_001")
    return {
        "developer_mode": developer_mode,
        "current_page": page,
        "selected_user_id": user_id,
    }
