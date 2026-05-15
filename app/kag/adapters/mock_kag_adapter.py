import logging

from app.kag.adapters.kag_adapter import KagAdapter

logger = logging.getLogger("rimas.kag.mock")


class MockKagAdapter(KagAdapter):
    def build_state(self, user_id: str, user_input: str, session_context: dict, limit: int = 10) -> dict:
        if not user_id:
            raise ValueError("user_id is required")

        primary_goal = self._decide_primary_goal(user_input)
        logger.debug(
            "kag_mock_build",
            extra={"user_id": user_id, "primary_goal": primary_goal},
        )

        category = self._decide_category(primary_goal)
        excluded_nodes = self._build_excluded_nodes(session_context or {})
        candidates = self._filter_candidates(self._mock_candidates(), excluded_nodes)[: self._normalize_limit(limit)]
        recommended_content_ids = [candidate["content_id"] for candidate in candidates]
        return {
            "status": "success",
            "recommendation_goal": {
                "primary_goal": primary_goal,
            },
            "recommended_content_ids": recommended_content_ids,
            "recommendation_category": category,
            "route": self._decide_route(primary_goal),
            "target_section": self._decide_target_section(category),
            "traversal_reason": f"mock traversal for {primary_goal}",
            "matched_nodes": [],
            "excluded_nodes": excluded_nodes,
            "candidate_tracks": candidates,
            "diversity_metadata": {"source": "mock"},
        }

    @staticmethod
    def _mock_candidates() -> list[dict]:
        return [
            {"content_id": "track_001", "artist": "Nova Lane", "genre": ["rnb", "indie"]},
            {"content_id": "track_002", "artist": "Luna Field", "genre": ["dream_pop", "ambient"]},
            {"content_id": "track_003", "artist": "Mira Tone", "genre": ["pop", "electro_pop"]},
        ]

    @staticmethod
    def _normalize_limit(limit: int) -> int:
        try:
            parsed = int(limit)
        except (TypeError, ValueError):
            parsed = 10
        return max(1, min(parsed, 50))

    @staticmethod
    def _build_excluded_nodes(session_context: dict) -> list[dict]:
        nodes = []
        for artist in session_context.get("disliked_artists", []) or []:
            if artist:
                nodes.append({"type": "artist", "value": artist})
        for track in session_context.get("disliked_tracks", []) or []:
            if track:
                nodes.append({"type": "track", "value": track})
        for genre in session_context.get("disliked_genres", []) or []:
            if genre:
                nodes.append({"type": "genre", "value": genre})
        return nodes

    @staticmethod
    def _filter_candidates(candidates: list[dict], excluded_nodes: list[dict]) -> list[dict]:
        excluded_artists = {node["value"] for node in excluded_nodes if node.get("type") == "artist"}
        excluded_tracks = {node["value"] for node in excluded_nodes if node.get("type") == "track"}
        excluded_genres = {node["value"] for node in excluded_nodes if node.get("type") == "genre"}
        return [
            candidate
            for candidate in candidates
            if candidate.get("content_id") not in excluded_tracks
            and candidate.get("artist") not in excluded_artists
            and not (set(candidate.get("genre", [])) & excluded_genres)
        ]

    def _decide_primary_goal(self, user_input: str) -> str:
        text = user_input or ""
        if "이유" in text or "왜" in text:
            return "recommendation_reason_question"
        if "최신" in text or "새로 나온" in text or "신곡" in text:
            return "new_release_recommendation"
        if "비슷" in text:
            return "similar_taste_recommendation"
        if "취향" in text or "새로운" in text:
            return "new_taste_discovery"
        return "personalized_recommendation"

    def _decide_category(self, primary_goal: str) -> str:
        if primary_goal == "new_release_recommendation":
            return "new_release"
        if primary_goal == "new_taste_discovery":
            return "discovery_candidate"
        return "personalized_match"

    def _decide_route(self, primary_goal: str) -> str:
        if primary_goal == "new_release_recommendation":
            return "new_release"
        if primary_goal == "new_taste_discovery":
            return "safe_discovery"
        return "personalized"

    def _decide_target_section(self, category: str) -> str:
        if category == "new_release":
            return "new_release_section"
        if category == "discovery_candidate":
            return "discovery_section"
        return "personalized_section"
