import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN, TYPE_ENDPOINT, TYPE_DEVICE
from .coordinator import ModbusCoordinator
from .devices.modbusdevice import ModbusDevice

_LOGGER = logging.getLogger(__name__)

async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    return await _get_diagnostics(hass, entry)

async def async_get_device_diagnostics(hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry) -> dict[str, Any]:
    return await _get_diagnostics(hass, entry)

async def _get_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    entry_type = entry.data.get("conf_type", TYPE_DEVICE)

    # ------------------------------------------------------------------
    # 1. Endpoint Diagnostics
    # ------------------------------------------------------------------
    if entry_type == TYPE_ENDPOINT:
        endpoints = hass.data.get(DOMAIN, {}).get("endpoints", {})
        bus_manager = endpoints.get(entry.entry_id)
        if not bus_manager:
            return {"error": "Bus manager not found for endpoint"}

        # Per-slave breakdown
        slave_stats = {}
        for slave_id, stats in getattr(bus_manager, "devices_traffic", {}).items():
            slave_stats[str(slave_id)] = stats.to_dict()

        return {
            "entry_type": "endpoint",
            "title": entry.title,
            "device_mode": entry.data.get("device_mode"),
            "connection_info": {
                "ip": entry.data.get("ip_address"),
                "port": entry.data.get("port"),
                "serial_port": entry.data.get("serial_port"),
                "serial_baud": entry.data.get("serial_baud"),
            },
            "bus_health": {
                "connected": getattr(bus_manager, "connected", False),
                "total_devices": getattr(bus_manager, "total_devices_count", 0),
                "active_devices": getattr(bus_manager, "active_devices_count", 0),
                "error_devices": getattr(bus_manager, "error_devices_count", 0),
                "problem_slave_ids": getattr(bus_manager, "problem_slaves", []),
                "bus_utilization_percent": getattr(bus_manager, "utilization_percent", 0.0),
                "queue_depth": getattr(bus_manager, "queue_depth", 0),
            },
            "bus_traffic": bus_manager.traffic.to_dict() if hasattr(bus_manager, "traffic") else {},
            "slaves_traffic": slave_stats,
        }

    # ------------------------------------------------------------------
    # 2. Device Diagnostics
    # ------------------------------------------------------------------
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not coordinator or not isinstance(coordinator, ModbusCoordinator):
        return {"error": "Coordinator not found for device"}

    modbus_device: ModbusDevice = coordinator._modbusDevice
    if not modbus_device:
        return {"error": "ModbusDevice not initialized"}

    dev_traffic = modbus_device.traffic
    bus_traffic = getattr(modbus_device._client._bus, "traffic", None)

    return {
        "entry_type": "device",
        "title": entry.title,
        "manufacturer": modbus_device.manufacturer,
        "model": modbus_device.model,
        "slave_id": modbus_device._slave_id,
        "last_update_success": coordinator.last_update_success,
        "device_traffic": dev_traffic.to_dict() if dev_traffic else {},
        "endpoint_traffic": bus_traffic.to_dict() if bus_traffic else {},
    }