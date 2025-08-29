"""Config flow for LG Air Conditioner integration."""
import logging
from typing import Any, Dict, Optional
import voluptuous as vol
import socket
import paho.mqtt.client as mqtt

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    CONF_CONNECTION_TYPE,
    CONF_SOCKET_HOST,
    CONF_SOCKET_PORT,
    CONF_MQTT_BROKER,
    CONF_MQTT_PORT,
    CONF_MQTT_USERNAME,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_TOPIC_STATE,
    CONF_MQTT_TOPIC_SEND,
    CONF_MQTT_TOPIC_RECV,
    CONF_SCAN_INTERVAL,
    CONNECTION_TYPE_SOCKET,
    CONNECTION_TYPE_MQTT,
    DEFAULT_SOCKET_PORT,
    DEFAULT_MQTT_PORT,
    DEFAULT_MQTT_TOPIC_STATE,
    DEFAULT_MQTT_TOPIC_SEND,
    DEFAULT_MQTT_TOPIC_RECV,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

CONNECTION_TYPES = [CONNECTION_TYPE_SOCKET, CONNECTION_TYPE_MQTT]


class LGAirConditionerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LG Air Conditioner."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._data = {}
        self._errors = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return LGAirConditionerOptionsFlow(config_entry)

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step."""
        if user_input is None:
            return await self._show_config_form()

        self._data[CONF_NAME] = user_input[CONF_NAME]
        self._data[CONF_CONNECTION_TYPE] = user_input[CONF_CONNECTION_TYPE]

        if user_input[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_SOCKET:
            return await self.async_step_socket()
        else:
            return await self.async_step_mqtt()

    async def async_step_socket(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the socket configuration step."""
        errors = {}
        
        if user_input is not None:
            # Test socket connection
            valid = await self.hass.async_add_executor_job(
                self._test_socket_connection,
                user_input[CONF_SOCKET_HOST],
                user_input[CONF_SOCKET_PORT],
            )
            
            if valid:
                self._data.update(user_input)
                return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
            else:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SOCKET_HOST): str,
                vol.Required(CONF_SOCKET_PORT, default=DEFAULT_SOCKET_PORT): int,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }
        )

        return self.async_show_form(
            step_id="socket", data_schema=data_schema, errors=errors
        )

    async def async_step_mqtt(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the MQTT configuration step."""
        errors = {}
        
        if user_input is not None:
            # Test MQTT connection
            valid = await self.hass.async_add_executor_job(
                self._test_mqtt_connection,
                user_input[CONF_MQTT_BROKER],
                user_input[CONF_MQTT_PORT],
                user_input.get(CONF_MQTT_USERNAME),
                user_input.get(CONF_MQTT_PASSWORD),
            )
            
            if valid:
                self._data.update(user_input)
                return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
            else:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_MQTT_BROKER): str,
                vol.Required(CONF_MQTT_PORT, default=DEFAULT_MQTT_PORT): int,
                vol.Optional(CONF_MQTT_USERNAME): str,
                vol.Optional(CONF_MQTT_PASSWORD): str,
                vol.Optional(CONF_MQTT_TOPIC_STATE, default=DEFAULT_MQTT_TOPIC_STATE): str,
                vol.Optional(CONF_MQTT_TOPIC_SEND, default=DEFAULT_MQTT_TOPIC_SEND): str,
                vol.Optional(CONF_MQTT_TOPIC_RECV, default=DEFAULT_MQTT_TOPIC_RECV): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }
        )

        return self.async_show_form(
            step_id="mqtt", data_schema=data_schema, errors=errors
        )

    async def _show_config_form(self):
        """Show the configuration form to select connection type."""
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="LG Air Conditioner"): str,
                vol.Required(CONF_CONNECTION_TYPE): vol.In(CONNECTION_TYPES),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=self._errors,
        )

    def _test_socket_connection(self, host: str, port: int) -> bool:
        """Test socket connection."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _test_mqtt_connection(self, broker: str, port: int, username: str, password: str) -> bool:
        """Test MQTT connection."""
        try:
            client = mqtt.Client()
            if username and password:
                client.username_pw_set(username, password)
            
            connected = False
            error_msg = None
            
            def on_connect(client, userdata, flags, rc):
                nonlocal connected, error_msg
                if rc == 0:
                    connected = True
                else:
                    error_msg = f"Connection failed with code {rc}"
                    _LOGGER.error("MQTT connection failed: %s", error_msg)
            
            client.on_connect = on_connect
            client.connect(broker, port, 60)
            client.loop_start()
            
            import time
            for _ in range(10):  # Wait up to 5 seconds
                if connected:
                    break
                time.sleep(0.5)
            
            client.loop_stop()
            client.disconnect()
            
            if not connected and error_msg:
                _LOGGER.error("MQTT test connection failed: %s", error_msg)
            
            return connected
        except Exception as e:
            _LOGGER.error("MQTT connection test error: %s", e)
            return False


class LGAirConditionerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for LG Air Conditioner."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        if self.config_entry.data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_SOCKET:
            return await self.async_step_socket()
        else:
            return await self.async_step_mqtt()

    async def async_step_socket(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle socket options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SOCKET_HOST,
                    default=self.config_entry.options.get(
                        CONF_SOCKET_HOST, self.config_entry.data[CONF_SOCKET_HOST]
                    ),
                ): str,
                vol.Required(
                    CONF_SOCKET_PORT,
                    default=self.config_entry.options.get(
                        CONF_SOCKET_PORT, self.config_entry.data[CONF_SOCKET_PORT]
                    ),
                ): int,
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, self.config_entry.data[CONF_SCAN_INTERVAL]
                    ),
                ): int,
            }
        )

        return self.async_show_form(step_id="socket", data_schema=data_schema)

    async def async_step_mqtt(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle MQTT options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_MQTT_BROKER,
                    default=self.config_entry.options.get(
                        CONF_MQTT_BROKER, self.config_entry.data[CONF_MQTT_BROKER]
                    ),
                ): str,
                vol.Required(
                    CONF_MQTT_PORT,
                    default=self.config_entry.options.get(
                        CONF_MQTT_PORT, self.config_entry.data[CONF_MQTT_PORT]
                    ),
                ): int,
                vol.Optional(
                    CONF_MQTT_USERNAME,
                    default=self.config_entry.options.get(
                        CONF_MQTT_USERNAME, self.config_entry.data.get(CONF_MQTT_USERNAME, "")
                    ),
                ): str,
                vol.Optional(
                    CONF_MQTT_PASSWORD,
                    default=self.config_entry.options.get(
                        CONF_MQTT_PASSWORD, self.config_entry.data.get(CONF_MQTT_PASSWORD, "")
                    ),
                ): str,
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, self.config_entry.data[CONF_SCAN_INTERVAL]
                    ),
                ): int,
            }
        )

        return self.async_show_form(step_id="mqtt", data_schema=data_schema)
