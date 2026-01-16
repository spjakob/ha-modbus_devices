"""Config flow to configure Modbus Devices integration"""
import asyncio
import glob
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from typing import Any

from .const import DOMAIN, CONF_DEVICE_MODE, CONF_NAME, CONF_DEVICE_MODEL, CONF_IP, CONF_PORT, CONF_SLAVE_ID, CONF_SCAN_INTERVAL, CONF_SCAN_INTERVAL_FAST
from .const import CONF_MODE_SELECTION, CONF_ADD_TCPIP, CONF_ADD_RTU
from .const import CONF_SERIAL_PORT, CONF_SERIAL_BAUD
from .const import DEVICE_MODE_TCPIP, DEVICE_MODE_RTU
from .const import DEFAULT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_FAST
from .const import CONF_TYPE, TYPE_ENDPOINT, TYPE_DEVICE, CONF_ENDPOINT_ID

from .devices.helpers import get_available_drivers

_LOGGER = logging.getLogger(__name__)

# Defaults for Endpoints
ENDPOINT_DATA_TCPIP = {
    CONF_DEVICE_MODE: DEVICE_MODE_TCPIP,
    CONF_NAME: "Modbus TCP Endpoint",
    CONF_IP: "192.168.1.1",
    CONF_PORT: 502,
}

ENDPOINT_DATA_RTU = {
    CONF_DEVICE_MODE: DEVICE_MODE_RTU,
    CONF_NAME: "Modbus RTU Endpoint",
    CONF_SERIAL_PORT: "",
    CONF_SERIAL_BAUD: 9600,
}

# Defaults for Devices
DEVICE_DATA_DEFAULT = {
    CONF_NAME: "My Modbus Device",
    CONF_DEVICE_MODEL: None,
    CONF_ENDPOINT_ID: None,
    CONF_SLAVE_ID: 1,
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL_FAST: DEFAULT_SCAN_INTERVAL_FAST
}


class ModbusFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return ModbusOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        # Menu: Create Endpoint or Create Device
        MENU_OPTIONS = [
            "add_tcp_endpoint",
            "add_rtu_endpoint",
            "add_device"
        ]

        # If the user selected a menu option via the `user` step logic or standard menu logic
        # But here we implement a custom menu
        if user_input is not None:
             selection = user_input.get(CONF_MODE_SELECTION)
             if selection == "add_tcp_endpoint":
                 return await self.async_step_add_tcp_endpoint()
             elif selection == "add_rtu_endpoint":
                 return await self.async_step_add_rtu_endpoint()
             elif selection == "add_device":
                 return await self.async_step_add_device()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_MODE_SELECTION): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=MENU_OPTIONS,
                        translation_key="mode_selection"
                        # We rely on strings.json to translate these keys if possible,
                        # or just raw strings for now if translation key mapping is tricky.
                        # Actually, let's use simple dict for options to be safe
                    )
                )
            }),
            errors=errors
        )

    # ------------------------------------------------------------------
    # Endpoint Steps
    # ------------------------------------------------------------------
    async def async_step_add_tcp_endpoint(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors = {}
        if user_input is not None:
            user_input[CONF_TYPE] = TYPE_ENDPOINT
            user_input[CONF_DEVICE_MODE] = DEVICE_MODE_TCPIP
            # Check unique ID? usually IP:Port
            # But ConfigEntry doesn't enforce uniqueness unless we call async_set_unique_id
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="add_tcp_endpoint",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=ENDPOINT_DATA_TCPIP[CONF_NAME]): cv.string,
                vol.Required(CONF_IP, default=ENDPOINT_DATA_TCPIP[CONF_IP]): cv.string,
                vol.Required(CONF_PORT, default=ENDPOINT_DATA_TCPIP[CONF_PORT]): int,
            }),
            errors=errors
        )

    async def async_step_add_rtu_endpoint(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors = {}
        ports = await async_get_ports()

        if user_input is not None:
            user_input[CONF_TYPE] = TYPE_ENDPOINT
            user_input[CONF_DEVICE_MODE] = DEVICE_MODE_RTU
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        baud_rates = [9600, 14400, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

        return self.async_show_form(
            step_id="add_rtu_endpoint",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=ENDPOINT_DATA_RTU[CONF_NAME]): cv.string,
                vol.Required(CONF_SERIAL_PORT, default=ENDPOINT_DATA_RTU[CONF_SERIAL_PORT]): selector.SelectSelector(selector.SelectSelectorConfig(options=ports, custom_value=True, mode=selector.SelectSelectorMode.DROPDOWN)),
                vol.Required(CONF_SERIAL_BAUD, default=ENDPOINT_DATA_RTU[CONF_SERIAL_BAUD]): vol.In(baud_rates),
            }),
            errors=errors
        )

    # ------------------------------------------------------------------
    # Device Steps
    # ------------------------------------------------------------------
    async def async_step_add_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors = {}

        # Get list of Endpoints
        endpoints = self._get_endpoints()
        if not endpoints:
             errors["base"] = "no_endpoints"
             # If no endpoints, we might want to tell the user to go back

        if user_input is not None:
            user_input[CONF_TYPE] = TYPE_DEVICE
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        DEVICE_MODELS = sorted(await get_available_drivers())

        return self.async_show_form(
            step_id="add_device",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=DEVICE_DATA_DEFAULT[CONF_NAME]): cv.string,
                vol.Required(CONF_ENDPOINT_ID): selector.SelectSelector(selector.SelectSelectorConfig(options=endpoints)),
                vol.Required(CONF_DEVICE_MODEL): selector.SelectSelector(selector.SelectSelectorConfig(options=DEVICE_MODELS)),
                vol.Required(CONF_SLAVE_ID, default=DEVICE_DATA_DEFAULT[CONF_SLAVE_ID]): int,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEVICE_DATA_DEFAULT[CONF_SCAN_INTERVAL]): int,
                vol.Optional(CONF_SCAN_INTERVAL_FAST, default=DEVICE_DATA_DEFAULT[CONF_SCAN_INTERVAL_FAST]): int,
            }),
            errors=errors
        )

    def _get_endpoints(self):
        """Return a list of available endpoints for selector."""
        entries = self.hass.config_entries.async_entries(DOMAIN)
        options = []
        for entry in entries:
            # We identify endpoints by the 'conf_type' field OR implicit check
            if entry.data.get(CONF_TYPE) == TYPE_ENDPOINT:
                options.append(selector.SelectOptionDict(value=entry.entry_id, label=entry.title))
        return options


class ModbusOptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        entry_type = self._config_entry.data.get(CONF_TYPE)

        # Detect legacy entry (missing CONF_TYPE)
        if not entry_type:
            # Check if it looks like a device (has model) or endpoint (unlikely in legacy)
            # Legacy code mixed them. Legacy entries were devices with embedded connection.
            # We treat legacy entries as "Devices needing Endpoint".
            entry_type = TYPE_DEVICE # Treat as device
            is_legacy = True
        else:
            is_legacy = False

        if entry_type == TYPE_ENDPOINT:
            return await self.async_step_endpoint_options(user_input)
        else:
            return await self.async_step_device_options(user_input, is_legacy)

    async def async_step_endpoint_options(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
             # Update entry
             new_data = {**self._config_entry.data, **user_input}
             self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)
             return self.async_create_entry(title="", data={})

        data = self._config_entry.data
        schema = {}
        # Simple schema based on mode
        if data.get(CONF_DEVICE_MODE) == DEVICE_MODE_TCPIP:
            schema = {
                vol.Required(CONF_IP, default=data.get(CONF_IP)): cv.string,
                vol.Required(CONF_PORT, default=data.get(CONF_PORT)): int,
            }
        else:
            ports = await async_get_ports()
            baud_rates = [9600, 14400, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
            schema = {
                vol.Required(CONF_SERIAL_PORT, default=data.get(CONF_SERIAL_PORT)): selector.SelectSelector(selector.SelectSelectorConfig(options=ports, custom_value=True, mode=selector.SelectSelectorMode.DROPDOWN)),
                vol.Required(CONF_SERIAL_BAUD, default=data.get(CONF_SERIAL_BAUD)): vol.In(baud_rates),
            }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema))

    async def async_step_device_options(self, user_input: dict[str, Any] | None = None, is_legacy=False):
        errors = {}

        if user_input is not None:
            # If migrating from legacy, we must set the TYPE
            new_data = {**self._config_entry.data, **user_input}
            if is_legacy:
                new_data[CONF_TYPE] = TYPE_DEVICE
                # We intentionally do NOT remove old connection keys to allow easier reversion if needed.
                # The presence of extra keys does not harm the new logic.
                # for key in [CONF_IP, CONF_PORT, CONF_SERIAL_PORT, CONF_SERIAL_BAUD, CONF_DEVICE_MODE]:
                #    new_data.pop(key, None)

            self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)
            return self.async_create_entry(title="", data={})

        data = self._config_entry.data
        endpoints = self._get_endpoints()

        current_endpoint = data.get(CONF_ENDPOINT_ID)
        if not current_endpoint and not endpoints:
             errors["base"] = "no_endpoints"

        # Schema for device options
        # Allow changing Endpoint, Slave ID, Scan Interval
        DEVICE_MODELS = sorted(await get_available_drivers())

        schema = {
             vol.Required(CONF_ENDPOINT_ID, default=current_endpoint): selector.SelectSelector(selector.SelectSelectorConfig(options=endpoints)),
             vol.Required(CONF_SLAVE_ID, default=data.get(CONF_SLAVE_ID)): int,
             vol.Optional(CONF_SCAN_INTERVAL, default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): int,
             vol.Optional(CONF_SCAN_INTERVAL_FAST, default=data.get(CONF_SCAN_INTERVAL_FAST, DEFAULT_SCAN_INTERVAL_FAST)): int,
             # Optionally allow changing model? Yes.
             vol.Required(CONF_DEVICE_MODEL, default=data.get(CONF_DEVICE_MODEL)): selector.SelectSelector(selector.SelectSelectorConfig(options=DEVICE_MODELS)),
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema), errors=errors)

    def _get_endpoints(self):
        """Return a list of available endpoints for selector."""
        entries = self.hass.config_entries.async_entries(DOMAIN)
        options = []
        for entry in entries:
            if entry.data.get(CONF_TYPE) == TYPE_ENDPOINT:
                options.append(selector.SelectOptionDict(value=entry.entry_id, label=entry.title))
        return options

# Helper
async def async_get_ports():
    try:
        return await asyncio.to_thread(glob.glob, '/dev/serial/by-id/*')
    except Exception as e:
        _LOGGER.error("Error fetching serial ports: %s", e)
        return []
