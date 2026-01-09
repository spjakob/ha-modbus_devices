import logging

from homeassistant.helpers.entity import EntityCategory

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .connection import ConnectionParams, TCPConnectionParams, RTUConnectionParams

from .datatypes import ModbusMode, ModbusPollMode, ModbusDefaultGroups, ModbusGroup, ModbusDatapoint
from .datatypes import EntityDataSelect, EntityDataNumber
from ..rtu_bus import RTUBusManager, RTUBusClient

_LOGGER = logging.getLogger(__name__)

class ModbusDevice():
    # Default properties
    manufacturer = None
    model = None
    sw_version = None
    serial_number = None

    def __init__(self, connection_params: ConnectionParams, rtu_bus: RTUBusManager):
        if isinstance(connection_params, TCPConnectionParams):
            self._client = AsyncModbusTcpClient(host=connection_params.ip, port=connection_params.port)
        elif isinstance(connection_params, RTUConnectionParams):
            self._client = RTUBusClient(rtu_bus)
        else:
            raise ValueError("Unsupported connection parameters")
        self._slave_id = connection_params.slave_id

        self.Datapoints: dict[ModbusGroup, dict[str, ModbusDatapoint]] = {}
        self.loadDatapoints()
        self.loadConfigUI()
        _LOGGER.debug("Loaded datapoints for %s %s", self.manufacturer, self.model)

        self.firstRead = True

    def close(self):
        """Close the underlying client safely."""
        try:
            _LOGGER.debug("Shutting down and disconnecting device: %s %s",  self.manufacturer, self.model)
            self._client.close()
        except Exception as e:
            _LOGGER.warning("Error closing client for device %s %s: %s", self.manufacturer, self.model, e)
        finally:
            self._client = None

    def loadConfigUI(self):
        # Ensure default groups exist
        self.Datapoints.setdefault(ModbusDefaultGroups.CONFIG, {})
        self.Datapoints.setdefault(ModbusDefaultGroups.UI, {})

        # Add Config UI if we have config values
        if self.Datapoints[ModbusDefaultGroups.CONFIG]:
            self.Datapoints[ModbusDefaultGroups.UI] = {
                "Config Selection": ModbusDatapoint(entity_data=EntityDataSelect(category=EntityCategory.CONFIG)),
                "Config Value": ModbusDatapoint(entity_data=EntityDataNumber(category=EntityCategory.CONFIG, min_value=0, max_value=65535, step=1))
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
        # Ensure group exists and has datapoints
        if group not in self.Datapoints or not self.Datapoints[group]:
            _LOGGER.debug("No datapoints for group %s", group)
            return

        addresses = [
            (dp.address, dp.length)
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

        # If response.registers is shorter than requested, log a warning
        if not hasattr(response, 'registers') or len(response.registers) < n_reg:
            _LOGGER.warning("Partial or missing registers from device %s: requested %s, got %s", self._slave_id, n_reg, getattr(response, 'registers', None))

        _LOGGER.debug("Read data from address: %s - %s", start_addr, getattr(response, 'registers', None))

        # Process the registers and update data points
        for name, dp in self.Datapoints[group].items():
            offset = dp.address - start_addr
            registers = response.registers[offset:offset + dp.length]
            dp.from_raw(registers)

    """ ******************************************************* """
    """ **************** READ SINGLE VALUE ******************** """
    """ ******************************************************* """
    async def readValue(self, group: ModbusGroup, key: str) -> float | str:
        _LOGGER.debug("Reading value: Group: %s, Key: %s", group, key)

        if key not in self.Datapoints[group]:
            raise KeyError(f"Key '{key}' not found in group '{group}'")

        datapoint = self.Datapoints[group][key]
        length = datapoint.length

        method = self._get_read_method(group.mode) 
        response = await method(address=datapoint.address, count=length, device_id=self._slave_id)

        # Handle Modbus errors
        if response.isError():
            raise ModbusException(f"Error reading value for key '{key}': {response}")

        _LOGGER.debug("Read data: %s", response.registers)

        registers = response.registers[:length]
        datapoint.from_raw(registers)

        return datapoint.value

    """ ******************************************************* """
    """ **************** WRITE SINGLE VALUE ******************* """
    """ ******************************************************* """
    async def writeValue(self, group: ModbusGroup, key: str, value: float):
        _LOGGER.debug("Writing value: Group: %s, Key: %s, Value: %s", group, key, value)

        if key not in self.Datapoints[group]:
            raise KeyError(f"Key '{key}' not found in group '{group}'")

        datapoint = self.Datapoints[group][key]
        length = datapoint.length
        if length > 2:
            raise ValueError(f"Unsupported register length: {length}. Only 1 or 2 registers are supported.")

        # Get value as modbus registers
        registers = datapoint.to_raw(value)

        # Write the registers
        address = datapoint.address
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
        datapoint.value = value
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