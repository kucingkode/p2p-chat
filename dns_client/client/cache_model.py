from typing import Protocol
from dns_server.libs.record import Record


class ICacheModel(Protocol):
    def set(self, record: Record) -> None:
        pass

    def get(self, name: str) -> Record | None:
        pass

    def delete(self, name: str) -> None:
        pass
