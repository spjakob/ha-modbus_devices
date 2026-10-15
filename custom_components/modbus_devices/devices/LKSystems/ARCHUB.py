import logging

from ..modbusdevice import ModbusDevice
from ..const import ModbusMode, ModbusPollMode
from ..datatypes import ModbusDatapoint, ModbusGroup, ModbusDefaultGroups
from ..datatypes import ModbusSensor, ModbusNumber, ModbusSelect

from homeassistant.const import UnitOfTemperature
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
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
            "Serial Number": ModbusDatapoint(address=0, register_count=4, type='uint'),     # 4 registers for a 64-bit value
            "Software Version Major": ModbusDatapoint(address=4, type='uint'),
            "Software Version Minor": ModbusDatapoint(address=5, type='uint'),
            "Software Version Micro": ModbusDatapoint(address=6, type='uint'),
            # Address 50 is used for both Input (Number of Zones) and Holding (Temp Alarm) registers. This is valid in Modbus.
            "Number Of Zones": ModbusDatapoint(address=50, type='uint'),
        }

        # UNIT_STATUSES - Read
        self.Datapoints[GROUP_UNIT_STATUSES] = {
            "Actuator 1": ModbusSensor(address=60,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
            "Actuator 2": ModbusSensor(address=61,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
            "Actuator 3": ModbusSensor(address=62,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
            "Actuator 4": ModbusSensor(address=63,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
            "Actuator 5": ModbusSensor(address=64,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
            "Actuator 6": ModbusSensor(address=65,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
            "Actuator 7": ModbusSensor(address=66,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
            "Actuator 8": ModbusSensor(address=67,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
            "Actuator 9": ModbusSensor(address=68,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
            "Actuator 10": ModbusSensor(address=69,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
            "Actuator 11": ModbusSensor(address=70,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
            "Actuator 12": ModbusSensor(address=71,enum={0: "Closed", 1: "Open", 2: "Unallocated"}),
        }

        # ALARMS - Read-only
        self.Datapoints[GROUP_ALARMS] = {
            "Cooling Emergency Mode": ModbusSensor(address=80,enum={0: "Normal Mode", 1: "Emergency Mode"}),
        }

        # COMMANDS - Read/Write
        self.Datapoints[GROUP_COMMANDS] = {
            "Operating Mode": ModbusSelect(address=0, options={0: "Undefined", 1: "Heating", 2: "Cooling"}),
            "LED Enable": ModbusSelect(address=58, options={0: "Disable", 1: "Enable"}),
        }

        # CONFIGURATION - Read/Write
        self.Datapoints[ModbusDefaultGroups.CONFIG] = {
            "Temperature Alarm High Level": ModbusNumber(address=50, scaling=0.1, deviceClass=NumberDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS, min_value=-100, max_value=100, step=0.1),
            "Temperature Alarm Low Level": ModbusNumber(address=51, scaling=0.1, deviceClass=NumberDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS, min_value=-100, max_value=100, step=0.1),
            "Humidity Alarm High Level": ModbusNumber(address=52, scaling=0.1, deviceClass=NumberDeviceClass.HUMIDITY, units=PERCENTAGE, min_value=0, max_value=100, step=0.1),
            "Humidity Alarm Low Level": ModbusNumber(address=53, scaling=0.1, deviceClass=NumberDeviceClass.HUMIDITY, units=PERCENTAGE, min_value=0, max_value=100, step=0.1),
            "Battery Alarm Low Level": ModbusNumber(address=54, scaling=0.1, deviceClass=NumberDeviceClass.BATTERY, units=PERCENTAGE, min_value=0, max_value=100, step=0.1),
            "Battery Alarm Critical Level": ModbusNumber(address=55, scaling=0.1, deviceClass=NumberDeviceClass.BATTERY, units=PERCENTAGE, min_value=0, max_value=100, step=0.1),
            "Cooling Emergency Number of Zones": ModbusNumber(address=56, min_value=0, max_value=12),
            "Coling Mode Humidity Limit": ModbusNumber(address=57, scaling=0.1, deviceClass=NumberDeviceClass.HUMIDITY, units=PERCENTAGE, min_value=0, max_value=100, step=0.1),
        }

    async def onAfterFirstRead(self):
        # Update device info
        self.serial_number = self.Datapoints[GROUP_DEVICE_INFO]["Serial Number"].value
        number_of_zones = self.Datapoints[GROUP_DEVICE_INFO]["Number Of Zones"].value

        a = self.Datapoints[GROUP_DEVICE_INFO]["Software Version Major"].value
        b = self.Datapoints[GROUP_DEVICE_INFO]["Software Version Minor"].value
        c = self.Datapoints[GROUP_DEVICE_INFO]["Software Version Micro"].value
        self.sw_version = f"{a}.{b}.{c}"

        _LOGGER.info(
            "Initial setup of %s from %s with serial number %s running firmware version %s:", 
            self.model, self.manufacturer, self.serial_number, self.sw_version
        )
        _LOGGER.info("%s zones detected and activating entities for these", number_of_zones)
        
        # Dynamically assign SENSOR datapoints to a separate group for each zone
        for i in range(1, int(number_of_zones) + 1):
            # Create a new dynamic group
            self.dynamic_groups[f"GROUP_SENSORS_ZONE_{i}"] = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)

            base_register = i * 100
            _LOGGER.debug("Setting up zone %s adding temperature register %s ", i, base_register)

            # Assign a dictionary of datapoints to the new dynamic group
            self.Datapoints[self.dynamic_groups[f"GROUP_SENSORS_ZONE_{i}"]] = {
                f"Zone {i} Actual Temperature": ModbusSensor(
                    address=base_register,
                    scaling=0.1,
                    deviceClass=SensorDeviceClass.TEMPERATURE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfTemperature.CELSIUS),
                f"Zone {i} Actual Humidity": ModbusSensor(
                    address=base_register + 1,
                    type='uint',
                    scaling=0.1,
                    deviceClass=SensorDeviceClass.HUMIDITY, stateClass=SensorStateClass.MEASUREMENT, units=PERCENTAGE),
                f"Zone {i} Actual Battery": ModbusSensor(
                    address=base_register + 2,
                    type='uint',
                    deviceClass=SensorDeviceClass.BATTERY, stateClass=SensorStateClass.MEASUREMENT, units=PERCENTAGE),
                f"Zone {i} Actual Signal Strength": ModbusSensor(
                    address=base_register + 3,
                    deviceClass=SensorDeviceClass.SIGNAL_STRENGTH, stateClass=SensorStateClass.MEASUREMENT, units=SIGNAL_STRENGTH_DECIBELS_MILLIWATT),
                f"Zone {i} Thermostat Address Raw": ModbusDatapoint(
                    address=base_register + 4, register_count=3, type='uint'),
                f"Zone {i} Connected Actuators": ModbusDatapoint(
                    address=base_register + 7, type='uint') # Corrected from +6 to +7
            }
        
        # Dynamically assign SETPOINT datapoints to a separate group for each zone
        for i in range(1, number_of_zones + 1):
            # Create a new dynamic group
            self.dynamic_groups[f"GROUP_SETPOINTS_ZONE_{i}"] = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ON)

            base_register = i * 100
            self.Datapoints[self.dynamic_groups[f"GROUP_SETPOINTS_ZONE_{i}"]] = {
                f"Zone {i} Target Temperature": ModbusNumber(
                    address=base_register, 
                    scaling=0.1, 
                    deviceClass=NumberDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS, min_value=-100, max_value=100, step=0.1),
                f"Zone {i} Override ": ModbusSelect(
                    address=base_register + 1, 
                    options={0: "Inactive", 1: "Active"}),
                f"Zone {i} Override Level": ModbusNumber(
                    address=base_register + 2, 
                    min_value=0, max_value=255)
            }

        # Add UI datapoints that are calculated
        for i in range(1, int(number_of_zones) + 1):
            self.Datapoints.setdefault(GROUP_UNIT_STATUSES, {})[f"Zone {i} Thermostat Address"] = ModbusSensor(icon="mdi:network-outline")
            self.Datapoints.setdefault(GROUP_UNIT_STATUSES, {})[f"Zone {i} Connected Actuators List"] = ModbusSensor(icon="mdi:valve")

    async def onAfterRead(self):
        number_of_zones = self.Datapoints[GROUP_DEVICE_INFO]["Number Of Zones"].value
        for i in range(1, int(number_of_zones) + 1):
            # Format the thermostat MAC address
            try:
                raw_mac_int = self.Datapoints[self.dynamic_groups[f"GROUP_SENSORS_ZONE_{i}"]][f"Zone {i} Thermostat Address Raw"].value
                if isinstance(raw_mac_int, int) and raw_mac_int > 0:
                    # Convert 48-bit integer to a byte string
                    mac_bytes = raw_mac_int.to_bytes(6, 'big')
                    # Format as a standard MAC address
                    formatted_mac = ":".join(f"{b:02X}" for b in mac_bytes)
                    self.Datapoints[GROUP_UNIT_STATUSES][f"Zone {i} Thermostat Address"].value = formatted_mac
                else:
                    self.Datapoints[GROUP_UNIT_STATUSES][f"Zone {i} Thermostat Address"].value = "N/A"
            except (KeyError, AttributeError, TypeError):
                 self.Datapoints[GROUP_UNIT_STATUSES][f"Zone {i} Thermostat Address"].value = "Error"

            # Parse the connected actuators bitfield
            try:
                bitfield = self.Datapoints[self.dynamic_groups[f"GROUP_SENSORS_ZONE_{i}"]][f"Zone {i} Connected Actuators"].value
                if isinstance(bitfield, int):
                    connected = []
                    for j in range(12):
                        if (bitfield >> j) & 1:
                            connected.append(str(j + 1))
                    self.Datapoints[GROUP_UNIT_STATUSES][f"Zone {i} Connected Actuators List"].value = ", ".join(connected) if connected else "None"
                else:
                    self.Datapoints[GROUP_UNIT_STATUSES][f"Zone {i} Connected Actuators List"].value = "N/A"
            except (KeyError, AttributeError, TypeError):
                self.Datapoints[GROUP_UNIT_STATUSES][f"Zone {i} Connected Actuators List"].value = "Error"
