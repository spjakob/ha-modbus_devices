import time
from dataclasses import dataclass, field

@dataclass
class ModbusTrafficStats:
    tx_count: int = 0
    rx_count: int = 0
    tx_bytes: int = 0
    rx_bytes: int = 0
    errors: int = 0
    last_activity: float = 0.0
    start_time: float = field(default_factory=time.monotonic)

    def record_tx(self, bytes_):
        self.tx_count += 1
        self.tx_bytes += bytes_
        self.last_activity = time.monotonic()

    def record_rx(self, bytes_):
        self.rx_count += 1
        self.rx_bytes += bytes_
        self.last_activity = time.monotonic()

    def record_error(self):
        self.errors += 1
        self.last_activity = time.monotonic()

    @property
    def tx_rate(self):
        dt = time.monotonic() - self.start_time
        return self.tx_bytes / dt if dt > 0 else 0

    @property
    def rx_rate(self):
        dt = time.monotonic() - self.start_time
        return self.rx_bytes / dt if dt > 0 else 0
    
    # Helper for diagnostics
    def to_dict(self) -> dict:
        return {
            "tx_frames": self.tx_count,
            "rx_frames": self.rx_count,
            "tx_bytes": self.tx_bytes,
            "rx_bytes": self.rx_bytes,
            "errors": self.errors,
            "last_activity_monotonic": self.last_activity,
            "tx_rate_Bps": round(self.tx_rate, 1),
            "rx_rate_Bps": round(self.rx_rate, 1),
        }