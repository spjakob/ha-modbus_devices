import logging
import time

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from .const import DOMAIN, TYPE_ENDPOINT, TYPE_DEVICE
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity

from .devices.datatypes import ModbusGroup, ModbusDefaultGroups, ModbusDatapoint, EntityDataSensor

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup sensor from a config entry created in the integrations UI."""

    entry_type = config_entry.data.get("conf_type")

    # -------------------------------------------------------------
    # 1. ENDPOINT SENSORS (Statistics)
    # -------------------------------------------------------------
    if entry_type == TYPE_ENDPOINT:
        # Get the manager
        bus_manager = hass.data[DOMAIN]["endpoints"].get(config_entry.entry_id)
        if not bus_manager:
            return

        entities = []
        entities.append(ModbusEndpointCounterSensor(bus_manager, config_entry, "packets", "packets"))
        entities.append(ModbusEndpointCounterSensor(bus_manager, config_entry, "bits", "bits"))
        entities.append(ModbusEndpointRateSensor(bus_manager, config_entry))
        entities.append(ModbusEndpointUtilizationSensor(bus_manager, config_entry))
        entities.append(ModbusEndpointQueueSensor(bus_manager, config_entry))
        entities.append(ModbusEndpointHealthSensor(bus_manager, config_entry, hass))
        async_add_entities(entities, False)
        return

    # -------------------------------------------------------------
    # 2. DEVICE SENSORS
    # -------------------------------------------------------------
    # Legacy handling: if no type, assume device
    if not entry_type or entry_type == TYPE_DEVICE:
        coordinator:ModbusCoordinator = hass.data[DOMAIN].get(config_entry.entry_id)
        if not coordinator:
            return

        # Load entities
        ha_entities = []
        for group, datapoints in coordinator._modbusDevice.Datapoints.items():
            if group != ModbusDefaultGroups.CONFIG:
                for key, datapoint in datapoints.items():
                    if isinstance(datapoint.entity_data, EntityDataSensor):
                        ha_entities.append(ModbusSensorEntity(coordinator, group, key, datapoint))

        # Add Device Counters (Diagnostic)
        ha_entities.append(ModbusDeviceCounterSensor(coordinator, "packets", "packets"))
        ha_entities.append(ModbusDeviceCounterSensor(coordinator, "bits", "bits"))

        async_add_entities(ha_entities, False)


class ModbusSensorEntity(ModbusBaseEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator:ModbusCoordinator, group:ModbusGroup, key:str, modbusDataPoint:ModbusDatapoint):
        """Initialize ModbusBaseEntity."""
        super().__init__(coordinator, group, key, modbusDataPoint)

    def _loadEntitySettings(self):
        """Sensor Entity properties"""
        self._attr_device_class = self.modbusDataPoint.entity_data.deviceClass
        self._attr_state_class = self.modbusDataPoint.entity_data.stateClass
        self._attr_native_unit_of_measurement = self.modbusDataPoint.entity_data.units
        self._attr_suggested_display_precision = self.modbusDataPoint.entity_data.precision

        """Cusom Entity properties"""
        self.enum = self.modbusDataPoint.entity_data.enum

    @property
    def native_value(self):
        """Return the value of the sensor."""
        val = self.coordinator.get_value(self._group, self._key)

        # Check if self.enum exists and is a dictionary
        if self.enum and isinstance(self.enum, dict):
            mapped_value = self.enum.get(val)
            if mapped_value is not None:
                return mapped_value
            else:
                return val
        else:
            # If no enum, return the raw value
            return val

class ModbusDeviceCounterSensor(SensorEntity):
    """Sensor for tracking packets/bits for a specific device."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: ModbusCoordinator, counter_type: str, unit: str):
        self.coordinator = coordinator
        self._counter_type = counter_type # 'packets' or 'bits'

        self._attr_native_unit_of_measurement = unit
        self._attr_name = f"Total {counter_type.capitalize()}"
        self._attr_unique_id = f"{coordinator.device_id}_total_{counter_type}"
        self._attr_device_info = {
            "identifiers": coordinator.identifiers,
        }

    @property
    def native_value(self):
        device = self.coordinator._modbusDevice
        if self._counter_type == 'packets':
            return device.traffic.tx_count + device.traffic.rx_count
        elif self._counter_type == 'bits':
            return (device.traffic.tx_bytes + device.traffic.rx_bytes) * 8
        return 0

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        """Connect to dispatcher."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

class ModbusEndpointCounterSensor(SensorEntity):
    """Sensor for tracking packets/bits for a shared endpoint (Bus)."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_has_entity_name = True

    def __init__(self, bus_manager, config_entry, counter_type: str, unit: str):
        self.bus_manager = bus_manager
        self._counter_type = counter_type

        self._attr_native_unit_of_measurement = unit
        self._attr_name = f"Total {counter_type.capitalize()}"
        self._attr_unique_id = f"{config_entry.entry_id}_total_{counter_type}"

        # Link to the Endpoint Device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
            manufacturer="Modbus Endpoint",
            model="Bus Statistics",
        )

    @property
    def native_value(self):
        if self._counter_type == 'packets':
            return self.bus_manager.traffic.tx_count + self.bus_manager.traffic.rx_count
        elif self._counter_type == 'bits':
            return self.bus_manager.traffic.tx_bytes * 8 + self.bus_manager.traffic.rx_bytes * 8
        return 0

    @property
    def available(self) -> bool:
        return True

    @property
    def should_poll(self) -> bool:
        return True

class ModbusEndpointRateSensor(SensorEntity):
    """Sensor for tracking average bits per second for an endpoint."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "bps"
    _attr_name = "Average Data Rate"

    def __init__(self, bus_manager, config_entry):
        self.bus_manager = bus_manager
        self._unique_id = f"{config_entry.entry_id}_rate_bps"

        # Internal state for calculating rate
        self._last_total_bits = 0
        self._last_time = time.time()
        self._current_rate = 0.0

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
            manufacturer="Modbus Endpoint",
            model="Bus Statistics",
        )

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_value(self):
        return round(self._current_rate, 2)

    @property
    def should_poll(self) -> bool:
        return True

    def update(self):
        """Calculate the rate since last poll."""
        current_bits = self.bus_manager.traffic.tx_bytes * 8 + self.bus_manager.traffic.rx_bytes * 8
        current_time = time.time()

        delta_bits = current_bits - self._last_total_bits
        delta_time = current_time - self._last_time

        # Avoid division by zero
        if delta_time > 0:
            self._current_rate = delta_bits / delta_time

        self._last_total_bits = current_bits
        self._last_time = current_time


class ModbusEndpointHealthSensor(SensorEntity):
    """Sensor for tracking overall bus health and connected devices status."""

    _attr_has_entity_name = True
    _attr_name = "Bus Health"

    def __init__(self, bus_manager, config_entry, hass=None):
        self.bus_manager = bus_manager
        self.config_entry = config_entry
        self._hass = hass
        self._unique_id = f"{config_entry.entry_id}_bus_health"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
            manufacturer="Modbus Endpoint",
            model="Bus Statistics",
        )

    def _get_endpoint_coordinators(self) -> list[ModbusCoordinator]:
        hass = self._hass or getattr(self, "hass", None)
        if not hass:
            return []
        coordinators = []
        domain_data = hass.data.get(DOMAIN, {})
        for entry_id, obj in domain_data.items():
            if isinstance(obj, ModbusCoordinator):
                dev_entry = hass.config_entries.async_get_entry(entry_id)
                if dev_entry and dev_entry.data.get("endpoint_id") == self.config_entry.entry_id:
                    coordinators.append(obj)
        return coordinators

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_value(self) -> str:
        if not self.bus_manager.connected:
            return "Disconnected"

        coordinators = self._get_endpoint_coordinators()
        failed_coords = [c for c in coordinators if not c.last_update_success] if coordinators else []

        total = len(coordinators) if coordinators else self.bus_manager.total_devices_count
        if total == 0:
            return "No Devices"

        active = self.bus_manager.active_devices_count
        errors = self.bus_manager.error_devices_count

        if len(failed_coords) == total and total > 0:
            return "Offline"

        if failed_coords or errors > 0:
            return "Degraded"

        if active == 0 and total > 0:
            return "Offline"

        return "OK"

    @property
    def icon(self) -> str:
        state = self.native_value
        if state == "OK":
            return "mdi:check-network"
        elif state == "Degraded":
            return "mdi:alert-network"
        return "mdi:close-network"

    @property
    def extra_state_attributes(self) -> dict:
        traffic = self.bus_manager.traffic
        coordinators = self._get_endpoint_coordinators()
        failed_devices = [
            f"{c.devicename} (Slave {getattr(c._modbusDevice, '_slave_id', '?')})"
            for c in coordinators if not c.last_update_success
        ]
        return {
            "total_devices": len(coordinators) if coordinators else self.bus_manager.total_devices_count,
            "active_devices": self.bus_manager.active_devices_count,
            "devices_with_errors": max(len(failed_devices), self.bus_manager.error_devices_count),
            "failed_devices": failed_devices,
            "problem_slave_ids": self.bus_manager.problem_slaves,
            "timeouts_total": traffic.timeouts,
            "crc_errors_total": traffic.crc_errors,
            "modbus_exceptions_total": traffic.exceptions,
            "connection_errors_total": traffic.connection_errors,
            "last_error_type": traffic.last_error_type,
            "bus_utilization_percent": getattr(self.bus_manager, "utilization_percent", 0.0),
            "queue_depth": getattr(self.bus_manager, "queue_depth", 0),
            "error_summary": {
                "timeouts": traffic.timeouts,
                "crc_errors": traffic.crc_errors,
                "exceptions": traffic.exceptions,
                "connection_errors": traffic.connection_errors,
            },
        }

    @property
    def available(self) -> bool:
        return True

    @property
    def should_poll(self) -> bool:
        return True


class ModbusEndpointUtilizationSensor(SensorEntity):
    """Sensor for tracking bus utilization percentage for an endpoint."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "%"
    _attr_name = "Bus Utilization"
    _attr_icon = "mdi:gauge"

    def __init__(self, bus_manager, config_entry):
        self.bus_manager = bus_manager
        self._unique_id = f"{config_entry.entry_id}_bus_utilization"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
            manufacturer="Modbus Endpoint",
            model="Bus Statistics",
        )

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_value(self):
        return getattr(self.bus_manager, "utilization_percent", 0.0)

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def available(self) -> bool:
        return True


class ModbusEndpointQueueSensor(SensorEntity):
    """Sensor for tracking current request queue depth for an endpoint."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "requests"
    _attr_name = "Bus Queue Depth"
    _attr_icon = "mdi:tray-full"

    def __init__(self, bus_manager, config_entry):
        self.bus_manager = bus_manager
        self._unique_id = f"{config_entry.entry_id}_queue_depth"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
            manufacturer="Modbus Endpoint",
            model="Bus Statistics",
        )

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_value(self):
        return getattr(self.bus_manager, "queue_depth", 0)

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def available(self) -> bool:
        return True

