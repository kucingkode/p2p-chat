from dataclasses import dataclass


@dataclass
class Message:
    sender: tuple[str, int]
    content: str
    sent_at: float
    received_at: float
