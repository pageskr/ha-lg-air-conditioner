"""Switch platform for LG Air Conditioner."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up LG Air Conditioner switch entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for device_num in coordinator.devices:
        entities.extend([
            LGAirConditionerPowerSwitch(coordinator, device_num),
            LGAirConditionerLockSwitch(coordinator, device_num),
        ])
    
    async_add_entities(entities)


class LGAirConditionerPowerSwitch(LGAirConditionerEntity, SwitchEntity):
    """LG Air Conditioner power switch entity."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, device_num, "power_switch")
        self._attr_icon = "mdi:air-conditioner"

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return f"에어컨 {self.device_num} 전원 스위치"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.device.is_on

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device.is_available

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        # Generate control packet to turn on
        packet = self.device.get_control_packet(
            True, 
            self.device.hvac_mode if self.device.hvac_mode != "off" else "cool",
            self.device.target_temperature,
            self.device.fan_mode
        )
        
        # Send command
        success = await self.coordinator.async_send_command(self.device_num, packet)
        if success:
            self.device.is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        # Generate control packet to turn off
        packet = self.device.get_control_packet(
            False,
            self.device.hvac_mode,
            self.device.target_temperature,
            self.device.fan_mode
        )
        
        # Send command
        success = await self.coordinator.async_send_command(self.device_num, packet)
        if success:
            self.device.is_on = False
            self.async_write_ha_state()


class LGAirConditionerLockSwitch(LGAirConditionerEntity, SwitchEntity):
    """LG Air Conditioner lock switch entity."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, device_num, "lock_switch")

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return f"에어컨 {self.device_num} 잠금 스위치"

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:lock" if self.is_on else "mdi:lock-open"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on (locked)."""
        return self.device.is_locked

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device.is_available

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (lock)."""
        # Update lock state
        self.device.is_locked = True
        
        # Generate control packet
        packet = self.device.get_control_packet(
            self.device.is_on,
            self.device.hvac_mode,
            self.device.target_temperature,
            self.device.fan_mode
        )
        
        # Send command
        success = await self.coordinator.async_send_command(self.device_num, packet)
        if success:
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (unlock)."""
        # Update lock state
        self.device.is_locked = False
        
        # Generate control packet
        packet = self.device.get_control_packet(
            self.device.is_on,
            self.device.hvac_mode,
            self.device.target_temperature,
            self.device.fan_mode
        )
        
        # Send command
        success = await self.coordinator.async_send_command(self.device_num, packet)
        if success:
            self.async_write_ha_state()
