"""Device representation for LG Air Conditioner."""
import logging
from typing import Optional, Dict, Any

from .const import (
    HVAC_MODE_MAP,
    FAN_MODE_MAP,
    POWER_ON,
    POWER_OFF,
)

_LOGGER = logging.getLogger(__name__)


class LGAirConditionerDevice:
    """Representation of an LG Air Conditioner device."""

    def __init__(self, device_num: str) -> None:
        """Initialize the device."""
        self.device_num = device_num
        self.is_on = False
        self.hvac_mode = "off"
        self.target_temperature = 24
        self.current_temperature = 24
        self.fan_mode = "auto"
        self.error_code = "00"
        self.filter_alarm = False
        self._raw_state = None
        self._last_parsed_state: Dict[str, Any] = {}

    def update_from_hex(self, hex_data: str) -> bool:
        """Update device state from hex data. Returns True if state changed."""
        try:
            # Clean the hex data
            hex_data = hex_data.strip().upper()
            
            if len(hex_data) < 32:
                _LOGGER.error("Invalid hex data length: %s (len=%d)", hex_data, len(hex_data))
                return False

            # Parse state
            parsed_state = self._parse_hex_data(hex_data)
            if not parsed_state:
                return False

            # Check if state changed
            if parsed_state == self._last_parsed_state:
                _LOGGER.debug("State unchanged for device %s", self.device_num)
                return False

            # Update device attributes
            self._raw_state = hex_data
            self.is_on = parsed_state["power"]
            self.hvac_mode = parsed_state["mode"]
            self.target_temperature = parsed_state["target_temp"]
            self.current_temperature = parsed_state["current_temp"]
            self.fan_mode = parsed_state["fan_mode"]
            self.error_code = parsed_state["error_code"]
            self.filter_alarm = parsed_state["filter_alarm"]
            
            # Store last parsed state
            self._last_parsed_state = parsed_state
            
            _LOGGER.info(
                "Device %s state updated - hex parsing state: %s",
                self.device_num,
                parsed_state
            )
            
            return True
            
        except Exception as err:
            _LOGGER.exception("Error parsing device state for device %s: %s", self.device_num, err)
            return False

    def _parse_hex_data(self, hex_data: str) -> Optional[Dict[str, Any]]:
        """Parse hex data and return state dictionary."""
        try:
            # Verify this is a state response (80 00 B0 pattern)
            if not hex_data.startswith("8000B0"):
                _LOGGER.warning("Not a state response packet: %s", hex_data[:6])
                return None
            
            # Extract device number from packet
            device_num_hex = hex_data[8:10]
            if device_num_hex != self.device_num:
                _LOGGER.warning("Device number mismatch: expected %s, got %s", self.device_num, device_num_hex)
                return None
            
            # Parse power state
            power_state = hex_data[10:12]
            is_on = power_state == POWER_ON
            
            # Parse HVAC mode
            mode_state = hex_data[12:14]
            hvac_mode = HVAC_MODE_MAP.get(mode_state, "off")
            
            # Parse temperatures
            set_temp_hex = hex_data[14:16]
            set_temp = int(set_temp_hex, 16)
            # Validate temperature range
            if not (16 <= set_temp <= 30):
                _LOGGER.warning("Invalid set temperature: %d", set_temp)
                set_temp = 24  # Default
            
            current_temp_hex = hex_data[16:18]
            current_temp = int(current_temp_hex, 16)
            # Validate temperature range
            if not (0 <= current_temp <= 50):
                _LOGGER.warning("Invalid current temperature: %d", current_temp)
                current_temp = 24  # Default
            
            # Parse fan mode
            fan_state = hex_data[18:20]
            fan_mode = FAN_MODE_MAP.get(fan_state, "auto")
            
            # Parse error and filter
            error_code = hex_data[20:22]
            filter_state = hex_data[22:24]
            filter_alarm = filter_state == "01"
            
            state = {
                "device_num": self.device_num,
                "power": is_on,
                "mode": hvac_mode,
                "target_temp": set_temp,
                "current_temp": current_temp,
                "fan_mode": fan_mode,
                "error_code": error_code,
                "filter_alarm": filter_alarm,
                "raw_hex": hex_data
            }
            
            _LOGGER.debug("Hex parsing state for device %s: %s", self.device_num, state)
            
            return state
            
        except Exception as err:
            _LOGGER.error("Error in _parse_hex_data: %s", err)
            return None

    def get_control_packet(self, power: bool, mode: str, temperature: int, fan: str) -> str:
        """Generate control packet for the device."""
        from .const import REVERSE_HVAC_MODE_MAP, REVERSE_FAN_MODE_MAP, CONTROL_PACKET_FORMAT
        
        power_hex = POWER_ON if power else POWER_OFF
        mode_hex = REVERSE_HVAC_MODE_MAP.get(mode, "00")
        temp_hex = f"{temperature:02X}"
        fan_hex = REVERSE_FAN_MODE_MAP.get(fan, "03")
        
        packet = CONTROL_PACKET_FORMAT.format(
            device_num=self.device_num,
            power=power_hex,
            mode=mode_hex,
            temp=temp_hex,
            fan=fan_hex,
        )
        
        return packet

    @property
    def is_available(self) -> bool:
        """Return True if device is available."""
        return self._raw_state is not None
