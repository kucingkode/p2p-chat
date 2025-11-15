import time
import threading
from ..libs.record import Record


class RegistryModel:
    registry: dict[str, Record] = {}
    lock = threading.Lock()
    _stop_event = threading.Event()

    def __init__(self):
        threading.Thread(target=self._cleanup_loop, daemon=True).start()

    def __del__(self):
        self._stop_event.set()

    def register(self, name: str, ip: str, port: int, ttl: int) -> Record:
        with self.lock:
            self.registry[name] = Record(
                name=name, ip=ip, port=port, expires_at=time.time() + ttl
            )

        print(f"[registry-model] REGISTER {name} -> {ip}:{port} (ttl={ttl})")

        return self.registry[name]

    def query(self, name: str) -> Record | None:
        with self.lock:
            record = self.registry.get(name)
            if record:
                print(f"[registry-model] QUERY {name} -> {record.ip}:{record.port}")
            return record

    def deregister(self, name: str) -> bool:
        with self.lock:
            if name in self.registry:
                del self.registry[name]
                print(f"[registry-model] DEREGISTER {name}")
                return True

            return False

    def cleanup(self):
        now = time.time()

        with self.lock:
            expired = [n for n, v in self.registry.items() if v.expires_at <= now]
            for n in expired:
                print(f"[registry-model] expired: {n}")
                del self.registry[n]

    def _cleanup_loop(self):
        while not self._stop_event.is_set():
            self.cleanup()
            time.sleep(5)
