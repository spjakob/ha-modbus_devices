import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import ModbusDatapoint, ModbusGroup, ModbusMode, ModbusPollMode
from ..datatypes import EntityDataSensor

from homeassistant.const import UnitOfTemperature
from homeassistant.const import PERCENTAGE
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

_LOGGER = logging.getLogger(__name__)

# Define groups
GROUP_SENSORS = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)

class Device(ModbusDevice):
    # Override static device information
    manufacturer="Shandong Renke"
    model="RS-WS-N01-8"

    def loadDatapoints(self):
        # SENSORS - Read-only
        self.Datapoints[GROUP_SENSORS] = {
            "Humidity": ModbusDatapoint(address=0, scaling=0.1, entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.HUMIDITY, stateClass=SensorStateClass.MEASUREMENT, units=PERCENTAGE)),
            "Temperature": ModbusDatapoint(address=1, scaling=0.1, entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.TEMPERATURE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfTemperature.CELSIUS)),
        }