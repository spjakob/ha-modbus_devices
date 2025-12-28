import logging
from .CASA_R4 import GROUP_SETPOINTS, ModbusDefaultGroups, Device as BaseDevice

_LOGGER = logging.getLogger(__name__)

class Device(BaseDevice):
    # Override static device information
    manufacturer="Swegon"
    model="CASA R7"

    def loadDatapoints(self):
        super().loadDatapoints() 

        # Modify datapoints    
        self.Datapoints[GROUP_SETPOINTS]["Temperature Setpoint"].Scaling = 1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling FreshAir Max"].Scaling=1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling FreshAir Start"].Scaling=1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling RoomTemp Start"].Scaling=1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling SupplyTemp Min"].Scaling=1