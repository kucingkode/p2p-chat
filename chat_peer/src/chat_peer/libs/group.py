from dataclasses import dataclass, field
from .peer import Peer
from .message import Message


@dataclass
class Group:
    name: str
    token: str
    peers: list[Peer] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
