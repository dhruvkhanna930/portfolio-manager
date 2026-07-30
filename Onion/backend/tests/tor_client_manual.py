"""Manual test: connect to a hidden service via Tor's SOCKS5 proxy and exchange bytes.

Run: venv/Scripts/python.exe tests/tor_client_manual.py <onion_address> [message]
"""

import sys

import socks

VIRTUAL_PORT = 8080


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: tor_client_manual.py <onion_address> [message]")
        raise SystemExit(1)

    onion_address = sys.argv[1]
    message = sys.argv[2] if len(sys.argv) > 2 else "hello from client over real Tor"

    s = socks.socksocket()
    s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
    s.settimeout(30)
    print(f"[client] connecting to {onion_address}:{VIRTUAL_PORT} via Tor SOCKS...")
    s.connect((onion_address, VIRTUAL_PORT))
    print("[client] connected, sending message")
    s.sendall(message.encode("utf-8"))
    resp = s.recv(65536)
    print(f"[client] received: {resp!r}")
    s.close()

    assert resp == b"ACK:" + message.encode("utf-8")
    print("CLIENT TEST PASSED")


if __name__ == "__main__":
    main()
