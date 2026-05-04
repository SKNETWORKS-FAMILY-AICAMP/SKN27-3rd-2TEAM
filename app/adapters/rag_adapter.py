from abc import ABC, abstractmethod


class RagAdapter(ABC):
    @abstractmethod
    def build_state(self, kag_state):
        raise NotImplementedError
