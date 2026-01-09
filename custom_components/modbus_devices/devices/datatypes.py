import struct
import uuid

from collections import namedtuple
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
class ModbusMode(Enum):
    NONE = 0        # Used for virtual data points
    COILS = 1
    INPUT = 3
    HOLDING = 4

class ModbusPollMode(Enum):
    POLL_OFF = 0      # Values will not be read automatically
    POLL_ON = 1         # Values will be read each poll interval
    POLL_ONCE = 2       # Just read them once, for example for static configuration

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
    address: int = 0                                   # 0-indexed address
    length: int = 1                                     # Number of registers
    scaling: float = 1                                  # Multiplier for raw value  
    offset: float = 0.0                                 # Offset     
    value: int | float | str = 0                        # Scaled value, usually "read only"
    entity_data: EntityData | None = None               # Entity parameters
    type: Literal['int', 'float', 'string'] = 'int'     # Type of the datapoint

    def from_raw(self, registers: list[int]):
        if len(registers) != self.length:
            return

        if self.type == 'int':
            combined_value = 0
            for reg in registers:
                combined_value = (combined_value << 16) | reg

            raw_value = self.twos_complement(combined_value, bits=16*self.length)

            # Apply scaling and offset
            self.value = raw_value * self.scaling + self.offset

        elif self.type == 'float':
            # Convert registers to IEEE 754 float (big-endian)
            byte_array = bytearray()
            for reg in registers:
                byte_array += reg.to_bytes(2, byteorder='big')
            
            if self.length == 2:
                raw_value = struct.unpack('>f', byte_array)[0]  # 32-bit float
            elif self.length == 4:
                raw_value = struct.unpack('>d', byte_array)[0]  # 64-bit double
            else:
                # Fallback: treat as integer
                combined_value = int.from_bytes(byte_array, byteorder='big')
                raw_value = combined_value
            
            # Apply scaling and offset
            self.value = raw_value * self.scaling + self.offset

        elif self.type == 'string':
            try:
                self.value = ''.join(chr(reg) for reg in registers)
            except ValueError:
                self.value = ''

    def to_raw(self, value) -> list[int]:
        if self.type == 'int':
            # Reverse scaling and offset
            scaled_value = int(round((value - self.offset) / self.scaling))
            if scaled_value < 0:
                scaled_value = self.twos_complement(scaled_value, bits=16*self.length)

        elif self.type == 'float':
            # Reverse scaling and offset
            scaled_value = (value - self.offset) / self.scaling
            if self.length == 2:
                bytes_value = struct.pack('>f', scaled_value)  # 32-bit float
            elif self.length == 4:
                bytes_value = struct.pack('>d', scaled_value)  # 64-bit double
            else:
                # Fallback: convert to integer
                scaled_value = int(round(scaled_value))
                bytes_value = scaled_value.to_bytes(self.length*2, byteorder='big', signed=False)

            # Convert bytes to registers
            registers = []
            for i in range(0, len(bytes_value), 2):
                registers.append(int.from_bytes(bytes_value[i:i+2], byteorder='big'))
            return registers

        elif self.type == 'string':
            regs = [ord(c) for c in value]
            while len(regs) < self.length:
                regs.append(0)
            return regs[:self.length]

        # Default integer conversion to registers
        registers = []
        for _ in range(self.length):
            registers.insert(0, scaled_value & 0xFFFF)
            scaled_value >>= 16
        return registers

    def twos_complement(self, number: int, bits: int = 16) -> int:
        """Convert unsigned integer to signed integer using two's complement."""
        if number < 0:
            return number
        if number >= (1 << (bits - 1)):
            number -= (1 << bits)
        return number