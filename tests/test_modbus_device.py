import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.modbus_devices.devices.modbusdevice import (
    ModbusDevice,
    ModbusGroup,
    ModbusDatapoint,
    ModbusMode,
    ModbusPollMode,
)
from custom_components.modbus_devices.devices.connection import (
    TCPConnectionParams,
    RTUConnectionParams,
)
from custom_components.modbus_devices.rtu_bus import RTUBusManager


@pytest.fixture
def mock_tcp_params():
    return TCPConnectionParams(ip="127.0.0.1", port=502, slave_id=1)


@pytest.fixture
def mock_rtu_params():
    return RTUConnectionParams(slave_id=1)


@pytest.fixture
def mock_rtu_bus():
    return MagicMock(spec=RTUBusManager)


@pytest.fixture
def modbus_device(mock_tcp_params, mock_rtu_bus):
    # Mocking AsyncModbusTcpClient to avoid network calls
    with patch(
        "custom_components.modbus_devices.devices.modbusdevice.AsyncModbusTcpClient"
    ) as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.connect = AsyncMock()
        mock_client.close = MagicMock()

        device = ModbusDevice(mock_tcp_params, mock_rtu_bus)
        device.Datapoints = {}  # Clear for testing
        return device


@pytest.mark.asyncio
async def test_read_group_address_calculation(modbus_device):
    # Setup a mock group and datapoints
    group = ModbusGroup(mode=ModbusMode.HOLDING, poll_mode=ModbusPollMode.POLL_ON)

    dp1 = MagicMock(spec=ModbusDatapoint)
    dp1.address = 10
    dp1.register_count = 2
    dp1.from_modbus = MagicMock()

    dp2 = MagicMock(spec=ModbusDatapoint)
    dp2.address = 15
    dp2.register_count = 1
    dp2.from_modbus = MagicMock()

    modbus_device.Datapoints[group] = {"dp1": dp1, "dp2": dp2}

    # Setup the mock client response
    mock_response = MagicMock()
    mock_response.isError.return_value = False
    mock_response.registers = [0] * 10  # Enough for the range 10 to 16

    modbus_device._client.read_holding_registers = AsyncMock(return_value=mock_response)

    await modbus_device.readGroup(group)

    # Expected range: start at 10, end at 15+1=16. Count = 6.
    modbus_device._client.read_holding_registers.assert_awaited_once_with(
        address=10, count=6, device_id=1
    )


@pytest.mark.asyncio
async def test_read_group_empty(modbus_device):
    group = ModbusGroup(mode=ModbusMode.HOLDING, poll_mode=ModbusPollMode.POLL_ON)
    modbus_device.Datapoints[group] = {}

    # Should not crash and not call read
    await modbus_device.readGroup(group)
    assert modbus_device._client.read_holding_registers.call_count == 0


@pytest.mark.asyncio
async def test_write_value_valid(modbus_device):
    group = ModbusGroup(mode=ModbusMode.HOLDING, poll_mode=ModbusPollMode.POLL_ON)

    dp = MagicMock(spec=ModbusDatapoint)
    dp.address = 100
    dp.register_count = 1
    dp.to_modbus.return_value = [123]
    dp.value = None

    modbus_device.Datapoints[group] = {"write_key": dp}

    # Setup the write response
    mock_response = MagicMock()
    mock_response.isError.return_value = False

    modbus_device._client.write_register = AsyncMock(return_value=mock_response)

    await modbus_device.writeValue(group, "write_key", 123)

    modbus_device._client.write_register.assert_awaited_once_with(
        address=100, value=123, device_id=1
    )
    assert dp.value == 123


@pytest.mark.asyncio
async def test_write_value_unsupported_register_count(modbus_device):
    group = ModbusGroup(mode=ModbusMode.HOLDING, poll_mode=ModbusPollMode.POLL_ON)

    dp = MagicMock(spec=ModbusDatapoint)
    dp.address = 100
    dp.register_count = 3  # Too many

    modbus_device.Datapoints[group] = {"write_key": dp}

    with pytest.raises(ValueError, match="Unsupported register count"):
        await modbus_device.writeValue(group, "write_key", 123)
