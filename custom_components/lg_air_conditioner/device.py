"""Device representation for LG Air Conditioner."""
import logging
from typing import Optional

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

    def update_from_hex(self, hex_data: str) -> None:
        """Update device state from hex data."""
        try:
            # Clean the hex data
            hex_data = hex_data.strip().upper()
            
            if len(hex_data) < 32:
                _LOGGER.error("Invalid hex data length: %s (len=%d)", hex_data, len(hex_data))
                return

            self._raw_state = hex_data
            
            # Parse the hex data based on the protocol
            # Response format: 80 00 B0 XX ...
            # Where XX at position 8-9 is device number
            # Positions are in hex string (2 chars per byte):
            # 0-1: 80 (header)
            # 2-3: 00 
            # 4-5: B0 (response type)
            # 6-7: message length or type
            # 8-9: Device number
            # 10-11: Power state
            # 12-13: HVAC mode
            # 14-15: Set temperature
            # 16-17: Current temperature
            # 18-19: Fan mode
            # 20-21: Error code
            # 22-23: Filter alarm
            
            # Verify this is a state response
            if not hex_data.startswith("8000B0"):
                _LOGGER.warning("Not a state response packet: %s", hex_data[:6])
                return
            
            power_state = hex_data[10:12]
            self.is_on = power_state == POWER_ON
            
            mode_state = hex_data[12:14]
            self.hvac_mode = HVAC_MODE_MAP.get(mode_state, "off")
            
            # Temperature conversion (hex to decimal)
            try:
                set_temp_hex = hex_data[14:16]
                set_temp = int(set_temp_hex, 16)
                # Validate temperature range
                if 16 <= set_temp <= 30:
                    self.target_temperature = set_temp
                else:
                    _LOGGER.warning("Invalid set temperature: %d", set_temp)
                
                current_temp_hex = hex_data[16:18]
                current_temp = int(current_temp_hex, 16)
                # Validate temperature range
                if 0 <= current_temp <= 50:
                    self.current_temperature = current_temp
                else:
                    _LOGGER.warning("Invalid current temperature: %d", current_temp)
            except ValueError as e:
                _LOGGER.error("Error parsing temperature values: %s", e)
            
            fan_state = hex_data[18:20]
            self.fan_mode = FAN_MODE_MAP.get(fan_state, "auto")
            
            self.error_code = hex_data[20:22]
            filter_state = hex_data[22:24]
            self.filter_alarm = filter_state == "01"
            
            _LOGGER.info(
                "Device %s updated - Power: %s, Mode: %s, Target: %s°C, Current: %s°C, Fan: %s, Error: %s",
                self.device_num,
                self.is_on,
                self.hvac_mode,
                self.target_temperature,
                self.current_temperature,
                self.fan_mode,
                self.error_code,
            )
            
        except Exception as err:
            _LOGGER.exception("Error parsing device state for device %s: %s", self.device_num, err)

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
