from app.kag.adapters.kag_adapter import KagAdapter
from app.kag.connection import Neo4j_Connection
from app.kag.constant import (
    primary_goal_from_user_input,
    recommendation_category_for_primary_goal,
    route_for_primary_goal,
    target_section_for_category,
)


class RealKagAdapter(KagAdapter):
    """Neo4j 기반 실제 KAG 어댑터. MVP 이후 구현."""

    def __init__(self, neo4j_connection: Neo4j_Connection | None = None):
        self._connection = neo4j_connection or Neo4j_Connection()

    def build_state(self, user_id: str, user_input: str, session_context: dict) -> dict:
        if not user_id:
            raise ValueError("user_id is required")

        primary_goal = self._decide_primary_goal(user_input)
        category = self._decide_category(primary_goal)
        recommended_content_ids = self._get_recommended_content_ids(primary_goal)

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
            "excluded_nodes": [],
            "candidate_tracks": [
                {"content_id": content_id}
                for content_id in recommended_content_ids
            ],
            "diversity_metadata": {"source": "SpotifySong_Catalog"},
        }

    def _decide_primary_goal(self, user_input: str) -> str:
        return primary_goal_from_user_input(user_input)

    def _decide_category(self, primary_goal: str) -> str:
        return recommendation_category_for_primary_goal(primary_goal)

    def _decide_route(self, primary_goal: str) -> str:
        return route_for_primary_goal(primary_goal)

    def _decide_target_section(self, category: str) -> str:
        return target_section_for_category(category)

    def _get_recommended_content_ids(self, primary_goal: str) -> list[str]:
        raise NotImplementedError("Neo4j 기반 recommended_content_ids 조회 미구현")
