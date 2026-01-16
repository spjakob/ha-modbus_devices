import logging

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
            return device.device_tx_packets + device.device_rx_packets
        elif self._counter_type == 'bits':
            return device.device_tx_bits + device.device_rx_bits
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

        # Link to the Endpoint Device (the Config Entry itself creates a device? No, we need to create one)
        # We use the config entry ID as the device identifier for the Endpoint.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title, # Title is set in Config Flow (e.g. "RTU Endpoint /dev/ttyUSB0")
            manufacturer="Modbus Endpoint",
            model="Bus Statistics",
            # via_device removed to fix warning
        )

    @property
    def native_value(self):
        if self._counter_type == 'packets':
            return self.bus_manager.tx_packets + self.bus_manager.rx_packets
        elif self._counter_type == 'bits':
            return self.bus_manager.tx_bits + self.bus_manager.rx_bits
        return 0

    @property
    def available(self) -> bool:
        return True

    # Note: How does this sensor update?
    # It needs to listen to updates.
    # The BusManager doesn't have a listener mechanism.
    # But when ANY coordinator updates, it schedules an update?
    # Or we can make this sensor poll?
    # Or we can have the ModbusDevice trigger an update on the bus manager?
    # Current implementation of BusManager has `update_counters`.
    # We can add a simple observer pattern to BusManager?
    # Or we can just let HA poll it (it's a local sensor, so it's fast).
    # SensorEntity defaults to push. If `should_poll` is True (default for non-push), HA polls it.
    # So we can just rely on polling.

    @property
    def should_poll(self) -> bool:
        return True
