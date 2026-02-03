from __future__ import annotations
import logging
from typing import Any
from pymodbus.client import AsyncModbusTcpClient

_LOGGER = logging.getLogger(__name__)

class TCPBusManager:
    """
    Manages a shared Modbus TCP connection and statistics for an endpoint (IP:Port).
    """

    def __init__(self, *, hass, host: str, port: int) -> None:
        self.hass = hass
        self.host = host
        self.port = port
        self.users: set[str] = set()
        self.client = AsyncModbusTcpClient(host=self.host, port=self.port)

        # Statistics
        self.tx_packets = 0
        self.rx_packets = 0
        self.tx_bits = 0
        self.rx_bits = 0

    async def async_connect(self) -> None:
        """Connect the underlying client."""
        _LOGGER.debug("Connecting to TCP bus: %s:%s", self.host, self.port)
        await self.client.connect()

    async def async_close(self) -> None:
        """Close the underlying client."""
        _LOGGER.debug("Closing TCP bus: %s:%s", self.host, self.port)
        self.client.close()

    async def attach(self, entry_id: str) -> None:
        """Attach a user to the bus. Connects if it's the first user."""
        if not self.users:
            # First user, connect the bus
            await self.async_connect()
        self.users.add(entry_id)

    async def detach(self, entry_id: str) -> bool:
        """Detach a user. Closes if it's the last user."""
        self.users.discard(entry_id)
        if not self.users:
            # Last user, close the bus
            await self.async_close()
        return not self.users

    def update_counters(self, tx_bytes: int, rx_bytes: int) -> None:
        """Update the shared bus counters."""
        self.tx_packets += 1
        self.rx_packets += 1
        self.tx_bits += tx_bytes * 8
        self.rx_bits += rx_bytes * 8