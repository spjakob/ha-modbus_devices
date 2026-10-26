
import logging
from .CASA_Base import GROUP_SETPOINTS, GROUP_DEVICE_INFO, GROUP_ALARMS, GROUP_UNIT_STATUSES, ModbusDefaultGroups, Device as BaseDevice
from ..datatypes import ModbusSensor, ModbusBinarySensor
from homeassistant.const import UnitOfTime
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass

_LOGGER = logging.getLogger(__name__)

class Device(BaseDevice):
    # Override static device information
    model="CASA W4"

    def loadDatapoints(self):
        super().loadDatapoints()

        # Registers end at 6045 on W4 (FW 2.2), reading 6046 fails the whole group
        self.Datapoints[GROUP_DEVICE_INFO]["Serial Number"].register_count = 23

        # Alarm registers above 6137 do not exist on W4
        for name in [name for name, dp in self.Datapoints[GROUP_ALARMS].items() if dp.address >= 6138]:
            self.Datapoints[GROUP_ALARMS].pop(name)

        # Add entities
        self.Datapoints[GROUP_UNIT_STATUSES]["Boost Time Left"] = ModbusSensor(address=6307, deviceClass=SensorDeviceClass.DURATION, units=UnitOfTime.MINUTES, icon="mdi:timer-outline")
        self.Datapoints[GROUP_UNIT_STATUSES]["Fireplace Active"] = ModbusBinarySensor(address=6334, icon="mdi:fireplace")
        self.Datapoints[GROUP_UNIT_STATUSES]["Filter Guard"] = ModbusBinarySensor(address=6341, deviceClass=BinarySensorDeviceClass.PROBLEM, icon="mdi:air-filter")
        self.Datapoints[GROUP_UNIT_STATUSES]["Hours To Service"] = ModbusSensor(address=6342, deviceClass=SensorDeviceClass.DURATION, units=UnitOfTime.HOURS, icon="mdi:wrench-clock")

        # Modify scaling
        self.Datapoints[GROUP_SETPOINTS]["Temperature Setpoint"].scaling = 1

        # Modify scaling on configuration tags
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling FreshAir Max"].scaling=1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling FreshAir Start"].scaling=1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling RoomTemp Start"].scaling=1
