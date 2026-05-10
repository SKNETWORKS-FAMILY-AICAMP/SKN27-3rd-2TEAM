from abc import ABC, abstractmethod


class RagAdapter(ABC):
    @abstractmethod
    def build_state(self, kag_state: dict) -> dict:
        """KAG_STATE를 기반으로 RAG_STATE를 생성한다."""
