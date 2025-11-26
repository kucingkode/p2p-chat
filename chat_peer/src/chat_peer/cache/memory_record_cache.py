from dns_client import RecordCache
from dns_client import Record
from ..infra.logger import Logger
import threading
import time


class MemoryRecordCache(RecordCache):
    def __init__(self, logger: Logger) -> None:
        super().__init__()
        self._cache: dict[str, Record] = {}
        self._lock = threading.Lock()
        self._logger = logger

    def set(self, record: Record):
        with self._lock:
            self._cache[record.name] = record
            self._logger.debug(f"cache set '{record.name}'")

    def get(self, name: str) -> Record | None:
        with self._lock:
            r = self._cache.get(name)

            if not r or r.expires_at <= time.time():
                self._logger.debug(f"cache miss '{name}'")
                return None

        self._logger.debug(f"cache hit '{name}'")
        return r

    def delete(self, name: str) -> None:
        with self._lock:
            del self._cache[name]
        self._logger.debug(f"cache del '{name}'")
