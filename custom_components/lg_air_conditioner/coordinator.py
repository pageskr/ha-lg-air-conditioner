"""DataUpdateCoordinator for LG Air Conditioner."""
import asyncio
import logging
import binascii
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

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
    DEFAULT_SCAN_INTERVAL,
    DEVICE_COUNT,
    STATE_REQUEST_PACKET_FORMAT,
)
from .socket_client import LGSocketClient
from .mqtt_client import LGMQTTClient
from .device import LGAirConditionerDevice

_LOGGER = logging.getLogger(__name__)


class LGAirConditionerCoordinator(DataUpdateCoordinator):
    """Class to manage fetching LG Air Conditioner data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
        self.hass = hass
        self.devices: Dict[str, LGAirConditionerDevice] = {}
        self._client = None
        self._last_states: Dict[str, str] = {}
        
        scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

        # Initialize devices
        for i in range(1, DEVICE_COUNT + 1):
            device_num = f"{i:02d}"
            self.devices[device_num] = LGAirConditionerDevice(device_num)

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh and initialize connection."""
        await self._async_initialize_connection()
        
        # For MQTT mode, request initial state after connection
        if self.entry.data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_MQTT:
            await asyncio.sleep(1)  # Give MQTT time to connect
            for device_num in self.devices:
                await self._client.async_request_state(device_num)
                await asyncio.sleep(0.5)  # Small delay between requests
        
        await super().async_config_entry_first_refresh()

    async def _async_initialize_connection(self) -> None:
        """Initialize the connection based on configuration."""
        if self.entry.data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_SOCKET:
            self._client = LGSocketClient(
                self.entry.data[CONF_SOCKET_HOST],
                self.entry.data[CONF_SOCKET_PORT],
            )
        else:
            self._client = LGMQTTClient(
                self.hass,
                self.entry.data[CONF_MQTT_BROKER],
                self.entry.data[CONF_MQTT_PORT],
                self.entry.data.get(CONF_MQTT_USERNAME),
                self.entry.data.get(CONF_MQTT_PASSWORD),
                self.entry.data[CONF_MQTT_TOPIC_STATE],
                self.entry.data[CONF_MQTT_TOPIC_SEND],
                self.entry.data[CONF_MQTT_TOPIC_RECV],
                self._on_state_update,
            )
            await self._client.async_connect()

    def _on_state_update(self, device_num: str, state_data: str) -> None:
        """Handle state updates from MQTT."""
        if device_num in self.devices:
            self.devices[device_num].update_from_hex(state_data)
            self._last_states[device_num] = state_data
            # Schedule the update in the event loop
            self.hass.loop.call_soon_threadsafe(
                lambda: self.async_set_updated_data(self.devices)
            )

    async def _async_update_data(self) -> Dict[str, LGAirConditionerDevice]:
        """Fetch data from API endpoint."""
        try:
            # Request state for all devices
            for device_num in self.devices:
                if self.entry.data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_SOCKET:
                    # Socket mode: send request and get response
                    state_data = await self._client.async_send_command(
                        STATE_REQUEST_PACKET_FORMAT.format(device_num=device_num)
                    )
                    if state_data:
                        self.devices[device_num].update_from_hex(state_data)
                        self._last_states[device_num] = state_data
                else:
                    # MQTT mode: send state request
                    await self._client.async_request_state(device_num)
            
            return self.devices
            
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def async_send_command(self, device_num: str, command: str) -> bool:
        """Send command to device."""
        try:
            if self.entry.data[CONF_CONNECTION_TYPE] == CONNECTION_TYPE_SOCKET:
                result = await self._client.async_send_command(command)
                return result is not None
            else:
                return await self._client.async_send_command(command)
        except Exception as err:
            _LOGGER.error("Error sending command: %s", err)
            return False

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self._client and hasattr(self._client, "async_disconnect"):
            await self._client.async_disconnect()


class LGAirConditionerEntity(CoordinatorEntity):
    """Base entity for LG Air Conditioner."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
        entity_type: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.device_num = device_num
        self.entity_type = entity_type
        self._attr_unique_id = f"{DOMAIN}_{device_num}_{entity_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_num)},
            "name": f"LG Air Conditioner {device_num}",
            "manufacturer": "LG Electronics",
            "model": "Air Conditioner",
        }

    @property
    def device(self) -> LGAirConditionerDevice:
        """Return the device."""
        return self.coordinator.devices[self.device_num]
