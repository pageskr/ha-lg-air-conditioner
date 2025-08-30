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
                _LOGGER.info("Subscribed to topic: %s", self.topic_recv)
                # Subscribe to state topics for all devices
                for i in range(1, 5):
                    topic = self.topic_state.format(device_num=f"{i:02d}")
                    client.subscribe(topic)
                    _LOGGER.info("Subscribed to state topic: %s", topic)
            else:
                _LOGGER.error("Failed to connect to MQTT broker, code %s", rc)

        def on_message(client, userdata, msg):
            try:
                _LOGGER.debug("MQTT message received on topic %s: %s", msg.topic, msg.payload[:20])
                
                # Always process messages on ew11b/recv topic
                if msg.topic == self.topic_recv:
                    # Handle raw binary data from ew11b/recv
                    hex_data = binascii.hexlify(msg.payload).decode()
                    _LOGGER.debug("Received hex data on %s: %s", self.topic_recv, hex_data)
                    
                    # Process new format packets (10XXa3...)
                    if len(hex_data) >= 24 and hex_data[:2].upper() == "10" and hex_data[4:6].upper() == "A3":
                        # Extract target device number from position 8-10
                        device_num = hex_data[8:10].upper()
                        _LOGGER.debug("New format state packet detected for device %s", device_num)
                        
                        # Process the state update
                        self.hass.add_job(self.callback, device_num, hex_data.upper())
                        _LOGGER.info("Processing state update for device %s from %s", device_num, self.topic_recv)
                        
                    # Process response format packets (8000B0...)
                    elif len(hex_data) >= 32 and hex_data.upper().startswith("8000B0"):
                        if len(hex_data) > 32:
                            hex_data = hex_data[:32]
                        device_num = hex_data[8:10].upper()
                        _LOGGER.debug("Response format state packet detected for device %s", device_num)
                        
                        # Process the state update
                        self.hass.add_job(self.callback, device_num, hex_data.upper())
                        _LOGGER.info("Processing state update for device %s from %s", device_num, self.topic_recv)
                    else:
                        if len(hex_data) >= 6:
                            _LOGGER.debug("Non-state packet received: %s (first 6 chars: %s)", hex_data[:32], hex_data[:6])
                        else:
                            _LOGGER.warning("Received data too short: %d bytes", len(hex_data))
                        
                elif msg.topic.startswith(self.topic_state.replace("{device_num}", "")):
                    # Handle state messages from lgac/state/{device_num}
                    device_num = msg.topic.split("/")[-1]
                    hex_data = msg.payload.decode('utf-8').strip().upper()
                    _LOGGER.debug("State message for device %s on topic %s: %s", device_num, msg.topic, hex_data)
                    
                    # Process both packet formats
                    if (len(hex_data) >= 24 and hex_data[:2] == "10" and hex_data[4:6] == "A3") or \
                       (len(hex_data) >= 32 and hex_data.startswith("8000B0")):
                        # Process the state update
                        self.hass.add_job(self.callback, device_num, hex_data)
                        _LOGGER.info("Processing state update for device %s from state topic", device_num)
                    else:
                        _LOGGER.warning("Invalid state message format on %s", msg.topic)
                        
            except Exception as err:
                _LOGGER.exception("Error processing MQTT message: %s", err)

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
        
        # Generate state request packet using device method
        from .device import LGAirConditionerDevice
        device = LGAirConditionerDevice(device_num)
        packet = device.get_status_request_packet()
        
        _LOGGER.info("Requesting state for device %s with packet: %s", device_num, packet)
        
        # Publish as hex string (lgac_forward.py expects hex string)
        result = await self.hass.async_add_executor_job(
            self._client.publish, self.topic_send, packet
        )
        
        if result.rc == 0:
            _LOGGER.debug("State request sent successfully for device %s", device_num)
        else:
            _LOGGER.error("Failed to send state request for device %s, rc=%s", device_num, result.rc)

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
