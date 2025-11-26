import pytest
from chat_peer.infra.logger import create_logger
from chat_peer.libs.crypto import generate_rsa_keypair
from chat_peer.chat.chat_model import ChatModel


def create_peer(name: str, port: int):
    private_key, public_key = generate_rsa_keypair()
    model = ChatModel(create_logger(name), "127.0.0.1", port, private_key, public_key)
    model.listen()

    return model


@pytest.mark.benchmark(group="peer_ops")
def test_advertise_latency(benchmark):

    peer1 = create_peer("peer-1", 8081)
    peer2 = create_peer("peer-2", 8082)

    peer1.create_group("group")

    @benchmark
    def _one():
        peer1.advertise_group("group", ("127.0.0.1", 8082))

    del peer1
    del peer2


@pytest.mark.benchmark(group="peer_ops")
def test_conversation_latency(benchmark):
    peer3 = create_peer("peer-3", 8083)
    peer4 = create_peer("peer-4", 8084)

    peer3.create_group("group")
    peer3.advertise_group("group", ("127.0.0.1", 8084))

    @benchmark
    def _one():
        peer3.send("group", "content")

    del peer3
    del peer4
