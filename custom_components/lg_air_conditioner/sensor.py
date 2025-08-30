"""Sensor platform for LG Air Conditioner."""
import logging
from typing import Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import LGAirConditionerCoordinator, LGAirConditionerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LG Air Conditioner sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for device_num in coordinator.devices:
        entities.extend([
            LGAirConditionerCurrentTempSensor(coordinator, device_num),
            LGAirConditionerSetTempSensor(coordinator, device_num),
            LGAirConditionerPipe1TempSensor(coordinator, device_num),
            LGAirConditionerPipe2TempSensor(coordinator, device_num),
            LGAirConditionerOutdoorTempSensor(coordinator, device_num),
            LGAirConditionerModeSensor(coordinator, device_num),
            LGAirConditionerFanModeSensor(coordinator, device_num),
            LGAirConditionerSwingModeSensor(coordinator, device_num),
            LGAirConditionerStateSensor(coordinator, device_num),
        ])
    
    async_add_entities(entities)


class LGAirConditionerCurrentTempSensor(LGAirConditionerEntity, SensorEntity):
    """Current temperature sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "temperature")
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 현재온도"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.device.current_temperature

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.device.is_available:
            return "mdi:sync-alert"
        if self.native_value and self.native_value >= 28:
            return "mdi:home-thermometer"
        return "mdi:home-thermometer-outline"


class LGAirConditionerSetTempSensor(LGAirConditionerEntity, SensorEntity):
    """Set temperature sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "set_temperature")
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 설정온도"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.device.target_temperature

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.device.is_available:
            return "mdi:sync-alert"
        if self.native_value and self.native_value < 24:
            return "mdi:thermometer-alert"
        return "mdi:thermometer"


class LGAirConditionerPipe1TempSensor(LGAirConditionerEntity, SensorEntity):
    """Pipe 1 temperature sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "pipe1_temperature")
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:thermometer-chevron-down"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 배관1온도"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.device.pipe1_temperature


class LGAirConditionerPipe2TempSensor(LGAirConditionerEntity, SensorEntity):
    """Pipe 2 temperature sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "pipe2_temperature")
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:thermometer-chevron-down"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 배관2온도"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.device.pipe2_temperature


class LGAirConditionerOutdoorTempSensor(LGAirConditionerEntity, SensorEntity):
    """Outdoor temperature sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "outdoor_temperature")
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:hydraulic-oil-temperature"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 실외온도"

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.device.outdoor_temperature


class LGAirConditionerModeSensor(LGAirConditionerEntity, SensorEntity):
    """HVAC mode sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "hvac_mode")

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 운전모드"

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        return self.device.hvac_mode

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.device.is_available:
            return "mdi:sync-alert"
        
        mode_icons = {
            "cool": "mdi:snowflake",
            "dry": "mdi:water-percent",
            "fan_only": "mdi:fan",
            "auto": "mdi:rotate-3d-variant",
            "heat": "mdi:fire",
        }
        return mode_icons.get(self.native_value, "mdi:sync-alert")


class LGAirConditionerFanModeSensor(LGAirConditionerEntity, SensorEntity):
    """Fan mode sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "fan_mode")

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 팬속도"

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        return self.device.fan_mode

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.device.is_available:
            return "mdi:sync-alert"
        
        fan_icons = {
            "low": "mdi:fan-speed-1",
            "medium": "mdi:fan-speed-2",
            "high": "mdi:fan-speed-3",
            "auto": "mdi:fan-auto",
            "silent": "mdi:fan-minus",
            "power": "mdi:car-turbocharger",
        }
        return fan_icons.get(self.native_value, "mdi:sync-alert")


class LGAirConditionerSwingModeSensor(LGAirConditionerEntity, SensorEntity):
    """Swing mode sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "swing_mode")

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 스윙모드"

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        return self.device.swing_mode

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.device.is_available:
            return "mdi:sync-alert"
        
        if self.native_value == "auto":
            return "mdi:arrow-decision-auto"
        return "mdi:ray-start-arrow"


class LGAirConditionerStateSensor(LGAirConditionerEntity, SensorEntity):
    """Raw state sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "state")

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 상태"

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        return self.device._raw_state if self.device._raw_state else ""

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.device.is_available:
            return "mdi:barcode-scan"
        return "mdi:barcode-off"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.device._raw_state:
            return {}
        
        return {
            "room": self.device_num,
            "operon": f"{0x03 if not self.device.is_locked else 0x07:02X}",
            "operoff": f"{0x02 if not self.device.is_locked else 0x06:02X}",
            "lockon": f"{0x07 if self.device.is_on else 0x06:02X}",
            "lockoff": f"{0x03 if self.device.is_on else 0x02:02X}",
            "operscan": "00",
            "opermode": f"{self._calculate_opermode():02X}",
            "temperature": f"{self.device.target_temperature - 15:02X}",
            "checksumon": self._calculate_checksum(True),
            "checksumoff": self._calculate_checksum(False),
            "checksumlockon": self._calculate_checksum_lock(True),
            "checksumlockoff": self._calculate_checksum_lock(False),
            "checksumscan": self._calculate_checksum_scan(),
        }

    def _calculate_opermode(self) -> int:
        """Calculate opermode byte."""
        mode_map = {"cool": 0, "dry": 1, "fan_only": 2, "auto": 3, "heat": 4}
        hvac_val = mode_map.get(self.device.hvac_mode, 0)
        
        fan_map = {"low": 0x10, "medium": 0x20, "high": 0x30, "auto": 0x40, "silent": 0x50, "power": 0x60}
        fan_val = fan_map.get(self.device.fan_mode, 0x40)
        
        swing_val = 0x08 if self.device.swing_mode == "auto" else 0x00
        
        return hvac_val + fan_val + swing_val

    def _calculate_checksum(self, power_on: bool) -> str:
        """Calculate checksum for power command."""
        room = int(self.device_num, 16)
        if power_on:
            oper = 0x03 if not self.device.is_locked else 0x07
        else:
            oper = 0x02 if not self.device.is_locked else 0x06
        
        opermode = self._calculate_opermode()
        temperature = self.device.target_temperature - 15
        
        checksum = (0x80 + 0x00 + 0xA3 + room + oper + temperature + opermode) & 0xFF
        checksum = (checksum & 0xAA) + 85 - (checksum & 0x55)
        
        return f"{checksum:02X}"

    def _calculate_checksum_lock(self, lock_on: bool) -> str:
        """Calculate checksum for lock command."""
        room = int(self.device_num, 16)
        if lock_on:
            lock = 0x07 if self.device.is_on else 0x06
        else:
            lock = 0x03 if self.device.is_on else 0x02
        
        opermode = self._calculate_opermode()
        temperature = self.device.target_temperature - 15
        
        checksum = (0x80 + 0x00 + 0xA3 + room + lock + temperature + opermode) & 0xFF
        checksum = (checksum & 0xAA) + 85 - (checksum & 0x55)
        
        return f"{checksum:02X}"

    def _calculate_checksum_scan(self) -> str:
        """Calculate checksum for scan command."""
        room = int(self.device_num, 16)
        opermode = self._calculate_opermode()
        temperature = self.device.target_temperature - 15
        
        checksum = (0x80 + 0x00 + 0xA3 + room + 0x00 + temperature + opermode) & 0xFF
        checksum = (checksum & 0xAA) + 85 - (checksum & 0x55)
        
        return f"{checksum:02X}"
