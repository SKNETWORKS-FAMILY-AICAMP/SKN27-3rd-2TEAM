import logging

from fastapi import APIRouter, HTTPException, Query

from app.services.main_recommendation_service import MainRecommendationService
from app.services.request_lifecycle_cache import DuplicateRequestError, request_lifecycle_cache

logger = logging.getLogger("rimas.api.recommendation")
router = APIRouter()

_service = MainRecommendationService()


@router.get("/main")
def get_main_recommendations(
    user_id: str = Query(..., description="사용자 ID"),
    session_id: str = Query(..., description="세션 ID"),
    request_id: str | None = Query(None, description="중복 요청 차단용 요청 ID"),
):
    """메인 추천 페이지 뷰모델 반환.

    - Redis에서 SESSION_CONTEXT 로드 (cache hit 시 DB 조회 없음)
    - KAG + RAG Mock으로 추천 구성
    - 프론트엔드에서 페이지 마운트 시 1회만 호출
    """
    logger.info("main_recommendation_request", extra={"user_id": user_id, "session_id": session_id})
    if request_id:
        try:
            request_lifecycle_cache.start(request_id)
        except DuplicateRequestError as exc:
            raise HTTPException(status_code=409, detail="중복 요청이 처리 중입니다.") from exc
    try:
        view_model, session_degraded = _service.get_page_view_model(user_id=user_id, session_id=session_id)
        return {
            "status": "success",
            "session_degraded": session_degraded,
            "page_type": "main_recommendation_page",
            "view_model": view_model,
        }
    except Exception as exc:
        logger.error("main_recommendation_error", extra={"error": str(exc)}, exc_info=True)
        raise HTTPException(status_code=500, detail="추천 서비스 오류가 발생했습니다.")
    finally:
        if request_id:
            request_lifecycle_cache.finish(request_id)
