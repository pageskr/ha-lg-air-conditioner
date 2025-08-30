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
    """Power switch."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, device_num, "power_sw")

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return f"에어컨 {self.device_num} 전원"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
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

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        # Generate control packet
        packet = self.device.get_control_packet(
            True, self.device.hvac_mode, self.device.target_temperature, self.device.fan_mode
        )
        
        # Send command twice as per YAML
        success = await self.coordinator.async_send_command(self.device_num, packet)
        if success:
            await self.coordinator.async_send_command(self.device_num, packet)
            self.device.is_on = True
            self.async_write_ha_state()
            # Request state update
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        # Generate control packet
        packet = self.device.get_control_packet(
            False, self.device.hvac_mode, self.device.target_temperature, self.device.fan_mode
        )
        
        # Send command twice as per YAML
        success = await self.coordinator.async_send_command(self.device_num, packet)
        if success:
            await self.coordinator.async_send_command(self.device_num, packet)
            self.device.is_on = False
            self.async_write_ha_state()
            # Request state update
            await self.coordinator.async_request_refresh()


class LGAirConditionerLockSwitch(LGAirConditionerEntity, SwitchEntity):
    """Lock switch."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, device_num, "lock_sw")

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return f"에어컨 {self.device_num} 잠금"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self.device.is_locked

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.device.is_available:
            return "mdi:sync-alert"
        return "mdi:lock" if self.is_on else "mdi:lock-open-outline"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (lock)."""
        # Set lock state first
        self.device.is_locked = True
        
        # Generate control packet with current power state
        packet = self.device.get_control_packet(
            self.device.is_on, self.device.hvac_mode, self.device.target_temperature, self.device.fan_mode
        )
        
        # Send command twice as per YAML
        success = await self.coordinator.async_send_command(self.device_num, packet)
        if success:
            await self.coordinator.async_send_command(self.device_num, packet)
            self.async_write_ha_state()
            # Request state update
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (unlock)."""
        # Set lock state first
        self.device.is_locked = False
        
        # Generate control packet with current power state
        packet = self.device.get_control_packet(
            self.device.is_on, self.device.hvac_mode, self.device.target_temperature, self.device.fan_mode
        )
        
        # Send command twice as per YAML
        success = await self.coordinator.async_send_command(self.device_num, packet)
        if success:
            await self.coordinator.async_send_command(self.device_num, packet)
            self.async_write_ha_state()
            # Request state update
            await self.coordinator.async_request_refresh()
