from typing import Callable, Any
import threading
import socket

type PacketHandler = Callable[[bytes, Any, UdpSocket]]


class UdpSocket:

    def __init__(self, timeout: float | None = None) -> None:
        super().__init__()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._stop_event = threading.Event()
        self._sock.settimeout(timeout)

    def __del__(self):
        self._stop_event.set()
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except:
            pass

    def bind(self, host: str, port: int, handler: PacketHandler):
        self._sock.bind((host, port))
        threading.Thread(target=self._recv_loop, args=(self._sock, handler)).start()

        print(f"[udp-socket] listening {host}:{port}")

    def send(self, data: bytes, address: Any):
        self._sock.sendto(data, address)

    def recv(self, bufsize: int = 4096) -> bytes:
        resp, _ = self._sock.recvfrom(bufsize)
        return resp

    def _recv_loop(self, sock: socket.socket, handler: PacketHandler):
        while not self._stop_event.is_set():
            try:
                data, address = sock.recvfrom(4096)
                args = (data, address, self)
                threading.Thread(target=handler, args=args).start()
            except Exception as e:
                print("error:", e)
