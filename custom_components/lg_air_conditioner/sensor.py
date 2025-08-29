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
        temp_name = "현재 온도" if self._temp_type == "current" else "설정 온도"
        return f"에어컨 {self.device_num} {temp_name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._temp_type == "current":
            return self.device.current_temperature
        else:
            return self.device.target_temperature

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
