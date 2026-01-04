import logging
from .CASA_Base import GROUP_SETPOINTS, GROUP_UNIT_STATUSES, ModbusDefaultGroups, GROUP_SENSORS, GROUP_UI, Device as BaseDevice
from ..datatypes import ModbusDatapoint, ModbusSensorData
from homeassistant.const import PERCENTAGE, REVOLUTIONS_PER_MINUTE

_LOGGER = logging.getLogger(__name__)

class Device(BaseDevice):
    # Override static device information
    manufacturer="Swegon"
    model="CASA R7"

    def loadDatapoints(self):
        super().loadDatapoints()

        # Modify datapoints
        self.Datapoints[GROUP_SETPOINTS]["Temperature Setpoint"].Scaling = 1
        self.Datapoints[GROUP_UNIT_STATUSES]["Heat Exchanger"].Scaling = 0.1
        self.Datapoints[GROUP_SENSORS]["Absolute Humidity"].Scaling=0.01

        # Replace HE output with HE RPM
        self.Datapoints[GROUP_UNIT_STATUSES].pop("Heat Exchanger")
        self.Datapoints[GROUP_SENSORS]["Heat Exchanger RPM"] = ModbusDatapoint(Address=6233, Scaling=1.0, DataType=ModbusSensorData(units=REVOLUTIONS_PER_MINUTE, icon="mdi:hvac"))

        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling FreshAir Max"].Scaling=1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling FreshAir Start"].Scaling=1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling RoomTemp Start"].Scaling=1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling SupplyTemp Min"].Scaling=1

        self.Datapoints[GROUP_UI]["Supply temp Efficiency"] = ModbusDatapoint(DataType=ModbusSensorData(units=PERCENTAGE))
        self.Datapoints[GROUP_UI]["Extract temp Efficiency"] = ModbusDatapoint(DataType=ModbusSensorData(units=PERCENTAGE))

    def onAfterRead(self):
        super().onAfterRead()

        # Calculate efficiency
        fresh = self.Datapoints[GROUP_SENSORS]["Fresh Air Temp"].Value
        sup = self.Datapoints[GROUP_SENSORS]["Supply Temp before re-heater"].Value
        extract = self.Datapoints[GROUP_SENSORS]["Extract Temp"].Value
        exhaust = self.Datapoints[GROUP_SENSORS]["Exhaust Temp"].Value

        try:
            supefficiency = ((sup - fresh) / (extract - fresh)) * 100
            self.Datapoints[GROUP_UI]["Supply temp Efficiency"].Value = round(supefficiency, 1)
        except ZeroDivisionError:
            self.Datapoints[GROUP_UI]["Supply temp Efficiency"].Value = 0
        try:
            exhefficiency = ((extract - exhaust) / (extract - fresh)) * 100
            self.Datapoints[GROUP_UI]["Extract temp Efficiency"].Value = round(exhefficiency, 1)
        except ZeroDivisionError:
            self.Datapoints[GROUP_UI]["Extract temp Efficiency"].Value = 0