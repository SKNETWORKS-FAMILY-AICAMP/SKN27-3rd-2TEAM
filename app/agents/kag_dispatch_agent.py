import logging
import os
import time

from app.agents.base_agent import BaseAgent
from app.kag.adapters.kag_adapter import KagAdapter
from app.kag.adapters.mock_kag_adapter import MockKagAdapter

logger = logging.getLogger("rimas.agent.kag_dispatch")


class KagDispatchAgent(BaseAgent):
    """SESSION_CONTEXT를 받아 KAG_STATE를 생성한다.
    Neo4j 기반 추천 방향 탐색 역할 — KAG_STATE만 반환하며 RAG/LLM을 직접 호출하지 않는다.
    """

    def __init__(self, kag_adapter: KagAdapter | None = None):
        self._adapter = kag_adapter or self._build_default_adapter()

    def run(
        self,
        user_id: str,
        user_input: str,
        session_context: dict,
        kag_input_json: dict | None = None,
    ) -> dict:
        start = time.perf_counter()
        try:
            normalized_input = (
                (kag_input_json or {})
                .get("query_context", {})
                .get("normalized_query", user_input)
            )
            constraints = (kag_input_json or {}).get("constraints", {})
            adapter_context = self._merge_constraint_exclusions(session_context, constraints)
            adapter_context = self._merge_query_context(adapter_context, (kag_input_json or {}).get("query_context", {}))
            kag_state = self._adapter.build_state(
                user_id,
                normalized_input,
                adapter_context,
                limit=constraints.get("max_candidates", 10),
            )
            ms = round((time.perf_counter() - start) * 1000, 1)
            logger.info(
                "kag_dispatch_ok",
                extra={
                    "user_id": user_id,
                    "primary_goal": kag_state.get("recommendation_goal", {}).get("primary_goal"),
                    "ms": ms,
                },
            )
            return kag_state
        except Exception as exc:
            ms = round((time.perf_counter() - start) * 1000, 1)
            logger.error(
                "kag_dispatch_error",
                extra={"user_id": user_id, "error": str(exc), "ms": ms},
                exc_info=True,
            )
            return {"status": "error", "error_reason": str(exc)}

    @staticmethod
    def _build_default_adapter() -> KagAdapter:
        mode = os.getenv("RIMAS_KAG_MODE", "mock").strip().lower()
        if mode == "real":
            from app.kag.adapters.real_kag_adapter import RealKagAdapter

            return RealKagAdapter()
        return MockKagAdapter()

    @staticmethod
    def _merge_constraint_exclusions(session_context: dict, constraints: dict) -> dict:
        merged_context = dict(session_context or {})
        field_map = {
            "excluded_artists": "disliked_artists",
            "excluded_tracks": "disliked_tracks",
            "excluded_genres": "disliked_genres",
        }
        for source_field, target_field in field_map.items():
            merged_context[target_field] = KagDispatchAgent._merge_unique(
                constraints.get(source_field, []),
                merged_context.get(target_field, []),
            )
        return merged_context

    @staticmethod
    def _merge_query_context(session_context: dict, query_context: dict) -> dict:
        merged_context = dict(session_context or {})
        merged_context["artist_candidates"] = KagDispatchAgent._merge_unique(
            query_context.get("artist_candidates", []),
            merged_context.get("artist_candidates", []),
        )
        return merged_context

    @staticmethod
    def _merge_unique(new_items: list, existing_items: list) -> list[str]:
        merged = []
        seen = set()
        for value in list(new_items or []) + list(existing_items or []):
            text = str(value).strip()
            if text and text not in seen:
                seen.add(text)
                merged.append(text)
        return merged
