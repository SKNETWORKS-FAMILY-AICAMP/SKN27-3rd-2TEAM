from abc import ABC, abstractmethod


class KagAdapter(ABC):
    @abstractmethod
    def build_state(self, user_id, user_input, ml_output):
        raise NotImplementedError
