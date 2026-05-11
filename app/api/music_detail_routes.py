import json
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from app.cache import latest_state_cache
from app.config.settings import create_database_connection
from app.repositories import query_constants
from app.repositories.music_catalog_repository import MusicCatalogRepository
from app.services.music_detail_service import MusicDetailService

logger = logging.getLogger("rimas.api.music_detail")
router = APIRouter()


def get_music_detail_service() -> MusicDetailService:
    connection = None
    try:
        connection = create_database_connection()
    except Exception as exc:
        logger.warning("music_detail_catalog_unavailable", extra={"error": str(exc)})
        yield MusicDetailService()
        return

    try:
        yield MusicDetailService(music_catalog_repository=MusicCatalogRepository(connection))
    finally:
        connection.close()


@router.get("/detail/{content_id}")
def get_music_detail(
    content_id: str,
    user_id: str | None = Query(None, description="사용자 ID"),
    session_id: str | None = Query(None, description="세션 ID (latest RAG state 연결용)"),
    request_id: str | None = Query(None, description="요청 ID"),
    service: MusicDetailService = Depends(get_music_detail_service),
):
    """Music Detail ViewModel을 반환한다.

    session_id가 있으면 Redis에서 latest RAG_STATE를 로드해 근거 데이터와 연결한다.
    user_id가 있으면 detail view log를 interaction_logs에 저장한다.
    """
    recent_rag_state: dict | None = None
    if session_id:
        recent_rag_state = latest_state_cache.get_latest_rag_state(session_id)

    try:
        detail = service.get_detail(content_id=content_id, recent_rag_state=recent_rag_state)
    except Exception as exc:
        logger.error("music_detail_error", extra={"content_id": content_id, "error": str(exc)}, exc_info=True)
        raise HTTPException(status_code=500, detail="음악 상세 정보를 조회하지 못했습니다.")

    if user_id:
        _save_view_log(
            content_id=content_id,
            user_id=user_id,
            session_id=session_id or "",
            request_id=request_id or f"req_{uuid4().hex}",
            source_type=detail.get("source", "unknown"),
            rag_state=recent_rag_state or {},
        )

    return {"status": "success", "music_detail": detail}


def _save_view_log(
    content_id: str,
    user_id: str,
    session_id: str,
    request_id: str,
    source_type: str,
    rag_state: dict,
) -> None:
    try:
        conn = create_database_connection()
        compact_rag = json.dumps(
            {"source_type": source_type, "content_id": content_id, "rag_available": bool(rag_state)},
            ensure_ascii=False,
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    query_constants.INSERT_DETAIL_VIEW_LOG,
                    {
                        "log_id": f"log_{uuid4().hex}",
                        "request_id": request_id,
                        "user_id": user_id,
                        "session_id": session_id,
                        "user_input": content_id,
                        "response_type": "music_detail_view",
                        "compact_rag_state_json": compact_rag,
                    },
                )
        conn.close()
        logger.info("detail_view_log_saved", extra={"content_id": content_id, "user_id": user_id})
    except Exception as exc:
        logger.warning("detail_view_log_error", extra={"content_id": content_id, "error": str(exc)})
