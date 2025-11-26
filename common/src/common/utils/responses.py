from abc import ABC, abstractmethod
import json


class Response(ABC):
    status: str

    @abstractmethod
    def dump(self) -> bytes:
        pass


class OkResponse(Response):
    data: dict

    def __init__(self, data: dict = {}) -> None:
        super().__init__()
        self.status = "OK"
        self.data = data

    def dump(self) -> bytes:
        return json.dumps(
            {
                "status": self.status,
                "data": self.data or {},
            }
        ).encode()


class ErrorResponse(Response):
    msg: str

    def __init__(self, msg: str) -> None:
        super().__init__()
        self.status = "ERROR"
        self.msg = msg

    def dump(self) -> bytes:
        return json.dumps(
            {
                "status": self.status,
                "msg": self.msg,
            }
        ).encode()
