import logging

from app.rag.adapters.rag_adapter import RagAdapter

logger = logging.getLogger("rimas.rag.real")


class RealRagAdapter(RagAdapter):
    """Elasticsearch 기반 실제 RAG 어댑터. MVP 이후 구현.

    Real RAG Flow:
      RealRagAdapter → RetrievalOrchestrator → MetadataRetriever + VectorRetriever
        → Reranker → RagStateBuilder + RetrievalTraceBuilder → ContractValidator
    """

    def __init__(self, es_client=None):
        self._es = es_client

    def build_state(self, kag_state: dict, rag_input_json: dict | None = None) -> dict:
        # TODO: Elasticsearch Hybrid Retrieval + Reranking 구현
        raise NotImplementedError("RealRagAdapter is not yet implemented")
