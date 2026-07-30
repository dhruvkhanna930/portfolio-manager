"""Wire framing: 4-byte big-endian length prefix + msgpack envelope dict.

msgpack (not JSON) so raw bytes (ciphertext, pubkeys) travel without base64 bloat.
"""

import asyncio
import socket
import struct

import msgpack

LENGTH_PREFIX_FORMAT = ">I"
LENGTH_PREFIX_SIZE = struct.calcsize(LENGTH_PREFIX_FORMAT)
MAX_ENVELOPE_SIZE = 10 * 1024 * 1024


def pack_envelope(envelope: dict) -> bytes:
    body = msgpack.packb(envelope, use_bin_type=True)
    return struct.pack(LENGTH_PREFIX_FORMAT, len(body)) + body


def unpack_body(body: bytes) -> dict:
    return msgpack.unpackb(body, raw=False)


# ---- asyncio stream versions (used by inbound listeners) ----

async def write_envelope(writer: asyncio.StreamWriter, envelope: dict) -> None:
    writer.write(pack_envelope(envelope))
    await writer.drain()


async def read_envelope(reader: asyncio.StreamReader) -> dict:
    header = await reader.readexactly(LENGTH_PREFIX_SIZE)
    (length,) = struct.unpack(LENGTH_PREFIX_FORMAT, header)
    if length > MAX_ENVELOPE_SIZE:
        raise ValueError("envelope exceeds max size")
    body = await reader.readexactly(length)
    return unpack_body(body)


# ---- blocking socket versions (used by the SOCKS outbound client thread) ----

def send_envelope_sync(sock: socket.socket, envelope: dict) -> None:
    sock.sendall(pack_envelope(envelope))


def _recv_exactly_sync(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed while reading envelope")
        buf.extend(chunk)
    return bytes(buf)


def read_envelope_sync(sock: socket.socket) -> dict:
    header = _recv_exactly_sync(sock, LENGTH_PREFIX_SIZE)
    (length,) = struct.unpack(LENGTH_PREFIX_FORMAT, header)
    if length > MAX_ENVELOPE_SIZE:
        raise ValueError("envelope exceeds max size")
    body = _recv_exactly_sync(sock, length)
    return unpack_body(body)
