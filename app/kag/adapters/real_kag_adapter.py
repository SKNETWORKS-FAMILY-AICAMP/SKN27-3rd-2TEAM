from app.kag.adapters.execute_querys import execute_kag_track_ids
from app.kag.adapters.kag_adapter import KagAdapter
from app.kag.connection import Neo4j_Connection
from app.kag.constant import KagSessionInput


class RealKagAdapter(KagAdapter):
    """Neo4j 기반 실제 KAG 어댑터. MVP 이후 구현."""

    def __init__(self, neo4j_connection: Neo4j_Connection | None = None):
        self._connection = neo4j_connection or Neo4j_Connection()

    def build_state(self, user_id: str, user_input: str, session_context: dict) -> dict:
        if not user_id:
            raise ValueError("user_id is required")

        _session_context = KagSessionInput(session_context)
        _primary_goal = _session_context.primary_goal()
        _category = _session_context.recommendation_category()
        _recommended_content_ids = self._get_recommended_content_ids(_primary_goal, session_context)

        return {
            "status": "success",
            "recommendation_goal": {
                "primary_goal": _primary_goal,
            },
            "recommended_content_ids": _recommended_content_ids,
            "recommendation_category": _category,
            "route": _session_context.route(),
            "target_section": _session_context.target_section(),
            "traversal_reason": f"mock traversal for {_primary_goal}",
            "matched_nodes": [],
            "excluded_nodes": [],
            "candidate_tracks": [
                {"content_id": content_id}
                for content_id in _recommended_content_ids
            ],
            "diversity_metadata": {"source": "SpotifySong_Catalog"},
        }

    def _get_recommended_content_ids(self, primary_goal: str, session_context: dict) -> list[str]:
        return execute_kag_track_ids(primary_goal, session_context, self._connection)
