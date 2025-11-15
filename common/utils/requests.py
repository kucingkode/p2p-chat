from abc import ABC, abstractmethod


class Request(ABC):
    method: str

    @abstractmethod
    def dump(self) -> bytes:
        pass
