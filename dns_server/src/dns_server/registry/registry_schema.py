from common.utils.errors import ValidationError
from common.utils.requests import Request
import json


class RegisterRequest(Request):
    name: str
    port: int
    ttl: int

    def __init__(self, name: str, port: int, ttl: int):
        super().__init__()
        self.method = "REGISTER"
        self.name = name
        self.port = port
        self.ttl = ttl
        self._validate()

    def dump(self) -> bytes:
        return json.dumps(
            {
                "method": self.method,
                "name": self.name,
                "port": self.port,
                "ttl": self.ttl,
            }
        ).encode()

    def _validate(self):
        if self.port > 65535 or self.port < 0:
            raise ValidationError(f"Invalid port, got: {self.port}")


class QueryRequest(Request):
    name: str

    def __init__(self, name: str):
        super().__init__()
        self.method = "QUERY"
        self.name = name

    def dump(self) -> bytes:
        return json.dumps({"method": self.method, "name": self.name}).encode()


class DeregisterRequest(Request):
    name: str

    def __init__(self, name: str):
        super().__init__()
        self.method = "DEREGISTER"
        self.name = name

    def dump(self) -> bytes:
        return json.dumps({"method": self.method, "name": self.name}).encode()
