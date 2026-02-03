from __future__ import annotations
import asyncio
import logging
from typing import Any
from pymodbus.client import AsyncModbusTcpClient

_LOGGER = logging.getLogger(__name__)

class TCPBusClient:
    """Wrapper for shared AsyncModbusTcpClient with locking."""
    def __init__(self, client: AsyncModbusTcpClient, lock: asyncio.Lock):
        self._client = client
        self._lock = lock

    def __getattr__(self, name: str):
        """Proxy calls to the underlying client with locking."""
        attr = getattr(self._client, name)
        if not callable(attr):
            return attr

        async def wrapper(*args, **kwargs):
            # Manual acquire to handle settle time after cancellation
            await self._lock.acquire()
            try:
                if not self._client.connected:
                    await self._client.connect()
                return await attr(*args, **kwargs)
            finally:
                try:
                    # Settle time: Shielded from cancellation to ensure
                    # the lock remains held even if HA cancels this task.
                    # This prevents rapid-fire collisions.
                    await asyncio.shield(asyncio.sleep(0.2))
                finally:
                    self._lock.release()
        return wrapper

    async def connect(self):
        """Ensure connection is open."""
        async with self._lock:
            if not self._client.connected:
                await self._client.connect()

    def close(self):
        """Do not close the shared connection directly."""
        pass

class TCPBusManager:
    """
    Manages shared statistics and connection for a specific Modbus TCP endpoint (IP:Port).
    """

    def __init__(self, *, hass, host: str, port: int) -> None:
        self.hass = hass
        self.host = host
        self.port = port
        self.users: set[str] = set()

        # Shared Client and Lock
        # We use a 5s timeout and 0 retries to ensure we fail within HA's update window
        self._client = AsyncModbusTcpClient(host, port=port, timeout=5, retries=0)
        self._lock = asyncio.Lock()

        # Statistics
        self.tx_packets = 0
        self.rx_packets = 0
        self.tx_bits = 0
        self.rx_bits = 0

    def get_client(self) -> TCPBusClient:
        """Return a thread-safe wrapper around the shared client."""
        return TCPBusClient(self._client, self._lock)

    def attach(self, entry_id: str) -> None:
        self.users.add(entry_id)

    def detach(self, entry_id: str) -> bool:
        self.users.discard(entry_id)
        if not self.users:
            self._client.close()
        return not self.users

    def update_counters(self, tx_bytes: int, rx_bytes: int) -> None:
        """Update the shared bus counters."""
        self.tx_packets += 1
        self.rx_packets += 1
        self.tx_bits += tx_bytes * 8
        self.rx_bits += rx_bytes * 8
