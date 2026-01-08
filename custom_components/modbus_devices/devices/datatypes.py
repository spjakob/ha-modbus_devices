from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum
import uuid

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
    value: float = 0.0                                  # Scaled value, usually "read only"
    entity_data: EntityData | None = None               # Entity parameters

    def from_raw(self, registers: list[int]) :
        if len(registers) != self.length:
            return

        if self.length <= 2:
            # Combine registers into a single value (big-endian)
            combined_value = 0
            for reg in registers:
                combined_value = (combined_value << 16) | reg

            newVal = self.twos_complement(combined_value)
            self.value = newVal * self.scaling + self.offset
        else:
            # Assume this is a text string
            try:
                newVal = ''.join(chr(value) for value in registers)
                self.value = newVal
            except ValueError as e:
                pass

    def to_raw(self, value) -> list[int]:
        scaled_value = int(round((value - self.offset) / self.scaling))
        if scaled_value < 0:
            scaled_value = self.twos_complement(scaled_value, bits=16 * self.length)

        # Prepare the registers
        registers = []
        for _ in range(self.length):
            registers.insert(0, scaled_value & 0xFFFF)  # Extract the least significant 16 bits
            scaled_value >>= 16  # Shift the value to the next 16 bits

        return registers

    def twos_complement(self, number: int, bits: int = 16) -> int:
        if number < 0:
            return number  # If the number is negative, no need for two's complement conversion.
        
        max_value = (1 << bits)  # Maximum value for the given bit-width.
        if number >= max_value // 2:
            return number - max_value  # Convert to negative value in two's complement.
        
        return number  # Return the number as is if it's already non-negative.