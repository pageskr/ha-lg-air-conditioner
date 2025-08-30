"""Binary sensor platform for LG Air Conditioner."""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
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
    """Set up LG Air Conditioner binary sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for device_num in coordinator.devices:
        entities.extend([
            LGAirConditionerPowerSensor(coordinator, device_num),
            LGAirConditionerFilterSensor(coordinator, device_num),
            LGAirConditionerLockSensor(coordinator, device_num),
        ])
    
    async_add_entities(entities)


class LGAirConditionerPowerSensor(LGAirConditionerEntity, BinarySensorEntity):
    """LG Air Conditioner power state sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "power")
        self._attr_device_class = BinarySensorDeviceClass.POWER

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 전원"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.device.is_on

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device.is_available


class LGAirConditionerFilterSensor(LGAirConditionerEntity, BinarySensorEntity):
    """LG Air Conditioner filter alarm sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "filter_alarm")
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 필터 알람"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.device.filter_alarm

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device.is_available


class LGAirConditionerLockSensor(LGAirConditionerEntity, BinarySensorEntity):
    """LG Air Conditioner lock state sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_num, "lock")
        self._attr_device_class = BinarySensorDeviceClass.LOCK

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"에어컨 {self.device_num} 잠금"

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:lock" if self.is_on else "mdi:lock-open"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on (locked)."""
        return self.device.is_locked

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device.is_available
