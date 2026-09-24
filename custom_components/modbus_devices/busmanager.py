from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient

try:
    from pymodbus.pdu import ExceptionResponse
except ImportError:
    ExceptionResponse = None

try:
    from pymodbus.exceptions import ModbusException, ModbusIOException, ConnectionException
except ImportError:
    ModbusException = None
    ModbusIOException = None
    ConnectionException = None

from .devices.modbustraffic import ModbusTrafficStats

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# Base bus manager
# ============================================================================
class BaseBusManager(ABC):
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._client = None
        self._users: set[str] = set()

        # Traffic statistics
        self.traffic = ModbusTrafficStats()              # bus-level
        self._device_traffic: dict[int, ModbusTrafficStats] = {}

        # Context for packet tracing
        self._active_slave: int | None = None

    # ------------------------------------------------------------------
    # Backward compatibility properties for endpoint statistics
    # ------------------------------------------------------------------
    @property
    def tx_packets(self) -> int:
        return self.traffic.tx_count

    @property
    def rx_packets(self) -> int:
        return self.traffic.rx_count

    @property
    def tx_bits(self) -> int:
        return self.traffic.tx_bytes * 8

    @property
    def rx_bits(self) -> int:
        return self.traffic.rx_bytes * 8

    # ------------------------------------------------------------------
    # Bus health overview properties
    # ------------------------------------------------------------------
    @property
    def total_devices_count(self) -> int:
        return len(self._device_traffic)

    @property
    def active_devices_count(self) -> int:
        return sum(1 for s in self._device_traffic.values() if s.is_active)

    @property
    def error_devices_count(self) -> int:
        return sum(1 for s in self._device_traffic.values() if not s.is_active or s.has_recent_error)

    @property
    def problem_slaves(self) -> list[int]:
        return [slave_id for slave_id, s in self._device_traffic.items() if not s.is_active or s.has_recent_error]

    @property
    def devices_traffic(self) -> dict[int, ModbusTrafficStats]:
        return self._device_traffic

    # ------------------------------------------------------------------
    # Device registration
    # ------------------------------------------------------------------

    def register_device(self, slave_id: int, stats: ModbusTrafficStats) -> None:
        """Register per-device traffic stats."""
        self._device_traffic[slave_id] = stats

    def unregister_device(self, slave_id: int) -> None:
        self._device_traffic.pop(slave_id, None)

    # ------------------------------------------------------------------
    # Packet tracing (called by pymodbus)
    # ------------------------------------------------------------------
    def _bus_packet_trace(self, is_tx: bool, packet: bytes) -> bytes:
        """Trace packets at both bus and device level."""

        # Bus-level stats
        if is_tx:
            self.traffic.record_tx(len(packet))
        else:
            self.traffic.record_rx(len(packet))

        # Device-level stats (if we know who is active)
        if self._active_slave is not None:
            stats = self._device_traffic.get(self._active_slave)
            if stats:
                if is_tx:
                    stats.record_tx(len(packet))
                else:
                    stats.record_rx(len(packet))

        return packet

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    async def async_start(self) -> None:
        ...

    @abstractmethod
    async def async_stop(self) -> None:
        ...

    @property
    def connected(self) -> bool:
        return self._client is not None

    # ------------------------------------------------------------------
    # Reference tracking (Home Assistant config entries)
    # ------------------------------------------------------------------

    def attach(self, entry_id: str) -> None:
        self._users.add(entry_id)

    async def detach(self, entry_id: str) -> bool:
        self._users.discard(entry_id)

        if not self._users:
            await self.async_stop()
            return True

        return False

    # ------------------------------------------------------------------
    # Serialized execution
    # ------------------------------------------------------------------

    def _classify_error(self, err_or_response: Any) -> str:
        """Classify error into 'timeout', 'crc', 'exception', 'connection', or 'unknown'."""
        if err_or_response is None:
            return "unknown"

        # 1. Modbus protocol exception (Illegal Function, Illegal Address, etc.)
        if hasattr(err_or_response, "exception_code"):
            return "exception"
        if ExceptionResponse is not None and isinstance(err_or_response, ExceptionResponse):
            return "exception"

        # 2. Connection-level errors
        if ConnectionException is not None and isinstance(err_or_response, ConnectionException):
            return "connection"
        if isinstance(err_or_response, (ConnectionError, BrokenPipeError, ConnectionResetError, ConnectionRefusedError)):
            return "connection"

        err_str = str(err_or_response).lower()
        err_cls = err_or_response.__class__.__name__.lower()

        if "connection" in err_cls or "connection" in err_str or "socket" in err_str or "reset by peer" in err_str or "broken pipe" in err_str:
            return "connection"

        # 3. CRC / Framing errors
        if "crc" in err_str or "checksum" in err_str or "frame" in err_str or "framing" in err_str:
            return "crc"

        # 4. Timeout / No response errors
        if isinstance(err_or_response, (asyncio.TimeoutError, TimeoutError)):
            return "timeout"
        if ModbusIOException is not None and isinstance(err_or_response, ModbusIOException):
            return "timeout"
        if "timeout" in err_str or "timed out" in err_str or "no response" in err_str:
            return "timeout"

        if "illegal" in err_str or "exceptionresponse" in err_cls:
            return "exception"

        return "unknown"

    async def execute(self, slave_id: int, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute a Modbus call with locking and slave context."""
        await self.async_start()

        async with self._lock:
            self._active_slave = slave_id
            try:
                result = await func(*args, **kwargs)
                if hasattr(result, "isError") and result.isError():
                    err_type = self._classify_error(result)
                    self.traffic.record_error(err_type)
                    stats = self._device_traffic.get(slave_id)
                    if stats:
                        stats.record_error(err_type)
                else:
                    self.traffic.record_success()
                    stats = self._device_traffic.get(slave_id)
                    if stats:
                        stats.record_success()
                return result
            except Exception as e:
                err_type = self._classify_error(e)
                # Record error at bus level
                self.traffic.record_error(err_type)
                
                # Record error at device level if known
                stats = self._device_traffic.get(slave_id)
                if stats:
                    stats.record_error(err_type)

                # Re-raise so the device/coordinator sees the exception
                raise
            finally:
                self._active_slave = None   


# ============================================================================
# RTU bus manager
# ============================================================================
class RTUBusManager(BaseBusManager):
    """Shared Modbus RTU serial bus."""

    def __init__(self, *, port: str, baudrate: int, parity: str='N', stopbits: int=1, timeout: float=3, retries: int=0) -> None:
        super().__init__()

        self.port = port
        self.retries = retries
        self._serial_cfg = {
            "baudrate": baudrate,
            "parity": parity,
            "stopbits": stopbits,
            "timeout": timeout,
            "retries": retries,
        }

    async def async_start(self) -> None:
        if self._client is not None:
            return

        _LOGGER.debug("Opening Modbus RTU bus on %s", self.port)

        client = AsyncModbusSerialClient(port=self.port, **self._serial_cfg, trace_packet=self._bus_packet_trace)

        await client.connect()

        if not client.connected:
            client.close()
            raise ConnectionError(f"Failed to open RTU port {self.port}")

        self._client = client

    async def async_stop(self) -> None:
        if self._client is None:
            return

        _LOGGER.debug("Closing Modbus RTU bus on %s", self.port)
        self._client.close()
        self._client = None

    def matches_serial_config(self, *, baudrate: int, parity: str='N', stopbits: int=1, timeout: float, **kwargs) -> bool:
        return (
            self._serial_cfg.get("baudrate") == baudrate
            and self._serial_cfg.get("parity") == parity
            and self._serial_cfg.get("stopbits") == stopbits
            and self._serial_cfg.get("timeout") == timeout
        )


# ============================================================================
# TCP bus manager
# ============================================================================
class TCPBusManager(BaseBusManager):
    """Shared Modbus TCP connection."""

    def __init__(self, *, host: str, port: int, timeout: float=3, retries: int=0) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries

    async def async_start(self) -> None:
        if self._client is not None:
            return

        _LOGGER.debug("Opening Modbus TCP bus %s:%s", self.host, self.port)

        client = AsyncModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
            retries=self.retries,
            trace_packet=self._bus_packet_trace
        )

        await client.connect()

        if not client.connected:
            client.close()
            raise ConnectionError(
                f"Failed to connect to Modbus TCP {self.host}:{self.port}"
            )

        self._client = client
        _LOGGER.debug("Created client!")

    async def async_stop(self) -> None:
        if self._client is None:
            return

        _LOGGER.debug("Closing Modbus TCP bus %s:%s", self.host, self.port)
        self._client.close()
        self._client = None


# ============================================================================
# Bus client (one per device)
# ============================================================================

class BusClient:
    """
    Device-facing Modbus client proxy.
    Each BusClient represents exactly ONE slave/device.
    """

    def __init__(self, bus: BaseBusManager, slave_id: int) -> None:
        self._bus = bus
        self.slave_id = slave_id

    async def connect(self) -> None:
        # Optional explicit connect; bus auto-connects anyway
        await self._bus.async_start()

    async def close(self) -> None:
        # Lifecycle is owned by the bus manager
        return

    @property
    def connected(self) -> bool:
        return self._bus.connected

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        async def proxy(*args, **kwargs):
            await self._bus.async_start() 
            client = self._bus._client
            if client is None:
                raise ConnectionError("Modbus client not available")

            method = getattr(client, name)
            if not callable(method):
                return method

            return await self._bus.execute(self.slave_id, method, *args, **kwargs)

        return proxy
