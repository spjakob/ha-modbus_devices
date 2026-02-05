import logging

from ..modbusdevice import ModbusDevice
from ..const import ModbusMode, ModbusPollMode, ModbusDataType
from ..datatypes import ModbusDatapoint, ModbusGroup
from ..datatypes import EntityDataSensor, EntityDataSelect, EntityDataNumber, EntityDataButton

from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfLength, UnitOfPressure, UnitOfTemperature, UnitOfVolume
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

_LOGGER = logging.getLogger(__name__)

# GROUP_LIVE: Dynamic values, polled frequently
GROUP_LIVE = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ON)

# GROUP_SETTINGS: Static configuration, read ONLY ONCE at startup
GROUP_SETTINGS = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ONCE)

# GROUP_ACTIONS: Write-only buttons, never polled
GROUP_ACTIONS = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_OFF)

class Device(ModbusDevice):
    manufacturer = "Generic"
    model = "QDY30A"

    def loadDatapoints(self):
        # --- LIVE SENSORS ---
        self.Datapoints[GROUP_LIVE] = {
            "Water Level": ModbusDatapoint(
                address=4,
                scaling=0.001, # Default fallback
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.DISTANCE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfLength.METERS,
                    icon="mdi:ruler",
                    precision=3
                )
            ),
            "Water Level (Float)": ModbusDatapoint(
                address=22,
                register_count=2,
                type=ModbusDataType.FLOAT,
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.DISTANCE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfLength.METERS,
                    icon="mdi:ruler-square",
                    category=EntityCategory.DIAGNOSTIC
                )
            ),
        }

        # --- CONFIGURATION ---
        self.Datapoints[GROUP_SETTINGS] = {
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
                    options={
                        0: "1200", 1: "2400", 2: "4800", 3: "9600",
                        4: "19200", 5: "38400", 6: "57600", 7: "115200"
                    },
                    icon="mdi:serial-port"
                )
            ),
            "Zero Offset": ModbusDatapoint(
                address=12,
                entity_data=EntityDataNumber(
                    category=EntityCategory.CONFIG,
                    min_value=-32768, max_value=32767,
                    icon="mdi:align-vertical-bottom"
                )
            ),
            "Parity": ModbusDatapoint(
                address=37,
                entity_data=EntityDataSelect(
                    category=EntityCategory.CONFIG,
                    options={0: "None", 1: "Odd", 2: "Even"},
                    icon="mdi:check-network-outline"
                )
            ),

            # --- DIAGNOSTICS ---
            "Measurement Unit": ModbusDatapoint(
                address=2,
                entity_data=EntityDataSelect(
                    category=EntityCategory.DIAGNOSTIC,
                    options={
                        0: "MPa", 1: "kPa", 2: "Pa", 3: "bar", 4: "mbar",
                        5: "kg/cm2", 6: "PSI", 7: "mH2O", 8: "mmH2O",
                        16: "m", 17: "cm", 18: "mm", 20: "°C", 23: "Empty"
                    },
                    icon="mdi:scale"
                )
            ),
            "Decimal Point Position": ModbusDatapoint(
                address=3,
                entity_data=EntityDataSelect(
                    category=EntityCategory.DIAGNOSTIC,
                    options={0: "x1", 1: "x0.1", 2: "x0.01", 3: "x0.001"},
                    icon="mdi:decimal"
                )
            ),
            "Zero Point": ModbusDatapoint(
                address=5,
                entity_data=EntityDataNumber(
                    category=EntityCategory.DIAGNOSTIC,
                    icon="mdi:arrow-collapse-down"
                )
            ),
            "Full Scale Range": ModbusDatapoint(
                address=6,
                entity_data=EntityDataNumber(
                    category=EntityCategory.DIAGNOSTIC,
                    icon="mdi:arrow-expand-up"
                )
            ),
        }

        # --- ACTIONS ---
        self.Datapoints[GROUP_ACTIONS] = {
            "Save Settings": ModbusDatapoint(
                address=15,
                entity_data=EntityDataButton(icon="mdi:content-save-settings")
            ),
            "Factory Reset": ModbusDatapoint(
                address=16,
                entity_data=EntityDataButton(icon="mdi:restart-alert")
            )
        }

    def onAfterFirstRead(self):
        """
        CALLED ONCE: Logic to auto-detect scaling based on 
        static config registers read during startup.
        """
        try:
            dp_unit = self.Datapoints[GROUP_SETTINGS].get("Measurement Unit")
            dp_dec = self.Datapoints[GROUP_SETTINGS].get("Decimal Point Position")
            dp_level = self.Datapoints[GROUP_LIVE].get("Water Level")

            if dp_unit and dp_dec and dp_level and dp_unit.value is not None and dp_dec.value is not None:
                unit_val = int(dp_unit.value)
                dec_val = int(dp_dec.value)

                # 1. Decimal Multiplier (0=x1 ... 3=x0.001)
                decimal_multipliers = {0: 1.0, 1: 0.1, 2: 0.01, 3: 0.001}
                base_mult = decimal_multipliers.get(dec_val, 0.001)

                # 2. Unit Multiplier (Convert to Meters)
                # 16=m, 17=cm, 18=mm
                unit_multipliers = {
                    16: 1.0,    # m
                    17: 0.01,   # cm
                    18: 0.001   # mm
                }

                # 3. Apply
                if unit_val in unit_multipliers:
                    unit_mult = unit_multipliers[unit_val]
                    final_scaling = base_mult * unit_mult
                    dp_level.scaling = final_scaling
                    _LOGGER.info("QDY30A: Auto-detected scaling: %s (Unit ID: %s, Dec ID: %s)", final_scaling, unit_val, dec_val)
                else:
                    _LOGGER.warning("QDY30A: Unknown Unit ID %s. Scaling defaults to 0.001 (mm)", unit_val)

        except Exception as e:
            _LOGGER.error("QDY30A: Startup scaling calc failed: %s", e)

    async def writeValue(self, group: ModbusGroup, key: str, value: float):
        if key == "Save Settings":
            value = 0 
        elif key == "Factory Reset":
            value = 1
        await super().writeValue(group, key, value)