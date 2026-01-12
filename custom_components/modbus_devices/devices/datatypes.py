import struct
import uuid

from .const import ByteOrder, WordOrder, ModbusDataType, ModbusMode, ModbusPollMode
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

###########################################
###### DATA TYPES FOR HOME ASSISTANT ######
###########################################
@dataclass
class EntityData:
    attrs: dict | None = None  # Home Assistant extra state attributes
    category: str = None                # None | "config" | "diagnostic"
    deviceClass: str = None             # None | Load value from HA device class 
    enabledDefault: bool = True         # Entity enabled by default
    icon: str = None                    # None | "mdi:thermometer"....

@dataclass
class EntityDataSensor(EntityData):
    stateClass: str = None              # None | Set to valid "SensorStateClass" to enable long term storage
    units: str = None                   # None | from homeassistant.const import UnitOf....
    enum: dict = field(default_factory=dict)

@dataclass
class EntityDataNumber(EntityData):
    units: str = None                   # None | from homeassistant.const import UnitOf....
    min_value: int = 0
    max_value: int = 65535
    step: int = 1

@dataclass
class EntityDataSelect(EntityData):
    options: dict = field(default_factory=dict)

@dataclass
class EntityDataBinarySensor(EntityData):
    pass

@dataclass
class EntityDataSwitch(EntityData):
    pass

@dataclass
class EntityDataButton(EntityData):
    pass

################################################
###### DATA TYPES FOR MODBUS FUNCTIONALITY ######
################################################
class ModbusGroup:
    def __init__(self, mode: ModbusMode, poll_mode: ModbusPollMode):
        # Initialize mode and poll_mode
        self.mode = mode
        self.poll_mode = poll_mode
        # Generate a unique ID automatically when the instance is created
        self._unique_id = str(uuid.uuid4())

    @property
    def unique_id(self):
        return self._unique_id  # Return the auto-generated unique ID

    def __eq__(self, other):
        # Ensure equality is based on mode and poll_mode
        if isinstance(other, ModbusGroup):
            return (self.mode == other.mode) and (self.poll_mode == other.poll_mode)
        return False

    def __hash__(self):
        # Hash based on mode, poll_mode, and unique_id to ensure uniqueness in dict
        return hash((self.mode, self.poll_mode, self.unique_id))
    
class ModbusDefaultGroups(Enum):
    CONFIG = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_OFF)
    UI = ModbusGroup(ModbusMode.NONE, ModbusPollMode.POLL_OFF)

    @property
    def unique_id(self):
        return self.value.unique_id  # Access the unique_id property directly
    
    @property
    def mode(self):
        return self.value.mode  # Access the mode property directly
    
    @property
    def poll_mode(self):
        return self.value.poll_mode  # Access the poll_mode property directly

@dataclass
class ModbusDatapoint:
    address: int = 0                                            # 0-indexed address
    length: int = 1                                             # Number of registers
    scaling: float = 1                                          # Multiplier for raw value  
    offset: float = 0.0                                         # Offset     
    type: ModbusDataType = ModbusDataType.INT                   # Type of the datapoint
    value: int | float | str = 0                                # Scaled value, usually "read only"
    entity_data: EntityData | None = None                       # Entity parameters

    def from_modbus(self, registers: list[int], byte_order=ByteOrder.MSB, word_order=WordOrder.NORMAL):
        # Convert from modbus registers to formatted value
        if len(registers) != self.length:
            raise ValueError(f"Datapoint at address {self.address}: expected {self.length} registers, got {len(registers)}")

        # Convert registers to bytes with correct per-register byte order
        b = bytearray()
        for reg in registers:
            b += reg.to_bytes(2, byteorder='big' if byte_order == ByteOrder.MSB else 'little')

        # Apply word swap if needed
        if word_order == WordOrder.SWAP and len(registers) > 1:
            b = self.modbus_word_swap(b)

        # Interpret bytes
        if self.type in (ModbusDataType.INT , ModbusDataType.UINT ):
            combined_value = int.from_bytes(b, byteorder='big', signed=(self.type == ModbusDataType.INT))
            calculated_value = combined_value * self.scaling + self.offset
            # Preserve float only when scaling/offset create a fractional part
            if calculated_value % 1 != 0:
                self.value = calculated_value
            else:
                self.value = int(calculated_value)

        elif self.type == ModbusDataType.FLOAT:
            if self.length == 2:
                self.value = struct.unpack('>f', b)[0] * self.scaling + self.offset
            elif self.length == 4:
                self.value = struct.unpack('>d', b)[0] * self.scaling + self.offset
            else:
                # Fallback: treat as integer
                combined_value = int.from_bytes(b, byteorder='big')
                self.value = combined_value * self.scaling + self.offset

        elif self.type == ModbusDataType.STRING:
            try:
                # If device uses 1 register per char we remove the 0's
                if all(b[i] == 0x00 for i in range(0, len(b), 2)):
                    b = b[1::2]

                # Stop at first NULL and decode
                self.value = b.split(b"\x00", 1)[0].decode("ascii", errors="ignore")
            except ValueError:
                self.value = ''

    def to_modbus(self, value, byte_order=ByteOrder.MSB, word_order=WordOrder.NORMAL) -> list[int]:
        # Convert from formatted value to modbus registers
        if self.type in (ModbusDataType.INT, ModbusDataType.UINT):
            scaled_value = int(round((value - self.offset) / self.scaling))
            b = scaled_value.to_bytes(self.length*2, byteorder='big', signed=(self.type == ModbusDataType.INT))

        elif self.type == ModbusDataType.FLOAT:
            scaled_value = (value - self.offset) / self.scaling
            if self.length == 2:
                b = struct.pack('>f', scaled_value)
            elif self.length == 4:
                b = struct.pack('>d', scaled_value)
            else:
                scaled_value = int(round(scaled_value))
                b = scaled_value.to_bytes(self.length*2, byteorder='big')

        elif self.type == ModbusDataType.STRING:
            # Will we ever write a string? We don't know the format at all...
            b = value.encode('utf-8')
            b = b.ljust(self.length * 2, b'\x00')

        # Apply word swap if needed
        if word_order == WordOrder.SWAP and self.length > 1 and self.type != ModbusDataType.STRING:
            b = self.modbus_word_swap(b)

        # Convert to registers with per-register byte order
        registers = []
        for i in range(0, len(b), 2):
            reg_bytes = b[i:i+2]
            if byte_order == ByteOrder.MSB:
                registers.append(int.from_bytes(reg_bytes, byteorder='big'))
            else:
                registers.append(int.from_bytes(reg_bytes, byteorder='little'))

        return registers
    
    def modbus_word_swap(self, b: bytes) -> bytes:
        swapped = bytearray()
        # Process 4-byte chunks
        for i in range(0, len(b), 4):
            chunk = b[i:i+4]
            swapped.extend(chunk[2:4] + chunk[0:2] if len(chunk) == 4 else chunk)

        return bytes(swapped)