"""The Transport interface. RealTorTransport and MockTransport both implement this;
no other module ever branches on which one is active.
"""

from abc import ABC, abstractmethod
from typing import Awaitable, Callable

ReceiveHandler = Callable[[dict], Awaitable[dict]]


class TransportError(Exception):
    pass


class Transport(ABC):
    @abstractmethod
    async def start(self, internal_target_port: int) -> str:
        """Bring up the inbound listener (and, for real Tor, the hidden service).
        Returns this instance's own address string."""

    @abstractmethod
    async def send_envelope(self, peer_address: str, envelope: dict, timeout: float | None = None) -> dict:
        """Connect to peer_address, send envelope, return their reply envelope.
        Raises TransportError on any connection/timeout failure."""

    @abstractmethod
    def set_receive_handler(self, handler: ReceiveHandler) -> None:
        """handler(envelope) -> reply_envelope, invoked for each inbound connection."""

    @abstractmethod
    def validate_address(self, address: str) -> bool:
        ...

    @property
    @abstractmethod
    def connect_timeout(self) -> float:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...
