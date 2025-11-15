from dns_server.registry.registry_schema import (
    Request,
    RegisterRequest,
    QueryRequest,
)
from dns_server.libs.record import Record
from common.adapters.udp_adapter import UdpAdapter
from .cache_model import ICacheModel
import json


class DNSException(Exception):
    pass


class DNSClient:
    def __init__(self, host: str, port: int, cache: ICacheModel) -> None:
        self.host = host
        self.port = port
        self.adapter = UdpAdapter()
        self._cache = cache

    def register(self, name: str, port: int, ttl: int) -> Record:
        entry = self._cache.get(name)
        if entry:
            return entry

        r = Record(**self._fetch(RegisterRequest(name, port, ttl)))
        self._cache.set(r)

        return r

    def query(self, name: str) -> Record:
        res = self._fetch(QueryRequest(name))
        return Record(**res)

    def deregister(self, name: str) -> None:
        self._fetch(QueryRequest(name))
        self._cache.delete(name)

    def _fetch[T](self, request: Request):
        self.adapter.send(
            request.dump(),
            (self.host, self.port),
        )

        res = self.adapter.recv()

        payload = json.loads(res.decode())
        status = payload["status"]

        if status == "OK":
            return payload["data"]
        elif status == "ERROR":
            raise DNSException(payload["msg"])
        else:
            raise Exception(f"invalid response status, got: {status}")
