"""Support for Grundfos MAGNA3 pumps via Modbus."""
import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import (
    ModbusDatapoint,
    ModbusGroup,
    ModbusDefaultGroups,
    EntityDataSensor,
    EntityDataNumber,
    EntityDataSelect,
)
from ..const import ModbusMode, ModbusPollMode
from ..datatypes import ModbusDatapoint, ModbusGroup
from ..datatypes import EntityDataSensor

from homeassistant.const import (
    UnitOfPressure,
    UnitOfVolumeFlowRate,
    UnitOfFrequency,
    UnitOfTemperature,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfElectricCurrent,
    UnitOfTime,
    UnitOfVolume,
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import EntityCategory

_LOGGER = logging.getLogger(__name__)

# Define groups
GROUP_INPUTS = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)


class Device(ModbusDevice):
    """Representation of a Grundfos MAGNA3 Modbus device."""

    # Override static device information
    manufacturer = "Grundfos"
    model = "MAGNA3"

    def loadDatapoints(self):
        # SENSORS (Input Registers)
        self.Datapoints[GROUP_INPUTS] = {
            "Head": ModbusDatapoint(
                address=300,
                scaling=0.001,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.PRESSURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPressure.BAR,
                ),
            ),
            "Volume Flow": ModbusDatapoint(
                address=301,
                scaling=0.1,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLUME_FLOW_RATE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
                ),
            ),
            "Relative Performance": ModbusDatapoint(
                address=302,
                scaling=0.01,
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    icon="mdi:gauge",
                ),
            ),
            "Motor Speed": ModbusDatapoint(
                address=303,
                scaling=1,
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=REVOLUTIONS_PER_MINUTE,
                    icon="mdi:fan",
                ),
            ),
            "Frequency": ModbusDatapoint(
                address=304,
                scaling=0.1,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.FREQUENCY,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfFrequency.HERTZ,
                ),
            ),
            "Actual Setpoint": ModbusDatapoint(
                address=307,
                scaling=0.01,
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    icon="mdi:target",
                ),
            ),
            "Motor Current": ModbusDatapoint(
                address=308,
                scaling=0.1,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                ),
            ),
            "Total Power (Electrical)": ModbusDatapoint(
                address=311,
                length=2,
                type="uint",
                scaling=1,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPower.WATT,
                ),
            ),
            "Power Electronics Temp": ModbusDatapoint(
                address=317,
                scaling=0.01,
                offset=-273.15,
                # Disabled: Pump reports 0 (invalid) despite datasheet saying supported
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.TEMPERATURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfTemperature.CELSIUS,
                    enabledDefault=False,
                ),
            ),
            "Electronics Temp": ModbusDatapoint(
                address=320,
                scaling=0.01,
                offset=-273.15,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.TEMPERATURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfTemperature.CELSIUS,
                ),
            ),
            "Pump Liquid Temperature": ModbusDatapoint(
                address=321,
                scaling=0.01,
                offset=-273.15,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.TEMPERATURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfTemperature.CELSIUS,
                ),
            ),
            "Specific Energy Consumption": ModbusDatapoint(
                address=325,
                scaling=1,
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units="Wh/m³",
                    icon="mdi:lightning-bolt",
                ),
            ),
            "Operating Time": ModbusDatapoint(
                address=326,
                length=2,
                type="uint",
                scaling=1,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.DURATION,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfTime.HOURS,
                ),
            ),
            "Total Energy (Electrical)": ModbusDatapoint(
                address=331,
                length=2,
                type="uint",
                scaling=1,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                ),
            ),
            "Number of Starts": ModbusDatapoint(
                address=333,
                length=2,
                type="uint",
                scaling=1,
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="starts",
                    icon="mdi:counter",
                ),
            ),
            "Remote Temperature 2": ModbusDatapoint(
                address=336,
                scaling=0.01,
                offset=-273.15,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.TEMPERATURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfTemperature.CELSIUS,
                ),
            ),
            "User Setpoint": ModbusDatapoint(
                address=337,
                scaling=0.01,
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    icon="mdi:target",
                ),
            ),
            "Differential Pressure": ModbusDatapoint(
                address=338,
                scaling=0.001,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.PRESSURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPressure.BAR,
                ),
            ),
            "Max Flow Limit": ModbusDatapoint(
                address=344,
                scaling=0.1,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLUME_FLOW_RATE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
                ),
            ),
            "Heat Energy": ModbusDatapoint(
                address=351,
                length=2,
                type="uint",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                ),
            ),
            "Heat Power": ModbusDatapoint(
                address=353,
                length=2,
                type="uint",
                scaling=0.001,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER,  # Fixed: kW is Power, not Energy
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPower.KILO_WATT,
                ),
            ),
            "Heat Differential Temp": ModbusDatapoint(
                address=355,
                scaling=0.01,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.TEMPERATURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfTemperature.CELSIUS,
                ),
            ),
            "Volume 1": ModbusDatapoint(
                address=356,
                length=2,
                type="uint",
                scaling=0.01,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.WATER,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfVolume.CUBIC_METERS,
                ),
            ),
            "Volume 2": ModbusDatapoint(
                address=360,
                length=2,
                type="uint",
                scaling=0.01,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.WATER,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfVolume.CUBIC_METERS,
                ),
            ),
        }

        # CONFIGURATION - Read/Write
        self.Datapoints[ModbusDefaultGroups.CONFIG] = {
            "Software Defined Modbus Address": ModbusDatapoint(
                address=2,
                entity_data=EntityDataNumber(
                    min_value=1,
                    max_value=247,
                    step=1,
                    category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            "Software Defined Bit Rate": ModbusDatapoint(
                address=3,
                entity_data=EntityDataSelect(
                    options={
                        0: "1200 bit/s",
                        1: "2400 bit/s",
                        2: "4800 bit/s",
                        3: "9600 bit/s",
                        4: "19200 bit/s",
                        5: "38400 bit/s",
                    },
                    category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            "Auto Ack Control Bits": ModbusDatapoint(
                address=4,
                entity_data=EntityDataSelect(
                    options={
                        0: "Disabled",
                        1: "Enabled",
                    },
                    category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            "Software Defined Parity": ModbusDatapoint(
                address=8,
                entity_data=EntityDataSelect(
                    options={
                        0: "No parity",
                        1: "Even parity",
                        2: "Odd parity",
                    },
                    category=EntityCategory.DIAGNOSTIC,
                ),
            ),
        }