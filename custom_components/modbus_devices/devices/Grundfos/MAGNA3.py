import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import ModbusDatapoint, ModbusGroup, ModbusMode, ModbusPollMode
from ..datatypes import EntityDataSensor

# Import specific units used in this device
from homeassistant.const import (
    UnitOfPressure,
    UnitOfVolumeFlowRate,
    UnitOfFrequency,
    UnitOfTemperature,
    UnitOfEnergy,
    UnitOfPower
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

_LOGGER = logging.getLogger(__name__)

# Define groups
GROUP_INPUTS = ModbusGroup(ModbusMode.INPUT, ModbusPollMode.POLL_ON)

class Device(ModbusDevice):
    # Override static device information
    manufacturer = "Grundfos"
    model = "MAGNA3"

    def loadDatapoints(self):
        # SENSORS
        self.Datapoints[GROUP_INPUTS] = {
            "Head": ModbusDatapoint(
                address=300,
                scaling=0.001,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.PRESSURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPressure.BAR
                )
            ),
            "Volume Flow": ModbusDatapoint(
                address=301,
                scaling=0.1,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.VOLUME_FLOW_RATE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
                )
            ),
            "Frequency": ModbusDatapoint(
                address=304,
                scaling=0.1,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.FREQUENCY,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfFrequency.HERTZ
                )
            ),
            "Pump Liquid Temperature": ModbusDatapoint(
                address=321,
                scaling=0.01,
                offset=-273.15,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.TEMPERATURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfTemperature.CELSIUS
                )
            ),
            "Remote Temperature 2": ModbusDatapoint(
                address=336,
                scaling=0.01,
                offset=-273.15,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.TEMPERATURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfTemperature.CELSIUS
                )
            ),
            "Differential Pressure": ModbusDatapoint(
                address=338,
                scaling=0.001,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.PRESSURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPressure.BAR
                )
            ),
            "Heat Energy": ModbusDatapoint(
                address=352,
                length=2,
                type='uint',
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.ENERGY,
                    stateClass=SensorStateClass.TOTAL_INCREASING,
                    units=UnitOfEnergy.KILO_WATT_HOUR
                )
            ),
            "Heat Differential Temp": ModbusDatapoint(
                address=354,
                scaling=0.01,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.TEMPERATURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfTemperature.CELSIUS
                )
            ),
            "Heat Power": ModbusDatapoint(
                address=355,
                length=2,
                type='uint',
                scaling=0.001,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.POWER,  # Fixed: kW is Power, not Energy
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPower.KILO_WATT
                )
            ),
        }