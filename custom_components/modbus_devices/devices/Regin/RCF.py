####################################################
##### Based on RCF MAN EN 210504               #####
####################################################

import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import ModbusDatapoint, ModbusGroup, ModbusDefaultGroups, ModbusMode, ModbusPollMode
from ..datatypes import EntityDataSensor, EntityDataSelect, EntityDataNumber, EntityDataBinarySensor, EntityDataSwitch, EntityDataButton

from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.const import PERCENTAGE
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.number import NumberDeviceClass

_LOGGER = logging.getLogger(__name__)

# Define groups
GROUP_DEVICE_INFO = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ONCE)
GROUP_SENSORS = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)

class Device(ModbusDevice):
    # Override static device information
    manufacturer = "Regin"
    model = "RCF"

    def loadDatapoints(self):
        # DEVICE_INFO - Read-only
        self.Datapoints[GROUP_DEVICE_INFO] = {
            "Software Type": ModbusDatapoint(address=1, entity_data=EntityDataSensor(enum={0: "RCP", 1: "RC"})),
            "Major version": ModbusDatapoint(address=2),
            "Minor version": ModbusDatapoint(address=3),
            "Branch version": ModbusDatapoint(address=4),
            "Revision": ModbusDatapoint(address=5),
        }

        # SENSORS - Read
        self.Datapoints[GROUP_SENSORS] = {
            "Current running mode": ModbusDatapoint(address=7, entity_data=EntityDataSensor(enum={0: "Off", 1: "Economy/Standby", 2: "Not Used", 3: "Not Used", 4: "Comfort"})),
            "Current control": ModbusDatapoint(address=8, entity_data=EntityDataSensor(enum={0: "Off", 1: "Heating", 2: "Cooling"})),
            "Current fan speed": ModbusDatapoint(address=9, entity_data=EntityDataSensor(enum={0: "Off", 1: "Fan speed 1", 2: "Fan speed 2", 3: "Fan speed 3"})),
            
            "Room temperature": ModbusDatapoint(address=11, scaling=0.1, entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.TEMPERATURE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfTemperature.CELSIUS)),
            "Room temperature external": ModbusDatapoint(address=12, scaling=0.1, entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.TEMPERATURE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfTemperature.CELSIUS)),
            "Room temperature internal": ModbusDatapoint(address=13, scaling=0.1, entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.TEMPERATURE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfTemperature.CELSIUS)),
            "Change over temperature": ModbusDatapoint(address=14, scaling=0.1, entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.TEMPERATURE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfTemperature.CELSIUS)),
            
            "Controller setpoint": ModbusDatapoint(address=20, scaling=0.1),
            "Controller output signal": ModbusDatapoint(address=21, scaling=0.1, entity_data=EntityDataSensor(units=PERCENTAGE)),
            "Heating output signal": ModbusDatapoint(address=22, scaling=0.1, entity_data=EntityDataSensor(units=PERCENTAGE)),
            "Cooling output signal": ModbusDatapoint(address=23, scaling=0.1, entity_data=EntityDataSensor(units=PERCENTAGE)),
        }

        # CONFIGURATION - Read/Write
        self.Datapoints[ModbusDefaultGroups.CONFIG] = {
            "Fan speed 1 output": ModbusDatapoint(address=7, entity_data=EntityDataNumber(units=PERCENTAGE, icon="mdi:fan", min_value=0, max_value=100, step=1)),
            "Fan speed 2 output": ModbusDatapoint(address=8, entity_data=EntityDataNumber(units=PERCENTAGE, icon="mdi:fan", min_value=0, max_value=100, step=1)),
            "Fan speed 3 output": ModbusDatapoint(address=9, entity_data=EntityDataNumber(units=PERCENTAGE, icon="mdi:fan", min_value=0, max_value=100, step=1)),
        }


    def onAfterFirstRead(self):
        # Update device info

        a = self.Datapoints[GROUP_DEVICE_INFO]["Software Type"].value
        b = self.Datapoints[GROUP_DEVICE_INFO]["Major version"].value
        c = self.Datapoints[GROUP_DEVICE_INFO]["Minor version"].value
        d = self.Datapoints[GROUP_DEVICE_INFO]["Branch version"].value
        e = self.Datapoints[GROUP_DEVICE_INFO]["Revision"].value
        self.sw_version = '{}{}.{}.{}-{}'.format(a,b,c,d,e)
