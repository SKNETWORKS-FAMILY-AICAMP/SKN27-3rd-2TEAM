import logging

from fastapi import APIRouter, HTTPException, Query

from app.services import session_cache_service
from app.services.session_flush_service import flush_session

logger = logging.getLogger("rimas.api.session")
router = APIRouter()


@router.get("/{session_id}/history")
def get_history(
    session_id: str,
    user_id: str = Query(..., description="사용자 ID"),
):
    """Redis에서 세션 히스토리 반환 (DB 조회 없음)."""
    try:
        history = session_cache_service.get_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as exc:
        logger.error("history_error", extra={"session_id": session_id, "error": str(exc)}, exc_info=True)
        raise HTTPException(status_code=500, detail="히스토리 조회 오류가 발생했습니다.")


@router.post("/{session_id}/flush")
def flush(
    session_id: str,
    user_id: str = Query(..., description="사용자 ID"),
    flush_logs: bool = Query(False, description="interaction_logs 삭제 여부 (local/dev 환경에서만 허용)"),
):
    """Redis 세션을 PostgreSQL로 플러시하고 캐시를 삭제한다."""
    logger.info("flush_request", extra={"session_id": session_id, "user_id": user_id, "flush_logs": flush_logs})
    try:
        result = flush_session(session_id=session_id, user_id=user_id, flush_logs=flush_logs)
        return {"session_id": session_id, **result}
    except Exception as exc:
        logger.error("flush_error", extra={"session_id": session_id, "error": str(exc)}, exc_info=True)
        raise HTTPException(status_code=500, detail="세션 플러시 오류가 발생했습니다.")


@router.delete("/{session_id}")
def clear(session_id: str):
    """Redis 세션만 삭제 (DB 저장 없음)."""
    try:
        session_cache_service.clear(session_id)
        return {"session_id": session_id, "cleared": True}
    except Exception as exc:
        logger.error("clear_error", extra={"session_id": session_id, "error": str(exc)}, exc_info=True)
        raise HTTPException(status_code=500, detail="세션 삭제 오류가 발생했습니다.")
