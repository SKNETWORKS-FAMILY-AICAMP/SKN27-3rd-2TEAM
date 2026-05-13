from app.kag.adapters.kag_adapter import KagAdapter


class RealKagAdapter(KagAdapter):
    """Neo4j 기반 실제 KAG 어댑터. MVP 이후 구현."""

    def build_state(self, user_id: str, user_input: str, session_context: dict) -> dict:
        if not user_id:
            raise ValueError("user_id is required")
