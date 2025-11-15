.PHONY: server client

server:
	uv run -m dns_server.main

client:
	uv run -m chat_peer.main