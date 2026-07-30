"""Demo-safety fallback: loopback transport implementing the same interface as
RealTorTransport, so business logic never branches on which one is active.
"""

import asyncio

from app.network import protocol
from app.tor.base import Transport, TransportError


class MockTransport(Transport):
    def __init__(self):
        self._server: asyncio.base_events.Server | None = None
        self._own_address: str | None = None
        self._receive_handler = None

    @property
    def connect_timeout(self) -> float:
        return 3.0

    def set_receive_handler(self, handler) -> None:
        self._receive_handler = handler

    def validate_address(self, address: str) -> bool:
        return address.startswith("mock://")

    async def start(self, internal_target_port: int) -> str:
        self._server = await asyncio.start_server(
            self._handle_conn, "127.0.0.1", internal_target_port
        )
        self._own_address = f"mock://127.0.0.1:{internal_target_port}"
        return self._own_address

    async def _handle_conn(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            envelope = await protocol.read_envelope(reader)
            if self._receive_handler:
                reply = await self._receive_handler(envelope)
            else:
                reply = {"v": 1, "type": "ACK"}
            await protocol.write_envelope(writer, reply)
        except Exception:
            pass
        finally:
            writer.close()

    async def send_envelope(self, peer_address: str, envelope: dict, timeout: float | None = None) -> dict:
        timeout = timeout if timeout is not None else self.connect_timeout
        host_port = peer_address.removeprefix("mock://")
        host, port_str = host_port.split(":")
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, int(port_str)), timeout=timeout
            )
            await protocol.write_envelope(writer, envelope)
            reply = await asyncio.wait_for(protocol.read_envelope(reader), timeout=timeout)
            writer.close()
            return reply
        except Exception as exc:
            raise TransportError(str(exc)) from exc

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
