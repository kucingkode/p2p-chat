import time
import threading
from ..libs.record import Record
import json
import os


class RegistryModel:
    registry: dict[str, Record] = {}
    lock = threading.Lock()
    _stop_event = threading.Event()

    def __init__(self):
        threading.Thread(target=self._cleanup_loop, daemon=True).start()
        self._load()

    def __del__(self):
        self._stop_event.set()

    def register(self, name: str, ip: str, port: int, ttl: int) -> Record:
        with self.lock:
            self.registry[name] = Record(
                name=name, ip=ip, port=port, expires_at=time.time() + ttl
            )
            self._save()

        # print(f"[registry-model] REGISTER {name} -> {ip}:{port} (ttl={ttl})")

        return self.registry[name]

    def query(self, name: str) -> Record | None:
        with self.lock:
            record = self.registry.get(name)
            # if record:
            #     print(f"[registry-model] QUERY {name} -> {record.ip}:{record.port}")
            # else:
            #     print(f"[registry-model] QUERY {name} -> NOT FOUND")
            return record

    def deregister(self, name: str) -> bool:
        with self.lock:
            if name in self.registry:
                del self.registry[name]
                self._save()
                # print(f"[registry-model] DEREGISTER {name} -> OK")
                return True
            else:
                # print(f"[registry-model] DEREGISTER {name} -> NOT FOUND")
                return False

    def _cleanup(self):
        now = time.time()

        with self.lock:
            expired = [n for n, v in self.registry.items() if v.expires_at <= now]
            for n in expired:
                # print(f"[registry-model] expired: {n}")
                del self.registry[n]

    def _load(self):
        if not os.path.exists("registry.json"):
            return

        with open("registry.json", "r") as f:
            data = json.load(f)

        print(data)

        for k, v in data.items():
            self.registry[k] = Record(**v)

    def _save(self):
        data = {}

        for k, v in self.registry.items():
            data[k] = v.to_dict()

        with open("registry.json", "w") as f:
            json.dump(data, f)

    def _cleanup_loop(self):
        while not self._stop_event.is_set():
            self._cleanup()
            time.sleep(5)
            self._save()
