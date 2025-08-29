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
            
            if len(hex_data) < 24:  # Minimum packet length
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
            # Check for new packet format (10XXa3...)
            if hex_data.startswith("10") and hex_data[4:6] == "A3":
                # New format: 10 02 a3 00 01 00 32 0c 70 7b 7d 28 00 18 2e 9f
                # Position: 0  2  4  6  8  10 12 14 16 18 20 22 24 26 28 30
                device_num_hex = hex_data[8:10]  # Target device number
                
                if device_num_hex != self.device_num:
                    _LOGGER.debug("Device number mismatch: expected %s, got %s", self.device_num, device_num_hex)
                    return None
                
                # Parse packet data starting from position 12
                status_byte = hex_data[12:14]
                
                # Parse status byte (contains power and mode)
                # Assuming format similar to original but need to decode
                if status_byte in ["32", "3A", "38"]:  # Examples from log
                    is_on = True
                    # Extract mode from the status
                    mode_val = int(status_byte, 16) & 0x0F
                    hvac_mode = HVAC_MODE_MAP.get(f"{mode_val:02X}", "cool")
                else:
                    is_on = False
                    hvac_mode = "off"
                
                # Temperature data appears to be at positions 14-16
                temp_data = hex_data[14:16]
                current_temp = int(temp_data, 16) if temp_data.isdigit() or all(c in '0123456789ABCDEF' for c in temp_data) else 24
                
                # Set temperature might be at positions 16-18
                set_temp_data = hex_data[16:18]
                set_temp = int(set_temp_data, 16) if set_temp_data.isdigit() or all(c in '0123456789ABCDEF' for c in set_temp_data) else 24
                
                # Validate temperatures
                if not (0 <= current_temp <= 50):
                    current_temp = 24
                if not (16 <= set_temp <= 30):
                    set_temp = 24
                
                # Fan mode and other data
                fan_mode = "auto"  # Default for now
                error_code = "00"
                filter_alarm = False
                
                _LOGGER.debug("Parsed new format packet: device=%s, power=%s, mode=%s, current=%d, set=%d",
                            device_num_hex, is_on, hvac_mode, current_temp, set_temp)
                
            # Check for response packet format (8000B0...)
            elif hex_data.startswith("8000B0"):
                # Original format
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
                if not (16 <= set_temp <= 30):
                    set_temp = 24
                
                current_temp_hex = hex_data[16:18]
                current_temp = int(current_temp_hex, 16)
                if not (0 <= current_temp <= 50):
                    current_temp = 24
                
                # Parse fan mode
                fan_state = hex_data[18:20]
                fan_mode = FAN_MODE_MAP.get(fan_state, "auto")
                
                # Parse error and filter
                error_code = hex_data[20:22]
                filter_state = hex_data[22:24]
                filter_alarm = filter_state == "01"
                
            else:
                _LOGGER.warning("Unknown packet format: %s", hex_data[:6])
                return None
            
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
