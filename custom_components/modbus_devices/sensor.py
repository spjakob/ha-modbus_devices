import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        if group != ModbusDefaultGroups.CONFIG:
            for key, datapoint in datapoints.items():
                if isinstance(datapoint.entity_data, EntityDataSensor):
                    ha_entities.append(ModbusSensorEntity(coordinator, group, key, datapoint))

    # --- Add bus statistics sensors ---
    if not hass.data[DOMAIN].get("bus_sensors_added"):
        hass.data[DOMAIN]["bus_sensors_added"] = True
        bus_coordinators = hass.data[DOMAIN].get("bus_coordinators", {})
        for bus_coordinator in bus_coordinators.values():
            ha_entities.append(BusStatisticsSensor(bus_coordinator, "sent"))
            ha_entities.append(BusStatisticsSensor(bus_coordinator, "received"))

async_add_entities(ha_entities, True)

class BusStatisticsSensor(CoordinatorEntity, SensorEntity):
    """Representation of a bus statistics sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "B"
    _attr_has_entity_name = True
    _attr_entity_category = "diagnostic"

    def __init__(self, coordinator, sensor_type: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type # "sent" or "received"
        self._attr_unique_id = f"bus_{coordinator.endpoint}_{sensor_type}"
        self._attr_name = f"Bytes {sensor_type}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self._sensor_type)
        return None

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