"""Sensor platform for LG Air Conditioner."""
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
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
            LGAirConditionerTemperatureSensor(coordinator, device_num, "current"),
            LGAirConditionerTemperatureSensor(coordinator, device_num, "target"),
            LGAirConditionerTemperatureSensor(coordinator, device_num, "pipe1"),
            LGAirConditionerTemperatureSensor(coordinator, device_num, "pipe2"),
            LGAirConditionerTemperatureSensor(coordinator, device_num, "outdoor"),
            LGAirConditionerModeSensor(coordinator, device_num, "hvac_mode"),
            LGAirConditionerModeSensor(coordinator, device_num, "fan_mode"),
            LGAirConditionerModeSensor(coordinator, device_num, "swing_mode"),
            LGAirConditionerErrorSensor(coordinator, device_num),
        ])
    
    async_add_entities(entities)


class LGAirConditionerTemperatureSensor(LGAirConditionerEntity, SensorEntity):
    """LG Air Conditioner temperature sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
        temp_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, f"temperature_{temp_type}")
        self._temp_type = temp_type
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        name_map = {
            "current": "현재 온도",
            "target": "설정 온도",
            "pipe1": "배관1 온도",
            "pipe2": "배관2 온도",
            "outdoor": "실외 온도",
        }
        return f"에어컨 {self.device_num} {name_map.get(self._temp_type, self._temp_type)}"

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        icon_map = {
            "current": "mdi:thermometer",
            "target": "mdi:thermometer",
            "pipe1": "mdi:thermometer-chevron-down",
            "pipe2": "mdi:thermometer-chevron-down",
            "outdoor": "mdi:hydraulic-oil-temperature",
        }
        return icon_map.get(self._temp_type, "mdi:thermometer")

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._temp_type == "current":
            return self.device.current_temperature
        elif self._temp_type == "target":
            return self.device.target_temperature
        elif self._temp_type == "pipe1":
            return self.device.pipe1_temperature
        elif self._temp_type == "pipe2":
            return self.device.pipe2_temperature
        elif self._temp_type == "outdoor":
            return self.device.outdoor_temperature
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device.is_available


class LGAirConditionerModeSensor(LGAirConditionerEntity, SensorEntity):
    """LG Air Conditioner mode sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
        mode_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, mode_type)
        self._mode_type = mode_type

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        name_map = {
            "hvac_mode": "운전 모드",
            "fan_mode": "팬 속도",
            "swing_mode": "스윙 모드",
        }
        return f"에어컨 {self.device_num} {name_map.get(self._mode_type, self._mode_type)}"

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self._mode_type == "hvac_mode":
            mode = self.device.hvac_mode
            icon_map = {
                "cool": "mdi:snowflake",
                "dry": "mdi:water-percent",
                "fan_only": "mdi:fan",
                "auto": "mdi:rotate-3d-variant",
                "heat": "mdi:fire",
                "off": "mdi:power",
            }
            return icon_map.get(mode, "mdi:sync-alert")
        elif self._mode_type == "fan_mode":
            mode = self.device.fan_mode
            icon_map = {
                "low": "mdi:fan-speed-1",
                "medium": "mdi:fan-speed-2",
                "high": "mdi:fan-speed-3",
                "auto": "mdi:fan-auto",
                "silent": "mdi:fan-minus",
                "power": "mdi:car-turbocharger",
            }
            return icon_map.get(mode, "mdi:fan")
        elif self._mode_type == "swing_mode":
            mode = self.device.swing_mode
            return "mdi:arrow-decision-auto" if mode == "auto" else "mdi:ray-start-arrow"
        return "mdi:information"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._mode_type == "hvac_mode":
            return self.device.hvac_mode
        elif self._mode_type == "fan_mode":
            return self.device.fan_mode
        elif self._mode_type == "swing_mode":
            return self.device.swing_mode
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device.is_available


class LGAirConditionerErrorSensor(LGAirConditionerEntity, SensorEntity):
    """LG Air Conditioner error code sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "error_code")
        self._attr_icon = "mdi:alert-circle"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 에러 코드"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.device.error_code

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device.is_available
