import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import ModbusDatapoint, ModbusGroup, ModbusMode, ModbusPollMode
from ..datatypes import ModbusSensorData

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
            "Humidity": ModbusDatapoint(Address=0, Scaling=0.1, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.HUMIDITY, stateClass=SensorStateClass.MEASUREMENT, units=PERCENTAGE)),
            "Temperature": ModbusDatapoint(Address=1, Scaling=0.1, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.TEMPERATURE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfTemperature.CELSIUS)),
        }