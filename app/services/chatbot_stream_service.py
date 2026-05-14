import logging
from typing import Iterator

from app.services.chatbot_service import ChatbotService

logger = logging.getLogger("rimas.service.chatbot_stream")

_CHUNK_SIZE = 12


class ChatbotStreamService:
    def __init__(self, chatbot_service: ChatbotService | None = None):
        self._chatbot_service = chatbot_service or ChatbotService()

    def stream_response(self, user_id: str, session_id: str, user_input: str) -> Iterator[dict]:
        try:
            result = self._chatbot_service.submit_message(user_id, session_id, user_input)
        except Exception as exc:
            logger.error("stream_service_error", extra={"error": str(exc)}, exc_info=True)
            yield {"event": "error", "data": {"message": str(exc)}}
            return

        response_state = result.get("response_state", {})
        text = response_state.get("chatbot_response", "")

        for chunk in _chunk_text(text):
            yield {"event": "delta", "data": {"text": chunk}}

        yield {
            "event": "final",
            "data": {
                "status": result.get("status"),
                "response_state": response_state,
                "latency_ms": result.get("latency_ms"),
            },
        }
        yield {"event": "done", "data": {}}


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE) -> list[str]:
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)] or [""]
