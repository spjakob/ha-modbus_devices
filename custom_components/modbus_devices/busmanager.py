from __future__ import annotations

import asyncio
import collections
import logging
import time
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
# Bus utilization tracker
# ============================================================================
class BusUtilizationTracker:
    """Tracks bus utilization (% time busy) over a sliding time window."""

    def __init__(self, window_seconds: float = 60.0) -> None:
        self.window_seconds = window_seconds
        self._history: collections.deque[tuple[float, float]] = collections.deque()  # (end_time, duration)
        self._current_busy_start: float | None = None

    def start_busy(self) -> None:
        if self._current_busy_start is None:
            self._current_busy_start = time.monotonic()

    def end_busy(self) -> None:
        if self._current_busy_start is not None:
            now = time.monotonic()
            duration = max(0.0, now - self._current_busy_start)
            self._history.append((now, duration))
            self._current_busy_start = None
            self._cleanup(now)

    def _cleanup(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._history and self._history[0][0] < cutoff:
            self._history.popleft()

    @property
    def utilization_percent(self) -> float:
        """Calculate bus utilization percentage over the sliding window."""
        now = time.monotonic()
        self._cleanup(now)
        total_busy = 0.0
        cutoff = now - self.window_seconds

        for end_time, duration in self._history:
            start_time = end_time - duration
            if start_time < cutoff:
                total_busy += max(0.0, end_time - cutoff)
            else:
                total_busy += duration

        if self._current_busy_start is not None:
            current_start = max(self._current_busy_start, cutoff)
            total_busy += max(0.0, now - current_start)

        pct = (total_busy / self.window_seconds) * 100.0
        return min(100.0, max(0.0, round(pct, 1)))


# ============================================================================
# Base bus manager
# ============================================================================
class BaseBusManager(ABC):
    def __init__(self, queue_timeout: float = 20.0, turnaround_delay: float = 0.02) -> None:
        self._lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()
        self._startup_lock = asyncio.Lock()
        self._client = None
        self._users: set[str] = set()

        # Queue tracking & turnaround configuration
        self._waiting_count: int = 0
        self.queue_timeout: float = queue_timeout
        self._turnaround_delay: float = turnaround_delay

        # Utilization tracking
        self._utilization_tracker = BusUtilizationTracker(window_seconds=60.0)

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

    @property
    def queue_depth(self) -> int:
        """Return the number of requests currently waiting in queue for the bus lock."""
        return self._waiting_count

    @property
    def utilization_percent(self) -> float:
        """Return the bus utilization percentage over the sliding 60-second window."""
        return self._utilization_tracker.utilization_percent

    @property
    def startup_lock(self) -> asyncio.Lock:
        """Return the startup lock used to serialize initial device refreshes."""
        return self._startup_lock

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
        """Execute a Modbus call with queue management, cancellation shielding, and slave context."""
        await self.async_start()

        # 1. Wait for bus lock with a queue timeout
        self._waiting_count += 1
        try:
            await asyncio.wait_for(self._lock.acquire(), timeout=self.queue_timeout)
        except asyncio.TimeoutError:
            _LOGGER.warning(
                "Bus queue timeout: Device (Slave %s) waited more than %.1fs for bus lock. "
                "Dropping request to relieve bus congestion.",
                slave_id, self.queue_timeout
            )
            self.traffic.record_error("timeout")
            stats = self._device_traffic.get(slave_id)
            if stats:
                stats.record_error("timeout")
            raise TimeoutError(f"Bus queue timeout for slave {slave_id} after {self.queue_timeout}s")
        finally:
            self._waiting_count -= 1

        # 2. Lock is acquired: execute the wire transaction shielded against cancellation
        self._utilization_tracker.start_busy()
        self._active_slave = slave_id
        try:
            coro_or_val = func(*args, **kwargs)
            if asyncio.iscoroutine(coro_or_val) or isinstance(coro_or_val, asyncio.Future):
                wire_task = asyncio.ensure_future(coro_or_val)
                try:
                    result = await asyncio.shield(wire_task)
                except asyncio.CancelledError:
                    _LOGGER.warning(
                        "Request for Slave %s was cancelled by caller while active on bus. "
                        "Shielding transaction until physical wire is clear...",
                        slave_id
                    )
                    try:
                        await wire_task
                    except Exception as wire_err:
                        _LOGGER.debug("Shielded transaction for Slave %s completed with: %s", slave_id, wire_err)
                    raise
            else:
                result = coro_or_val

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
        except asyncio.CancelledError:
            raise
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
            self._utilization_tracker.end_busy()
            try:
                # Small inter-frame delay to ensure RS485 bus quiet time (turnaround)
                if self._turnaround_delay > 0:
                    try:
                        await asyncio.sleep(self._turnaround_delay)
                    except asyncio.CancelledError:
                        pass
            finally:
                self._lock.release()


# ============================================================================
# RTU bus manager
# ============================================================================
class RTUBusManager(BaseBusManager):
    """Shared Modbus RTU serial bus."""

    def __init__(
        self,
        *,
        port: str,
        baudrate: int,
        parity: str = 'N',
        stopbits: int = 1,
        timeout: float = 3,
        retries: int = 0,
        queue_timeout: float = 20.0,
        turnaround_delay: float = 0.02,
    ) -> None:
        super().__init__(queue_timeout=queue_timeout, turnaround_delay=turnaround_delay)

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

        async with self._connect_lock:
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
        async with self._connect_lock:
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

    def __init__(
        self,
        *,
        host: str,
        port: int,
        timeout: float = 3,
        retries: int = 0,
        queue_timeout: float = 20.0,
        turnaround_delay: float = 0.005,
    ) -> None:
        super().__init__(queue_timeout=queue_timeout, turnaround_delay=turnaround_delay)
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries

    async def async_start(self) -> None:
        if self._client is not None:
            return

        async with self._connect_lock:
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
        async with self._connect_lock:
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

    @property
    def startup_lock(self) -> asyncio.Lock:
        return self._bus.startup_lock

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
