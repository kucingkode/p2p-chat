from typing import Callable, Any, Protocol
from .responses import Response, ErrorResponse
import json

type RouteHandler = Callable[[dict, Any], Response]


class Sendable(Protocol):
    def send(self, data: bytes, address: Any):
        pass


class Router:
    handlers: dict[str, RouteHandler] = {}

    def handler(self, data: bytes, address: Any, socket: Sendable):
        try:
            payload = json.loads(data.decode())
        except Exception:
            socket.send(ErrorResponse("invalid json").dump(), address)
            return

        method = payload.get("method")
        if not method:
            socket.send(ErrorResponse("missing field 'method'").dump(), address)
            return

        del payload["method"]

        handler = self.handlers[method]
        if not handler:
            socket.send(ErrorResponse(f"unsupported method '{method}'").dump(), address)
            return

        response = handler(payload, address)
        socket.send(response.dump(), address)

    def add_route(self, method: str, handler: RouteHandler):
        self.handlers[method] = handler
