"""Binary sensor platform for LG Air Conditioner."""
import logging
from typing import Optional

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
            LGAirConditionerLockSensor(coordinator, device_num),
            LGAirConditionerOutdoorSensor(coordinator, device_num),
        ])
    
    async_add_entities(entities)


class LGAirConditionerPowerSensor(LGAirConditionerEntity, BinarySensorEntity):
    """Power status binary sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device_num, "power")
        self._attr_device_class = BinarySensorDeviceClass.POWER

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"에어컨 {self.device_num} 가동"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.device.is_on

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
        
        if self.is_on:
            return mode_icons.get(self.device.hvac_mode, "mdi:air-conditioner")
        return "mdi:air-conditioner"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "oper": "on" if self.is_on else "off",
            "curr_temperature": f"{self.device.current_temperature}°C",
            "set_temperature": f"{self.device.target_temperature}°C",
            "mode": self.device.hvac_mode,
            "speed": self.device.fan_mode,
            "swing": self.device.swing_mode,
            "lock": "on" if self.device.is_locked else "off",
            "outdoor_oper": "on" if self.device.outdoor_temperature > 0 else "off",
            "outdoor_temperature": f"{self.device.outdoor_temperature}°C",
            "pipe1_temperature": f"{self.device.pipe1_temperature}°C",
            "pipe2_temperature": f"{self.device.pipe2_temperature}°C",
            "states": self.device._raw_state if self.device._raw_state else "",
        }


class LGAirConditionerLockSensor(LGAirConditionerEntity, BinarySensorEntity):
    """Lock status binary sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device_num, "lock")
        self._attr_device_class = BinarySensorDeviceClass.LOCK

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"에어컨 {self.device_num} 잠금"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.device.is_locked

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.device.is_available:
            return "mdi:sync-alert"
        return "mdi:lock" if self.is_on else "mdi:lock-open-outline"


class LGAirConditionerOutdoorSensor(LGAirConditionerEntity, BinarySensorEntity):
    """Outdoor unit operation binary sensor."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device_num, "outdoor_oper")
        self._attr_device_class = BinarySensorDeviceClass.POWER

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"에어컨 {self.device_num} 실외기"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        # Outdoor unit is on if outdoor temperature is reported (>0)
        return self.device.outdoor_temperature > 0

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.device.is_available:
            return "mdi:sync-alert"
        return "mdi:hvac" if self.is_on else "mdi:hvac-off"
