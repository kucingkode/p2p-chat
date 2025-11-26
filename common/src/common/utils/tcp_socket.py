from typing import Callable, Any
import threading
import socket

type PacketHandler = Callable[[TcpSocket, Any], None]


class TcpSocket:
    _sock: socket.socket

    def __init__(self, sock: socket.socket | None = None) -> None:
        super().__init__()

        self._stop_event = threading.Event()

        if not sock:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        else:
            self._sock = sock

    def __del__(self):
        self._stop_event.set()
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except:
            pass

    def listen(self, host: str, port: int, handler: PacketHandler):
        self._sock.bind((host, port))
        self._sock.listen(5)
        threading.Thread(target=self._accept_loop, args=(handler,)).start()

    def send(self, data: bytes):
        self._sock.sendall(data)

    def connect(self, ip: str, port: int, handler: PacketHandler):
        address = (ip, int(port))
        self._sock.connect(address)
        threading.Thread(target=handler, args=(self, address)).start()

    def recv_exact(self, size=4096):
        data = b""
        while len(data) < size:
            chunk = self._sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Connection closed before full packet received")
            data += chunk
        return data

    def _accept_loop(self, handler: PacketHandler):
        while not self._stop_event.is_set():
            try:
                conn, address = self._sock.accept()
                args = (TcpSocket(sock=conn), address)
                threading.Thread(target=handler, args=args).start()
            except Exception as e:
                print("accept error:", e)
