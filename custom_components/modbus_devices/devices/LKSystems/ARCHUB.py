import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import ModbusDatapoint, ModbusGroup, ModbusDefaultGroups, ModbusMode, ModbusPollMode
from ..datatypes import ModbusSensorData, ModbusNumberData, ModbusSelectData

from homeassistant.const import UnitOfTemperature
from homeassistant.const import PERCENTAGE
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.number import NumberDeviceClass

_LOGGER = logging.getLogger(__name__)

# Define static groups
GROUP_DEVICE_INFO = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ONCE)
GROUP_UNIT_STATUSES = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)  
GROUP_ALARMS = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)
GROUP_COMMANDS = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ON)

class Device(ModbusDevice):
    # Override static device information
    manufacturer="LKSystems"
    model="ARCHUB"

     # Dict that stores dynamic groups
    dynamic_groups: dict[str, ModbusGroup] = {}

    def loadDatapoints(self):
        # DEVICE_INFO - Read-only
        self.Datapoints[GROUP_DEVICE_INFO] = {
            "Serial Number": ModbusDatapoint(Address=0, Length=4),     # 4 registers for a 64-bit value
            "Software Version Major": ModbusDatapoint(Address=4),
            "Software Version Minor": ModbusDatapoint(Address=5),
            "Software Version Micro": ModbusDatapoint(Address=6),
            "Number Of Zones": ModbusDatapoint(Address=50),
        }

        # UNIT_STATUSES - Read
        self.Datapoints[GROUP_UNIT_STATUSES] = {
            "Actuator 1": ModbusDatapoint(Address=60,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
            "Actuator 2": ModbusDatapoint(Address=61,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
            "Actuator 3": ModbusDatapoint(Address=62,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
            "Actuator 4": ModbusDatapoint(Address=63,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
            "Actuator 5": ModbusDatapoint(Address=64,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
            "Actuator 6": ModbusDatapoint(Address=65,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
            "Actuator 7": ModbusDatapoint(Address=66,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
            "Actuator 8": ModbusDatapoint(Address=67,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
            "Actuator 9": ModbusDatapoint(Address=68,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
            "Actuator 10": ModbusDatapoint(Address=69,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
            "Actuator 11": ModbusDatapoint(Address=70,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
            "Actuator 12": ModbusDatapoint(Address=71,DataType=ModbusSensorData(enum={0: "Closed", 1: "Open", 2: "Unallocated"})),
        }

        # ALARMS - Read-only
        self.Datapoints[GROUP_ALARMS] = {
            "Cooling Emergency Mode": ModbusDatapoint(Address=80,DataType=ModbusSensorData(enum={0: "Normal Mode", 1: "Emergency Mode"})),
        }

        # COMMANDS - Read/Write
        self.Datapoints[GROUP_COMMANDS] = {
            "Operating Mode": ModbusDatapoint(Address=0, DataType=ModbusSelectData(options={0: "Undefined", 1: "Heating", 2: "Cooling"})),
            "LED Enable": ModbusDatapoint(Address=58, DataType=ModbusSelectData(options={0: "Disable", 1: "Enable"})),
        }

        # CONFIGURATION - Read/Write
        self.Datapoints[ModbusDefaultGroups.CONFIG] = {
            "Temperature Alarm High Level": ModbusDatapoint(Address=50, Scaling=0.1, DataType=ModbusNumberData(deviceClass=NumberDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS, min_value=-100, max_value=100, step=0.1)),
            "Temperature Alarm Low Level": ModbusDatapoint(Address=51, Scaling=0.1, DataType=ModbusNumberData(deviceClass=NumberDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS, min_value=-100, max_value=100, step=0.1)),
            "Humidity Alarm High Level": ModbusDatapoint(Address=52, Scaling=0.1, DataType=ModbusNumberData(deviceClass=NumberDeviceClass.HUMIDITY, units=PERCENTAGE, min_value=0, max_value=100, step=0.1)),
            "Humidity Alarm Low Level": ModbusDatapoint(Address=53, Scaling=0.1, DataType=ModbusNumberData(deviceClass=NumberDeviceClass.HUMIDITY, units=PERCENTAGE, min_value=0, max_value=100, step=0.1)),
            "Battery Alarm Low Level": ModbusDatapoint(Address=54, Scaling=0.1, DataType=ModbusNumberData(deviceClass=NumberDeviceClass.BATTERY, units=PERCENTAGE, min_value=0, max_value=100, step=0.1)),
            "Battery Alarm Critical Level": ModbusDatapoint(Address=55, Scaling=0.1, DataType=ModbusNumberData(deviceClass=NumberDeviceClass.BATTERY, units=PERCENTAGE, min_value=0, max_value=100, step=0.1)),
            "Cooling Emergency Number of Zones": ModbusDatapoint(Address=56, DataType=ModbusNumberData(min_value=0, max_value=12)),
            "Coling Mode Humidity Limit": ModbusDatapoint(Address=57, Scaling=0.1, DataType=ModbusNumberData(deviceClass=NumberDeviceClass.HUMIDITY, units=PERCENTAGE, min_value=0, max_value=100, step=0.1)),
        }

    def onAfterFirstRead(self):
        # Update device info
#       serial_registers = self.Datapoints[GROUP_DEVICE_INFO]["Serial Number"].Value
#       packed_bytes = struct.pack('>HHHH', *serial_registers)
#       self.serial_number = struct.unpack('>Q', packed_bytes)[0]
        self.serial_number=42
        number_of_zones = self.Datapoints[GROUP_DEVICE_INFO]["Number Of Zones"].Value

        a = self.Datapoints[GROUP_DEVICE_INFO]["Software Version Major"].Value
        b = self.Datapoints[GROUP_DEVICE_INFO]["Software Version Minor"].Value
        c = self.Datapoints[GROUP_DEVICE_INFO]["Software Version Micro"].Value
        self.sw_version = f"{a}.{b}.{c}"

        _LOGGER.info(
            "Initial setup of %s from %s with serial number %s running firmware version %s:", 
            self.model, self.manufacturer, self.serial_number, self.sw_version
        )
        _LOGGER.info("%s zones detected and activating entities for these", number_of_zones)
        
        # Dynamically assign SENSOR datapoints to a separate group for each zone
        for i in range(1, number_of_zones + 1):
            # Create a new dynamic group
            self.dynamic_groups[f"GROUP_SENSORS_ZONE_{i}"] = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)

            base_register = i * 100
            _LOGGER.debug("Setting up zone %s adding temperature register %s ", i, base_register)

            # Assign a dictionary of datapoints to the new dynamic group
            self.Datapoints[self.dynamic_groups[f"GROUP_SENSORS_ZONE_{i}"]] = {
                f"Zone {i} Actual Temperature": ModbusDatapoint(
                    Address=base_register,
                    Scaling=0.1,
                    DataType=ModbusSensorData(deviceClass=NumberDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS)),
                f"Zone {i} Actual Humidity": ModbusDatapoint(
                    Address=base_register + 1,
                    Scaling=0.1,
                    DataType=ModbusSensorData(deviceClass=SensorDeviceClass.HUMIDITY, units=PERCENTAGE)),
                f"Zone {i} Actual Battery": ModbusDatapoint(
                    Address=base_register + 2,
                    DataType=ModbusSensorData(deviceClass=SensorDeviceClass.BATTERY, units=PERCENTAGE)),
                f"Zone {i} Actual Signal Strength": ModbusDatapoint(
                    Address=base_register + 3),
                f"Zone {i} Thermostat Address": ModbusDatapoint(
                    Address=base_register + 4, Length=3),
                f"Zone {i} Connected Actuators": ModbusDatapoint(
                    Address=base_register + 6)
            }
        
        # Dynamically assign SETPOINT datapoints to a separate group for each zone
        for i in range(1, number_of_zones + 1):
            # Create a new dynamic group
            self.dynamic_groups[f"GROUP_SETPOINTS_ZONE_{i}"] = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ON)

            base_register = i * 100
            self.Datapoints[self.dynamic_groups[f"GROUP_SETPOINTS_ZONE_{i}"]] = {
                f"Zone {i} Target Temperature": ModbusDatapoint(
                    Address=base_register, 
                    Scaling=0.1, 
                    DataType=ModbusNumberData(deviceClass=NumberDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS, min_value=-100, max_value=100, step=0.1)),
                f"Zone {i} Override ": ModbusDatapoint(
                    Address=base_register + 1, 
                    DataType=ModbusSelectData(options={0: "Inactive", 1: "Active"})),
                f"Zone {i} Override Level": ModbusDatapoint(
                    Address=base_register + 2, 
                    DataType=ModbusNumberData(min_value=0, max_value=255))
            }
