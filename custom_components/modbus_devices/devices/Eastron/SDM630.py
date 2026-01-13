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
    EntityDataButton,
)
from homeassistant.helpers.entity import EntityCategory

# Import correct unit constants
from homeassistant.const import (
    UnitOfAngle,
    UnitOfElectricPotential, 
    UnitOfElectricCurrent, 
    UnitOfPower, 
    UnitOfEnergy,
    UnitOfApparentPower,
    UnitOfReactivePower,
    POWER_FACTOR,
    UnitOfFrequency,
    PERCENTAGE,
    UnitOfTime,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.button import ButtonDeviceClass

_LOGGER = logging.getLogger(__name__)

# Define groups
GROUP_MAIN = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)

class Device(ModbusDevice):
    # Override static device information
    manufacturer = "Eastron"
    model = "SDM630"

    def loadDatapoints(self):
        # MAIN SENSORS (INPUT REGISTERS)
        self.Datapoints[GROUP_MAIN] = {
            "Phase 1 line to neutral volts": ModbusDatapoint(address=0, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.VOLTAGE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricPotential.VOLT, enabled_default=False)),
            "Phase 2 line to neutral volts": ModbusDatapoint(address=2, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.VOLTAGE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricPotential.VOLT, enabled_default=False)),
            "Phase 3 line to neutral volts": ModbusDatapoint(address=4, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.VOLTAGE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricPotential.VOLT, enabled_default=False)),
            "Phase 1 current": ModbusDatapoint(address=6, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.CURRENT, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricCurrent.AMPERE, enabled_default=False)),
            "Phase 2 current": ModbusDatapoint(address=8, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.CURRENT, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricCurrent.AMPERE, enabled_default=False)),
            "Phase 3 current": ModbusDatapoint(address=10, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.CURRENT, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricCurrent.AMPERE, enabled_default=False)),
            "Phase 1 power": ModbusDatapoint(address=12, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfPower.WATT, enabled_default=False)),
            "Phase 2 power": ModbusDatapoint(address=14, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfPower.WATT, enabled_default=False)),
            "Phase 3 power": ModbusDatapoint(address=16, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfPower.WATT, enabled_default=False)),
            "Phase 1 volt amps (VA)": ModbusDatapoint(address=18, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.APPARENT_POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfApparentPower.VOLT_AMPERE, enabled_default=False)),
            "Phase 2 volt amps (VA)": ModbusDatapoint(address=20, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.APPARENT_POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfApparentPower.VOLT_AMPERE, enabled_default=False)),
            "Phase 3 volt amps (VA)": ModbusDatapoint(address=22, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.APPARENT_POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfApparentPower.VOLT_AMPERE, enabled_default=False)),
            "Phase 1 reactive power": ModbusDatapoint(address=24, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.REACTIVE_POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfReactivePower.VAR, enabled_default=False)),
            "Phase 2 reactive power": ModbusDatapoint(address=26, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.REACTIVE_POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfReactivePower.VAR, enabled_default=False)),
            "Phase 3 reactive power": ModbusDatapoint(address=28, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.REACTIVE_POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfReactivePower.VAR, enabled_default=False)),
            "Phase 1 power factor": ModbusDatapoint(address=30, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.POWER_FACTOR, stateClass=SensorStateClass.MEASUREMENT, units=POWER_FACTOR, enabled_default=False)),
            "Phase 2 power factor": ModbusDatapoint(address=32, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.POWER_FACTOR, stateClass=SensorStateClass.MEASUREMENT, units=POWER_FACTOR, enabled_default=False)),
            "Phase 3 power factor": ModbusDatapoint(address=34, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.POWER_FACTOR, stateClass=SensorStateClass.MEASUREMENT, units=POWER_FACTOR, enabled_default=False)),
            "Phase 1 phase angle": ModbusDatapoint(address=36, length=2, type='float', entity_data=EntityDataSensor(stateClass=SensorStateClass.MEASUREMENT, units=UnitOfAngle.DEGREES, icon="mdi:angle-acute", enabled_default=False)),
            "Phase 2 phase angle": ModbusDatapoint(address=38, length=2, type='float', entity_data=EntityDataSensor(stateClass=SensorStateClass.MEASUREMENT, units=UnitOfAngle.DEGREES, icon="mdi:angle-acute", enabled_default=False)),
            "Phase 3 phase angle": ModbusDatapoint(address=40, length=2, type='float', entity_data=EntityDataSensor(stateClass=SensorStateClass.MEASUREMENT, units=UnitOfAngle.DEGREES, icon="mdi:angle-acute", enabled_default=False)),
            "Average line to neutral volts": ModbusDatapoint(address=42, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.VOLTAGE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricPotential.VOLT, enabled_default=False)),
            "Average line current": ModbusDatapoint(address=46, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.CURRENT, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricCurrent.AMPERE, enabled_default=False)),
            "Sum of line currents": ModbusDatapoint(address=48, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.CURRENT, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricCurrent.AMPERE, enabled_default=False)),
            "Total system power": ModbusDatapoint(address=52, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfPower.WATT, enabled_default=False)),
            "Total system volt amps": ModbusDatapoint(address=56, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.APPARENT_POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfApparentPower.VOLT_AMPERE, enabled_default=False)),
            "Total system VAr": ModbusDatapoint(address=60, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.REACTIVE_POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfReactivePower.VAR, enabled_default=False)),
            "Total system power factor": ModbusDatapoint(address=62, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.POWER_FACTOR, stateClass=SensorStateClass.MEASUREMENT, units=POWER_FACTOR, enabled_default=False)),
            "Total system phase angle": ModbusDatapoint(address=66, length=2, type='float', entity_data=EntityDataSensor(stateClass=SensorStateClass.MEASUREMENT, units=UnitOfAngle.DEGREES, icon="mdi:angle-acute", enabled_default=False)),
            "Frequency of supply voltages": ModbusDatapoint(address=70, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.FREQUENCY, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfFrequency.HERTZ, enabled_default=False)),
            "Total Import kWh": ModbusDatapoint(address=72, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.ENERGY, stateClass=SensorStateClass.TOTAL_INCREASING, units=UnitOfEnergy.KILO_WATT_HOUR, enabled_default=False)),
            "Total Export kWh": ModbusDatapoint(address=74, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.ENERGY, stateClass=SensorStateClass.TOTAL_INCREASING, units=UnitOfEnergy.KILO_WATT_HOUR, enabled_default=False)),
            "Total Import kVArh": ModbusDatapoint(address=76, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.ENERGY, stateClass=SensorStateClass.TOTAL_INCREASING, units="kVArh", enabled_default=False)),
            "Total Export kVArh": ModbusDatapoint(address=78, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.ENERGY, stateClass=SensorStateClass.TOTAL_INCREASING, units="kVArh", enabled_default=False)),
            "Total VAh": ModbusDatapoint(address=80, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.ENERGY, stateClass=SensorStateClass.TOTAL_INCREASING, units="kVAh", enabled_default=False)),
            "Ah": ModbusDatapoint(address=82, length=2, type='float', entity_data=EntityDataSensor(stateClass=SensorStateClass.TOTAL_INCREASING, units="Ah", enabled_default=False)),
            "Total system power demand": ModbusDatapoint(address=84, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfPower.WATT, enabled_default=True)),
            "Maximum total system power demand": ModbusDatapoint(address=86, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.APPARENT_POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfApparentPower.VOLT_AMPERE, enabled_default=True)),
            "Total system VA demand": ModbusDatapoint(address=100, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.APPARENT_POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfApparentPower.VOLT_AMPERE, enabled_default=True)),
            "Max total system VA demand": ModbusDatapoint(address=102, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.APPARENT_POWER, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfApparentPower.VOLT_AMPERE, enabled_default=True)),
            "Neutral current demand": ModbusDatapoint(address=104, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.CURRENT, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricCurrent.AMPERE, enabled_default=True)),
            "Max neutral current demand": ModbusDatapoint(address=106, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.CURRENT, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricCurrent.AMPERE, enabled_default=True)),
            "Line 1 to Line 2 volts": ModbusDatapoint(address=200, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.VOLTAGE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricPotential.VOLT, enabled_default=False)),
            "Line 2 to Line 3 volts": ModbusDatapoint(address=202, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.VOLTAGE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricPotential.VOLT, enabled_default=False)),
            "Line 3 to Line 1 volts": ModbusDatapoint(address=204, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.VOLTAGE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricPotential.VOLT, enabled_default=False)),
            "Average line to line volts": ModbusDatapoint(address=206, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.VOLTAGE, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricPotential.VOLT, enabled_default=False)),
            "Neutral current": ModbusDatapoint(address=224, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.CURRENT, stateClass=SensorStateClass.MEASUREMENT, units=UnitOfElectricCurrent.AMPERE, enabled_default=False)),
            "Phase 1 L/N volts THD": ModbusDatapoint(address=234, length=2, type='float', entity_data=EntityDataSensor(stateClass=SensorStateClass.MEASUREMENT, units=PERCENTAGE, enabled_default=False)),
            "Phase 1 Current THD": ModbusDatapoint(address=240, length=2, type='float', entity_data=EntityDataSensor(stateClass=SensorStateClass.MEASUREMENT, units=PERCENTAGE, enabled_default=False)),
            "Total kWh": ModbusDatapoint(address=342, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.ENERGY, stateClass=SensorStateClass.TOTAL_INCREASING, units=UnitOfEnergy.KILO_WATT_HOUR, enabled_default=False)),
            "Total kVArh": ModbusDatapoint(address=344, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.ENERGY, stateClass=SensorStateClass.TOTAL_INCREASING, units="kVArh", enabled_default=False)),
            "L3 total kVArh": ModbusDatapoint(address=380, length=2, type='float', entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.ENERGY, stateClass=SensorStateClass.TOTAL_INCREASING, units="kVArh", enabled_default=False)),
        }

        # CONFIGURATION (HOLDING REGISTERS)
        self.Datapoints[ModbusDefaultGroups.CONFIG] = {
            "Demand Period": ModbusDatapoint(
                address=2, type='uint', length=1,
                entity_data=EntityDataSelect(options={0: "0 min", 5: "5 min", 8: "8 min", 10: "10 min", 15: "15 min", 20: "20 min", 30: "30 min", 60: "60 min"}, category=EntityCategory.CONFIG, enabled_default=True)
            ),
            "System Type": ModbusDatapoint(
                address=10, type='uint', length=1,
                entity_data=EntityDataSelect(options={1: "1P2W", 2: "3P3W", 3: "3P4W"}, category=EntityCategory.CONFIG, enabled_default=True)
            ),
            "Pulse1 Width": ModbusDatapoint(
                address=12, type='uint', length=1,
                entity_data=EntityDataSelect(options={60: "60 ms", 100: "100 ms", 200: "200 ms"}, category=EntityCategory.CONFIG, enabled_default=False)
            ),
            "Password Lock": ModbusDatapoint(
                address=14, type='uint', length=1,
                entity_data=EntityDataSelect(options={0: "Disabled", 1: "Enabled"}, category=EntityCategory.CONFIG, enabled_default=False)
            ),
            "Network Parity Stop": ModbusDatapoint(
                address=18, type='uint', length=1,
                entity_data=EntityDataSelect(options={0: "N,1", 1: "E,1", 2: "O,1", 3: "N,2"}, category=EntityCategory.DIAGNOSTIC, enabled_default=True)
            ),
            "Network Node": ModbusDatapoint(
                address=20, type='uint', length=1,
                entity_data=EntityDataNumber(min_value=1, max_value=247, step=1, category=EntityCategory.DIAGNOSTIC, enabled_default=True)
            ),
            "Pulse1 Divisor1": ModbusDatapoint(
                address=22, type='uint', length=1,
                entity_data=EntityDataSelect(options={0: "0.001 kWh/imp", 1: "0.01 kWh/imp", 2: "0.1 kWh/imp", 3: "1 kWh/imp", 4: "10 kWh/imp", 5: "100 kWh/imp"}, category=EntityCategory.CONFIG, enabled_default=False)
            ),
            "Password": ModbusDatapoint(
                address=24, type='uint', length=1,
                entity_data=EntityDataNumber(min_value=0, max_value=9999, step=1, category=EntityCategory.CONFIG, enabled_default=False)
            ),
            "Network Baud Rate": ModbusDatapoint(
                address=28, type='uint', length=1,
                entity_data=EntityDataSelect(options={0: "2400", 1: "4800", 2: "9600", 3: "19200", 4: "38400"}, category=EntityCategory.DIAGNOSTIC, enabled_default=True)
            ),
            "Pulse 1 Energy Type": ModbusDatapoint(
                address=86, type='uint', length=1,
                entity_data=EntityDataSelect(options={1: "Active Energy", 2: "Reactive Energy"}, category=EntityCategory.CONFIG, enabled_default=False)
            ),
            "Reset": ModbusDatapoint(
                address=61456, type='uint', length=1,
                entity_data=EntityDataNumber(min_value=0, max_value=9999, step=1, category=EntityCategory.CONFIG, enabled_default=True)
            ),
            "Serial number": ModbusDatapoint(
                address=64512, type='uint', length=2, # Assuming 2 registers for serial
                entity_data=EntityDataSensor(category=EntityCategory.DIAGNOSTIC, icon="mdi:information-outline", enabled_default=True)
            ),
        }

