from __future__ import annotations
import asyncio
import logging
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ConnectionException

_LOGGER = logging.getLogger(__name__)

class TCPBusClient:
    """Wrapper for shared AsyncModbusTcpClient with locking."""
    def __init__(self, manager: TCPBusManager, lock: asyncio.Lock):
        self._manager = manager
        self._lock = lock

    def __getattr__(self, name: str):
        """Proxy calls to the underlying client with locking."""
        attr = getattr(self._manager.client, name)
        if not callable(attr):
            return attr

        async def wrapper(*args, **kwargs):
            # Manual acquire to handle settle time after cancellation
            await self._lock.acquire()
            try:
                # Add detailed logging before the call
                unit_id = kwargs.get("device_id")
                log_details = f"unit {unit_id}"
                if "address" in kwargs:
                    log_details += f", address {kwargs['address']}"
                if "count" in kwargs:
                    log_details += f", count {kwargs['count']}"
                if "value" in kwargs:
                    log_details += f", value {kwargs['value']}"
                if "values" in kwargs:
                    log_details += f", values {kwargs['values']}"
                _LOGGER.debug("Requesting '%s' on %s:%s for %s", name, self._manager.host, self._manager.port, log_details)
                
                if not self._manager.client.connected:
                    _LOGGER.debug("Connecting to shared client: %s:%s", self._manager.host, self._manager.port)
                    await self._manager.client.connect()
                return await attr(*args, **kwargs)
            except asyncio.CancelledError:
                _LOGGER.debug("Modbus request '%s' cancelled for %s:%s", name, self._manager.host, self._manager.port)
                raise
            except ConnectionException as exc:
                _LOGGER.error("Modbus connection error during '%s' on %s:%s: %s", name, self._manager.host, self._manager.port, exc)
                await self._manager.reconnect()
                raise
            except Exception as exc:
                _LOGGER.error("Modbus error during '%s' on %s:%s: %s", name, self._manager.host, self._manager.port, exc)
                raise
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
            if not self._manager.client.connected:
                try:
                    await self._manager.client.connect()
                except Exception as e:
                    _LOGGER.error("Failed to connect to TCP bus: %s", e)
                    raise

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
        self.client = AsyncModbusTcpClient(host, port=port, timeout=30, retries=0)
        self._lock = asyncio.Lock()

        # Statistics
        self.tx_packets = 0
        self.rx_packets = 0
        self.tx_bits = 0
        self.rx_bits = 0

    async def reconnect(self):
        """Close and recreate the client to recover from a bad state."""
        _LOGGER.warning("Reconnecting Modbus TCP client for %s:%s", self.host, self.port)
        self.client.close()
        self.client = AsyncModbusTcpClient(self.host, port=self.port, timeout=5, retries=0)


    def get_client(self) -> TCPBusClient:
        """Return a thread-safe wrapper around the shared client."""
        return TCPBusClient(self, self._lock)

    def attach(self, entry_id: str) -> None:
        self.users.add(entry_id)

    def detach(self, entry_id: str) -> bool:
        self.users.discard(entry_id)
        if not self.users:
            self.client.close()
        return not self.users

    def update_counters(self, tx_bytes: int, rx_bytes: int) -> None:
        """Update the shared bus counters."""
        self.tx_packets += 1
        self.rx_packets += 1
        self.tx_bits += tx_bytes * 8
        self.rx_bits += rx_bytes * 8
