from abc import ABC, abstractmethod


class KagAdapter(ABC):
    @abstractmethod
    def build_state(self, user_id: str, user_input: str, session_context: dict, limit: int = 10) -> dict:
        """Build KAG_STATE from SESSION_CONTEXT."""
