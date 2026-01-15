from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

class TCPBusManager:
    """
    Manages shared statistics for a specific Modbus TCP endpoint (IP:Port).
    It does NOT manage the actual Modbus clients, as those are
    individual to each device (Unit ID).
    """

    def __init__(self, *, hass, host: str, port: int) -> None:
        self.hass = hass
        self.host = host
        self.port = port

        self._users: set[str] = set()

        # Statistics
        self.tx_packets = 0
        self.rx_packets = 0
        self.tx_bits = 0
        self.rx_bits = 0
        self.sensors_created = False

    # ------------------------------------------------------------------
    # Reference tracking
    # ------------------------------------------------------------------

    def attach(self, entry_id: str) -> None:
        self._users.add(entry_id)

    def detach(self, entry_id: str) -> bool:
        self._users.discard(entry_id)

        # Return True if no users left (signal to remove from global registry)
        return not self._users

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------
    def update_counters(self, tx_bytes: int, rx_bytes: int) -> None:
        """Update the shared bus counters."""
        self.tx_packets += 1
        self.rx_packets += 1
        self.tx_bits += tx_bytes * 8
        self.rx_bits += rx_bytes * 8
