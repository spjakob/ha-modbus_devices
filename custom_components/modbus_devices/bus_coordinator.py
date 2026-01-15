"""Coordinator for Modbus bus statistics."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .statistics import STATS_MANAGER

_LOGGER = logging.getLogger(__name__)

class BusCoordinator(DataUpdateCoordinator):
    """Coordinator for bus statistics."""

    def __init__(self, hass: HomeAssistant, endpoint: str, device_info: dict):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Modbus Bus {endpoint}",
            update_interval=timedelta(seconds=30),  # Or make this configurable
        )
        self.endpoint = endpoint
        self.device_info = device_info

    async def _async_update_data(self) -> dict[str, int] | None:
        """Fetch latest data from stats manager."""
        try:
            stats = STATS_MANAGER.get_stats(self.endpoint)
            return stats or {"sent": 0, "received": 0}
        except Exception as err:
            raise UpdateFailed(f"Error communicating with stats manager: {err}") from err
