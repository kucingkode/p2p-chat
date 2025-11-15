from dataclasses import dataclass
import json

"""

Public key message structure:
[header]
length: fixed 256 bytes
---
[body]
No encryption

Advertise message structure:
[header]
length: fixed 256 bytes
---
[key]
RSA encrypted
---
[nonce]
---
[body]
AES encrypted

Conversation message structure:
[header]
length: fixed 256 bytes
---
[key]
RSA encrypted
---
[nonce]
---
[body]
AES encrypted

"""


@dataclass
class Header:
    type: str
    id: str
    sender: tuple[str, int]
    key_len: int
    nonce_len: int
    body_len: int

    def dump(self) -> bytes:
        return json.dumps(
            {
                "type": self.type,
                "id": self.id,
                "sender": self.sender,
                "key_len": self.key_len,
                "nonce_len": self.nonce_len,
                "body_len": self.body_len,
            }
        ).encode()


@dataclass
class AdvertisementBody:
    group: str
    token: str

    def dump(self) -> bytes:
        return json.dumps(
            {
                "group": self.group,
                "token": self.token,
            }
        ).encode()


@dataclass
class ConversationBody:
    sender: tuple[str, int]
    content: str
    timestamp: float
    group: str
    group_token: str

    def dump(self) -> bytes:
        return json.dumps(
            {
                "sender": self.sender,
                "content": self.content,
                "timestamp": self.timestamp,
                "group": self.group,
                "group_token": self.group_token,
            }
        ).encode()
