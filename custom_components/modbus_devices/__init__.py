"""Support for Modbus devices."""
import logging

from functools import partial
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from homeassistant.const import CONF_DEVICES
from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_NAME,
    CONF_DEVICE_MODE,
    CONF_DEVICE_MODEL,
    CONF_IP,
    CONF_PORT,
    CONF_SERIAL_PORT,
    CONF_SERIAL_BAUD,
    CONF_SLAVE_ID,
    CONF_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL_FAST,
    DEVICE_MODE_TCPIP, DEVICE_MODE_RTU,
    CONF_TYPE, TYPE_ENDPOINT, TYPE_DEVICE, CONF_ENDPOINT_ID
)

from .coordinator import ModbusCoordinator
from .devices.connection import TCPConnectionParams, RTUConnectionParams
from .endpoint import async_setup_endpoint, async_unload_endpoint
from .rtu_bus import RTUBusManager
from .tcp_bus import TCPBusManager

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    entry_type = entry.data.get(CONF_TYPE)

    # -------------------------------------------------------------
    # 1. SETUP ENDPOINT
    # -------------------------------------------------------------
    if entry_type == TYPE_ENDPOINT:
        _LOGGER.debug("Setting up Modbus Endpoint: %s", entry.title)
        if not await async_setup_endpoint(hass, entry):
            return False

        # We also want to setup sensors for the endpoint (statistics)
        # We can reuse the PLATFORMS mechanism.
        # But we need to make sure sensor.py knows how to handle an Endpoint entry.
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setups(entry, [PLATFORMS[4]]) # Only SENSOR platform for stats
        )
        return True

    # -------------------------------------------------------------
    # 2. SETUP DEVICE
    # -------------------------------------------------------------

    # Legacy check: if no type, it's a legacy entry.
    if not entry_type:
        _LOGGER.warning("Device '%s' is legacy/orphaned. Please reconfigure it to select an Endpoint.", entry.title)
        # We return False to indicate setup failed, but we want the user to be able to configure it.
        # Returning False puts it in "Setup Failed". The Options Flow is still accessible.
        return False

    if entry_type == TYPE_DEVICE:
        _LOGGER.debug("Setting up Modbus Device: %s", entry.title)

        endpoint_id = entry.data.get(CONF_ENDPOINT_ID)
        endpoints = hass.data.get(DOMAIN, {}).get("endpoints", {})
        bus_manager = endpoints.get(endpoint_id)

        if not bus_manager:
            _LOGGER.error("Endpoint %s not found for device %s. Ensure Endpoint is added and loaded.", endpoint_id, entry.title)
            # Retrying might help if endpoint loads later?
            # ConfigEntryNotReady would be appropriate if we expect it to come up.
            from homeassistant.exceptions import ConfigEntryNotReady
            raise ConfigEntryNotReady(f"Endpoint {endpoint_id} not available")

        # Create connection params based on what the bus manager is (RTU or TCP)
        # Note: The Device entry only holds Slave ID.
        # We infer the connection type from the Bus Manager type.
        slave_id = entry.data[CONF_SLAVE_ID]

        if isinstance(bus_manager, TCPBusManager):
             # For TCP, ModbusDevice expects TCPConnectionParams
             # But wait, ModbusDevice logic currently creates its own AsyncModbusTcpClient if passed TCPParams.
             # We want to share the bus manager?
             # Original design: TCP was not shared. My previous plan: TCPBusManager for stats.
             # New design: Endpoint IS the manager.
             # Does ModbusDevice need to change? Yes.
             # It should accept the manager directly or params.
             connection_params = TCPConnectionParams(bus_manager.host, bus_manager.port, slave_id)
             # We will need to update ModbusDevice to use the shared manager if possible, or we pass the manager separately.
        else:
             connection_params = RTUConnectionParams(bus_manager.port, 9600, slave_id) # Baudrate doesn't matter for params here if we pass bus

        name = entry.data[CONF_NAME]
        device_model = entry.data.get(CONF_DEVICE_MODEL, None)
        scan_interval = entry.data[CONF_SCAN_INTERVAL]
        scan_interval_fast = entry.data[CONF_SCAN_INTERVAL_FAST]

        # Create device registry entry
        device_registry = dr.async_get(hass)
        dev = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, entry.entry_id)},
            name=name
        )

        # Set up coordinator
        # We pass the bus_manager (either RTU or TCP)
        coordinator = ModbusCoordinator(
            hass,
            dev,
            device_model,
            connection_params,
            scan_interval,
            scan_interval_fast,
            bus_manager=bus_manager
        )
        hass.data[DOMAIN][entry.entry_id] = coordinator

        await coordinator.async_config_entry_first_refresh()

        # Forward the setup to the platforms.
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        )

        entry.async_on_unload(entry.add_update_listener(update_listener))
        hass.services.async_register(DOMAIN, "request_update", partial(service_request_update, hass))

        return True

    return False

# Service-call to update values
async def service_request_update(hass, call: ServiceCall):
    """Handle the service call to update entities for a specific device."""
    device_id = call.data.get("device_id")
    if not device_id:
        _LOGGER.error("Device ID is required")
        return

    # Get the device entry from the device registry
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get(device_id)
    if not device_entry:
        _LOGGER.error("No device entry found for device ID %s", device_id)
        return
    
    """Find the coordinator corresponding to the given device ID."""
    for entry_id, coordinator in hass.data[DOMAIN].items():
        # Filter out endpoints (which are bus managers, not coordinators)
        if isinstance(coordinator, ModbusCoordinator):
            if getattr(coordinator, "device_id", None) == device_id:
                await coordinator._async_update_data()
                return

    _LOGGER.warning("No coordinator found for device ID %s", device_id)

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug("Updating Modbus Devices entry!")
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_type = entry.data.get(CONF_TYPE)

    if entry_type == TYPE_ENDPOINT:
        return await async_unload_endpoint(hass, entry)

    _LOGGER.debug("Unloading Modbus Devices entry!")

    # Unload entries
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Close coordinator
        coordinator = hass.data[DOMAIN].get(entry.entry_id)
        if coordinator and isinstance(coordinator, ModbusCoordinator):
            coordinator.close()
            # Note: We do NOT close the bus here, as it is owned by the Endpoint entry.
            # We might want to detach?
            if hasattr(coordinator.bus_manager, "detach"):
                # But our current Manager implementation is simple.
                # RTUBusManager has reference counting.
                # Since we are not using the "attach/detach" in the new Init flow (we just fetch it),
                # we should probably just rely on the Endpoint managing the bus life.
                pass

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
