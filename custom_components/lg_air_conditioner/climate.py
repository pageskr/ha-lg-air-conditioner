"""Climate platform for LG Air Conditioner."""
import logging
from typing import Any, List, Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import LGAirConditionerCoordinator, LGAirConditionerEntity

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.FAN_MODE
)

HVAC_MODES = [
    HVACMode.OFF,
    HVACMode.HEAT,
    HVACMode.COOL,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
    HVACMode.AUTO,
]

FAN_MODES = ["low", "medium", "high", "auto", "power", "nature"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LG Air Conditioner climate entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for device_num in coordinator.devices:
        entities.append(LGAirConditionerClimate(coordinator, device_num))
    
    async_add_entities(entities)


class LGAirConditionerClimate(LGAirConditionerEntity, ClimateEntity):
    """LG Air Conditioner climate entity."""

    def __init__(
        self,
        coordinator: LGAirConditionerCoordinator,
        device_num: str,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator, device_num, "climate")
        self._attr_supported_features = SUPPORT_FLAGS
        self._attr_hvac_modes = HVAC_MODES
        self._attr_fan_modes = FAN_MODES
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_min_temp = 18
        self._attr_max_temp = 30
        self._attr_target_temperature_step = 1

    @property
    def name(self) -> str:
        """Return the name of the climate entity."""
        return f"에어컨 {self.device_num}"

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return float(self.device.current_temperature)

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the temperature we try to reach."""
        return float(self.device.target_temperature)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation mode."""
        if not self.device.is_on:
            return HVACMode.OFF
        
        mode_map = {
            "heat": HVACMode.HEAT,
            "cool": HVACMode.COOL,
            "dry": HVACMode.DRY,
            "fan_only": HVACMode.FAN_ONLY,
            "auto": HVACMode.AUTO,
        }
        return mode_map.get(self.device.hvac_mode, HVACMode.OFF)

    @property
    def fan_mode(self) -> Optional[str]:
        """Return the fan setting."""
        return self.device.fan_mode

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device.is_available

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        # Generate control packet
        power = self.device.is_on
        mode = self.device.hvac_mode
        packet = self.device.get_control_packet(
            power, mode, int(temperature), self.device.fan_mode
        )
        
        # Send command
        success = await self.coordinator.async_send_command(self.device_num, packet)
        if success:
            self.device.target_temperature = int(temperature)
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target operation mode."""
        if hvac_mode == HVACMode.OFF:
            # Turn off
            packet = self.device.get_control_packet(
                False, self.device.hvac_mode, self.device.target_temperature, self.device.fan_mode
            )
        else:
            # Change mode
            mode_map = {
                HVACMode.HEAT: "heat",
                HVACMode.COOL: "cool",
                HVACMode.DRY: "dry",
                HVACMode.FAN_ONLY: "fan_only",
                HVACMode.AUTO: "auto",
            }
            mode = mode_map.get(hvac_mode, "auto")
            packet = self.device.get_control_packet(
                True, mode, self.device.target_temperature, self.device.fan_mode
            )
        
        # Send command
        success = await self.coordinator.async_send_command(self.device_num, packet)
        if success:
            if hvac_mode == HVACMode.OFF:
                self.device.is_on = False
            else:
                self.device.is_on = True
                self.device.hvac_mode = mode_map.get(hvac_mode, "auto")
            self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        # Generate control packet
        packet = self.device.get_control_packet(
            self.device.is_on, self.device.hvac_mode, self.device.target_temperature, fan_mode
        )
        
        # Send command
        success = await self.coordinator.async_send_command(self.device_num, packet)
        if success:
            self.device.fan_mode = fan_mode
            self.async_write_ha_state()
