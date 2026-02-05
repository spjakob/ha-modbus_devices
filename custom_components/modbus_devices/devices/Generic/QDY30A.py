import logging

from ..modbusdevice import ModbusDevice
from ..const import ModbusMode, ModbusPollMode, ModbusDataType
from ..datatypes import ModbusDatapoint, ModbusGroup
from ..datatypes import EntityDataSensor, EntityDataSelect, EntityDataNumber, EntityDataButton

from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfLength
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

_LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# 1. SPLIT GROUPS
# --------------------------------------------------------------------------------------
GROUP_LIVE_1 = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ON)
GROUP_LIVE_2 = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ON)

GROUP_SETTINGS_1 = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ONCE)
GROUP_SETTINGS_2 = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_ONCE)

GROUP_ACTIONS = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_OFF)

class Device(ModbusDevice):
    manufacturer = "Generic"
    model = "QDY30A"

    def loadDatapoints(self):
        # ------------------------------------------------------------------
        # STEP 1: DEFINE SETTINGS
        # ------------------------------------------------------------------
        self.Datapoints[GROUP_SETTINGS_1] = {
            # --- WRITABLE (Allowed by Datasheet Sec 5) ---
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
            
            # --- READ ONLY (Calibration Data - Datasheet Sec 6) ---
            "Measurement Unit": ModbusDatapoint(
                address=2,
                entity_data=EntityDataSensor(
                    category=EntityCategory.DIAGNOSTIC,
                    icon="mdi:scale",
                    # Use 'enum' to map integer values to strings for display
                    enum={
                        0: "MPa", 1: "kPa", 2: "Pa", 3: "bar", 4: "mbar",
                        5: "kg/cm2", 6: "PSI", 7: "mH2O", 8: "mmH2O",
                        16: "m", 17: "cm", 18: "mm", 20: "°C", 23: "Empty"
                    }
                )
            ),
            "Decimal Point Position": ModbusDatapoint(
                address=3,
                entity_data=EntityDataSensor(
                    category=EntityCategory.DIAGNOSTIC,
                    icon="mdi:decimal",
                    enum={0: "x1", 1: "x0.1", 2: "x0.01", 3: "x0.001"}
                )
            ),
            "Zero Point": ModbusDatapoint(
                address=5,
                entity_data=EntityDataSensor(
                    category=EntityCategory.DIAGNOSTIC,
                    icon="mdi:arrow-collapse-down"
                )
            ),
            "Full Scale Range": ModbusDatapoint(
                address=6,
                entity_data=EntityDataSensor(
                    category=EntityCategory.DIAGNOSTIC,
                    icon="mdi:arrow-expand-up"
                )
            ),
            
            # --- WRITABLE (Allowed by Datasheet Sec 5) ---
            "Zero Offset": ModbusDatapoint(
                address=12,
                entity_data=EntityDataNumber(
                    category=EntityCategory.CONFIG,
                    min_value=-32768, max_value=32767,
                    icon="mdi:align-vertical-bottom"
                )
            ),
        }

        self.Datapoints[GROUP_SETTINGS_2] = {
            # --- WRITABLE (Allowed by Datasheet Sec 5 - "Check Bit") ---
            "Parity": ModbusDatapoint(
                address=37,
                entity_data=EntityDataSelect(
                    category=EntityCategory.CONFIG,
                    options={0: "None", 1: "Odd", 2: "Even"},
                    icon="mdi:check-network-outline"
                )
            ),
        }

        # ------------------------------------------------------------------
        # STEP 2: DEFINE LIVE SENSORS
        # ------------------------------------------------------------------
        self.Datapoints[GROUP_LIVE_1] = {
            "Water Level": ModbusDatapoint(
                address=4,
                # Scaling defaults to 1.0 (Fixed in onAfterFirstRead)
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.DISTANCE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfLength.METERS,
                    icon="mdi:ruler",
                    precision=3
                )
            ),
        }
        
        self.Datapoints[GROUP_LIVE_2] = {
            "Water Level (Float)": ModbusDatapoint(
                address=22,
                register_count=2,
                type=ModbusDataType.FLOAT,
                # Scaling defaults to 1.0 (Fixed in onAfterFirstRead)
                entity_data=EntityDataSensor(
                    deviceClass=SensorDeviceClass.DISTANCE,
                    stateClass=SensorStateClass.MEASUREMENT,
                    units=UnitOfLength.METERS,
                    icon="mdi:ruler-square",
                    precision=3,
                    category=EntityCategory.DIAGNOSTIC
                )
            ),
        }

        # ------------------------------------------------------------------
        # STEP 3: ACTIONS
        # ------------------------------------------------------------------
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
            dp_unit = self.Datapoints[GROUP_SETTINGS_1].get("Measurement Unit")
            dp_dec = self.Datapoints[GROUP_SETTINGS_1].get("Decimal Point Position")
            
            dp_level = self.Datapoints[GROUP_LIVE_1].get("Water Level")
            dp_level_float = self.Datapoints[GROUP_LIVE_2].get("Water Level (Float)")

            if dp_unit and dp_dec and dp_unit.value is not None and dp_dec.value is not None:
                # Value will now be the string from the enum (e.g. "cm"), so we map it back or handle it.
                # However, dp.value usually holds the internal value. 
                # Wait, EntityDataSensor transforms output for HA, but dp.value in modbus_devices usually stores the raw/processed numeric value.
                # Let's assume dp.value is the raw integer (e.g. 17) because formatting happens in the Entity, not the Datapoint.
                # If your integration converts it immediately to string in dp.value, this logic needs adjustment.
                # Based on `datatypes.py` -> `from_modbus`:
                # It sets `self.value`. It does NOT apply the enum map there. The Entity applies the enum.
                # So `dp_unit.value` IS the integer (17). Safe to proceed.
                
                unit_val = int(dp_unit.value)
                dec_val = int(dp_dec.value)

                # 1. Decimal Multiplier
                decimal_multipliers = {0: 1.0, 1: 0.1, 2: 0.01, 3: 0.001}
                base_mult = decimal_multipliers.get(dec_val, 0.001)

                # 2. Unit Multiplier (Convert to Meters)
                unit_multipliers = {
                    16: 1.0,    # m
                    17: 0.01,   # cm
                    18: 0.001   # mm
                }

                # 3. Apply Scaling
                if unit_val in unit_multipliers:
                    unit_mult = unit_multipliers[unit_val]
                    
                    # A) Integer Sensor
                    if dp_level:
                        new_scale = base_mult * unit_mult
                        dp_level.scaling = new_scale
                        
                        # Fix value (Current value is RAW * 1.0, so just multiply by new scale)
                        if isinstance(dp_level.value, (int, float)):
                             dp_level.value = dp_level.value * new_scale
                        
                    # B) Float Sensor
                    if dp_level_float:
                        new_scale = unit_mult
                        dp_level_float.scaling = new_scale
                        
                        # Fix value (Current value is RAW * 1.0, so just multiply by new scale)
                        if isinstance(dp_level_float.value, (int, float)):
                            dp_level_float.value = dp_level_float.value * new_scale

                    _LOGGER.info("QDY30A: Auto-detected scaling: %s (Unit ID: %s, Dec ID: %s). Value corrected.", unit_mult, unit_val, dec_val)
                else:
                    _LOGGER.warning("QDY30A: Unknown Unit ID %s.", unit_val)

        except Exception as e:
            _LOGGER.error("QDY30A: Startup scaling calc failed: %s", e)

    async def writeValue(self, group: ModbusGroup, key: str, value: float):
        if key == "Save Settings":
            value = 0 
        elif key == "Factory Reset":
            value = 1
        await super().writeValue(group, key, value)