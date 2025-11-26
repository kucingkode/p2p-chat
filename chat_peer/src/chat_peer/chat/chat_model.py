from typing import Callable

import json
import time
import uuid
import secrets
import threading
from common.utils.tcp_socket import TcpSocket
from ..infra.logger import Logger
from .chat_schema import Header, ConversationBody, AdvertisementBody
from ..libs.group import Group
from ..libs.peer import Peer
from ..libs.message import Message
from ..libs.crypto import (
    public_key_from_json,
    public_key_to_json,
    rsa_encrypt,
    rsa_decrypt,
    generate_aes_key,
    aes_decrypt,
    aes_encrypt,
    rsa,
)


HEADER_SIZE = 256

type Address = tuple[str, int]


def address_str(address: Address):
    return f"{address[0]}:{address[1]}"


def eq_address(a: Address, b: Address):
    return a[0] == b[0] and a[1] == b[1]


class ChatModel:

    def __init__(
        self,
        logger: Logger,
        host: str,
        port: int,
        private_key: rsa.RSAPrivateKey,
        public_key: rsa.RSAPublicKey,
    ) -> None:
        self._logger = logger
        self._address = (host, port)
        self._public_key = public_key
        self._private_key = private_key
        self._groups: dict[str, Group] = {}
        self._peers: dict[str, Peer] = {}
        self._seen: set[str] = set[str]()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def __del__(self):
        self._stop_event.set()

    # ===================================
    # PUBLIC
    # ===================================

    def create_group(self, name: str):
        if name in self._groups:
            raise Exception("Group already exist")

        token = secrets.token_hex(16)
        group = Group(name, token, [], [])
        self._groups[name] = group

        self._logger.debug(f"group created '{name}'")

        return group

    def advertise_group(self, group_name: str, dest: Address):
        group = self._groups[group_name]
        if not group:
            raise Exception(f"Unknown group '{group_name}'")

        peer = self._get_peer(dest)
        if not peer.conn:
            peer.conn = self._initiate_connection(peer)

        group.peers.append(peer)

        body = AdvertisementBody(group.name, group.token).dump()
        msg = self._create_message("ADVERTISEMENT", body, peer.public_key)

        peer.conn.send(msg)

        self._logger.debug(f"-> ADVERTISEMENT to {address_str(peer.address)}")

    def send(self, group_name: str, content: str):
        group = self._groups.get(group_name)
        if not group:
            raise Exception(f"Unknown group '{group_name}'")

        for peer in group.peers:
            if not peer.conn or not peer.public_key:
                continue

            ts = time.time()
            body = ConversationBody(
                sender=self._address,
                content=content,
                timestamp=ts,
                group=group.name,
                group_token=group.token,
            ).dump()

            msg = self._create_message("CONVERSATION", body, peer.public_key)
            peer.conn.send(msg)

            chat_msg = Message(self._address, content, ts, ts)
            self._insert_message(group_name, chat_msg)

            self._logger.debug(f"-> CONVERSATION to {address_str(peer.address)}")

    def listen(self):
        tcp = TcpSocket()
        tcp.listen(self._address[0], self._address[1], self._handler)

    # ===================================
    # PRIVATE
    # ===================================

    def _insert_message(self, group_name: str, message: Message):
        group = self._groups[group_name]

        i = len(group.messages)
        while i > 0 and group.messages[i - 1].sent_at > message.sent_at:
            i -= 1

        group.messages.insert(i, message)

    def _forward(
        self,
        group: Group,
        header: Header,
        key: bytes,
        nonce: bytes,
        body: bytes,
    ):
        if not group:
            raise Exception(f"Unknown group '{group}'")

        for peer in group.peers:
            if not peer.conn or not peer.public_key:
                continue

            if eq_address(peer.address, header.sender):
                continue

            new_key = rsa_encrypt(peer.public_key, key)
            header.key_len = len(new_key)

            peer.conn.send(
                header.dump().ljust(HEADER_SIZE, b" ") + new_key + nonce + body
            )

            self._logger.debug(
                f"forwarded CONVERSATION ({address_str(header.sender)} -> {address_str(peer.address)})"
            )

    def _handler(self, conn: TcpSocket, _):
        while not self._stop_event.is_set():
            # Get header
            header_bytes = conn.recv_exact(256)
            header = Header(**json.loads(header_bytes.decode()))

            # Get and decrypt key
            key: bytes | None = None
            if header.key_len:
                key = conn.recv_exact(header.key_len)
                key = rsa_decrypt(self._private_key, key)

            # Get nonce
            nonce: bytes | None = None
            if header.nonce_len:
                nonce = conn.recv_exact(header.nonce_len)

            # Get and decrypt body
            body_bytes = conn.recv_exact(header.body_len)
            body_bytes_unmodified = body_bytes
            if key and nonce:
                body_bytes = aes_decrypt(key, nonce, body_bytes)

            # Ignore if seen
            if header.id in self._seen:
                continue
            else:
                self._seen.add(header.id)

            # Get peer
            peer = self._get_peer(header.sender)

            # self._logger.debug(peer)

            if header.type == "PING":
                pong = self._create_message("PONG", b"")
                conn.send(pong)

            if header.type == "PUBLIC_KEY":
                peer.conn = conn
                with self._lock:
                    peer.public_key = public_key_from_json(body_bytes.decode())
                self._exchange_public_key(peer)

                self._logger.debug(f"<- PUBLIC_KEY from {address_str(header.sender)}")

            elif header.type == "ADVERTISEMENT":
                if not key or not nonce:
                    continue

                body = AdvertisementBody(**json.loads(body_bytes.decode()))
                self._groups[body.group] = Group(body.group, body.token, [peer])

                self._logger.debug(
                    f"<- ADVERTISEMENT from {address_str(header.sender)}"
                )

            elif header.type == "CONVERSATION":
                if not key or not nonce:
                    continue

                body = ConversationBody(**json.loads(body_bytes.decode()))

                group = self._groups[body.group]
                if not group:
                    continue

                if body.group_token != group.token:
                    continue

                msg = Message(
                    sender=body.sender,
                    content=body.content,
                    received_at=time.time(),
                    sent_at=body.timestamp,
                )

                group.messages.append(msg)
                self._logger.debug(f"<- CONVERSATION from {address_str(header.sender)}")

                self._forward(
                    group=group,
                    header=header,
                    key=key,
                    nonce=nonce,
                    body=body_bytes_unmodified,
                )
            else:
                pass

    def _initiate_connection(self, peer: Peer):
        conn = TcpSocket()
        conn.connect(peer.address[0], peer.address[1], self._handler)

        peer.conn = conn
        self._exchange_public_key(peer)
        peer.wait_public_key()

        return conn

    def _exchange_public_key(self, peer: Peer):
        if not peer.conn:
            raise Exception("Peer have no connection")

        if not peer.public_key_sent:
            peer.public_key_sent = True
            public_key = public_key_to_json(self._public_key).encode()
            msg = self._create_message("PUBLIC_KEY", public_key)
            peer.conn.send(msg)

            self._logger.debug(f"-> PUBLIC_KEY to {address_str(peer.address)}")

        peer.wait_public_key()

    def _create_message(
        self,
        type: str,
        body: bytes,
        public_key: rsa.RSAPublicKey | None = None,
    ):

        if public_key:
            aes_key = generate_aes_key()
            key = rsa_encrypt(public_key, aes_key)

            nonce, body = aes_encrypt(aes_key, body)
        else:
            key = bytes()
            nonce = bytes()

        id = uuid.uuid4().hex
        header = Header(
            type=type,
            id=id,
            sender=self._address,
            key_len=len(key),
            nonce_len=len(nonce),
            body_len=len(body),
        ).dump()

        self._seen.add(id)

        if len(header) > HEADER_SIZE:
            raise Exception("Header JSON too large")

        return header.ljust(HEADER_SIZE, b" ") + key + nonce + body

    def _get_peer(self, address: tuple[str, int]) -> Peer:
        key = address_str(address)

        with self._lock:
            peer = self._peers.get(key)

            # Save peer if not saved yet
            if not peer:
                peer = Peer(
                    address=address,
                    groups=[],
                )

                self._peers[key] = peer

        return peer
