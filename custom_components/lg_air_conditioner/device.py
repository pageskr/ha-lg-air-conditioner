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
        self.is_locked = False
        self.hvac_mode = "off"
        self.target_temperature = 24
        self.current_temperature = 24
        self.fan_mode = "auto"
        self.swing_mode = "fix"
        self.pipe1_temperature = 0
        self.pipe2_temperature = 0
        self.outdoor_temperature = 0
        self.error_code = "00"
        self.filter_alarm = False
        self._raw_state = None
        self._last_parsed_state: Dict[str, Any] = {}

    def update_from_hex(self, hex_data: str) -> bool:
        """Update device state from hex data. Returns True if state changed."""
        try:
            # Clean the hex data
            hex_data = hex_data.strip().upper()
            
            if len(hex_data) < 32:  # Minimum packet length
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
            self.is_locked = parsed_state["locked"]
            self.hvac_mode = parsed_state["mode"]
            self.target_temperature = parsed_state["target_temp"]
            self.current_temperature = parsed_state["current_temp"]
            self.fan_mode = parsed_state["fan_mode"]
            self.swing_mode = parsed_state["swing_mode"]
            self.pipe1_temperature = parsed_state["pipe1_temp"]
            self.pipe2_temperature = parsed_state["pipe2_temp"]
            self.outdoor_temperature = parsed_state["outdoor_temp"]
            self.error_code = parsed_state.get("error_code", "00")
            self.filter_alarm = parsed_state.get("filter_alarm", False)
            
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
                # Format: 1002a300{room}00{status}{opermode}{set_temp}{current_temp}{pipe1}{pipe2}{outdoor}...{checksum}
                device_num_hex = hex_data[8:10]
                
                if device_num_hex != self.device_num:
                    _LOGGER.debug("Device number mismatch: expected %s, got %s", self.device_num, device_num_hex)
                    return None
                
                # Verify checksum
                if not self._verify_checksum(hex_data):
                    _LOGGER.warning("Checksum verification failed for device %s", self.device_num)
                    return None
                
                # Parse status byte (position 12-13)
                status_byte = int(hex_data[12:14], 16)
                # Status values: 2=off, 3=off+locked, 6=on+locked, 7=on+unlocked
                is_on = status_byte in [6, 7]
                is_locked = status_byte in [3, 6]
                
                # Parse opermode byte (position 14-15)
                opermode_byte = int(hex_data[14:16], 16)
                # Extract HVAC mode (bits 0-2)
                hvac_mode_val = opermode_byte & 0x07
                hvac_mode_map = {0: "cool", 1: "dry", 2: "fan_only", 3: "auto", 4: "heat"}
                hvac_mode = hvac_mode_map.get(hvac_mode_val, "off")
                
                # Extract fan mode (bits 4-6)
                fan_mode_val = opermode_byte & 0x70
                fan_mode_map = {16: "low", 32: "medium", 48: "high", 64: "auto", 80: "silent", 96: "power"}
                fan_mode = fan_mode_map.get(fan_mode_val, "auto")
                
                # Extract swing mode (bit 3)
                swing_mode = "auto" if (opermode_byte & 0x08) else "fix"
                
                # Parse temperatures
                set_temp = int(hex_data[16:18], 16) + 15
                # Validate temperature range
                if not (16 <= set_temp <= 30):
                    set_temp = 24
                
                # Current temperature calculation (similar to template sensor)
                current_temp_raw = int(hex_data[18:20], 16)
                if current_temp_raw > 40:
                    current_temp = round(64 - (current_temp_raw / 3), 1)
                else:
                    current_temp = self.current_temperature  # Keep previous value
                
                # Pipe temperatures
                pipe1_raw = int(hex_data[20:22], 16)
                pipe1_temp = round(64 - (pipe1_raw / 3), 1) if pipe1_raw > 40 else self.pipe1_temperature
                
                pipe2_raw = int(hex_data[22:24], 16)
                pipe2_temp = round(64 - (pipe2_raw / 3), 1) if pipe2_raw > 40 else self.pipe2_temperature
                
                # Outdoor temperature
                outdoor_raw = int(hex_data[24:26], 16)
                outdoor_temp = round(64 - (outdoor_raw / 3), 1) if outdoor_raw > 40 else 0
                
                _LOGGER.debug("Parsed new format packet: device=%s, power=%s, locked=%s, mode=%s, current=%.1f, set=%d",
                            device_num_hex, is_on, is_locked, hvac_mode, current_temp, set_temp)
                
            # Check for response packet format (8000B0...)
            elif hex_data.startswith("8000B0"):
                # This is likely a response to status request - parse differently if needed
                device_num_hex = hex_data[8:10]
                if device_num_hex != self.device_num:
                    _LOGGER.warning("Device number mismatch: expected %s, got %s", self.device_num, device_num_hex)
                    return None
                
                # For now, skip these packets as they might have different format
                _LOGGER.debug("Skipping response packet format for device %s", device_num_hex)
                return None
                
            else:
                _LOGGER.warning("Unknown packet format: %s", hex_data[:6])
                return None
            
            state = {
                "device_num": self.device_num,
                "power": is_on,
                "locked": is_locked,
                "mode": hvac_mode,
                "target_temp": set_temp,
                "current_temp": current_temp,
                "fan_mode": fan_mode,
                "swing_mode": swing_mode,
                "pipe1_temp": pipe1_temp,
                "pipe2_temp": pipe2_temp,
                "outdoor_temp": outdoor_temp,
                "error_code": "00",
                "filter_alarm": False,
                "raw_hex": hex_data
            }
            
            _LOGGER.debug("Hex parsing state for device %s: %s", self.device_num, state)
            
            return state
            
        except Exception as err:
            _LOGGER.error("Error in _parse_hex_data: %s", err)
            return None

    def _verify_checksum(self, hex_data: str) -> bool:
        """Verify packet checksum."""
        try:
            if len(hex_data) < 32:
                return False
                
            # Calculate checksum (sum of all bytes except checksum itself)
            packet_sum = 0
            for i in range(0, 30, 2):  # Up to position 29 (exclude checksum at 30-31)
                packet_sum += int(hex_data[i:i+2], 16)
            
            # Apply checksum algorithm from template
            checksum = packet_sum & 0xFF
            csum_odd = checksum & 0xAA  # 170 = 0xAA
            csum_even = 85 - (checksum & 0x55)  # 85 = 0x55
            calculated_checksum = csum_odd + csum_even
            
            # Compare with packet checksum
            packet_checksum = int(hex_data[30:32], 16)
            
            return calculated_checksum == packet_checksum
            
        except Exception as err:
            _LOGGER.error("Error verifying checksum: %s", err)
            return False

    def get_control_packet(self, power: bool, mode: str, temperature: int, fan: str) -> str:
        """Generate control packet for the device."""
        # Based on template sensor logic for control packets
        # Format: 8000A3{room}{status}{opermode}{temperature}{checksum}
        
        # Determine status byte
        if power:
            status = 0x07 if not self.is_locked else 0x06
        else:
            status = 0x02 if not self.is_locked else 0x03
        
        # Build opermode byte
        mode_map = {"cool": 0, "dry": 1, "fan_only": 2, "auto": 3, "heat": 4}
        hvac_val = mode_map.get(mode, 0)
        
        fan_map = {"low": 16, "medium": 32, "high": 48, "auto": 64, "silent": 80, "power": 96}
        fan_val = fan_map.get(fan, 64)
        
        swing_val = 8 if self.swing_mode == "auto" else 0
        
        opermode = hvac_val + fan_val + swing_val
        
        # Temperature adjustment
        temp_val = temperature - 15
        
        # Build packet without checksum
        packet = f"8000A3{self.device_num}{status:02X}{opermode:02X}{temp_val:02X}"
        
        # Calculate checksum
        packet_sum = 0x80 + 0x00 + 0xA3 + int(self.device_num, 16) + status + opermode + temp_val
        checksum = packet_sum & 0xFF
        csum_odd = checksum & 0xAA
        csum_even = 85 - (checksum & 0x55)
        checksum_final = csum_odd + csum_even
        
        packet += f"{checksum_final:02X}"
        
        return packet

    @property
    def is_available(self) -> bool:
        """Return True if device is available."""
        return self._raw_state is not None
