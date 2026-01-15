from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer

from .statistics import STATS_MANAGER, StatisticsManager

_LOGGER = logging.getLogger(__name__)


class CountingRtuFramer(ModbusRtuFramer):
    """A framer that counts sent and received bytes."""

    def __init__(self, client: AsyncModbusSerialClient | None = None, *, stats_manager: StatisticsManager, endpoint: str) -> None:
        """Initialize the counting framer."""
        super().__init__(client)
        self._stats_manager = stats_manager
        self._endpoint = endpoint

    def build_packet(self, message: bytes) -> bytes:
        """Count sent bytes."""
        packet = super().build_packet(message)
        self._stats_manager.add_bytes_sent(self._endpoint, len(packet))
        return packet

    def process_incoming_packet(self, data: bytes, callback: Callable[[Any], None], slave: int, **kwargs: Any) -> None:
        """Count received bytes."""
        self._stats_manager.add_bytes_received(self._endpoint, len(data))
        super().process_incoming_packet(data, callback, slave, **kwargs)


class RTUBusManager:
    """Owns a single Modbus RTU serial port and serializes all access."""

    def __init__(self, *, hass, port: str, baudrate: int, bytesize: int, parity: str, stopbits: int, timeout: float) -> None:
        self.hass = hass
        self.port = port

        self._serial_cfg = {
            "baudrate": baudrate,
            "bytesize": bytesize,
            "parity": parity,
            "stopbits": stopbits,
            "timeout": timeout,
        }

        self._lock = asyncio.Lock()
        self._client: AsyncModbusSerialClient | None = None
        self._users: set[str] = set()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_start(self) -> None:
        if self._client is not None:
            return

        _LOGGER.debug("Opening Modbus RTU bus on %s", self.port)

        framer = CountingRtuFramer(stats_manager=STATS_MANAGER, endpoint=self.port)
        client = AsyncModbusSerialClient(
            port=self.port,
            framer=framer,
            **self._serial_cfg,
        )

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

    # ------------------------------------------------------------------
    # Reference tracking
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
    # Validation
    # ------------------------------------------------------------------

    def matches_serial_config(self, *, baudrate: int, bytesize: int, parity: str, stopbits: int, timeout: float) -> bool:
        return self._serial_cfg == { 
            "baudrate": baudrate,
            "bytesize": bytesize,
            "parity": parity,
            "stopbits": stopbits,
            "timeout": timeout,
        }

    # ------------------------------------------------------------------
    # Internal execution helper
    # ------------------------------------------------------------------

    async def _execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        await self.async_start()

        async with self._lock:
            return await func(*args, **kwargs)


class RTUBusClient:
    """
    Proxy that looks like AsyncModbusSerialClient but routes all calls
    through a shared RTUBusManager.
    """

    def __init__(self, bus: RTUBusManager) -> None:
        self._bus = bus

    # ------------------------------
    # Explicit lifecycle methods
    # ------------------------------

    async def connect(self) -> None:
        """Ensure the RTU bus is started."""
        await self._bus.async_start()

    async def close(self) -> None:
        """
        NO-OP.

        The bus lifecycle is shared and reference-counted.
        """
        return

    @property
    def connected(self) -> bool:
        return self._bus._client is not None

    # ------------------------------
    # Dynamic method proxying
    # ------------------------------

    def __getattr__(self, name: str):
        """
        Proxy async Modbus calls to the shared RTU client,
        enforcing serialization.
        """

        if name.startswith("_"):
            raise AttributeError(name)

        async def proxy(*args, **kwargs):
            await self._bus.async_start()

            client = self._bus._client
            if client is None:
                raise ConnectionError("RTU client not available")

            method = getattr(client, name)
            if not callable(method):
                return method

            async with self._bus._lock:
                return await method(*args, **kwargs)

        return proxy
