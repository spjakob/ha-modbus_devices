import time
from dataclasses import dataclass, field

@dataclass
class ModbusTrafficStats:
    tx_count: int = 0
    rx_count: int = 0
    tx_bytes: int = 0
    rx_bytes: int = 0
    errors: int = 0
    timeouts: int = 0
    crc_errors: int = 0
    exceptions: int = 0
    connection_errors: int = 0
    last_error_type: str | None = None
    last_error_time: float = 0.0
    last_success_time: float = 0.0
    last_activity: float = 0.0
    start_time: float = field(default_factory=time.monotonic)

    def record_tx(self, bytes_: int):
        self.tx_count += 1
        self.tx_bytes += bytes_
        self.last_activity = time.monotonic()

    def record_rx(self, bytes_: int):
        self.rx_count += 1
        self.rx_bytes += bytes_
        self.last_activity = time.monotonic()
        self.last_success_time = time.monotonic()

    def record_success(self):
        self.last_activity = time.monotonic()
        self.last_success_time = time.monotonic()

    def record_error(self, error_type: str = "unknown"):
        self.errors += 1
        now = time.monotonic()
        self.last_activity = now
        self.last_error_time = now
        self.last_error_type = error_type

        if error_type == "timeout":
            self.timeouts += 1
        elif error_type == "crc":
            self.crc_errors += 1
        elif error_type == "exception":
            self.exceptions += 1
        elif error_type == "connection":
            self.connection_errors += 1

    @property
    def has_recent_error(self) -> bool:
        """True if the device's last transaction was an error."""
        return self.errors > 0 and self.last_error_time >= self.last_success_time

    @property
    def is_active(self) -> bool:
        """Considered active if communicated successfully within the last 5 minutes without ongoing failure."""
        if self.last_success_time == 0.0:
            return False
        if self.last_error_time > self.last_success_time:
            return False
        now = time.monotonic()
        return (now - self.last_success_time) < 300.0

    @property
    def tx_rate(self) -> float:
        dt = time.monotonic() - self.start_time
        return self.tx_bytes / dt if dt > 0 else 0.0

    @property
    def rx_rate(self) -> float:
        dt = time.monotonic() - self.start_time
        return self.rx_bytes / dt if dt > 0 else 0.0

    # Helper for diagnostics
    def to_dict(self) -> dict:
        return {
            "tx_frames": self.tx_count,
            "rx_frames": self.rx_count,
            "tx_bytes": self.tx_bytes,
            "rx_bytes": self.rx_bytes,
            "errors_total": self.errors,
            "timeouts": self.timeouts,
            "crc_errors": self.crc_errors,
            "modbus_exceptions": self.exceptions,
            "connection_errors": self.connection_errors,
            "last_error_type": self.last_error_type,
            "last_error_time": self.last_error_time,
            "last_success_time": self.last_success_time,
            "last_activity_monotonic": self.last_activity,
            "is_active": self.is_active,
            "has_recent_error": self.has_recent_error,
            "tx_rate_Bps": round(self.tx_rate, 1),
            "rx_rate_Bps": round(self.rx_rate, 1),
        }