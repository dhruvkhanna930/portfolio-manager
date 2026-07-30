"""Day 1 done-bar test: two peer processes exchange an encrypted MSG envelope
over real Tor hidden services and decrypt correctly.

Run as two separate processes:
  venv/Scripts/python.exe -u tests/test_full_roundtrip_manual.py --label a
  venv/Scripts/python.exe -u tests/test_full_roundtrip_manual.py --label b
"""

import argparse
import asyncio
import base64
import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import crypto
from app.tor.real_tor import RealTorTransport

SCRATCH = Path(__file__).resolve().parent / "_scratch_roundtrip"
SCRATCH.mkdir(exist_ok=True)

INTERNAL_PORTS = {"a": 9101, "b": 9102}
MESSAGE_TEXT = "hello A, this is B, encrypted end to end over real Tor"


async def wait_for_peer_info(label: str, timeout: float = 90.0) -> dict:
    path = SCRATCH / f"peer_{label}.json"
    start = time.monotonic()
    while not path.exists():
        if time.monotonic() - start > timeout:
            raise TimeoutError(f"timed out waiting for {path}")
        await asyncio.sleep(0.5)
    return json.loads(path.read_text())


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", choices=["a", "b"], required=True)
    args = parser.parse_args()
    label = args.label
    other = "b" if label == "a" else "a"

    my_pub_b64, my_priv_b64 = crypto.generate_keypair()
    print(f"[{label}] generated keypair, pub={my_pub_b64}")

    transport = RealTorTransport()
    received_event = asyncio.Event()
    received_plaintext = None

    if label == "a":
        async def handler(envelope: dict) -> dict:
            nonlocal received_plaintext
            print(f"[{label}] inbound envelope type={envelope.get('type')}")
            if envelope.get("type") == "MSG":
                sender_pub_b64 = base64.b64encode(envelope["sender_pubkey"]).decode("ascii")
                plaintext = crypto.decrypt_message(my_priv_b64, sender_pub_b64, envelope["sealed"])
                print(f"[{label}] DECRYPTED: {plaintext!r}")
                received_plaintext = plaintext
                received_event.set()
                return {"v": 1, "type": "ACK", "msg_id": envelope["msg_id"]}
            return {"v": 1, "type": "ACK"}

        transport.set_receive_handler(handler)

    onion_address = await transport.start(INTERNAL_PORTS[label])
    print(f"[{label}] ONION_ADDRESS={onion_address}")

    (SCRATCH / f"peer_{label}.json").write_text(
        json.dumps({"onion": onion_address, "pubkey": my_pub_b64})
    )

    peer_info = await wait_for_peer_info(other)
    print(f"[{label}] discovered peer {other}: {peer_info}")

    if label == "b":
        sealed = crypto.encrypt_message(my_priv_b64, peer_info["pubkey"], MESSAGE_TEXT)
        envelope = {
            "v": 1,
            "type": "MSG",
            "msg_id": str(uuid.uuid4()),
            "sender_onion": onion_address,
            "sender_pubkey": base64.b64decode(my_pub_b64),
            "sealed": sealed,
            "ts": time.time(),
        }
        print(f"[{label}] sending encrypted MSG to {peer_info['onion']}...")
        ack = await transport.send_envelope(peer_info["onion"], envelope)
        print(f"[{label}] received ACK: {ack}")
        assert ack.get("type") == "ACK" and ack.get("msg_id") == envelope["msg_id"]
        print("ROUNDTRIP TEST PASSED (sender side)")
    else:
        await asyncio.wait_for(received_event.wait(), timeout=60)
        assert received_plaintext == MESSAGE_TEXT
        print("ROUNDTRIP TEST PASSED (receiver side)")

    await transport.stop()


if __name__ == "__main__":
    asyncio.run(main())
