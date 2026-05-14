import logging

from app.rag.adapters.rag_adapter import RagAdapter
from app.rag.builders.rag_state_builder import RagStateBuilder
from app.rag.services.elasticsearch_retriever import ElasticsearchRagHit, ElasticsearchRagRetriever

logger = logging.getLogger("rimas.rag.real")


class RealRagAdapter(RagAdapter):
    """Elasticsearch 기반 Real RAG Adapter."""

    def __init__(self, retriever=None):
        self._retriever = retriever or ElasticsearchRagRetriever()

    def build_state(self, kag_state: dict, rag_input_json: dict | None = None) -> dict:
        rag_input_json = rag_input_json or {}
        content_ids = self._candidate_content_ids(kag_state, rag_input_json)
        query_text = str(rag_input_json.get("query_text") or "").strip()
        constraints = rag_input_json.get("retrieval_constraints", {}) or {}
        max_evidence_per_track = int(constraints.get("max_evidence_per_track", 3))

        if not content_ids:
            return self._fallback("empty_kag_candidates", query_text, content_ids)

        try:
            hits = self._retriever.search(
                query_text=query_text,
                content_ids=content_ids,
                max_evidence_per_track=max_evidence_per_track,
            )
        except Exception as exc:
            logger.warning("real_rag_retriever_error", extra={"error": str(exc)})
            return self._failed("retriever_error", query_text, content_ids, str(exc))

        evidence = self._build_evidence(hits, set(content_ids), kag_state, rag_input_json)
        if not evidence:
            return self._fallback("no_candidate_matched_evidence", query_text, content_ids)

        return RagStateBuilder.build(
            context_type=str(kag_state.get("recommendation_goal", {}).get("primary_goal", "")),
            base_context=query_text,
            source_type="elasticsearch",
            evidence=evidence,
            reason_summary="Elasticsearch evidence 기반으로 KAG 후보의 추천 근거를 구성했습니다.",
            reason_items=["KAG 후보 content_id 범위 안에서만 검색 근거를 사용했습니다."],
            query=query_text,
            normalized_query=query_text,
            retrieval_metadata={
                "source": "elasticsearch",
                "candidate_count": len(content_ids),
                "evidence_count": len(evidence),
            },
            retrieval_trace={
                "retrieval_strategy": "elasticsearch_candidate_filtered",
                "require_content_id_match": True,
                "filtered_content_ids": content_ids,
            },
        )

    @staticmethod
    def _candidate_content_ids(kag_state: dict, rag_input_json: dict) -> list[str]:
        raw_ids = (
            kag_state["recommended_content_ids"]
            if "recommended_content_ids" in kag_state
            else rag_input_json.get("kag_recommended_content_ids", [])
        )
        return [str(content_id) for content_id in raw_ids if str(content_id).strip()]

    @staticmethod
    def _build_evidence(
        hits: list[ElasticsearchRagHit],
        allowed_ids: set[str],
        kag_state: dict | None = None,
        rag_input_json: dict | None = None,
    ) -> list[dict]:
        excluded_artists, excluded_tracks = RealRagAdapter._excluded_sets(kag_state or {})
        target_section = (rag_input_json or {}).get("target_section", "personalized_section")
        evidence = []
        for hit in hits:
            if hit.content_id not in allowed_ids:
                continue
            if hit.content_id in excluded_tracks or hit.artist in excluded_artists:
                continue
            evidence.append(
                {
                    "content_id": hit.content_id,
                    "title": hit.title,
                    "artist": hit.artist,
                    "album": hit.album,
                    "genre": hit.genre,
                    "mood": hit.mood,
                    "evidence_summary": hit.content,
                    "release_type": hit.release_type,
                    "recommendation_category": RealRagAdapter._recommendation_category(hit, target_section),
                    "retrieval_score": hit.score,
                }
            )
        return evidence

    @staticmethod
    def _excluded_sets(kag_state: dict) -> tuple[set[str], set[str]]:
        excluded_artists = set()
        excluded_tracks = set()
        for node in kag_state.get("excluded_nodes", []) or []:
            value = node.get("value")
            if not value:
                continue
            if node.get("type") == "artist":
                excluded_artists.add(value)
            if node.get("type") == "track":
                excluded_tracks.add(value)
        return excluded_artists, excluded_tracks

    @staticmethod
    def _recommendation_category(hit: ElasticsearchRagHit, target_section: str) -> str:
        if hit.release_type == "new_release":
            return "new_release"
        if target_section == "discovery_section":
            return "discovery_candidate"
        if target_section == "new_release_section":
            return "new_release"
        return "personalized_match"

    @staticmethod
    def _fallback(reason: str, query_text: str, content_ids: list[str]) -> dict:
        state = RagStateBuilder.failure(reason)
        state["status"] = "fallback"
        state["query"] = query_text
        state["normalized_query"] = query_text
        state["retrieval_metadata"] = {
            "source": "elasticsearch",
            "reason": reason,
            "candidate_count": len(content_ids),
            "evidence_count": 0,
        }
        state["retrieval_trace"] = {
            "retrieval_strategy": "elasticsearch_candidate_filtered",
            "require_content_id_match": True,
            "filtered_content_ids": content_ids,
        }
        return state

    @staticmethod
    def _failed(reason: str, query_text: str, content_ids: list[str], error: str) -> dict:
        state = RagStateBuilder.failure(reason)
        state["status"] = "failed"
        state["query"] = query_text
        state["normalized_query"] = query_text
        state["retrieval_metadata"] = {
            "source": "elasticsearch",
            "reason": reason,
            "candidate_count": len(content_ids),
            "evidence_count": 0,
        }
        state["retrieval_trace"] = {
            "retrieval_strategy": "elasticsearch_candidate_filtered",
            "require_content_id_match": True,
            "filtered_content_ids": content_ids,
            "error": error,
        }
        return state
