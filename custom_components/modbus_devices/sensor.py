import logging

from homeassistant.components.sensor import SensorEntity

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

    async_add_entities(ha_entities, False)

class ModbusSensorEntity(ModbusBaseEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator:ModbusCoordinator, group:ModbusGroup, key:str, modbusDataPoint:ModbusDatapoint):
        """Initialize ModbusBaseEntity."""
        super().__init__(coordinator, group, key, modbusDataPoint)

        """Sensor Entity properties"""
        self._attr_device_class = modbusDataPoint.entity_data.deviceClass
        self._attr_state_class = modbusDataPoint.entity_data.stateClass
        self._attr_native_unit_of_measurement = modbusDataPoint.entity_data.units

        """Cusom Entity properties"""
        self.enum = modbusDataPoint.entity_data.enum

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