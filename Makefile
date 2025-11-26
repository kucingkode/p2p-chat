.PHONY: server client sync

server:
	uv run -m dns_server.main

client:
	uv run -m chat_peer.main

sync:
	uv sync --all-packages