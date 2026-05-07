def render_chat_history(renderer, chat_history):
    for message in chat_history:
        role = message.get("role", "assistant")
        content = message.get("content", "")
        if hasattr(renderer, "chat_message"):
            with renderer.chat_message(role):
                renderer.markdown(content)
            continue
        renderer.markdown(f"**{role}**: {content}")


def render_curator_response(renderer, response):
    if not response:
        return
    renderer.markdown(response)
