"""The Modbus Read/Write statistics manager."""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.framer import ModbusTcpFramer

_LOGGER = logging.getLogger(__name__)


class StatisticsManager:
    """Manages statistics for Modbus communication."""

    def __init__(self) -> None:
        """Initialize the statistics manager."""
        self._stats: dict[str, dict[str, int]] = defaultdict(lambda: {"sent": 0, "received": 0})

    def add_bytes_sent(self, endpoint: str, byte_count: int) -> None:
        """Add to the count of bytes sent."""
        if endpoint and byte_count > 0:
            self._stats[endpoint]["sent"] += byte_count
            _LOGGER.debug("Endpoint %s: %d bytes sent, total sent: %d", endpoint, byte_count, self._stats[endpoint]["sent"])

    def add_bytes_received(self, endpoint: str, byte_count: int) -> None:
        """Add to the count of bytes received."""
        if endpoint and byte_count > 0:
            self._stats[endpoint]["received"] += byte_count
            _LOGGER.debug("Endpoint %s: %d bytes received, total received: %d", endpoint, byte_count, self._stats[endpoint]["received"])

    def get_stats(self, endpoint: str) -> dict[str, int] | None:
        """Get statistics for a specific endpoint."""
        return self._stats.get(endpoint)

    def get_all_stats(self) -> dict[str, dict[str, int]]:
        """Get all statistics."""
        return self._stats


STATS_MANAGER = StatisticsManager()


class CountingTcpFramer(ModbusTcpFramer):
    """A framer that counts sent and received bytes for TCP."""

    def __init__(self, client: AsyncModbusTcpClient | None = None, *, stats_manager: StatisticsManager, endpoint: str) -> None:
        """Initialize the counting framer."""
        super().__init__(client)
        self._stats_manager = stats_manager
        self._endpoint = endpoint

    def build_packet(self, message: bytes) -> bytes:
        """Count sent bytes."""
        packet = super().build_packet(message)
        self._stats_manager.add_bytes_sent(self._endpoint, len(packet))
        return packet

    def process_incoming_packet(self, data: bytes, callback: Callable[[Any], None], slave: int, **kwargs: Any) -> None:
        """Count received bytes."""
        self._stats_manager.add_bytes_received(self._endpoint, len(data))
        super().process_incoming_packet(data, callback, slave, **kwargs)
