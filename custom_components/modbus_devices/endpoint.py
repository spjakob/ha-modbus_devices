from __future__ import annotations
import logging
from typing import Any
from .busmanager import TCPBusManager, RTUBusManager
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_endpoint(hass, entry):
    """Setup the Modbus Endpoint (RTU or TCP)."""
    hass.data.setdefault(DOMAIN, {}).setdefault("endpoints", {})

    device_mode = entry.data.get("device_mode")
    bus_manager = None

    # Default 2.0s timeout gives RS485 devices adequate time to respond without false timeouts
    endpoint_timeout = float(entry.data.get("timeout", entry.options.get("timeout", 2.0)))
    # Default 20.0s queue timeout protects bus from congestion and stale request buildup
    queue_timeout = float(entry.data.get("queue_timeout", entry.options.get("queue_timeout", 20.0)))

    if device_mode == "tcpip":
        ip = entry.data.get("ip_address")
        port = entry.data.get("port")
        bus_manager = TCPBusManager(
            host=ip,
            port=port,
            timeout=endpoint_timeout,
            retries=0,
            queue_timeout=queue_timeout,
        )
    elif device_mode == "rtu":
        port = entry.data.get("serial_port")
        baud = entry.data.get("serial_baud")
        bus_manager = RTUBusManager(
            port=port,
            baudrate=baud,
            parity="N",
            stopbits=1,
            timeout=endpoint_timeout,
            retries=0,
            queue_timeout=queue_timeout,
        )
    else:
        _LOGGER.error("Unknown device mode for endpoint: %s", device_mode)
        return False

    # Store manager
    hass.data[DOMAIN]["endpoints"][entry.entry_id] = bus_manager

    # We might want to forward setup to sensor platform to create stats sensors
    # But first, let's just make sure the manager is available.

    return True

async def async_unload_endpoint(hass, entry):
    """Unload the Modbus Endpoint."""
    if entry.entry_id in hass.data[DOMAIN]["endpoints"]:
        bus = hass.data[DOMAIN]["endpoints"].pop(entry.entry_id)
        # If the bus manager has a close method, call it.
        # RTUBusManager has async_stop() but it is ref-counted.
        # Here we are unloading the Endpoint itself, so we should force close?
        # Or let it close naturally if no users?
        # Since we are removing the Endpoint, we should probably clean up.
        # But RTUBusManager.async_stop is async.
        pass
    return True
