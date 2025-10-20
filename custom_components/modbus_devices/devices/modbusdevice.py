import logging

from typing import Dict

from homeassistant.helpers.entity import EntityCategory

from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from .connection import ConnectionParams, TCPConnectionParams, RTUConnectionParams

from .datatypes import ModbusMode, ModbusPollMode, ModbusDefaultGroups, ModbusGroup, ModbusDatapoint
from .datatypes import ModbusSelectData, ModbusNumberData

_LOGGER = logging.getLogger(__name__)

class ModbusDevice():
    # Default properties
    manufacturer = None
    model = None
    sw_version = None
    serial_number = None

    def __init__(self, connection_params: ConnectionParams):
        if isinstance(connection_params, TCPConnectionParams):
            self._client = AsyncModbusTcpClient(host=connection_params.ip, port=connection_params.port)
        elif isinstance(connection_params, RTUConnectionParams):
            self._client = AsyncModbusSerialClient(port=connection_params.serial_port, baudrate=connection_params.baud_rate)
        else:
            raise ValueError("Unsupported connection parameters")
        self._slave_id = connection_params.slave_id

        self.Datapoints: Dict[ModbusGroup, Dict[str, ModbusDatapoint]] = {}
        self.loadDatapoints()
        self.loadConfigUI()
        _LOGGER.debug("Loaded datapoints for %s %s", self.manufacturer, self.model)

        self.firstRead = True

    def loadConfigUI(self):
        # Ensure default groups exist
        self.Datapoints.setdefault(ModbusDefaultGroups.CONFIG, {})
        self.Datapoints.setdefault(ModbusDefaultGroups.UI, {})

        # Add Config UI if we have config values
        if self.Datapoints[ModbusDefaultGroups.CONFIG]:
            self.Datapoints[ModbusDefaultGroups.UI] = {
                "Config Selection": ModbusDatapoint(DataType=ModbusSelectData(category=EntityCategory.CONFIG)),
                "Config Value": ModbusDatapoint(DataType=ModbusNumberData(category=EntityCategory.CONFIG, min_value=0, max_value=65535, step=1))
            }

    def loadDatapoints(self):
        pass

    """ ******************************************************* """
    """ ************* FUNCTIONS CALLED ON EVENTS ************** """
    """ ******************************************************* """
    def onBeforeRead(self):
        pass
    def onAfterRead(self):
        pass
    def onAfterFirstRead(self):
        pass

    """ ******************************************************* """
    """ *********** EXTERNAL CALL TO READ ALL DATA ************ """
    """ ******************************************************* """
    async def readData(self):
        if self.firstRead:      
            await self._client.connect() 

        self.onBeforeRead()

        try:
            for group, _ in self.Datapoints.items():
                if group.poll_mode == ModbusPollMode.POLL_ON:
                    await self.readGroup(group)
                elif group.poll_mode == ModbusPollMode.POLL_ONCE and self.firstRead:
                    await self.readGroup(group)
        except Exception as err:
            raise

        if self.firstRead:   
            self.firstRead = False
            self.onAfterFirstRead()

        self.onAfterRead()

    """ ******************************************************* """
    """ ******************** READ GROUP *********************** """
    """ ******************************************************* """
    async def readGroup(self, group: ModbusGroup):
        """Read Modbus group registers and update data points."""
        MAX_REGISTERS_PER_READ = 125

        addresses = [
            (dp.Address, dp.Length)
            for dp in self.Datapoints[group].values()
        ]
        start_addr = min(addr for addr, _ in addresses)
        end_addr = max(addr + length for addr, length in addresses)
        n_reg = end_addr - start_addr

        if n_reg > MAX_REGISTERS_PER_READ:
            raise ValueError(
                f"Too many registers to read at once ({n_reg} requested, max {MAX_REGISTERS_PER_READ}) "
                f"for group {group}. Consider splitting the group."
        )

        method = self._get_read_method(group.mode)    
        response = await method(address=start_addr, count=n_reg, device_id=self._slave_id)

        # Handle Modbus errors
        if response.isError():
            raise ModbusException(f"Error reading group {group}: {response}")

        _LOGGER.debug("Read data from address: %s - %s", start_addr, response.registers)

        # Process the registers and update data points
        for name, dp in self.Datapoints[group].items():
            offset = dp.Address - start_addr
            registers = response.registers[offset:offset + dp.Length]
            dp.Value = self.process_registers(registers, dp.Scaling)

    """ ******************************************************* """
    """ **************** READ SINGLE VALUE ******************** """
    """ ******************************************************* """
    async def readValue(self, group: ModbusGroup, key: str) -> float | str:
        _LOGGER.debug("Reading value: Group: %s, Key: %s", group, key)

        if key not in self.Datapoints[group]:
            raise KeyError(f"Key '{key}' not found in group '{group}'")

        datapoint = self.Datapoints[group][key]
        length = datapoint.Length

        method = self._get_read_method(group.mode) 
        response = await method(address=datapoint.Address, count=length, device_id=self._slave_id)

        # Handle Modbus errors
        if response.isError():
            raise ModbusException(f"Error reading value for key '{key}': {response}")

        _LOGGER.debug("Read data: %s", response.registers)

        registers = response.registers[:length]
        datapoint.Value = self.process_registers(registers, datapoint.Scaling)

        return datapoint.Value

    """ ******************************************************* """
    """ **************** WRITE SINGLE VALUE ******************* """
    """ ******************************************************* """
    async def writeValue(self, group: ModbusGroup, key: str, value: float):
        _LOGGER.debug("Writing value: Group: %s, Key: %s, Value: %s", group, key, value)

        if key not in self.Datapoints[group]:
            raise KeyError(f"Key '{key}' not found in group '{group}'")

        datapoint = self.Datapoints[group][key]
        length = datapoint.Length
        if length > 2:
            raise ValueError(f"Unsupported register length: {length}. Only 1 or 2 registers are supported.")

        # Scale the value
        scaled_value = round(value / datapoint.Scaling)
        if scaled_value < 0:
            scaled_value = self.twos_complement(scaled_value, bits=16 * length)

        # Prepare the registers
        registers = []
        for _ in range(length):
            registers.insert(0, scaled_value & 0xFFFF)  # Extract the least significant 16 bits
            scaled_value >>= 16  # Shift the value to the next 16 bits

        # Write the registers
        address = datapoint.Address
        slave = self._slave_id

        if group.mode == ModbusMode.COILS:
            method = self._client.write_coil if length == 1 else self._client.write_coils
        else:
            method = self._client.write_register if length == 1 else self._client.write_registers

        response = await method(
            address=address,
            value=registers[0] if length == 1 else registers,
            device_id=slave,
        )

        if response.isError():
            raise ModbusException(f"Failed to write value for key '{key}': {response}")

        # Update the cached value
        datapoint.Value = value
        _LOGGER.debug("Successfully wrote value for key '%s': %s", key, value)

    """ ******************************************************* """
    """ *********** HELPER FOR PROCESSING REGISTERS *********** """
    """ ******************************************************* """
    def _get_read_method(self, mode: ModbusMode):
        dispatch = {
            ModbusMode.INPUT:   self._client.read_input_registers,
            ModbusMode.HOLDING: self._client.read_holding_registers,
            ModbusMode.COILS:   self._client.read_coils,
        }

        try:
            return dispatch[mode]
        except KeyError:
            raise ValueError(f"Unsupported Modbus mode: {mode}")

    def twos_complement(self, number: int, bits: int = 16) -> int:
        if number < 0:
            return number  # If the number is negative, no need for two's complement conversion.
        
        max_value = (1 << bits)  # Maximum value for the given bit-width.
        if number >= max_value // 2:
            return number - max_value  # Convert to negative value in two's complement.
        
        return number  # Return the number as is if it's already non-negative.

    def process_registers(self, registers: list[int], scaling: float) -> float | str:
        length = len(registers)

        if length <= 2:
            # Combine registers into a single value (big-endian)
            combined_value = 0
            for reg in registers:
                combined_value = (combined_value << 16) | reg

            newVal = self.twos_complement(combined_value)
            return newVal if scaling == 1.0 else newVal * scaling
        else:
            # Assume this is a text string
            try:
                newVal = ''.join(chr(value) for value in registers)
                return newVal.rstrip('\x00')
            except ValueError as e:
                # Failed to decode text, most likely just registers we are ignoring
                return registers