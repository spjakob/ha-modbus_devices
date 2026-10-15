"""Support for Grundfos MAGNA3 pumps via Modbus."""
import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import (
    ModbusDatapoint,
    ModbusGroup,
    ModbusDefaultGroups,
    ModbusSensor,
    ModbusNumber,
    ModbusSelect,
)
from ..const import ModbusMode, ModbusPollMode

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
            "Head": ModbusSensor(
                address=300,
                scaling=0.001,
                deviceClass=SensorDeviceClass.PRESSURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfPressure.BAR,
            ),
            "Volume Flow": ModbusSensor(
                address=301,
                scaling=0.1,
                deviceClass=SensorDeviceClass.VOLUME_FLOW_RATE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
                precision=1,
            ),
            "Relative Performance": ModbusSensor(
                address=302,
                scaling=0.01,
                stateClass=SensorStateClass.MEASUREMENT,
                units=PERCENTAGE,
                icon="mdi:gauge",
            ),
            "Motor Speed": ModbusSensor(
                address=303,
                scaling=1,
                stateClass=SensorStateClass.MEASUREMENT,
                units=REVOLUTIONS_PER_MINUTE,
                icon="mdi:fan",
            ),
            "Frequency": ModbusSensor(
                address=304,
                scaling=0.1,
                deviceClass=SensorDeviceClass.FREQUENCY,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfFrequency.HERTZ,
            ),
            "Actual Setpoint": ModbusSensor(
                address=307,
                scaling=0.01,
                stateClass=SensorStateClass.MEASUREMENT,
                units=PERCENTAGE,
                icon="mdi:target",
            ),
            "Motor Current": ModbusSensor(
                address=308,
                scaling=0.1,
                deviceClass=SensorDeviceClass.CURRENT,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfElectricCurrent.AMPERE,
            ),
            "Total Power (Electrical)": ModbusSensor(
                address=311,
                register_count=2,
                type="uint",
                scaling=1,
                deviceClass=SensorDeviceClass.POWER,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfPower.WATT,
            ),
            "Power Electronics Temp": ModbusSensor(
                address=317,
                scaling=0.01,
                offset=-273.15,
                # Disabled: Pump reports 0 (invalid) despite datasheet saying supported
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS,
                enabledDefault=False,
            ),
            "Electronics Temp": ModbusSensor(
                address=320,
                scaling=0.01,
                offset=-273.15,
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS,
            ),
            "Pump Liquid Temperature": ModbusSensor(
                address=321,
                scaling=0.01,
                offset=-273.15,
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS,
            ),
            "Specific Energy Consumption": ModbusSensor(
                address=325,
                scaling=1,
                stateClass=SensorStateClass.MEASUREMENT,
                units="Wh/m³",
                icon="mdi:lightning-bolt",
            ),
            "Operating Time": ModbusSensor(
                address=326,
                register_count=2,
                type="uint",
                scaling=1,
                deviceClass=SensorDeviceClass.DURATION,
                stateClass=SensorStateClass.TOTAL_INCREASING,
                units=UnitOfTime.HOURS,
            ),
            "Total Energy (Electrical)": ModbusSensor(
                address=331,
                register_count=2,
                type="uint",
                scaling=1,
                deviceClass=SensorDeviceClass.ENERGY,
                stateClass=SensorStateClass.TOTAL_INCREASING,
                units=UnitOfEnergy.KILO_WATT_HOUR,
            ),
            "Number of Starts": ModbusSensor(
                address=333,
                register_count=2,
                type="uint",
                scaling=1,
                stateClass=SensorStateClass.TOTAL_INCREASING,
                units="starts",
                icon="mdi:counter",
            ),
            "Remote Temperature 2": ModbusSensor(
                address=336,
                scaling=0.01,
                offset=-273.15,
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS,
            ),
            "User Setpoint": ModbusSensor(
                address=337,
                scaling=0.01,
                stateClass=SensorStateClass.MEASUREMENT,
                units=PERCENTAGE,
                icon="mdi:target",
            ),
            "Differential Pressure": ModbusSensor(
                address=338,
                scaling=0.001,
                deviceClass=SensorDeviceClass.PRESSURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfPressure.BAR,
            ),
            "Max Flow Limit": ModbusSensor(
                address=344,
                scaling=0.1,
                deviceClass=SensorDeviceClass.VOLUME_FLOW_RATE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
            ),
            "Heat Energy": ModbusSensor(
                address=351,
                register_count=2,
                type="uint",
                deviceClass=SensorDeviceClass.ENERGY,
                stateClass=SensorStateClass.TOTAL_INCREASING,
                units=UnitOfEnergy.KILO_WATT_HOUR,
            ),
            "Heat Power": ModbusSensor(
                address=353,
                register_count=2,
                type="uint",
                scaling=0.001,
                deviceClass=SensorDeviceClass.POWER,  # Fixed: kW is Power, not Energy
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfPower.KILO_WATT,
            ),
            "Heat Differential Temp": ModbusSensor(
                address=355,
                scaling=0.01,
                deviceClass=SensorDeviceClass.TEMPERATURE,
                stateClass=SensorStateClass.MEASUREMENT,
                units=UnitOfTemperature.CELSIUS,
            ),
            "Volume 1": ModbusSensor(
                address=356,
                register_count=2,
                type="uint",
                scaling=0.01,
                deviceClass=SensorDeviceClass.WATER,
                stateClass=SensorStateClass.TOTAL_INCREASING,
                units=UnitOfVolume.CUBIC_METERS,
            ),
            "Volume 2": ModbusSensor(
                address=360,
                register_count=2,
                type="uint",
                scaling=0.01,
                deviceClass=SensorDeviceClass.WATER,
                stateClass=SensorStateClass.TOTAL_INCREASING,
                units=UnitOfVolume.CUBIC_METERS,
            ),
        }

        # CONFIGURATION - Read/Write
        self.Datapoints[ModbusDefaultGroups.CONFIG] = {
            "Software Defined Modbus Address": ModbusNumber(
                address=2,
                min_value=1,
                max_value=247,
                step=1,
                category=EntityCategory.DIAGNOSTIC,
            ),
            "Software Defined Bit Rate": ModbusSelect(
                address=3,
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
            "Auto Ack Control Bits": ModbusSelect(
                address=4,
                options={
                    0: "Disabled",
                    1: "Enabled",
                },
                category=EntityCategory.DIAGNOSTIC,
            ),
            "Software Defined Parity": ModbusSelect(
                address=8,
                options={
                    0: "No parity",
                    1: "Even parity",
                    2: "Odd parity",
                },
                category=EntityCategory.DIAGNOSTIC,
            ),
        }