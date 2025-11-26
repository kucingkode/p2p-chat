import pytest
from common.utils.udp_socket import UdpSocket
from dns_server.registry.registry_schema import (
    RegisterRequest,
    QueryRequest,
    DeregisterRequest,
)


@pytest.mark.benchmark(group="dns_server_ops")
def test_register_latency(benchmark):
    """Measure single-register latency."""

    sock = UdpSocket(1)
    payload = RegisterRequest("test", 3000, 60)
    address = ("127.0.0.1", 8080)

    def setup():
        sock.send(DeregisterRequest("test").dump(), address)
        sock.recv()

    def one():
        sock.send(payload.dump(), address)
        sock.recv()

    benchmark.pedantic(one, setup=setup, rounds=100)


@pytest.mark.benchmark(group="dns_server_ops")
def test_query_latency(benchmark):
    """Measure single-query latency."""

    sock = UdpSocket(1)
    payload = QueryRequest("test")

    @benchmark
    def _one():
        sock.send(payload.dump(), ("127.0.0.1", 8080))
        sock.recv()


@pytest.mark.benchmark(group="dns_server_ops")
def test_deregister_latency(benchmark):
    """Measure single-query latency."""

    sock = UdpSocket(1)
    payload = DeregisterRequest("test")
    address = ("127.0.0.1", 8080)

    def setup():
        sock.send(RegisterRequest("test", 3000, 60).dump(), address)
        sock.recv()

    def one():
        sock.send(payload.dump(), address)
        sock.recv()

    benchmark.pedantic(one, setup=setup, rounds=100)
