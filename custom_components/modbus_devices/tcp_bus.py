from __future__ import annotations
import logging
import asyncio
import time
from typing import Any

_LOGGER = logging.getLogger(__name__)

class TCPBusManager:
    """
    Manages shared statistics for a specific Modbus TCP endpoint (IP:Port).
    """

    def __init__(self, *, hass, host: str, port: int) -> None:
        self.hass = hass
        self.host = host
        self.port = port
        self.users: set[str] = set()
        self.lock = asyncio.Lock()

        # Statistics
        self.tx_packets = 0
        self.rx_packets = 0
        self.tx_bits = 0
        self.rx_bits = 0

    def attach(self, entry_id: str) -> None:
        self.users.add(entry_id)

    def detach(self, entry_id: str) -> bool:
        self.users.discard(entry_id)
        return not self.users

    def update_counters(self, tx_bytes: int, rx_bytes: int) -> None:
        """Update the shared bus counters."""
        self.tx_packets += 1
        self.rx_packets += 1
        self.tx_bits += tx_bytes * 8
        self.rx_bits += rx_bytes * 8

    async def execute_with_lock(self, func):
        """Execute a Modbus operation with exclusive access and congestion monitoring."""
        start_wait = time.monotonic()
        async with self.lock:
            wait_time = time.monotonic() - start_wait
            if wait_time > 0.2:
                _LOGGER.warning(
                    "TCP Bus (%s:%s) Congestion: Waited %.3fs for lock.",
                    self.host, self.port, wait_time
                )
            elif wait_time > 0.05:
                _LOGGER.debug(
                    "TCP Bus (%s:%s) Busy: Waited %.3fs for lock.",
                    self.host, self.port, wait_time
                )
            return await func()
