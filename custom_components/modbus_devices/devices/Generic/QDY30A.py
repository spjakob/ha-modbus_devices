import logging

from ..modbusdevice import ModbusDevice
from ..const import ModbusMode, ModbusPollMode
from ..datatypes import ModbusDatapoint, ModbusGroup
from ..datatypes import EntityDataSensor, EntityDataSelect, EntityDataNumber, EntityDataButton

from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfLength, UnitOfPressure, UnitOfTemperature, UnitOfVolume
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

_LOGGER = logging.getLogger(__name__)

# Define groups
GROUP_MAIN = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ON)
GROUP_ACTIONS = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_OFF)

class Device(ModbusDevice):
    manufacturer = "Generic"
    model = "QDY30A"

    def loadDatapoints(self):
        self.Datapoints[GROUP_MAIN] = {
            # --- CONFIGURATION ---
            "Device Slave ID": ModbusDatapoint(
                address=0,
                entity_data=EntityDataNumber(
                    category=EntityCategory.CONFIG,
                    min_value=1, max_value=247,
                    icon="mdi:identifier"
                )
            ),
            "Baud Rate": ModbusDatapoint(
                address=1,
                entity_data=EntityDataSelect(
                    category=EntityCategory.CONFIG,
                    # Updated map based on your observation that 3 = 9600
                    options={0: "1200", 1: "2400", 2: "4800", 3: "9600", 4: "19200"},
                    icon="mdi:serial-port"
                )
            ),
            # Register 2 (17) is likely NOT Parity. Hiding it to avoid confusion.
            
            # --- SENSORS ---
            "Water Level": ModbusDatapoint(
                address=4,
                scaling=0.001, # Fixed scaling (mm -> m)
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.DISTANCE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfLength.METERS,
                    icon="mdi:ruler",
                    precision=3
                )
            ),
            "Sensor Range": ModbusDatapoint(
                address=6,
                scaling=0.001, # Fixed scaling (mm -> m)
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.DISTANCE,
                    units=UnitOfLength.METERS,
                    icon="mdi:arrow-expand-horizontal",
                    entity_category=EntityCategory.DIAGNOSTIC
                )
            ),
            "Pressure": ModbusDatapoint(
                address=11,
                scaling=1, # Raw Pascals
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.PRESSURE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfPressure.PA,
                    icon="mdi:gauge"
                )
            ),
            
            # --- TUNING ---
            "Response Filter": ModbusDatapoint(
                address=7,
                entity_data=EntityDataNumber(
                    category=EntityCategory.CONFIG,
                    min_value=0, max_value=63,
                    icon="mdi:blur"
                )
            ),
            "Zero Trim": ModbusDatapoint(
                address=8,
                entity_data=EntityDataNumber(
                    category=EntityCategory.CONFIG,
                    min_value=-1000, max_value=1000,
                    icon="mdi:arrow-expand-vertical"
                )
            ),
        }

        self.Datapoints[GROUP_ACTIONS] = {
            "Save Settings": ModbusDatapoint(
                address=15,
                entity_data=EntityDataButton(icon="mdi:content-save-settings")
            )
        }

    # Removed onAfterRead to prevent unstable scaling
    async def writeValue(self, group: ModbusGroup, key: str, value: float):
        if key == "Save Settings":
            value = 0 # Assuming 0 triggers the save
        await super().writeValue(group, key, value)