from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """모든 Agent의 마커 기반 클래스. 각 구현체가 run() 시그니처를 직접 선언한다."""

    @abstractmethod
    def run(self, **kwargs) -> dict:
        raise NotImplementedError
