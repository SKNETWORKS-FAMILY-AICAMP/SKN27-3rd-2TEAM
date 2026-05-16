import logging
import time

from app.agents.orchestrator_agent import OrchestratorAgent
from app.agents.recommendation_agent import build_display_reason
from app.cache import latest_state_cache, redis_client
from app.config.settings import APP_ENV, create_database_connection
from app.repositories.music_catalog_repository import MusicCatalogRepository
from app.services.logging_service import LoggingService
from app.services import session_cache_service

_DEBUG_ENVS = {"local", "dev", "development"}

logger = logging.getLogger("rimas.service.main_recommendation")


class MainRecommendationService:
    """메인 추천 페이지 — LLM 없이 KAG+RAG 결과로 뷰모델을 만든다.
    Redis에서 SESSION_CONTEXT를 읽고, 결과는 view_model_service로 변환한다.
    RDB 쿼리는 RAG builder 내부에서만 발생하므로 중복 조회 없음.
    """

    def __init__(
        self,
        orchestrator: OrchestratorAgent | None = None,
        music_catalog_repository=None,
        logging_service: LoggingService | None = None,
    ):
        self._orchestrator = orchestrator or OrchestratorAgent()
        self._music_catalog_repository = music_catalog_repository
        self._logging_service = logging_service or LoggingService()

    def get_page_view_model(self, user_id: str, session_id: str) -> tuple[dict, bool]:
        start = time.perf_counter()
        session_degraded = not redis_client.is_healthy()

        session_context = session_cache_service.load_context(session_id, user_id=user_id)

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

        view_model = self._build_view_model(
            user_id,
            session_context,
            kag_state,
            rag_state,
            ms,
            catalog_repository=self._get_music_catalog_repository(),
        )
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
        self._save_interaction_log(
            user_id=user_id,
            session_id=session_id,
            session_context=session_context,
            kag_state=kag_state,
            rag_state=rag_state,
            response_state=view_model,
            latency_ms=ms,
        )
        return view_model, session_degraded

    def _save_interaction_log(
        self,
        *,
        user_id: str,
        session_id: str,
        session_context: dict,
        kag_state: dict,
        rag_state: dict,
        response_state: dict,
        latency_ms: float,
    ) -> None:
        try:
            self._logging_service.save(
                user_id=user_id,
                session_id=session_id,
                user_input="",
                session_context=session_context,
                kag_state=kag_state,
                rag_state=rag_state,
                response_state=response_state,
                latency_ms=latency_ms,
                page_type="main_recommendation_page",
            )
        except Exception as exc:
            logger.error("main_recommendation_log_save_error", extra={"error": str(exc)}, exc_info=True)

    def _get_music_catalog_repository(self):
        if self._music_catalog_repository is not None:
            return self._music_catalog_repository
        try:
            return MusicCatalogRepository(create_database_connection())
        except Exception as exc:
            logger.error("main_recommendation_catalog_repository_error", extra={"error": str(exc)}, exc_info=True)
            return None

    @staticmethod
    def _build_view_model(
        user_id: str,
        session_context: dict,
        kag_state: dict,
        rag_state: dict,
        latency_ms: float,
        catalog_repository=None,
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
        used_content_ids: set[str] = set()
        disliked_artists = set(session_context.get("disliked_artists", []) or [])
        disliked_tracks = set(session_context.get("disliked_tracks", []) or [])
        disliked_genres = set(session_context.get("disliked_genres", []) or [])
        for item in evidence:
            target = category_map.get(item.get("recommendation_category"))
            content_id = item.get("content_id")
            artist = item.get("artist")
            if target not in groups:
                continue
            if not content_id or content_id in used_content_ids:
                continue
            if content_id in disliked_tracks or artist in disliked_artists:
                continue
            if set(item.get("genre", []) or []) & disliked_genres:
                continue
            groups[target].append(_to_card(item))
            used_content_ids.add(content_id)

        if catalog_repository:
            _fill_fallback_sections(
                groups=groups,
                repository=catalog_repository,
                session_context=session_context,
                used_content_ids=used_content_ids,
                disliked_artists=disliked_artists,
                disliked_genres=disliked_genres,
            )

        taste_badges = (
            session_context.get("recent_genres", []) +
            session_context.get("recent_moods", [])
        )

        view = {
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
        }
        if APP_ENV in _DEBUG_ENVS:
            view["debug"] = {
                "session_context": session_context,
                "kag_state": kag_state,
                "rag_state": rag_state,
                "latency_ms": latency_ms,
            }
        return view


def _fill_fallback_sections(
    *,
    groups: dict[str, list],
    repository,
    session_context: dict,
    used_content_ids: set[str],
    disliked_artists: set[str],
    disliked_genres: set[str],
) -> None:
    limit = 3
    if not groups["new_release"]:
        for item in repository.find_fallback_new_releases(
            limit=limit,
            excluded_content_ids=list(used_content_ids),
            excluded_artists=list(disliked_artists),
            excluded_genres=list(disliked_genres),
        ):
            _append_fallback_item(groups["new_release"], item, used_content_ids)

    if not groups["discovery"]:
        for item in repository.find_fallback_discovery(
            limit=limit,
            preferred_genres=session_context.get("recent_genres", []),
            excluded_content_ids=list(used_content_ids),
            excluded_artists=list(disliked_artists),
            excluded_genres=list(disliked_genres),
        ):
            _append_fallback_item(groups["discovery"], item, used_content_ids)


def _append_fallback_item(target: list, item: dict, used_content_ids: set[str]) -> None:
    content_id = item.get("content_id")
    if not content_id or content_id in used_content_ids:
        return
    target.append(_to_card(item))
    used_content_ids.add(content_id)


def _to_card(item: dict) -> dict:
    normalized = {
        **item,
        "genre": item.get("genre", item.get("genres", [])),
        "mood": item.get("mood", item.get("moods", [])),
    }
    return {
        "content_id": item.get("content_id"),
        "title": item.get("title"),
        "artist": item.get("artist"),
        "album": item.get("album"),
        "genre": normalized.get("genre", []),
        "mood": normalized.get("mood", []),
        "display_reason": build_display_reason(normalized),
    }
