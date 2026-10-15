"""Support for Regin RCF fan coil controllers via Modbus."""
import logging

from ..modbusdevice import ModbusDevice
from ..const import ModbusMode, ModbusPollMode
from ..datatypes import (
    ModbusDatapoint,
    ModbusGroup,
    ModbusDefaultGroups,
    ModbusSensor,
    ModbusSelect,
    ModbusNumber,
)

from homeassistant.const import (
    UnitOfTemperature,
    UnitOfTime,
    PERCENTAGE,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.number import NumberDeviceClass

_LOGGER = logging.getLogger(__name__)

# Define groups
GROUP_DEVICE_INFO = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ONCE)
GROUP_SENSORS = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)
GROUP_CONTROL = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ON)

class Device(ModbusDevice):
    """Representation of a Regin RCF Modbus device."""

    # Override static device information
    manufacturer = "Regin"
    model = "RCF"

    def loadDatapoints(self):
        # DEVICE_INFO - Read-only
        self.Datapoints[GROUP_DEVICE_INFO] = {
            "Software Type": ModbusSensor(
                address=1,
                enum={0: "RCP", 1: "RC"},
                category=EntityCategory.DIAGNOSTIC
            ),
            "Major version": ModbusSensor(
                address=2,
                category=EntityCategory.DIAGNOSTIC
            ),
            "Minor version": ModbusSensor(
                address=3,
                category=EntityCategory.DIAGNOSTIC
            ),
            "Branch version": ModbusSensor(
                address=4,
                category=EntityCategory.DIAGNOSTIC
            ),
            "Revision": ModbusSensor(
                address=5,
                category=EntityCategory.DIAGNOSTIC
            ),
        }

        # SENSORS - Read (Input Registers Function 04)
        self.Datapoints[GROUP_SENSORS] = {
            "Current running mode": ModbusSensor(
                address=7,
                enum={
                    0: "Off",
                    1: "Economy/Standby",
                    2: "Not Used",
                    3: "Not Used",
                    4: "Comfort",
                },
            ),
            "Current control": ModbusSensor(
                address=8,
                enum={
                    0: "Off",
                    1: "Heating",
                    2: "Cooling",
                },
            ),
            "Current fan speed": ModbusSensor(
                address=9,
                enum={
                    0: "Off",
                    1: "Speed 1",
                    2: "Speed 2",
                    3: "Speed 3",
                },
            ),
            "Room temperature": ModbusSensor(
                address=11,
                scaling=0.1,
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS
            ),
            "Room temperature external": ModbusSensor(
                address=12,
                scaling=0.1,
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS
            ),
            "Room temperature internal": ModbusSensor(
                address=13,
                scaling=0.1,
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS
            ),
            "Change over temperature": ModbusSensor(
                address=14,
                scaling=0.1,
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS
            ),
            "Controller setpoint": ModbusSensor(
                address=20,
                scaling=0.1,
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS
            ),
            "Controller output signal": ModbusSensor(
                address=21,
                scaling=0.1,
                stateClass=SensorStateClass.MEASUREMENT,
                units=PERCENTAGE
            ),
            "Heating output signal": ModbusSensor(
                address=22,
                scaling=0.1,
                stateClass=SensorStateClass.MEASUREMENT,
                units=PERCENTAGE
            ),
            "Cooling output signal": ModbusSensor(
                address=23,
                scaling=0.1,
                stateClass=SensorStateClass.MEASUREMENT,
                units=PERCENTAGE
            ),
            "Supply air temperature": ModbusSensor(
                address=47,
                scaling=0.1,
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS,
            ),
            "Supply air PID output": ModbusSensor(
                address=48,
                scaling=0.1,
                stateClass=SensorStateClass.MEASUREMENT,
                units=PERCENTAGE
            ),
            "Supply air setpoint": ModbusSensor(
                address=49,
                scaling=0.1,
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS,
            ),
        }

        # CONTROL - Read/Write (Holding Registers Function 03)
        self.Datapoints[GROUP_CONTROL] = {
            "Fan Mode": ModbusSelect(
                address=5,
                options={
                    0: "Off",
                    1: "Manual 1",
                    2: "Manual 2",
                    3: "Manual 3",
                    4: "Auto",
                },
            ),
            "Remote State": ModbusSelect(
                address=14,
                options={
                    0: "Off",
                    1: "Economy/Standby",
                    4: "Comfort",
                    5: "No Remote",
                },
            ),
            "Setpoint Offset": ModbusNumber(
                address=76,
                scaling=0.1,
                min_value=-10,
                max_value=10,
                step=0.1,
                units=UnitOfTemperature.CELSIUS,
                deviceClass=NumberDeviceClass.TEMPERATURE
            ),
        }

        # CONFIGURATION - Read/Write (Holding Registers Function 03)
        self.Datapoints[ModbusDefaultGroups.CONFIG] = {
            "Basic Setpoint": ModbusNumber(
                address=284,
                scaling=0.1,
                deviceClass=NumberDeviceClass.TEMPERATURE,
                units=UnitOfTemperature.CELSIUS,
                min_value=10,
                max_value=35,
                step=0.1
            ),
            "Change-over Select": ModbusSelect(
                address=13,
                options={
                    0: "Heating",
                    1: "Cooling",
                    2: "Auto",
                },
            ),
            "Fan speed 1 output": ModbusNumber(
                address=7,
                units=PERCENTAGE,
                icon="mdi:fan",
                min_value=0,
                max_value=100,
                step=1
            ),
            "Fan speed 2 output": ModbusNumber(
                address=8,
                units=PERCENTAGE,
                icon="mdi:fan",
                min_value=0,
                max_value=100,
                step=1
            ),
            "Fan speed 3 output": ModbusNumber(
                address=9,
                units=PERCENTAGE,
                icon="mdi:fan",
                min_value=0,
                max_value=100,
                step=1
            ),
            "Modbus Slave Address": ModbusNumber(
                address=44,
                min_value=1,
                max_value=247,
                category=EntityCategory.DIAGNOSTIC
            ),
            "Modbus Parity": ModbusSelect(
                address=45,
                options={
                    0: "8N2",
                    1: "8O1",
                    2: "8E1",
                    3: "8N1",
                },
                category=EntityCategory.DIAGNOSTIC,
            ),
            "Modbus Char Timeout": ModbusNumber(
                address=46,
                units=UnitOfTime.MILLISECONDS,
                category=EntityCategory.DIAGNOSTIC
            ),
            "Modbus Answer Delay": ModbusNumber(
                address=47,
                units=UnitOfTime.MILLISECONDS,
                category=EntityCategory.DIAGNOSTIC
            ),
            "Display Backlight Low": ModbusNumber(
                address=48,
                min_value=0,
                max_value=100,
                units=PERCENTAGE,
                category=EntityCategory.CONFIG
            ),
            "Display Backlight High": ModbusNumber(
                address=49,
                min_value=0,
                max_value=100,
                units=PERCENTAGE,
                category=EntityCategory.CONFIG
            ),
            "Display Contrast": ModbusNumber(
                address=50,
                min_value=0,
                max_value=15,
                category=EntityCategory.CONFIG
            ),
            "Display View Mode": ModbusSelect(
                address=51,
                options={
                    0: "Temp/Setp",
                    1: "Temp/Setp",
                    2: "Setpoint",
                    3: "Offset",
                },
                category=EntityCategory.CONFIG,
            ),
        }

    def onAfterFirstRead(self):
        # Update device info

        a = self.Datapoints[GROUP_DEVICE_INFO]["Software Type"].value
        b = self.Datapoints[GROUP_DEVICE_INFO]["Major version"].value
        c = self.Datapoints[GROUP_DEVICE_INFO]["Minor version"].value
        d = self.Datapoints[GROUP_DEVICE_INFO]["Branch version"].value
        e = self.Datapoints[GROUP_DEVICE_INFO]["Revision"].value
        self.sw_version = '{}{}.{}.{}-{}'.format(a,b,c,d,e)