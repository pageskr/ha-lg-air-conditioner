"""MQTT client for LG Air Conditioner."""
import asyncio
import logging
import binascii
from typing import Callable, Optional
import paho.mqtt.client as mqtt

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class LGMQTTClient:
    """MQTT client for LG Air Conditioner."""

    def __init__(
        self,
        hass: HomeAssistant,
        broker: str,
        port: int,
        username: Optional[str],
        password: Optional[str],
        topic_state: str,
        topic_send: str,
        topic_recv: str,
        callback: Callable[[str, str], None],
    ) -> None:
        """Initialize the MQTT client."""
        self.hass = hass
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.topic_state = topic_state
        self.topic_send = topic_send
        self.topic_recv = topic_recv
        self.callback = callback
        self._client = None
        self._connected = False
        self._last_values = {}

    async def async_connect(self) -> None:
        """Connect to MQTT broker."""
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self._connected = True
                _LOGGER.info("Connected to MQTT broker")
                # Subscribe to receive topic
                client.subscribe(self.topic_recv)
                # Subscribe to state topics for all devices
                for i in range(1, 5):
                    topic = self.topic_state.format(device_num=f"{i:02d}")
                    client.subscribe(topic)
            else:
                _LOGGER.error("Failed to connect to MQTT broker, code %s", rc)

        def on_message(client, userdata, msg):
            try:
                if msg.topic == self.topic_recv:
                    # Handle raw binary data from ew11b/recv
                    hex_data = binascii.hexlify(msg.payload).decode()
                    if len(hex_data) >= 32:
                        if len(hex_data) > 32:
                            hex_data = hex_data[:32]
                        device_num = hex_data[8:10]
                        # Check if value changed
                        if self._last_values.get(device_num) != hex_data:
                            self._last_values[device_num] = hex_data
                            self.hass.add_job(self.callback, device_num, hex_data)
                elif msg.topic.startswith(self.topic_state.split("/")[0]):
                    # Handle state messages from lgac/state/{device_num}
                    device_num = msg.topic.split("/")[-1]
                    hex_data = msg.payload.decode()
                    if self._last_values.get(device_num) != hex_data:
                        self._last_values[device_num] = hex_data
                        self.hass.add_job(self.callback, device_num, hex_data)
            except Exception as err:
                _LOGGER.error("Error processing MQTT message: %s", err)

        def on_disconnect(client, userdata, rc):
            self._connected = False
            _LOGGER.warning("Disconnected from MQTT broker")

        self._client = mqtt.Client()
        if self.username and self.password:
            self._client.username_pw_set(self.username, self.password)
        
        self._client.on_connect = on_connect
        self._client.on_message = on_message
        self._client.on_disconnect = on_disconnect

        await self.hass.async_add_executor_job(
            self._client.connect, self.broker, self.port, 60
        )
        self._client.loop_start()

    async def async_disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            await self.hass.async_add_executor_job(self._client.disconnect)

    async def async_request_state(self, device_num: str) -> None:
        """Request state for a specific device."""
        if not self._connected:
            _LOGGER.warning("Not connected to MQTT broker")
            return
        
        # Send state request packet
        from .const import STATE_REQUEST_PACKET_FORMAT
        packet = STATE_REQUEST_PACKET_FORMAT.format(device_num=device_num)
        
        await self.hass.async_add_executor_job(
            self._client.publish, self.topic_send, packet
        )

    async def async_send_command(self, command: str) -> bool:
        """Send command via MQTT."""
        if not self._connected:
            _LOGGER.warning("Not connected to MQTT broker")
            return False
        
        try:
            await self.hass.async_add_executor_job(
                self._client.publish, self.topic_send, command
            )
            return True
        except Exception as err:
            _LOGGER.error("Error sending MQTT command: %s", err)
            return False
