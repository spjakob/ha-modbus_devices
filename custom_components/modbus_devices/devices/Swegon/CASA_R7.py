import logging
from .CASA_Base import GROUP_SETPOINTS, GROUP_UNIT_STATUSES, ModbusDefaultGroups, GROUP_SENSORS, GROUP_UI, Device as BaseDevice
from ..datatypes import ModbusDatapoint, EntityDataSensor
from homeassistant.const import PERCENTAGE, REVOLUTIONS_PER_MINUTE

_LOGGER = logging.getLogger(__name__)

class Device(BaseDevice):
    # Override static device information
    model="CASA R7"

    def loadDatapoints(self):
        super().loadDatapoints()

        # Modify datapoints
        self.Datapoints[GROUP_SETPOINTS]["Temperature Setpoint"].scaling = 1
        self.Datapoints[GROUP_UNIT_STATUSES]["Heat Exchanger"].scaling = 0.1
        self.Datapoints[GROUP_SENSORS]["Absolute Humidity"].scaling=0.01

        # Replace HE output with HE RPM
        self.Datapoints[GROUP_UNIT_STATUSES].pop("Heat Exchanger")
        self.Datapoints[GROUP_SENSORS]["Heat Exchanger RPM"] = ModbusDatapoint(address=6233, scaling=1.0, entity_data=EntityDataSensor(units=REVOLUTIONS_PER_MINUTE, icon="mdi:hvac"))

        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling FreshAir Max"].scaling=1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling FreshAir Start"].scaling=1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling RoomTemp Start"].scaling=1
        self.Datapoints[ModbusDefaultGroups.CONFIG]["Night Cooling SupplyTemp Min"].scaling=1

        self.Datapoints[GROUP_UI]["Supply temp Efficiency"] = ModbusDatapoint(entity_data=EntityDataSensor(units=PERCENTAGE))
        self.Datapoints[GROUP_UI]["Extract temp Efficiency"] = ModbusDatapoint(entity_data=EntityDataSensor(units=PERCENTAGE))

    def onAfterRead(self):
        super().onAfterRead()

        # Calculate efficiency
        fresh = self.Datapoints[GROUP_SENSORS]["Fresh Air Temp"].value
        sup = self.Datapoints[GROUP_SENSORS]["Supply Temp before re-heater"].value
        extract = self.Datapoints[GROUP_SENSORS]["Extract Temp"].value
        exhaust = self.Datapoints[GROUP_SENSORS]["Exhaust Temp"].value

        try:
            supefficiency = ((sup - fresh) / (extract - fresh)) * 100
            self.Datapoints[GROUP_UI]["Supply temp Efficiency"].value = round(supefficiency, 1)
        except ZeroDivisionError:
            self.Datapoints[GROUP_UI]["Supply temp Efficiency"].value = 0
        try:
            exhefficiency = ((extract - exhaust) / (extract - fresh)) * 100
            self.Datapoints[GROUP_UI]["Extract temp Efficiency"].value = round(exhefficiency, 1)
        except ZeroDivisionError:
            self.Datapoints[GROUP_UI]["Extract temp Efficiency"].value = 0