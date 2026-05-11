import logging
import time

from app.agents.orchestrator_agent import OrchestratorAgent
from app.cache import latest_state_cache, redis_client
from app.services import session_cache_service

logger = logging.getLogger("rimas.service.main_recommendation")


class MainRecommendationService:
    """메인 추천 페이지 — LLM 없이 KAG+RAG 결과로 뷰모델을 만든다.
    Redis에서 SESSION_CONTEXT를 읽고, 결과는 view_model_service로 변환한다.
    RDB 쿼리는 RAG builder 내부에서만 발생하므로 중복 조회 없음.
    """

    def __init__(self, orchestrator: OrchestratorAgent | None = None):
        self._orchestrator = orchestrator or OrchestratorAgent()

    def get_page_view_model(self, user_id: str, session_id: str) -> tuple[dict, bool]:
        start = time.perf_counter()
        session_degraded = not redis_client.is_healthy()

        session_context = session_cache_service.load_context(session_id)

        result = self._orchestrator.run_recommendation(
            user_id=user_id,
            session_id=session_id,
            session_context=session_context,
        )

        ms = round((time.perf_counter() - start) * 1000, 1)
        kag_state = result.get("kag_state", {})
        rag_state = result.get("rag_state", {})

        logger.info(
            "main_recommendation_ok",
            extra={"user_id": user_id, "session_id": session_id, "ms": ms},
        )

        view_model = self._build_view_model(user_id, session_context, kag_state, rag_state, ms)
        latest_state_cache.save_latest_states(
            session_id=session_id,
            kag_state=kag_state,
            rag_state=rag_state,
            response_state=view_model,
            recommendation_metadata={
                "source_type": "main_recommendation",
                "user_id": user_id,
                "latency_ms": ms,
            },
        )
        return view_model, session_degraded

    @staticmethod
    def _build_view_model(
        user_id: str,
        session_context: dict,
        kag_state: dict,
        rag_state: dict,
        latency_ms: float,
    ) -> dict:
        evidence = rag_state.get("recommended_content_evidence", [])
        groups: dict[str, list] = {
            "personalized": [],
            "discovery": [],
            "new_release": [],
        }
        category_map = {
            "personalized_match": "personalized",
            "discovery_candidate": "discovery",
            "new_release": "new_release",
        }
        for item in evidence:
            target = category_map.get(item.get("recommendation_category"))
            if target in groups:
                groups[target].append({
                    "content_id": item.get("content_id"),
                    "title": item.get("title"),
                    "artist": item.get("artist"),
                    "album": item.get("album"),
                    "genre": item.get("genre", []),
                    "mood": item.get("mood", []),
                    "display_reason": item.get("evidence_summary", ""),
                })

        taste_badges = (
            session_context.get("recent_genres", []) +
            session_context.get("recent_moods", [])
        )

        return {
            "status": "success",
            "page_type": "main_recommendation_page",
            "user_id": user_id,
            "taste_badges": taste_badges,
            "today_theme": rag_state.get("recommendation_reason", {}).get("summary", ""),
            "character_message": rag_state.get("recommendation_scripts", {}).get("dj_intro", ""),
            "personalized": groups["personalized"],
            "new_release": groups["new_release"],
            "discovery": groups["discovery"],
            "personalized_guide": rag_state.get("recommendation_scripts", {}).get("discovery_message", ""),
            "debug": {
                "session_context": session_context,
                "kag_state": kag_state,
                "rag_state": rag_state,
                "latency_ms": latency_ms,
            },
        }
