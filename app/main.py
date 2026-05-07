from app.common.default_state import SESSION_DEFAULTS
from app.pages.chatbot_page import render_chatbot_page
from app.pages.main_recommendation_page import render_main_recommendation_page
from app.ui.components.sidebar import render_sidebar


def initialize_session_state(renderer):
    for key, value in SESSION_DEFAULTS.items():
        renderer.session_state.setdefault(key, value)


def main():
    import streamlit as st

    st.set_page_config(page_title="RIMAS", layout="wide")
    initialize_session_state(st)
    sidebar_state = render_sidebar(st)
    st.session_state["selected_user_id"] = sidebar_state["selected_user_id"]
    st.session_state["current_page"] = sidebar_state["current_page"]

    if st.session_state["current_page"] == "chatbot_page":
        render_chatbot_page(
            st,
            st.session_state["selected_user_id"],
            developer_mode=sidebar_state["developer_mode"],
        )
        return

    render_main_recommendation_page(
        st,
        st.session_state["selected_user_id"],
        developer_mode=sidebar_state["developer_mode"],
    )


if __name__ == "__main__":
    main()
