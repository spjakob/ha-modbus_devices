import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import ModbusDatapoint, ModbusGroup, ModbusMode, ModbusPollMode
from ..datatypes import EntityDataSensor

# Import correct unit constants
from homeassistant.const import (
    UnitOfElectricPotential, 
    UnitOfElectricCurrent, 
    UnitOfPower, 
    UnitOfEnergy
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

_LOGGER = logging.getLogger(__name__)

# Define groups
# The YAML specifies "input_type: input", so we use ModbusMode.INPUT
GROUP_MAIN = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)

class Device(ModbusDevice):
    # Override static device information
    manufacturer = "Eastron"
    model = "SDM630"

    def loadDatapoints(self):
        # MAIN SENSORS
        self.Datapoints[GROUP_MAIN] = {
            # Phases - Volts (Float32 = 2 registers)
            "Phase 1 Voltage": ModbusDatapoint(
                address=0, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLTAGE, 
                    stateClass=SensorStateClass.MEASUREMENT, 
                    units=UnitOfElectricPotential.VOLT
                )
            ),
            "Phase 2 Voltage": ModbusDatapoint(
                address=2, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLTAGE, 
                    stateClass=SensorStateClass.MEASUREMENT, 
                    units=UnitOfElectricPotential.VOLT
                )
            ),
            "Phase 3 Voltage": ModbusDatapoint(
                address=4, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLTAGE, 
                    stateClass=SensorStateClass.MEASUREMENT, 
                    units=UnitOfElectricPotential.VOLT
                )
            ),

            # Phases - Current
            "Phase 1 Current": ModbusDatapoint(
                address=6, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT, 
                    stateClass=SensorStateClass.MEASUREMENT, 
                    units=UnitOfElectricCurrent.AMPERE
                )
            ),
            "Phase 2 Current": ModbusDatapoint(
                address=8, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT, 
                    stateClass=SensorStateClass.MEASUREMENT, 
                    units=UnitOfElectricCurrent.AMPERE
                )
            ),
            "Phase 3 Current": ModbusDatapoint(
                address=10, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.CURRENT, 
                    stateClass=SensorStateClass.MEASUREMENT, 
                    units=UnitOfElectricCurrent.AMPERE
                )
            ),

            # Phases - Power
            "Phase 1 Power": ModbusDatapoint(
                address=12, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER, 
                    stateClass=SensorStateClass.MEASUREMENT, 
                    units=UnitOfPower.WATT
                )
            ),
            "Phase 2 Power": ModbusDatapoint(
                address=14, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER, 
                    stateClass=SensorStateClass.MEASUREMENT, 
                    units=UnitOfPower.WATT
                )
            ),
            "Phase 3 Power": ModbusDatapoint(
                address=16, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER, 
                    stateClass=SensorStateClass.MEASUREMENT, 
                    units=UnitOfPower.WATT
                )
            ),

            # Total Power
            "Total Power": ModbusDatapoint(
                address=52, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER, 
                    stateClass=SensorStateClass.MEASUREMENT, 
                    units=UnitOfPower.WATT                    
                )
            ),

            # Total kWh (Import)
            "Total kWh Import": ModbusDatapoint(
                address=72, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY, 
                    stateClass=SensorStateClass.TOTAL_INCREASING, 
                    units=UnitOfEnergy.KILO_WATT_HOUR
                )
            ),

            # Total kWh (Export)
            "Total kWh Export": ModbusDatapoint(
                address=74, 
                length=2, 
                datatype="float32", 
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY, 
                    stateClass=SensorStateClass.TOTAL_INCREASING, 
                    units=UnitOfEnergy.KILO_WATT_HOUR
                )
            ),
        }
