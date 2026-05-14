import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config.settings import create_database_connection
from app.repositories.music_catalog_repository import MusicCatalogRepository
from app.services.music_detail_service import MusicDetailService
from app.services.taste_event_service import TasteEventService

logger = logging.getLogger("rimas.api.taste")
router = APIRouter()


class TasteEventRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    session_id: str = Field(..., description="세션 ID")
    content_id: str = Field(..., description="콘텐츠 ID")
    event_type: str = Field(..., description="이벤트 타입")
    source: str = Field(..., description="이벤트 출처")
    request_id: str | None = Field(None, description="요청 ID")


def get_taste_event_service() -> TasteEventService:
    connection = None
    try:
        connection = create_database_connection()
    except Exception as exc:
        logger.warning("taste_event_catalog_unavailable", extra={"error": str(exc)})
        yield TasteEventService()
        return

    try:
        detail_service = MusicDetailService(music_catalog_repository=MusicCatalogRepository(connection))
        yield TasteEventService(detail_service=detail_service)
    finally:
        connection.close()


@router.post("/events")
def add_taste_event(
    req: TasteEventRequest,
    service: TasteEventService = Depends(get_taste_event_service),
):
    try:
        return service.add_to_taste(
            user_id=req.user_id,
            session_id=req.session_id,
            content_id=req.content_id,
            source=req.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
