import json
import logging
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.chatbot_service import ChatbotService
from app.services.chatbot_stream_service import ChatbotStreamService
from app.services.request_lifecycle_cache import DuplicateRequestError, request_lifecycle_cache

logger = logging.getLogger("rimas.api.chatbot")
router = APIRouter()


@lru_cache(maxsize=1)
def _get_service() -> ChatbotService:
    return ChatbotService()


@lru_cache(maxsize=1)
def _get_stream_service() -> ChatbotStreamService:
    return ChatbotStreamService(chatbot_service=_get_service())


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    session_id: str = Field(..., description="세션 ID")
    user_input: str = Field(..., min_length=1, description="사용자 입력 메시지")
    request_id: str | None = Field(None, description="중복 요청 차단용 요청 ID")


@router.post("/respond")
def respond(req: ChatRequest):
    """챗봇 메시지 처리.

    - 1 호출 = 1 턴 (중복 호출 금지)
    - SESSION_CONTEXT는 Redis에서만 로드 (DB 조회 없음)
    - 응답 후 Redis에 턴 저장 + SESSION_CONTEXT 업데이트
    """
    logger.info(
        "chatbot_request",
        extra={"user_id": req.user_id, "session_id": req.session_id},
    )
    if req.request_id:
        try:
            request_lifecycle_cache.start(req.request_id)
        except DuplicateRequestError as exc:
            raise HTTPException(status_code=409, detail="중복 요청이 처리 중입니다.") from exc
    try:
        result = _get_service().submit_message(
            user_id=req.user_id,
            session_id=req.session_id,
            user_input=req.user_input,
        )
        return result
    except Exception as exc:
        logger.error("chatbot_error", extra={"error": str(exc)}, exc_info=True)
        raise HTTPException(status_code=500, detail="챗봇 서비스 오류가 발생했습니다.")
    finally:
        if req.request_id:
            request_lifecycle_cache.finish(req.request_id)


@router.post("/respond/stream")
def respond_stream(req: ChatRequest):
    """챗봇 메시지 처리 — SSE 스트리밍."""

    def _to_sse(events):
        for event in events:
            yield f"event: {event['event']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"

    return StreamingResponse(
        _to_sse(
            _get_stream_service().stream_response(
                user_id=req.user_id,
                session_id=req.session_id,
                user_input=req.user_input,
            )
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
