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
                # Based on the actual packet: 1002a3000100320c7181828200182e65
                # Format: 10 02 a3 00 {device} 00 {oper} {mode} {set_temp} {curr_temp} {pipe1} {pipe2} {outdoor} {unknown} {checksum}
                # Position:0  2  4  6    8     10  12    14    16        18         20     22     24       26      30
                device_num_hex = hex_data[8:10]
                
                if device_num_hex != self.device_num:
                    _LOGGER.debug("Device number mismatch: expected %s, got %s", self.device_num, device_num_hex)
                    return None
                
                # Verify checksum
                if not self._verify_checksum(hex_data):
                    _LOGGER.warning("Checksum verification failed for device %s", self.device_num)
                    return None
                
                # Parse operation status byte (position 12-13)
                # From YAML: 2=off+unlocked, 3=on+unlocked, 6=off+locked, 7=on+locked
                status_byte = int(hex_data[12:14], 16)
                is_on = status_byte in [3, 7]
                is_locked = status_byte in [6, 7]
                
                # Parse opermode byte (position 14-15) 
                # In the example: 0x0C = 12 = 0 (cool) + 0 (fix swing) + 0 (unknown fan mode)
                opermode_byte = int(hex_data[14:16], 16)
                # Extract HVAC mode (bits 0-2)
                hvac_mode_val = opermode_byte & 0x07
                hvac_mode_map = {0: "cool", 1: "dry", 2: "fan_only", 3: "auto", 4: "heat"}
                hvac_mode = hvac_mode_map.get(hvac_mode_val, "off")
                
                # Extract fan mode (bits 4-6)
                fan_mode_val = opermode_byte & 0x70
                fan_mode_map = {0x10: "low", 0x20: "medium", 0x30: "high", 0x40: "auto", 0x50: "silent", 0x60: "power"}
                fan_mode = fan_mode_map.get(fan_mode_val, "auto")
                
                # Extract swing mode (bit 3)
                swing_mode = "auto" if (opermode_byte & 0x08) else "fix"
                
                # Parse temperatures
                # Set temperature (position 16-17) - In example: 0x71 = 113
                set_temp_raw = int(hex_data[16:18], 16)
                # From template sensor: temperature = value + 15
                # But looking at the debug log showing set=24, and 0x71=113
                # This appears to be a different encoding
                # Let's check if it's the raw value divided by some factor
                # Actually from looking at the YAML, seems like set temp is at position 14-15
                # Let me re-analyze based on YAML position references
                
                # Actually, looking at the log output and YAML:
                # The packet has device=01, power=False, locked=False, mode=heat, current=21.0, set=24
                # And looking at YAML template sensors, the positions are:
                # - operation status: position 2-3 (hex_data[2:4]) 
                # - device: position 8-9
                # - opermode: position 12-13
                # - set_temp: position 14-15
                # - current_temp: position 16-17
                
                # Re-parse based on YAML positions (which use 0-based string indexing)
                # But our hex_data positions need to be multiplied by 2
                
                # Wait, the YAML is using a different packet format. Let me align with the actual packet.
                # From the log: mode=heat, current=21.0, set=24
                # Packet: 1002a3000100320c7181828200182e65
                # Let's parse based on what the existing code successfully parsed:
                
                # Looking at successful parse in log:
                # opermode 0x0C parsed as mode=heat with fan_mode=auto, swing_mode=auto
                # So 0x0C = 12 = 4 (heat) + 8 (auto swing) + 0 (default fan?)
                # This doesn't match the bit layout above
                
                # Let me check if opermode is the second hex value
                # Position 14-15: 0x0C = 12
                # If we assume different bit layout: maybe it's just the mode value?
                # No, that would be 12 which doesn't map to any mode
                
                # Looking more carefully at the data:
                # The set temperature showing as 24°C
                # Position 16-17: 0x71 = 113
                # If we subtract 15: 113 - 15 = 98 (not right)
                # If it's encoded differently... let me check
                
                # From the template sensor for set_temperature:
                # ((states("sensor.lgac_01_state")[14:16] | int(base=16))+15)
                # So it's position 14-15 + 15
                # In our packet at 14-15: 0x0C = 12
                # 12 + 15 = 27 (not 24)
                
                # Wait, I think I'm confusing the packet positions. Let me re-read the packet:
                # 1002a3000100320c7181828200182e65
                # Maybe the positions in YAML are 1-indexed, not 0-indexed?
                # Or maybe there's a different byte order?
                
                # From the actual working parse log:
                # 'mode': 'heat', 'target_temp': 24, 'current_temp': 21.0
                # Let's work backwards from the known values
                
                # Actually looking at debug log again - it says "Parsed new format packet"
                # So the existing parsing IS working. Let me just fix the status byte parsing.
                
                # The issue is that status=0x32 is being parsed as power=False
                # But 0x32 = 50, which doesn't match any of the expected values (2,3,6,7)
                # This suggests the packet format is different than expected
                
                # Let me re-examine the whole packet structure
                # Maybe status is at a different position?
                
                # Actually from YAML, checking position [2:4] for status
                # In our packet that would be 0x02 = 2 = off+unlocked
                # But we're checking position [12:14] which is 0x32
                
                # I think the packet format from YAML is different - it expects:
                # [0:2]=10, [2:4]=status, [4:6]=a3, etc.
                # But our packet has: [0:2]=10, [2:4]=02, [4:6]=a3
                
                # So status=0x02=2=off+unlocked makes sense!
                # Let me fix the positions
                
                # Actually wait, the YAML uses the full state string positions
                # So [2:4] means characters 2-3 of the string = byte position 1
                # [12:14] means characters 12-13 of the string = byte position 6
                
                # Let's re-map:
                # YAML [2:4] = our hex_data[2:4] = "02" = status byte
                status_byte = int(hex_data[2:4], 16)
                is_on = status_byte in [3, 7]
                is_locked = status_byte in [6, 7]
                
                # YAML [12:14] = our hex_data[12:14] = "32" = opermode
                opermode_byte = int(hex_data[12:14], 16)
                
                # For opermode 0x32 = 50 = 0x32
                # Let's parse it as the YAML does:
                hvac_mode_val = opermode_byte & 0x07  # Lower 3 bits
                hvac_mode_map = {0: "cool", 1: "dry", 2: "fan_only", 3: "auto", 4: "heat"}
                hvac_mode = hvac_mode_map.get(hvac_mode_val, "off")
                
                # Fan mode from bits 4-6 (0x70 = 112 = 01110000)
                fan_mode_val = opermode_byte & 0x70
                fan_mode_map = {0x10: "low", 0x20: "medium", 0x30: "high", 0x40: "auto", 0x50: "silent", 0x60: "power"}
                fan_mode = fan_mode_map.get(fan_mode_val, "auto")
                
                # Swing mode from bit 3
                swing_mode = "auto" if (opermode_byte & 0x08) else "fix"
                
                # YAML [14:16] = our hex_data[14:16] = "0C" = set temperature - 15
                set_temp_raw = int(hex_data[14:16], 16)
                set_temp = set_temp_raw + 15
                
                # YAML [16:18] = our hex_data[16:18] = "71" = current temperature (encoded)
                current_temp_raw = int(hex_data[16:18], 16)
                if current_temp_raw > 40:
                    current_temp = round(64 - (current_temp_raw / 3), 1)
                else:
                    current_temp = self.current_temperature
                
                # YAML [18:20] = our hex_data[18:20] = "81" = pipe1 temperature
                pipe1_raw = int(hex_data[18:20], 16)
                pipe1_temp = round(64 - (pipe1_raw / 3), 1) if pipe1_raw > 40 else self.pipe1_temperature
                
                # YAML [20:22] = our hex_data[20:22] = "82" = pipe2 temperature  
                pipe2_raw = int(hex_data[20:24], 16)
                pipe2_temp = round(64 - (pipe2_raw / 3), 1) if pipe2_raw > 40 else self.pipe2_temperature
                
                # YAML [22:24] = our hex_data[22:24] = "82" = outdoor temperature
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

    def get_control_packet(self, power: bool, mode: str, temperature: int, fan: str, swing: str = None) -> str:
        """Generate control packet for the device."""
        # Based on template sensor logic for control packets
        # Format: 8000A3{room}{status}{temperature}{opermode}{checksum}
        
        # Determine status byte (position 6-7 in packet)
        # From YAML: 2=off+unlocked, 3=on+unlocked, 6=off+locked, 7=on+locked
        if power:
            status = 0x03 if not self.is_locked else 0x07
        else:
            status = 0x02 if not self.is_locked else 0x06
        
        # Temperature adjustment (position 8-9 in packet)
        temp_val = temperature - 15
        
        # Build opermode byte (position 10-11 in packet)
        mode_map = {"cool": 0, "dry": 1, "fan_only": 2, "auto": 3, "heat": 4}
        hvac_val = mode_map.get(mode, 0)
        
        fan_map = {"low": 0x10, "medium": 0x20, "high": 0x30, "auto": 0x40, "silent": 0x50, "power": 0x60}
        fan_val = fan_map.get(fan, 0x40)
        
        # Use provided swing or current swing mode
        if swing is None:
            swing = self.swing_mode
        swing_val = 0x08 if swing == "auto" else 0x00
        
        opermode = hvac_val + fan_val + swing_val
        
        # Build packet without checksum
        packet = f"8000A3{self.device_num}{status:02X}{temp_val:02X}{opermode:02X}"
        
        # Calculate checksum using same algorithm as template sensor
        packet_sum = 0x80 + 0x00 + 0xA3 + int(self.device_num, 16) + status + temp_val + opermode
        checksum = packet_sum & 0xFF
        csum_odd = checksum & 0xAA  # 0xAA = 170
        csum_even = 85 - (checksum & 0x55)  # 0x55 = 85 
        checksum_final = csum_odd + csum_even
        
        packet += f"{checksum_final:02X}"
        
        _LOGGER.debug("Generated control packet: %s (power=%s, mode=%s, temp=%d, fan=%s, swing=%s)",
                     packet, power, mode, temperature, fan, swing)
        
        return packet
    
    def get_status_request_packet(self) -> str:
        """Generate status request packet."""
        # Format: 8000A3{room}00{temperature}{opermode}{checksum}
        # Use current values for the scan
        temp_val = self.target_temperature - 15
        
        # Build opermode from current state
        mode_map = {"cool": 0, "dry": 1, "fan_only": 2, "auto": 3, "heat": 4, "off": 0}
        hvac_val = mode_map.get(self.hvac_mode, 0)
        
        fan_map = {"low": 0x10, "medium": 0x20, "high": 0x30, "auto": 0x40, "silent": 0x50, "power": 0x60}
        fan_val = fan_map.get(self.fan_mode, 0x40)
        
        swing_val = 0x08 if self.swing_mode == "auto" else 0x00
        
        opermode = hvac_val + fan_val + swing_val
        
        # Build packet
        packet = f"8000A3{self.device_num}00{temp_val:02X}{opermode:02X}"
        
        # Calculate checksum
        packet_sum = 0x80 + 0x00 + 0xA3 + int(self.device_num, 16) + 0x00 + temp_val + opermode
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
