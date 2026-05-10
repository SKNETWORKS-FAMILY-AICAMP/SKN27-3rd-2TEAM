import logging

from app.kag.adapters.kag_adapter import KagAdapter

logger = logging.getLogger("rimas.kag.mock")


class MockKagAdapter(KagAdapter):
    def build_state(self, user_id: str, user_input: str, session_context: dict) -> dict:
        if not user_id:
            raise ValueError("user_id is required")

        primary_goal = self._decide_primary_goal(user_input)
        logger.debug(
            "kag_mock_build",
            extra={"user_id": user_id, "primary_goal": primary_goal},
        )

        category = self._decide_category(primary_goal)
        return {
            "status": "success",
            "recommendation_goal": {
                "primary_goal": primary_goal,
            },
            "recommended_content_ids": ["track_001", "track_002", "track_003"],
            "recommendation_category": category,
            "route": self._decide_route(primary_goal),
            "target_section": self._decide_target_section(category),
        }

    def _decide_primary_goal(self, user_input: str) -> str:
        text = user_input or ""
        if "왜" in text or "이유" in text:
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
