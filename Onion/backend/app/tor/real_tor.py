"""Real Tor transport: ephemeral hidden service (via stem) for inbound,
SOCKS5 (via PySocks) through the local Tor daemon for outbound.
"""

import asyncio
import re
import socket
from typing import Callable

import socks
from stem.control import Controller

from app.network import protocol
from app.tor.base import Transport, TransportError

ONION_V3_RE = re.compile(r"^[a-z2-7]{56}\.onion$")


class RealTorTransport(Transport):
    def __init__(
        self,
        control_port: int = 9051,
        socks_port: int = 9050,
        virtual_port: int = 8080,
        persisted_key: str | None = None,
        on_key_generated: Callable[[str], None] | None = None,
    ):
        self._control_port = control_port
        self._socks_port = socks_port
        self._virtual_port = virtual_port
        self._persisted_key = persisted_key
        self._on_key_generated = on_key_generated
        self._controller: Controller | None = None
        self._service = None
        self._server: asyncio.base_events.Server | None = None
        self._receive_handler = None

    @property
    def connect_timeout(self) -> float:
        return 20.0

    def set_receive_handler(self, handler) -> None:
        self._receive_handler = handler

    def validate_address(self, address: str) -> bool:
        return bool(ONION_V3_RE.match(address))

    async def start(self, internal_target_port: int) -> str:
        self._server = await asyncio.start_server(
            self._handle_conn, "127.0.0.1", internal_target_port
        )

        self._controller = Controller.from_port(address="127.0.0.1", port=self._control_port)
        self._controller.authenticate()

        if self._persisted_key:
            service = self._controller.create_ephemeral_hidden_service(
                {self._virtual_port: internal_target_port},
                key_type="ED25519-V3",
                key_content=self._persisted_key,
                await_publication=True,
            )
        else:
            service = self._controller.create_ephemeral_hidden_service(
                {self._virtual_port: internal_target_port},
                key_type="NEW",
                key_content="ED25519-V3",
                await_publication=True,
            )
            if self._on_key_generated:
                self._on_key_generated(service.private_key)

        self._service = service
        return f"{service.service_id}.onion"

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
        try:
            return await asyncio.to_thread(self._blocking_send, peer_address, envelope, timeout)
        except Exception as exc:
            raise TransportError(str(exc)) from exc

    def _blocking_send(self, peer_address: str, envelope: dict, timeout: float) -> dict:
        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, "127.0.0.1", self._socks_port)
        s.settimeout(timeout)
        try:
            s.connect((peer_address, self._virtual_port))
            protocol.send_envelope_sync(s, envelope)
            return protocol.read_envelope_sync(s)
        finally:
            s.close()

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
        if self._controller is not None and self._service is not None:
            try:
                self._controller.remove_ephemeral_hidden_service(self._service.service_id)
            except Exception:
                pass
        if self._controller is not None:
            self._controller.close()
