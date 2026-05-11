from abc import ABC, abstractmethod


class KagAdapter(ABC):
    @abstractmethod
    def build_state(self, user_id: str, user_input: str, session_context: dict) -> dict:
        """SESSION_CONTEXT를 기반으로 KAG_STATE를 생성한다."""
