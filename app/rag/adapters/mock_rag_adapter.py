import logging

from app.rag.adapters.rag_adapter import RagAdapter
from app.rag.builders.rag_state_builder import RagStateBuilder

logger = logging.getLogger("rimas.rag.mock")


class MockRagAdapter(RagAdapter):
    """
    MusicCatalogRepository 없이 고정 목 데이터로 RAG_STATE를 반환한다.
    실제 DB 연결 없이 전체 Agent 흐름 검증용.
    """

    def build_state(self, kag_state: dict, rag_input_json: dict | None = None) -> dict:
        if not kag_state:
            raise ValueError("kag_state is required")

        primary_goal = kag_state.get("recommendation_goal", {}).get("primary_goal", "")
        genres = kag_state.get("user_context", {}).get("base_preference", {}).get("genres", [])
        moods = kag_state.get("user_context", {}).get("base_preference", {}).get("moods", [])

        logger.debug("rag_mock_build", extra={"primary_goal": primary_goal})

        evidence = self._filter_excluded(
            self._mock_evidence(genres, moods),
            kag_state.get("excluded_nodes", []),
        )
        query = (rag_input_json or {}).get("query_text", "")
        return RagStateBuilder.build(
            context_type=primary_goal,
            base_context=f"{'/'.join(genres)} 취향과 {'/'.join(moods)} 분위기를 기준으로 추천 근거를 제공한다.",
            source_type="mock_catalog",
            evidence=evidence,
            reason_summary="기존 개인화 추천을 기준으로 최신곡과 안전한 취향 탐색 후보를 함께 구성했다.",
            reason_items=[
                f"{'/'.join(genres)} 취향과 연결되는 곡을 포함했다.",
                f"{'/'.join(moods)} 분위기를 유지하면서 확장 가능한 곡을 포함했다.",
                "최근 업데이트된 곡 중 기존 취향과 일부 맞는 곡을 포함했다.",
            ],
            query=query,
            normalized_query=query,
            retrieval_metadata={},
            retrieval_trace={},
        )

    @staticmethod
    def _mock_evidence(genres: list, moods: list) -> list:
        g = genres or ["rnb", "indie"]
        m = moods or ["calm", "night"]
        return [
            {
                "content_id": "track_001",
                "title": "Midnight Loop",
                "artist": "Nova Lane",
                "album": "Night Sketch",
                "genre": g,
                "mood": m,
                "tempo": "medium",
                "release_type": "existing_catalog",
                "recommendation_category": "personalized_match",
                "evidence_summary": f"기존 {'/'.join(g)} 취향과 {'/'.join(m)} 분위기에 직접 연결되는 곡이다.",
                "match_reason": {"genre_match": True, "mood_match": True, "new_taste_expansion": False},
            },
            {
                "content_id": "track_002",
                "title": "Soft Orbit",
                "artist": "Luna Field",
                "album": "Orbit Notes",
                "genre": ["dream_pop", "ambient"],
                "mood": m,
                "tempo": "slow",
                "release_type": "existing_catalog",
                "recommendation_category": "discovery_candidate",
                "evidence_summary": f"{'/'.join(m)} 분위기를 유지하면서 dream pop 계열로 넓혀볼 수 있는 곡이다.",
                "match_reason": {"genre_match": False, "mood_match": True, "new_taste_expansion": True},
            },
            {
                "content_id": "track_003",
                "title": "Fresh Signal",
                "artist": "Mira Tone",
                "album": "Updated Signal",
                "genre": ["indie", "electro_pop"],
                "mood": ["bright", "clean"],
                "tempo": "medium",
                "release_type": "new_release",
                "recommendation_category": "new_release",
                "evidence_summary": "최근 업데이트된 곡 중 indie 선호와 일부 연결되는 곡이다.",
                "match_reason": {"genre_match": True, "mood_match": False, "new_taste_expansion": True},
            },
        ]

    @staticmethod
    def _filter_excluded(evidence: list[dict], excluded_nodes: list[dict]) -> list[dict]:
        excluded_artists = {node["value"] for node in excluded_nodes if node.get("type") == "artist"}
        excluded_tracks = {node["value"] for node in excluded_nodes if node.get("type") == "track"}
        return [
            item
        for item in evidence
        if item.get("content_id") not in excluded_tracks
        and item.get("artist") not in excluded_artists
        and not (set(item.get("genre", [])) & {node["value"] for node in excluded_nodes if node.get("type") == "genre"})
        ]
