import logging

from fastapi import APIRouter, HTTPException

from app.services.music_detail_service import MusicDetailService

logger = logging.getLogger("rimas.api.music_detail")
router = APIRouter()

_service = MusicDetailService()


@router.get("/detail/{content_id}")
def get_music_detail(content_id: str):
    """Music Detail ViewModel을 반환한다."""
    try:
        return {
            "status": "success",
            "music_detail": _service.get_detail(content_id=content_id),
        }
    except Exception as exc:
        logger.error("music_detail_error", extra={"content_id": content_id, "error": str(exc)}, exc_info=True)
        raise HTTPException(status_code=500, detail="음악 상세 정보를 조회하지 못했습니다.")
