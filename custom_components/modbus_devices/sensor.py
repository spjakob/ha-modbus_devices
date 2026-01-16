import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity

from .devices.datatypes import ModbusGroup, ModbusDefaultGroups, ModbusDatapoint, EntityDataSensor

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup sensor from a config entry created in the integrations UI."""
    # Find coordinator for this device
    coordinator:ModbusCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Load entities
    ha_entities = []

    # 1. Standard Modbus Data Sensors
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        if group != ModbusDefaultGroups.CONFIG:
            for key, datapoint in datapoints.items():
                if isinstance(datapoint.entity_data, EntityDataSensor):
                    ha_entities.append(ModbusSensorEntity(coordinator, group, key, datapoint))

    # 2. Device Statistics Sensors
    ha_entities.append(ModbusDeviceCounterSensor(coordinator, "packets", "packets"))
    ha_entities.append(ModbusDeviceCounterSensor(coordinator, "bits", "bits"))

    # 3. Endpoint (Bus) Statistics Sensors
    bus_manager = coordinator.rtu_bus or coordinator.tcp_bus
    if bus_manager and not bus_manager.sensors_created:
        bus_manager.sensors_created = True

        # Determine endpoint identifier and name
        if coordinator.rtu_bus:
            endpoint_id = f"rtu_{coordinator.rtu_bus.port}"
            endpoint_name = f"Modbus Endpoint {coordinator.rtu_bus.port}"
        else:
            endpoint_id = f"tcp_{coordinator.tcp_bus.host}_{coordinator.tcp_bus.port}"
            endpoint_name = f"Modbus Endpoint {coordinator.tcp_bus.host}:{coordinator.tcp_bus.port}"

        # Create endpoint sensors
        ha_entities.append(ModbusEndpointCounterSensor(coordinator, bus_manager, "packets", "packets", endpoint_id, endpoint_name))
        ha_entities.append(ModbusEndpointCounterSensor(coordinator, bus_manager, "bits", "bits", endpoint_id, endpoint_name))

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
    # Explicitly NOT Diagnostic, as requested

    def __init__(self, coordinator: ModbusCoordinator, bus_manager, counter_type: str, unit: str, endpoint_id: str, endpoint_name: str):
        self.coordinator = coordinator
        self.bus_manager = bus_manager
        self._counter_type = counter_type

        self._attr_native_unit_of_measurement = unit
        self._attr_name = f"Total {counter_type.capitalize()}"
        self._attr_unique_id = f"{endpoint_id}_total_{counter_type}"

        # Create a new Device entry for the Endpoint
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, endpoint_id)},
            name=endpoint_name,
            manufacturer="Modbus Endpoint",
            model="Bus Statistics",
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
        # Endpoint stats are available as long as the coordinator is running
        return True

    async def async_added_to_hass(self):
        """Connect to dispatcher."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
