from dataclasses import dataclass


@dataclass
class Record:
    name: str
    ip: str
    port: int
    expires_at: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "expires_at": self.expires_at,
        }
