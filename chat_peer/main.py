from typing import cast
import time
import threading

from textual import on
from textual.binding import Binding
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import (
    Button,
    Input,
    Select,
    TabbedContent,
    TabPane,
    Log,
    Tree,
    Markdown,
)

from .libs.message import Message
from .cache.cache_model import CacheModel
from dns_client import DNSClient
from .chat.chat_model import ChatModel
from .infra.logger import create_logger
from .libs.crypto import generate_rsa_keypair

help = """
available commands:
dns           Connect to DNS server
query         Query name from DNS server
register      Register name to DNS server
deregister    Deregister name from DNS server
listen        Bind chat peer to network socket
create-group  Create new chat group
advertise     Advertise chat group to other peer
sync          Sync UI with peer state
"""


class MainApp(App):
    CSS_PATH = "main.tcss"
    TITLE = "P2P Gossip Chat CLI"

    BINDINGS = [Binding("ctrl+x", "execute", "Execute", priority=True)]

    def compose(self) -> ComposeResult:
        self.theme = "nord"
        self.cache = CacheModel(create_logger("cache-model"))
        self.chat_model: ChatModel | None = None
        self.dns: DNSClient | None = None
        self.log_display = ""
        self.message_idx = 0

        with TabbedContent(initial="chat"):
            with TabPane("Chat", id="chat"):
                yield Container(
                    Select([]),
                    id="chat-group-select",
                )
                yield Log(highlight=False, id="chat-log")
                yield Container(
                    Input("", "Enter your message...", id="msg-input"),
                    Button("Send", id="send-msg", variant="primary"),
                    classes="input",
                )
            with TabPane("Peers", id="peers"):
                yield Tree("Peers")
            with TabPane("Control", id="control"):
                yield Log(highlight=True, id="control-log")
                yield Container(
                    Input("", "Enter your command...", id="cmd-input"),
                    Button("Run", id="send-cmd", variant="primary"),
                    classes="input",
                )

    def on_mount(self):
        threading.Thread(target=self.update_chat, daemon=True).start()

    def action_execute(self) -> None:
        tab = self.query_one(TabbedContent)

        match tab.active:
            case "chat":
                self.send()
            case "control":
                self.execute()

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "send-msg":
                self.send()
            case "send-cmd":
                self.execute()

        print(event.button.id)

    @on(Select.Changed)
    def select_changes(self) -> None:
        log = cast(Log, self.query_one("#chat-log"))
        log.clear()
        self.message_idx = 0

    def update_chat(self):
        i = 0
        while True:
            time.sleep(1)

            if not self.chat_model:
                continue

            group = self.query_one(Select).selection
            if not group:
                continue

            messages = self.chat_model._groups[group].messages
            log = cast(Log, self.query_one("#chat-log"))

            for i in range(self.message_idx, len(messages)):
                m = messages[i]
                str = f"[{m.sender[0]}:{m.sender[1]}] ({time.ctime(m.sent_at)})\n{m.content}\n\n"
                self.call_from_thread(log.write_line, str)

            self.message_idx = len(messages)

    def update_tree(self):
        if not self.chat_model:
            return

        tree = self.query_one(Tree)

        tree.clear()
        tree.root.expand()

        for name, group in self.chat_model._groups.items():
            group_node = tree.root.add(name, expand=True)
            for peer in group.peers:
                group_node.add_leaf(f"{peer.address[0]}:{peer.address[1]}")

    def send(self):
        if not self.chat_model:
            return

        input = cast(Input, self.query_one("#msg-input"))
        select = self.query_one(Select)

        group_name = select.selection
        if not group_name:
            return

        self.chat_model.send(group_name, input.value)
        input.clear()

    def execute(self):
        input = cast(Input, self.query_one("#cmd-input"))
        log = cast(Log, self.query_one("#control-log"))

        cmd = input.value

        log.write_line("\n>> " + cmd)
        input.clear()

        args = cmd.split(" ")

        match args[0]:
            case "clear":
                log.clear()
            case "dns":
                if len(args) < 2:
                    log.write_line("Error: expected 'dns <address>'")
                    return

                try:
                    host, port = args[1].split(":")
                    self.dns = DNSClient(host, int(port), self.cache)
                    log.write_line(f"DNS client created for {host}:{port}")
                except Exception as e:
                    log.write_line(repr(e))
            case "query":
                if not self.dns:
                    log.write_line("Error: DNS client not created yet")
                    return

                if len(args) < 2:
                    log.write_line("Error: expected 'query <name>'")
                    return

                try:
                    record = self.dns.query(args[1])
                    log.write_lines(
                        [
                            f"name={record.name}",
                            f"address={record.ip}:{record.port}",
                            f"expires_at={time.ctime(record.expires_at)}",
                        ]
                    )
                except Exception as e:
                    log.write_line(repr(e))

            case "register":
                if not self.dns:
                    log.write_line("Error: DNS client not created yet")
                    return

                if len(args) < 3:
                    log.write_line("Error: expected 'register <name> <port> [ttl]'")
                    return

                try:
                    ttl = int(args[2]) if args[2] else 86400
                    record = self.dns.register(args[1], int(args[2]), ttl)
                    log.write_lines(
                        [
                            f"name={record.name}",
                            f"address={record.ip}:{record.port}",
                            f"expires_at={time.ctime(record.expires_at)}",
                        ]
                    )
                except Exception as e:
                    log.write_line(repr(e))

            case "deregister":
                if not self.dns:
                    log.write_line("Error: DNS client not created yet")
                    return

                if len(args) < 2:
                    log.write_line("Error: expected 'deregister <name>'")
                    return

                try:
                    self.dns.deregister(args[1])
                    log.write_line("Deleted")
                except Exception as e:
                    log.write_line(repr(e))

            case "listen":
                if len(args) < 2:
                    log.write_line("Error: expected 'listen <address>'")
                    return

                try:
                    logger = create_logger("chat-model")
                    host, port = args[1].split(":")
                    private_key, public_key = generate_rsa_keypair()

                    self.chat_model = ChatModel(
                        logger, host, int(port), private_key, public_key
                    )
                    self.chat_model.listen()

                    log.write_line(f"Chat peer listening at {host}:{port}...")
                except Exception as e:
                    log.write_line(repr(e))

            case "create-group":
                if not self.chat_model:
                    log.write_line("Error: Chat peer not created yet")
                    return

                if len(args) < 2:
                    log.write_line("Error: expected 'create-group <name>'")
                    return

                try:
                    group = self.chat_model.create_group(args[1])
                    select = self.query_one(Select)
                    log.write_lines([f"name={group.name}", f"token={group.token}"])
                except Exception as e:
                    log.write_line(repr(e))

            case "advertise":
                if not self.chat_model:
                    log.write_line("Error: Chat peer not created yet")
                    return

                if len(args) < 3:
                    log.write_line("Error: expected 'advertise <group> <address>'")
                    return

                try:
                    if not ":" in args[2]:
                        if not self.dns:
                            log.write_line("Error: DNS client not created yet")
                            return

                        record = self.dns.query(args[2])
                        address = (record.ip, int(record.port))
                    else:
                        ip, port = args[2].split(":")
                        address = (ip, int(port))

                    self.chat_model.advertise_group(args[1], address)
                    log.write_line(f"Sent to {address[0]}:{address[1]}")

                except Exception as e:
                    log.write_line(repr(e))

            case "sync":
                if not self.chat_model:
                    return

                select = self.query_one(Select)
                select.set_options((v, v) for v in self.chat_model._groups)

                self.update_tree()
                log.write_line("Synchronized")

            case _:
                log.write_line(help.strip())


if __name__ == "__main__":
    app = MainApp()
    app.run()
