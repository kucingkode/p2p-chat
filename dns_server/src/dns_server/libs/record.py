from dataclasses import dataclass, asdict
import json


@dataclass
class Record:
    name: str
    ip: str
    port: int
    expires_at: float

    def to_dict(self) -> dict:
        return asdict(self)
