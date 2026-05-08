from abc import ABC, abstractmethod


class BaseValidator(ABC):
    @abstractmethod
    def validate(self, **kwargs) -> dict:
        """{"passed": bool, "errors": list[str]} 형태로 반환한다."""
        raise NotImplementedError
