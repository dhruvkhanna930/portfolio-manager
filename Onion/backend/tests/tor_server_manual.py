"""Manual test: bring up an ephemeral hidden service with a persisted key,
so the onion address survives restarts, and echo back anything received.

Run: venv/Scripts/python.exe tests/tor_server_manual.py
"""

import socket
import sys
import threading
from pathlib import Path

from stem.control import Controller

KEY_FILE = Path(__file__).resolve().parent / "_scratch_hs_key.txt"
INTERNAL_PORT = 9001
VIRTUAL_PORT = 8080


def run_echo_server(port: int, ready_event: threading.Event) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(1)
    ready_event.set()
    print(f"[server] echo listener up on 127.0.0.1:{port}")
    while True:
        conn, _addr = srv.accept()
        data = conn.recv(65536)
        print(f"[server] received: {data!r}")
        conn.sendall(b"ACK:" + data)
        conn.close()


def main() -> None:
    ready_event = threading.Event()
    t = threading.Thread(target=run_echo_server, args=(INTERNAL_PORT, ready_event), daemon=True)
    t.start()
    ready_event.wait(timeout=5)

    controller = Controller.from_port(address="127.0.0.1", port=9051)
    controller.authenticate()

    if KEY_FILE.exists():
        key_content = KEY_FILE.read_text().strip()
        print("[server] reusing persisted ED25519 key")
        service = controller.create_ephemeral_hidden_service(
            {VIRTUAL_PORT: INTERNAL_PORT},
            key_type="ED25519-V3",
            key_content=key_content,
            await_publication=True,
        )
    else:
        print("[server] no persisted key found, generating a new one")
        service = controller.create_ephemeral_hidden_service(
            {VIRTUAL_PORT: INTERNAL_PORT},
            key_type="NEW",
            key_content="ED25519-V3",
            await_publication=True,
        )
        KEY_FILE.write_text(service.private_key)

    onion_address = f"{service.service_id}.onion"
    print(f"[server] ONION_ADDRESS={onion_address}")
    print("[server] ready and waiting for connections. Ctrl+C to stop.")

    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        pass
    finally:
        controller.remove_ephemeral_hidden_service(service.service_id)
        controller.close()


if __name__ == "__main__":
    main()
