from .registry_model import RegistryModel
from .registry_schema import RegisterRequest, QueryRequest
from common.utils.responses import Response, OkResponse, ErrorResponse


class RegistryController:
    def __init__(self, model: RegistryModel) -> None:
        self.model = model

    def register(self, payload: dict, addr: str) -> Response:
        try:
            req = RegisterRequest(**payload)
            record = self.model.register(req.name, addr[0], req.port, req.ttl)
        except Exception as e:
            return ErrorResponse(repr(e))

        return OkResponse(record.to_dict())

    def query(self, payload: dict, _) -> Response:
        try:
            req = QueryRequest(**payload)
            record = self.model.query(req.name)
            if not record:
                raise Exception("Not found")
        except Exception as e:
            return ErrorResponse(repr(e))

        return OkResponse(record.to_dict())

    def deregister(self, payload: dict, _) -> Response:
        try:
            req = RegisterRequest(**payload)
            ok = self.model.deregister(req.name)
            if not ok:
                raise Exception("Not found")
        except Exception as e:
            return ErrorResponse(repr(e))

        return OkResponse()
