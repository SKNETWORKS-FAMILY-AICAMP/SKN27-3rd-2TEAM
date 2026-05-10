import logging
import time

from app.agents.base_agent import BaseAgent
from app.rag.adapters.mock_rag_adapter import MockRagAdapter
from app.rag.adapters.rag_adapter import RagAdapter

logger = logging.getLogger("rimas.agent.rag_dispatch")


class RagDispatchAgent(BaseAgent):
    """KAG_STATE를 받아 RAG_STATE(추천 근거)를 생성한다.
    Elasticsearch 기반 증거 검색 역할 — RAG_STATE만 반환하며 LLM을 직접 호출하지 않는다.
    """

    def __init__(self, rag_adapter: RagAdapter | None = None):
        self._adapter = rag_adapter or MockRagAdapter()

    def run(self, kag_state: dict) -> dict:
        start = time.perf_counter()
        try:
            rag_state = self._adapter.build_state(kag_state)
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
