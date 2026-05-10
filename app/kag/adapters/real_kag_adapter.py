import logging

from app.kag.adapters.kag_adapter import KagAdapter

logger = logging.getLogger("rimas.kag.real")


class RealKagAdapter(KagAdapter):
    """Neo4j 기반 실제 KAG 어댑터. MVP 이후 구현."""

    def __init__(self, neo4j_driver=None):
        self._driver = neo4j_driver

    def build_state(self, user_id: str, user_input: str, session_context: dict) -> dict:
        # TODO: Neo4j 쿼리로 user 관계 기반 추천 방향 및 content_ids 탐색
        raise NotImplementedError("RealKagAdapter is not yet implemented")
