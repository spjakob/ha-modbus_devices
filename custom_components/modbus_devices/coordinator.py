import async_timeout
import copy
import datetime as dt
import logging

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, ConfigEntryNotReady, ConfigEntryError

from .devices.helpers import load_device_class
from .devices.datatypes import ModbusDefaultGroups, ModbusDatapoint
from .devices.datatypes import EntityDataSelect, EntityDataNumber
from .devices.modbusdevice import ModbusDevice
from .entity import ModbusBaseEntity

_LOGGER = logging.getLogger(__name__)

class ModbusCoordinator(DataUpdateCoordinator):    
    def __init__(self, hass, device, device_model:str, connection_params, scan_interval, scan_interval_fast, rtu_bus):
        """Initialize coordinator parent"""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="ModbusDevice: " + device.name,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=dt.timedelta(seconds=scan_interval),
        )

        self.device_model = device_model
        self.connection_params = connection_params
        self.rtu_bus = rtu_bus

        self._fast_poll_enabled = False
        self._fast_poll_count = 0
        self._normal_poll_interval = scan_interval
        self._fast_poll_interval = scan_interval_fast

        self._device = device

        self._modbusDevice: ModbusDevice | None = None

        # Storage for config selection
        self.config_value_select:ModbusBaseEntity = None
        self.config_value_number:ModbusBaseEntity = None
        self.config_value_active:ModbusBaseEntity = None

    async def _async_setup(self):
        # Load modbus device driver
        device_class = await load_device_class(self.device_model)
        if device_class is not None:
            try:
                self._modbusDevice = device_class(self.connection_params, self.rtu_bus)
            except Exception as err:
                raise ConfigEntryNotReady("Could not read data from device!") from err
        else:
            raise ConfigEntryError

    def close(self):
        """Close the underlying device safely."""
        self._modbusDevice.close()

    @property
    def device_id(self):
        return self._device.id

    @property
    def devicename(self):
        return self._device.name

    @property
    def identifiers(self):
        return self._device.identifiers

    def setFastPollMode(self):
        _LOGGER.debug("Enabling fast poll mode")
        self._fast_poll_enabled = True
        self._fast_poll_count = 0
        self.update_interval = dt.timedelta(seconds=self._fast_poll_interval)
        self._schedule_refresh()

    def setNormalPollMode(self):
        _LOGGER.debug("Enabling normal poll mode")
        self._fast_poll_enabled = False
        self.update_interval = dt.timedelta(seconds=self._normal_poll_interval)


    async def _async_update_data(self):
        _LOGGER.debug("Coordinator updating data for: %s", self.devicename) 

        """ Counter for fast polling """
        if self._fast_poll_enabled:
            self._fast_poll_count += 1
            if self._fast_poll_count > 5:
                self.setNormalPollMode()

        """ Fetch data """
        try:
            async with async_timeout.timeout(20):
                await self._modbusDevice.readData()       
        except Exception as err:
            _LOGGER.warning("Failed to update %s: %s", self.devicename, err)
            raise UpdateFailed from err
        
        await self._async_update_deviceInfo()

    async def _async_update_deviceInfo(self) -> None:
        device_registry = dr.async_get(self.hass)
        device_registry.async_update_device(
            self.device_id,
            manufacturer=self._modbusDevice.manufacturer,
            model=self._modbusDevice.model,
            sw_version=self._modbusDevice.sw_version,
            serial_number=self._modbusDevice.serial_number,
        )
        _LOGGER.debug("Updated device data for: %s", self.devicename) 

    ################################
    ######## Configuration #########
    ################################   
    async def _swap_config_value_entity(self, datapoint: ModbusDatapoint):
        _LOGGER.debug("Changing CONFIG value entity type")

        # Disable old entity
        if self.config_value_active is not None:
            self.config_value_active.entity_enabled = False
            self.config_value_active.async_schedule_update_ha_state()
            self.config_value_active = None

        # Select active entity
        if isinstance(datapoint.entity_data, EntityDataNumber):
            self.config_value_active = self.config_value_number
        elif isinstance(datapoint.entity_data, EntityDataSelect):
            self.config_value_active = self.config_value_select
        else:
            _LOGGER.warning("Entity type not supported for config!")
            return

        # Enable active entity
        self.config_value_active.entity_enabled = True

    async def config_select(self, key):
        _LOGGER.debug("In config select: %s", key)

        # Change type of entitiy for config value
        old_dp = self.config_value_active.modbusDataPoint if self.config_value_active else None
        new_dp = self._modbusDevice.Datapoints[ModbusDefaultGroups.CONFIG][key]

        _LOGGER.debug("Dps: %s %s", old_dp, new_dp)

        if old_dp is None or type(old_dp.entity_data) != type(new_dp.entity_data):
            _LOGGER.debug("New type!")
            await self._swap_config_value_entity(new_dp)
        try:
            # Update entity settings and read value
            self.config_value_active.modbusDataPoint = new_dp
            self.config_value_active._group = ModbusDefaultGroups.CONFIG
            self.config_value_active._key = key
            self.config_value_active._loadEntitySettings()
            await self._modbusDevice.readValue(ModbusDefaultGroups.CONFIG, key)
        finally:
            _LOGGER.debug("Updating!")
            self.config_value_active.async_schedule_update_ha_state()

    def get_config_options(self):
        options = {}
        for i, config in enumerate(self._modbusDevice.Datapoints[ModbusDefaultGroups.CONFIG]):
            options.update({i:config})
        return options

    ################################
    ######### Read / Write #########
    ################################   
    def get_value(self, group, key):
        if group in self._modbusDevice.Datapoints:
            if key in self._modbusDevice.Datapoints[group]:
                return self._modbusDevice.Datapoints[group][key].value
        return None

    def get_attrs(self, group, key):
        if group in self._modbusDevice.Datapoints:
            if key in self._modbusDevice.Datapoints[group]:
                return self._modbusDevice.Datapoints[group][key].entity_data.attrs
        return None

    async def write_value(self, group, key, value):
        _LOGGER.debug("Write_Data: %s - %s - %s", group, key, value)
        try:
            await self._modbusDevice.writeValue(group, key, value)
        except Exception as exc:
            _LOGGER.error("Failed to write value '%s' to key '%s' in group '%s': %s", value, key, group, exc, exc_info=exc)
            raise

        self.setFastPollMode()