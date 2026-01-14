"""Support for Eastron SDM630 via Modbus."""
import logging

from ..modbusdevice import ModbusDevice
from ..const import ModbusMode, ModbusPollMode
from ..datatypes import (
    ModbusDatapoint,
    ModbusGroup,
    ModbusDefaultGroups,
    EntityDataSensor,
    EntityDataNumber,
    EntityDataSelect,
)

from homeassistant.const import (
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
    UnitOfPower,
    UnitOfEnergy,
    UnitOfApparentPower,
    UnitOfReactivePower,
    DEGREE,
    UnitOfFrequency,
    PERCENTAGE,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import EntityCategory

_LOGGER = logging.getLogger(__name__)

# Define groups
GROUP_INPUT_1 = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)
GROUP_INPUT_2 = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)
GROUP_INPUT_3 = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)
GROUP_INPUT_4 = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)
GROUP_INPUT_5 = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)
GROUP_HOLDING_RESET = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ONCE)
GROUP_HOLDING_INFO = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ONCE)

class Device(ModbusDevice):
    """Representation of an Eastron SDM630 Modbus device."""

    # Override static device information
    manufacturer = "Eastron"
    model = "SDM630"

    def loadDatapoints(self):
        # MAIN SENSORS (INPUT REGISTERS)
        self.Datapoints[GROUP_INPUT_1] = {
            "Phase 1 line to neutral volts": ModbusDatapoint(
                address=0,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLTAGE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricPotential.VOLT,
                    enabledDefault=True,
                ),
            ),
            "Phase 2 line to neutral volts": ModbusDatapoint(
                address=2,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLTAGE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricPotential.VOLT,
                    enabledDefault=True,
                ),
            ),
            "Phase 3 line to neutral volts": ModbusDatapoint(
                address=4,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLTAGE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricPotential.VOLT,
                    enabledDefault=True,
                ),
            ),
            "Phase 1 current": ModbusDatapoint(
                address=6,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Phase 2 current": ModbusDatapoint(
                address=8,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Phase 3 current": ModbusDatapoint(
                address=10,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Phase 1 power": ModbusDatapoint(
                address=12,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPower.WATT,
                    enabledDefault=True,
                ),
            ),
            "Phase 2 power": ModbusDatapoint(
                address=14,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPower.WATT,
                    enabledDefault=True,
                ),
            ),
            "Phase 3 power": ModbusDatapoint(
                address=16,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPower.WATT,
                    enabledDefault=True,
                ),
            ),
            "Phase 1 volt amps (VA)": ModbusDatapoint(
                address=18,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.APPARENT_POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfApparentPower.VOLT_AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Phase 2 volt amps (VA)": ModbusDatapoint(
                address=20,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.APPARENT_POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfApparentPower.VOLT_AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Phase 3 volt amps (VA)": ModbusDatapoint(
                address=22,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.APPARENT_POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfApparentPower.VOLT_AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Phase 1 reactive power": ModbusDatapoint(
                address=24,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.REACTIVE_POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
                    enabledDefault=True,
                ),
            ),
            "Phase 2 reactive power": ModbusDatapoint(
                address=26,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.REACTIVE_POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
                    enabledDefault=True,
                ),
            ),
            "Phase 3 reactive power": ModbusDatapoint(
                address=28,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.REACTIVE_POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
                    enabledDefault=True,
                ),
            ),
            "Phase 1 power factor": ModbusDatapoint(
                address=30,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER_FACTOR,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=None,
                    enabledDefault=False,
                ),
            ),
            "Phase 2 power factor": ModbusDatapoint(
                address=32,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER_FACTOR,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=None,
                    enabledDefault=False,
                ),
            ),
            "Phase 3 power factor": ModbusDatapoint(
                address=34,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER_FACTOR,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=None,
                    enabledDefault=False,
                ),
            ),
            "Phase 1 phase angle": ModbusDatapoint(
                address=36,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=DEGREE,
                    icon="mdi:angle-acute",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "Phase 2 phase angle": ModbusDatapoint(
                address=38,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=DEGREE,
                    icon="mdi:angle-acute",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "Phase 3 phase angle": ModbusDatapoint(
                address=40,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=DEGREE,
                    icon="mdi:angle-acute",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "Average line to neutral volts": ModbusDatapoint(
                address=42,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLTAGE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricPotential.VOLT,
                    enabledDefault=True,
                ),
            ),
            "Average line current": ModbusDatapoint(
                address=46,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Sum of line currents": ModbusDatapoint(
                address=48,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Total system power": ModbusDatapoint(
                address=52,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPower.WATT,
                    enabledDefault=True,
                ),
            ),
            "Total system volt amps": ModbusDatapoint(
                address=56,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.APPARENT_POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfApparentPower.VOLT_AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Total system VAr": ModbusDatapoint(
                address=60,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.REACTIVE_POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
                    enabledDefault=True,
                ),
            ),
            "Total system power factor": ModbusDatapoint(
                address=62,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER_FACTOR,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=None,
                    enabledDefault=False,
                ),
            ),
            "Total system phase angle": ModbusDatapoint(
                address=66,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=DEGREE,
                    icon="mdi:angle-acute",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "Frequency of supply voltages": ModbusDatapoint(
                address=70,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.FREQUENCY,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfFrequency.HERTZ,
                    enabledDefault=True,
                ),
            ),
            "Total Import kWh": ModbusDatapoint(
                address=72,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=True,
                    precision=0,
                ),
            ),
            "Total Export kWh": ModbusDatapoint(
                address=74,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=True,
                    precision=0,
                ),
            ),
            "Total Import kVArh": ModbusDatapoint(
                address=76,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=True,
                    precision=0,
                ),
            ),
            "Total Export kVArh": ModbusDatapoint(
                address=78,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=True,
                    precision=0,
                ),
            ),
            "Total VAh": ModbusDatapoint(
                address=80,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVAh",
                    enabledDefault=True,
                    precision=0,
                ),
            ),
            "Ah": ModbusDatapoint(
                address=82,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="Ah",
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Total system power demand": ModbusDatapoint(
                address=84,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPower.WATT,
                    enabledDefault=True,
                ),
            ),
            "Maximum total system power demand": ModbusDatapoint(
                address=86,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.APPARENT_POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfApparentPower.VOLT_AMPERE,
                    enabledDefault=True,
                ),
            ),
        }
        self.Datapoints[GROUP_INPUT_2] = {
            "Total system VA demand": ModbusDatapoint(
                address=100,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.APPARENT_POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfApparentPower.VOLT_AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Max total system VA demand": ModbusDatapoint(
                address=102,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.APPARENT_POWER,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfApparentPower.VOLT_AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Neutral current demand": ModbusDatapoint(
                address=104,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Max neutral current demand": ModbusDatapoint(
                address=106,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                ),
            ),
        }
        # MAIN SENSORS (INPUT REGISTERS)
        self.Datapoints[GROUP_INPUT_3] = {
            "Line 1 to Line 2 volts": ModbusDatapoint(
                address=200,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLTAGE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricPotential.VOLT,
                    enabledDefault=False,
                ),
            ),
            "Line 2 to Line 3 volts": ModbusDatapoint(
                address=202,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLTAGE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricPotential.VOLT,
                    enabledDefault=False,
                ),
            ),
            "Line 3 to Line 1 volts": ModbusDatapoint(
                address=204,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLTAGE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricPotential.VOLT,
                    enabledDefault=False,
                ),
            ),
            "Average line to line volts": ModbusDatapoint(
                address=206,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLTAGE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricPotential.VOLT,
                    enabledDefault=True,
                ),
            ),
        }
        self.Datapoints[GROUP_INPUT_4] = {
            "Neutral current": ModbusDatapoint(
                address=224,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                ),
            ),
            "Phase 1 L/N volts THD": ModbusDatapoint(
                address=234,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Phase 2 L/N volts THD": ModbusDatapoint(
                address=236,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Phase 3 L/N volts THD": ModbusDatapoint(
                address=238,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Phase 1 Current THD": ModbusDatapoint(
                address=240,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Phase 2 Current THD": ModbusDatapoint(
                address=242,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Phase 3 Current THD": ModbusDatapoint(
                address=244,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Average line to neutral volts THD": ModbusDatapoint(
                address=248,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Average line current THD": ModbusDatapoint(
                address=250,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Phase 1 current demand": ModbusDatapoint(
                address=258,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Phase 2 current demand": ModbusDatapoint(
                address=260,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Phase 3 current demand": ModbusDatapoint(
                address=262,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Maximum phase 1 current demand": ModbusDatapoint(
                address=264,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Maximum phase 2 current demand": ModbusDatapoint(
                address=266,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
            "Maximum phase 3 current demand": ModbusDatapoint(
                address=268,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfElectricCurrent.AMPERE,
                    enabledDefault=True,
                    precision=2,
                ),
            ),
        }
        # MAIN SENSORS (INPUT REGISTERS)
        self.Datapoints[GROUP_INPUT_5] = {
            "Line 1 to line 2 volts THD": ModbusDatapoint(
                address=334,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=False,
                    precision=2,
                ),
            ),
            "Line 2 to line 3 volts THD": ModbusDatapoint(
                address=336,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=False,
                    precision=2,
                ),
            ),
            "Line 3 to line 1 volts THD": ModbusDatapoint(
                address=338,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=False,
                    precision=2,
                ),
            ),
            "Average line to line volts THD": ModbusDatapoint(
                address=340,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=PERCENTAGE,
                    enabledDefault=False,
                    precision=2,
                ),
            ),
            "Total kWh": ModbusDatapoint(
                address=342,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=True,
                    precision=0,
                ),
            ),
            "Total kVArh": ModbusDatapoint(
                address=344,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=True,
                    precision=0,
                ),
            ),
            "L1 import kwh": ModbusDatapoint(
                address=346,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L2 import kwh": ModbusDatapoint(
                address=348,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L3 import kWh": ModbusDatapoint(
                address=350,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L1 export kWh": ModbusDatapoint(
                address=352,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L2 export kwh": ModbusDatapoint(
                address=354,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L3 export kWh": ModbusDatapoint(
                address=356,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L1 total kwh": ModbusDatapoint(
                address=358,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L2 total kWh": ModbusDatapoint(
                address=360,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L3 total kwh": ModbusDatapoint(
                address=362,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR,
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L1 import kvarh": ModbusDatapoint(
                address=364,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L2 import kvarh": ModbusDatapoint(
                address=366,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L3 import kvarh": ModbusDatapoint(
                address=368,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L1 export kvarh": ModbusDatapoint(
                address=370,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L2 export kvarh": ModbusDatapoint(
                address=372,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L3 export kvarh": ModbusDatapoint(
                address=374,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L1 total kvarh": ModbusDatapoint(
                address=376,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L2 total kvarh": ModbusDatapoint(
                address=378,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
            "L3 total kvarh": ModbusDatapoint(
                address=380,
                length=2,
                type="float",
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units="kVArh",
                    enabledDefault=False,
                    precision=0,
                ),
            ),
        }

        # CONFIGURATION (HOLDING REGISTERS)
        self.Datapoints[ModbusDefaultGroups.CONFIG] = {
            "Demand Period": ModbusDatapoint(
                address=2,
                type="float",
                length=2,
                entity_data=EntityDataSelect(
                    options={
                        0: "0 min",
                        5: "5 min",
                        8: "8 min",
                        10: "10 min",
                        15: "15 min",
                        20: "20 min",
                        30: "30 min",
                        60: "60 min",
                    },
                    category=EntityCategory.CONFIG,
                    enabledDefault=True,
                ),
            ),
            "System Type": ModbusDatapoint(
                address=10,
                type="float",
                length=2,
                entity_data=EntityDataSelect(
                    options={1: "1P2W", 2: "3P3W", 3: "3P4W"},
                    category=EntityCategory.CONFIG,
                    enabledDefault=True,
                ),
            ),
            "Pulse1 Width": ModbusDatapoint(
                address=12,
                type="float",
                length=2,
                entity_data=EntityDataSelect(
                    options={60: "60 ms", 100: "100 ms", 200: "200 ms"},
                    category=EntityCategory.CONFIG,
                    enabledDefault=False,
                ),
            ),
            "Password Lock": ModbusDatapoint(
                address=14,
                type="float",
                length=2,
                entity_data=EntityDataSelect(
                    options={0: "Disabled", 1: "Enabled"},
                    category=EntityCategory.CONFIG,
                    enabledDefault=False,
                ),
            ),
            "Network Parity Stop": ModbusDatapoint(
                address=18,
                type="float",
                length=2,
                entity_data=EntityDataSelect(
                    options={0: "N,1", 1: "E,1", 2: "O,1", 3: "N,2"},
                    category=EntityCategory.DIAGNOSTIC,
                    enabledDefault=True,
                ),
            ),
            "Network Node": ModbusDatapoint(
                address=20,
                type="float",
                length=2,
                entity_data=EntityDataNumber(
                    min_value=1,
                    max_value=247,
                    step=1,
                    category=EntityCategory.DIAGNOSTIC,
                    enabledDefault=True,
                ),
            ),
            "Pulse1 Divisor1": ModbusDatapoint(
                address=22,
                type="float",
                length=2,
                entity_data=EntityDataSelect(
                    options={
                        0: "0.001 kWh/imp",
                        1: "0.01 kWh/imp",
                        2: "0.1 kWh/imp",
                        3: "1 kWh/imp",
                        4: "10 kWh/imp",
                        5: "100 kWh/imp",
                    },
                    category=EntityCategory.CONFIG,
                    enabledDefault=False,
                ),
            ),
            "Password": ModbusDatapoint(
                address=24,
                type="float",
                length=2,
                entity_data=EntityDataNumber(
                    min_value=0,
                    max_value=9999,
                    step=1,
                    category=EntityCategory.CONFIG,
                    enabledDefault=False,
                ),
            ),
            "Network Baud Rate": ModbusDatapoint(
                address=28,
                type="float",
                length=2,
                entity_data=EntityDataSelect(
                    options={
                        0: "2400",
                        1: "4800",
                        2: "9600",
                        3: "19200",
                        4: "38400",
                    },
                    category=EntityCategory.DIAGNOSTIC,
                    enabledDefault=True,
                ),
            ),
            "Pulse 1 Energy Type": ModbusDatapoint(
                address=86,
                type="float",
                length=2,
                entity_data=EntityDataSelect(
                    options={1: "Active Energy", 2: "Reactive Energy"},
                    category=EntityCategory.CONFIG,
                    enabledDefault=False,
                ),
            ),
        }
        self.Datapoints[GROUP_HOLDING_RESET] = {
            "Reset": ModbusDatapoint(
                address=61456,
                type="uint",
                length=1,
                entity_data=EntityDataNumber(
                    min_value=0,
                    max_value=9999,
                    step=1,
                    category=EntityCategory.CONFIG,
                    enabledDefault=True,
                ),
            ),
        }
        self.Datapoints[GROUP_HOLDING_INFO] = {
            "Serial number": ModbusDatapoint(
                address=64512,
                type="uint",
                length=2,
                entity_data=EntityDataSensor(
                    category=EntityCategory.DIAGNOSTIC,
                    icon="mdi:information-outline",
                    enabledDefault=True,
                ),
            ),
        }