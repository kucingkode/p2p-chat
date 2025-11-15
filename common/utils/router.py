from typing import Callable, Any, Protocol
from .responses import Response, ErrorResponse
import json

type RouteHandler = Callable[[dict, Any], Response]


class Sendable(Protocol):
    def send(self, data: bytes, address: Any):
        pass


class Router:
    handlers: dict[str, RouteHandler] = {}

    def handler(self, data: bytes, address: Any, adapter: Sendable):
        try:
            payload = json.loads(data.decode())
        except Exception:
            adapter.send(ErrorResponse("invalid json").dump(), address)
            return

        method = payload.get("method")
        if not method:
            adapter.send(ErrorResponse("missing field 'method'").dump(), address)
            return

        del payload["method"]

        handler = self.handlers[method]
        if not handler:
            adapter.send(
                ErrorResponse(f"unsupported method '{method}'").dump(), address
            )
            return

        response = handler(payload, address)
        adapter.send(response.dump(), address)

    def add_route(self, method: str, handler: RouteHandler):
        self.handlers[method] = handler
