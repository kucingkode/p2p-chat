from common.utils.udp_socket import UdpSocket
from .registry.registry_model import RegistryModel
from .registry.registry_controller import RegistryController
from common.utils.router import Router
import time

HOST = "0.0.0.0"
PORT = 8080

if __name__ == "__main__":
    socket = UdpSocket()

    registry_model = RegistryModel()
    registry_controller = RegistryController(registry_model)

    router = Router()
    router.add_route("REGISTER", registry_controller.register)
    router.add_route("QUERY", registry_controller.query)
    router.add_route("DEREGISTER", registry_controller.deregister)

    socket.bind(HOST, PORT, router.handler)
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("shutting down")
            break
