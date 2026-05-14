import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.taste_event_service import TasteEventService

logger = logging.getLogger("rimas.api.taste")
router = APIRouter()

_service = TasteEventService()


class TasteEventRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    session_id: str = Field(..., description="세션 ID")
    content_id: str = Field(..., description="콘텐츠 ID")
    event_type: str = Field(..., description="이벤트 타입")
    source: str = Field(..., description="이벤트 출처")
    request_id: str | None = Field(None, description="요청 ID")


@router.post("/events")
def add_taste_event(req: TasteEventRequest):
    try:
        return _service.add_to_taste(
            user_id=req.user_id,
            session_id=req.session_id,
            content_id=req.content_id,
            source=req.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
