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
# GROUP_MAIN: Includes Config (0-3, 5-9) and Sensor (4). Poll ON to ensure atomic updates.
GROUP_MAIN = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ON)
# GROUP_ACTIONS: Buttons. Poll OFF (Write only).
GROUP_ACTIONS = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_OFF)

class Device(ModbusDevice):
    # Override static device information
    manufacturer = "Generic"
    model = "QDY30A"

    def loadDatapoints(self):
        # MAIN GROUP (Config + Sensor)
        self.Datapoints[GROUP_MAIN] = {
            # Configuration
            "Device Slave ID": ModbusDatapoint(
                address=0,
                entity_data=EntityDataNumber(
                    category=EntityCategory.CONFIG,
                    min_value=1,
                    max_value=247,
                    icon="mdi:identifier"
                )
            ),
            "Baud Rate": ModbusDatapoint(
                address=1,
                entity_data=EntityDataSelect(
                    category=EntityCategory.CONFIG,
                    options={0: "2400", 1: "4800", 2: "9600", 3: "19200", 4: "38400"},
                    icon="mdi:serial-port"
                )
            ),
            "Parity": ModbusDatapoint(
                address=2,
                entity_data=EntityDataSelect(
                    category=EntityCategory.CONFIG,
                    options={0: "None", 1: "Odd", 2: "Even"}
                )
            ),
            "Decimal Point Position": ModbusDatapoint(
                address=3,
                entity_data=EntityDataSelect(
                    category=EntityCategory.CONFIG,
                    options={0: "x1", 1: "x0.1", 2: "x0.01", 3: "x0.001"},
                    icon="mdi:decimal"
                )
            ),
            # Main Sensor
            "Water Level": ModbusDatapoint(
                address=4,
                scaling=0.001, # Default to x0.001
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.DISTANCE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfLength.METERS,
                    icon="mdi:ruler"
                )
            ),
            # More Configuration
            "Measurement Unit": ModbusDatapoint(
                address=5,
                entity_data=EntityDataSelect(
                    category=EntityCategory.CONFIG,
                    options={0: "mH2O", 1: "kPa", 2: "MPa", 3: "°C", 4: "L", 5: "bar", 6: "psi"},
                    icon="mdi:scale"
                )
            ),
            "Response Filter": ModbusDatapoint(
                address=7,
                entity_data=EntityDataNumber(
                    category=EntityCategory.CONFIG,
                    min_value=0,
                    max_value=63,
                    icon="mdi:blur"
                )
            ),
            "Zero Trim": ModbusDatapoint(
                address=8,
                entity_data=EntityDataNumber(
                    category=EntityCategory.CONFIG,
                    min_value=-1000,
                    max_value=1000,
                    icon="mdi:arrow-expand-vertical"
                )
            ),
            "Span Trim": ModbusDatapoint(
                address=9,
                entity_data=EntityDataNumber(
                    category=EntityCategory.CONFIG,
                    min_value=0,
                    max_value=65535,
                    icon="mdi:arrow-expand-all"
                )
            ),
        }

        # ACTIONS GROUP (Buttons)
        self.Datapoints[GROUP_ACTIONS] = {
            "Save Settings to EEPROM": ModbusDatapoint(
                address=15,
                entity_data=EntityDataButton(
                    icon="mdi:content-save-settings"
                )
            ),
            "Factory Reset": ModbusDatapoint(
                address=16,
                entity_data=EntityDataButton(
                    icon="mdi:restart-alert"
                )
            ),
        }

    def onAfterRead(self):
        # Update scaling based on Decimal Point Position
        try:
            dp_pos = self.Datapoints[GROUP_MAIN]["Decimal Point Position"].value
            # options: 0: x1, 1: x0.1, 2: x0.01, 3: x0.001
            # ensure value is valid int
            if isinstance(dp_pos, (int, float)):
                scaling_map = {0: 1, 1: 0.1, 2: 0.01, 3: 0.001}
                new_scaling = scaling_map.get(int(dp_pos), 0.001)
                self.Datapoints[GROUP_MAIN]["Water Level"].scaling = new_scaling
        except Exception as e:
            _LOGGER.warning("Failed to update Water Level scaling: %s", e)

        # Update Units and Device Class based on Measurement Unit
        try:
            unit_val = self.Datapoints[GROUP_MAIN]["Measurement Unit"].value
            if isinstance(unit_val, (int, float)):
                sensor_dp = self.Datapoints[GROUP_MAIN]["Water Level"]

                # Default
                new_unit = UnitOfLength.METERS
                new_device_class = SensorDeviceClass.DISTANCE

                # 0: mH2O, 1: kPa, 2: MPa, 3: °C, 4: L, 5: bar, 6: psi
                match int(unit_val):
                    case 0:
                        new_unit = UnitOfLength.METERS # Approximating mH2O to Meters
                        new_device_class = SensorDeviceClass.DISTANCE
                    case 1:
                        new_unit = UnitOfPressure.KPA
                        new_device_class = SensorDeviceClass.PRESSURE
                    case 2:
                        new_unit = UnitOfPressure.MPA
                        new_device_class = SensorDeviceClass.PRESSURE
                    case 3:
                        new_unit = UnitOfTemperature.CELSIUS
                        new_device_class = SensorDeviceClass.TEMPERATURE
                    case 4:
                        new_unit = UnitOfVolume.LITERS
                        new_device_class = SensorDeviceClass.VOLUME
                    case 5:
                        new_unit = UnitOfPressure.BAR
                        new_device_class = SensorDeviceClass.PRESSURE
                    case 6:
                        new_unit = UnitOfPressure.PSI
                        new_device_class = SensorDeviceClass.PRESSURE

                sensor_dp.entity_data.units = new_unit
                sensor_dp.entity_data.deviceClass = new_device_class
        except Exception as e:
            _LOGGER.warning("Failed to update Water Level units: %s", e)

    async def writeValue(self, group: ModbusGroup, key: str, value: float):
        # Intercept Save Settings button to write 0 instead of 1
        if key == "Save Settings to EEPROM":
            value = 0
            _LOGGER.debug("Intercepted 'Save Settings to EEPROM', writing 0")

        await super().writeValue(group, key, value)
