class ConnectionParams:
    """Base class for connection parameters."""
    pass

class TCPConnectionParams(ConnectionParams):
    def __init__(self, ip: str, port: int, slave_id: int = 1, device_id: str = None):
        self.ip = ip
        self.port = port
        self.slave_id = slave_id
        self.device_id = device_id

class RTUConnectionParams(ConnectionParams):
    def __init__(self, serial_port: str, baud_rate: int, slave_id: int = 1, device_id: str = None):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.slave_id = slave_id
        self.device_id = device_id
