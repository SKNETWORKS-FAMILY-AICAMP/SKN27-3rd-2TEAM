import logging
import os
import time

from app.agents.base_agent import BaseAgent
from app.rag.adapters.rag_real_adapter import RealRagAdapter
from app.rag.adapters.mock_rag_adapter import MockRagAdapter
from app.rag.adapters.rag_adapter import RagAdapter
from app.schemas.rag_input_schema import RagInputSchema

logger = logging.getLogger("rimas.agent.rag_dispatch")


class RagDispatchAgent(BaseAgent):
    """KAG_STATE를 받아 RAG_STATE(추천 근거)를 생성한다.
    Elasticsearch 기반 증거 검색 역할 — RAG_STATE만 반환하며 LLM을 직접 호출하지 않는다.
    """

    def __init__(self, rag_adapter: RagAdapter | None = None):
        self._adapter = rag_adapter or self._build_default_adapter()

    def run(
        self,
        kag_state: dict,
        user_id: str | None = None,
        session_id: str | None = None,
        request_id: str | None = None,
        intent_state: dict | None = None,
        kag_input_json: dict | None = None,
    ) -> dict:
        start = time.perf_counter()
        try:
            rag_input_json = self._build_rag_input_json(
                kag_state=kag_state,
                user_id=user_id,
                session_id=session_id,
                request_id=request_id,
                intent_state=intent_state,
                kag_input_json=kag_input_json,
            )
            rag_state = self._adapter.build_state(kag_state, rag_input_json=rag_input_json)
            ms = round((time.perf_counter() - start) * 1000, 1)
            evidence_count = len(rag_state.get("recommended_content_evidence", []))
            logger.info(
                "rag_dispatch_ok",
                extra={"evidence_count": evidence_count, "ms": ms},
            )
            return rag_state
        except Exception as exc:
            ms = round((time.perf_counter() - start) * 1000, 1)
            logger.error(
                "rag_dispatch_error",
                extra={"error": str(exc), "ms": ms},
                exc_info=True,
            )
            return {
                "status": "error",
                "error_reason": str(exc),
                "recommended_content_evidence": [],
            }

    @staticmethod
    def _build_rag_input_json(
        kag_state: dict,
        user_id: str | None,
        session_id: str | None,
        request_id: str | None,
        intent_state: dict | None,
        kag_input_json: dict | None,
    ) -> dict:
        kag_input_json = kag_input_json or {}
        query_context = kag_input_json.get("query_context", {})
        normalized_query = query_context.get("normalized_query", "")
        intent_type = (
            (intent_state or {}).get("intent_type")
            or kag_input_json.get("intent_type")
            or "personalized_recommendation"
        )
        rag_input = RagInputSchema(
            request_id=request_id or kag_input_json.get("request_id", ""),
            user_id=user_id or kag_input_json.get("user_id", ""),
            session_id=session_id or kag_input_json.get("session_id", ""),
            intent_type=intent_type,
            kag_recommended_content_ids=kag_state.get("recommended_content_ids", []),
            target_section=kag_state.get("target_section", "personalized_section"),
            query_text=normalized_query or "사용자 취향 기반 음악 추천 이유",
            evidence_need=[
                "track_description",
                "mood_reason",
                "recommendation_reason",
            ],
            retrieval_constraints={
                "max_evidence_per_track": 3,
                "require_content_id_match": True,
            },
        )
        return rag_input.model_dump()

    @staticmethod
    def _build_default_adapter() -> RagAdapter:
        mode = os.getenv("RIMAS_RAG_MODE", "mock").strip().lower()
        if mode == "real":
            return RealRagAdapter()
        return MockRagAdapter()
