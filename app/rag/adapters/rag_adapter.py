from abc import ABC, abstractmethod


class RagAdapter(ABC):
    @abstractmethod
    def build_state(self, kag_state: dict, rag_input_json: dict | None = None) -> dict:
        """KAG_STATE와 RAG_INPUT_JSON을 기반으로 RAG_STATE를 생성한다."""
