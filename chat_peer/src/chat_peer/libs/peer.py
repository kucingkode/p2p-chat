from dataclasses import dataclass, field
from common.utils.tcp_socket import TcpSocket
from ..libs.crypto import rsa
import time


@dataclass
class Peer:
    address: tuple[str, int]
    conn: TcpSocket | None = None
    public_key: rsa.RSAPublicKey | None = None
    public_key_sent: bool = False
    groups: list[str] = field(default_factory=list)

    def wait_public_key(self):
        while not self.public_key:
            pass
