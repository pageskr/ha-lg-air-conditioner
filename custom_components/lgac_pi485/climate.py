import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    HVACMode,
    FAN_LOW, FAN_MEDIUM, FAN_MIDDLE, FAN_HIGH, FAN_AUTO, FAN_FOCUS,
    SWING_OFF, SWING_VERTICAL, SWING_HORIZONTAL, SWING_BOTH,
    PRESET_ECO, PRESET_AWAY, PRESET_BOOST, PRESET_COMFORT, PRESET_HOME, PRESET_SLEEP, PRESET_ACTIVITY,
    ATTR_HVAC_MODE, ATTR_HVAC_MODES,
    ATTR_MAX_TEMP, ATTR_MIN_TEMP, ATTR_TARGET_TEMP_STEP,
    ATTR_FAN_MODE, ATTR_FAN_MODES,
    ATTR_SWING_MODE, ATTR_SWING_MODES,
    ATTR_PRESET_MODE, ATTR_PRESET_MODES,
    ClimateEntityFeature
)
from homeassistant.components.remote import (
    ATTR_COMMAND, DOMAIN, SERVICE_SEND_COMMAND
)
from homeassistant.const import (
    ATTR_TEMPERATURE, ATTR_ENTITY_ID, CONF_NAME, CONF_CUSTOMIZE, CONF_UNIQUE_ID,
    STATE_UNAVAILABLE, STATE_UNKNOWN
)
from homeassistant.core import callback
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.event import TrackTemplate, async_track_template_result, async_track_state_change_event
from homeassistant.helpers.template import result_as_boolean
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)

CONF_TEMP_SENSOR = 'temp_sensor'
CONF_POWER_TEMPLATE = 'power_template'
CONF_TARGET_TEMP = 'target_temp'

DEFAULT_NAME = 'LGAC Climate'
DEFAULT_MIN_TEMP = 18
DEFAULT_MAX_TEMP = 30
DEFAULT_TARGET_TEMP = 24
DEFAULT_TARGET_TEMP_STEP = 1
DEFAULT_HVAC_MODES = [HVACMode.OFF, HVACMode.COOL, HVACMode.AUTO, HVACMode.DRY, HVACMode.FAN_ONLY, HVACMode.HEAT]
DEFAULT_FAN_MODES = [FAN_LOW, FAN_MEDIUM, FAN_MIDDLE, FAN_HIGH, FAN_AUTO, FAN_FOCUS]
DEFAULT_SWING_MODES = [SWING_OFF, SWING_VERTICAL]
DEFAULT_PRESET_MODES = [PRESET_ECO, PRESET_AWAY, PRESET_BOOST, PRESET_COMFORT, PRESET_HOME, PRESET_SLEEP, PRESET_ACTIVITY]
DEFAULT_HVAC_MODE = HVACMode.OFF
DEFAULT_FAN_MODE = FAN_AUTO
DEFAULT_SWING_MODE = SWING_VERTICAL
DEFAULT_PRESET_MODE = None

ATTR_LAST_HVAC_MODE = 'last_hvac_mode'
ATTR_LAST_FAN_MODE = 'last_fan_mode'
ATTR_LAST_PRESET_MODE = 'last_preset_mode'
ATTR_LAST_SWING_MODE = 'last_swing_mode'
ATTR_SUPPORTED_FEATURES = 'supported_features'

COMMAND_POWER_OFF = 'off'
COMMAND_PRESET_MODES = 'presets'

CUSTOMIZE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_HVAC_MODES): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_FAN_MODES): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_SWING_MODES): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_PRESET_MODES): vol.All(cv.ensure_list, [cv.string])
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TEMP_SENSOR): cv.entity_id,
    vol.Optional(CONF_POWER_TEMPLATE): cv.template,
    vol.Optional(ATTR_MIN_TEMP, default=DEFAULT_MIN_TEMP): cv.positive_int,
    vol.Optional(ATTR_MAX_TEMP, default=DEFAULT_MAX_TEMP): cv.positive_int,
    vol.Optional(CONF_TARGET_TEMP, default=DEFAULT_TARGET_TEMP): cv.positive_int,
    vol.Optional(ATTR_TARGET_TEMP_STEP, default=DEFAULT_TARGET_TEMP_STEP): cv.positive_int,
    vol.Optional(ATTR_HVAC_MODE, default=DEFAULT_HVAC_MODE): cv.string,
    vol.Optional(ATTR_FAN_MODE, default=DEFAULT_FAN_MODE): cv.string,
    vol.Optional(ATTR_PRESET_MODE, default=DEFAULT_PRESET_MODE): vol.Maybe(cv.string),
    vol.Optional(ATTR_SWING_MODE, default=DEFAULT_SWING_MODE): vol.Maybe(cv.string),
    vol.Optional(CONF_CUSTOMIZE, default={}): CUSTOMIZE_SCHEMA,
    vol.Optional(CONF_UNIQUE_ID): cv.string,
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the lgac climate platform."""
    name = config.get(CONF_NAME)
    min_temp = config.get(ATTR_MIN_TEMP)
    max_temp = config.get(ATTR_MAX_TEMP)
    target_temp = config.get(CONF_TARGET_TEMP)
    target_temp_step = config.get(ATTR_TARGET_TEMP_STEP)
    hvac_modes = config.get(CONF_CUSTOMIZE).get(ATTR_HVAC_MODES, []) or DEFAULT_HVAC_MODES
    fan_modes = config.get(CONF_CUSTOMIZE).get(ATTR_FAN_MODES, []) or DEFAULT_FAN_MODES
    preset_modes = config.get(CONF_CUSTOMIZE).get(ATTR_PRESET_MODES, []) or DEFAULT_PRESET_MODES
    swing_modes = config.get(CONF_CUSTOMIZE).get(ATTR_SWING_MODES, []) or DEFAULT_SWING_MODES
    default_hvac_mode = config.get(ATTR_HVAC_MODE)
    default_fan_mode = config.get(ATTR_FAN_MODE)
    default_preset_mode = config.get(ATTR_PRESET_MODE)
    default_swing_mode = config.get(ATTR_SWING_MODE)
    temp_entity_id = config.get(CONF_TEMP_SENSOR)
    power_template = config.get(CONF_POWER_TEMPLATE)
    unique_id = config.get(CONF_UNIQUE_ID)

    async_add_entities([
        RemoteClimate(hass, name, min_temp, max_temp, target_temp, target_temp_step,
                      hvac_modes, fan_modes, swing_modes, preset_modes,
                      default_hvac_mode, default_fan_mode, default_swing_mode, default_preset_mode,
                      temp_entity_id, power_template, unique_id)
    ])


class RemoteClimate(ClimateEntity, RestoreEntity):
    def __init__(self, hass, name, min_temp, max_temp, target_temp, target_temp_step,
                 hvac_modes, fan_modes, swing_modes, preset_modes,
                 default_hvac_mode, default_fan_mode, default_swing_mode, default_preset_mode,
                 temp_entity_id, power_template, unique_id):
        """Representation of a LGAC Remote Climate device."""
        self.hass = hass
        self._name = name
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._target_temperature = target_temp
        self._target_temperature_step = target_temp_step
        self._unit_of_measurement = hass.config.units.temperature_unit
        self._current_temperature = None
        self._default_hvac_mode = default_hvac_mode
        self._current_hvac_mode = default_hvac_mode
        self._last_hvac_mode = default_hvac_mode
        self._default_fan_mode = default_fan_mode
        self._current_fan_mode = default_fan_mode
        self._last_fan_mode = default_fan_mode
        self._default_swing_mode = default_swing_mode
        self._current_swing_mode = default_swing_mode
        self._last_swing_mode = default_swing_mode
        self._default_preset_mode = default_preset_mode
        self._current_preset_mode = default_preset_mode
        self._last_preset_mode = default_preset_mode
        self._temp_entity_id = temp_entity_id
        self._power_template = power_template
        self._hvac_modes = hvac_modes
        self._fan_modes = fan_modes
        self._preset_modes = preset_modes
        self._swing_modes = swing_modes
        self._unique_id = unique_id
        self._support_flags = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.SWING_MODE | ClimateEntityFeature.PRESET_MODE |
            ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        )
        self._enabled_flags = self._support_flags

        if temp_entity_id:
            async_track_state_change_event(hass, temp_entity_id, self._async_temp_changed)

        if power_template:
            result = async_track_template_result(
                self.hass,
                [TrackTemplate(power_template, None)],
                self._async_power_changed,
            )
            result.async_refresh()
            self.async_on_remove(result.async_remove)

    async def _async_temp_changed(self, event):
        """Update current temperature."""
        new_state = event.data.get('new_state')
        if new_state is None or new_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            return

        self._async_update_temp(new_state)
        self.async_write_ha_state()

    @callback
    def _async_update_temp(self, state):
        """Update temperature with latest state from sensor."""
        try:
            self._current_temperature = float(state.state)
        except ValueError as ex:
            _LOGGER.error("Unable to update from sensor: %s", ex)

    def _async_power_changed(self, event, updates):
        """Update current power."""
        result = updates.pop().result

        if isinstance(result, TemplateError):
            _LOGGER.warning('Unable to update power from template: %s', result)
        else:
            self._current_hvac_mode = self._last_hvac_mode if result_as_boolean(result) else HVACMode.OFF
            self.schedule_update_ha_state()

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique id of this climate."""
        return self._unique_id

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """Return the sensor temperature."""
        return self._current_temperature

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._max_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._target_temperature_step

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool."""
        return self._current_hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return self._hvac_modes

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._current_fan_mode

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return self._fan_modes

    @property
    def swing_mode(self):
        """Return the current swing mode."""
        return self._current_swing_mode

    @property
    def swing_modes(self):
        """Return a list of available swing modes."""
        return self._swing_modes
        
    @property
    def preset_mode(self):
        """Return the current preset mode."""
        return self._current_preset_mode

    @property
    def preset_modes(self):
        """Return a list of available preset modes."""
        return self._preset_modes

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data = super().state_attributes
        data[ATTR_LAST_HVAC_MODE] = self._last_hvac_mode
        data[ATTR_LAST_FAN_MODE] = self._last_fan_mode
        data[ATTR_LAST_SWING_MODE] = self._last_swing_mode
        data[ATTR_LAST_PRESET_MODE] = self._last_preset_mode
        return data

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def is_on(self):
        """Return true if on."""
        return self._current_hvac_mode != HVACMode.OFF

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
            self.schedule_update_ha_state()

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        self._current_fan_mode = fan_mode
        self._last_fan_mode = fan_mode
        self.schedule_update_ha_state()

    def set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        self._current_hvac_mode = hvac_mode
        if hvac_mode != HVACMode.OFF:
            self._last_hvac_mode = hvac_mode
        self.schedule_update_ha_state()

    def set_swing_mode(self, swing_mode):
        """Set new swing mode."""
        self._current_swing_mode = swing_mode
        self._last_swing_mode = swing_mode
        self.schedule_update_ha_state()

    def set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        self._current_preset_mode = preset_mode
        self._last_preset_mode = preset_mode
        self.schedule_update_ha_state()

    def turn_on(self):
        """Turn device on."""
        self.set_hvac_mode(self._last_hvac_mode)

    def turn_off(self):
        """Turn device off."""
        self.set_hvac_mode(HVACMode.OFF)

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()

        if state is not None:
            self._current_hvac_mode = state.state
            self._last_hvac_mode = state.attributes.get(ATTR_LAST_HVAC_MODE, self._default_hvac_mode)
            self._last_fan_mode = state.attributes.get(ATTR_LAST_FAN_MODE, self._default_fan_mode)
            self._current_fan_mode = state.attributes.get(ATTR_FAN_MODE, self._last_fan_mode)
            self._last_swing_mode = state.attributes.get(ATTR_LAST_SWING_MODE, self._default_swing_mode)
            self._current_swing_mode = state.attributes.get(ATTR_SWING_MODE, self._last_swing_mode)
            self._last_preset_mode = state.attributes.get(ATTR_LAST_PRESET_MODE, self._default_preset_mode)
            self._current_preset_mode = state.attributes.get(ATTR_PRESET_MODE, self._last_preset_mode)
            self._target_temperature = state.attributes.get(ATTR_TEMPERATURE, self._target_temperature)

            enabled_flags = state.attributes.get(ATTR_SUPPORTED_FEATURES, self._enabled_flags)
            mask_flags = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.SWING_MODE | ClimateEntityFeature.PRESET_MODE
            if (enabled_flags & mask_flags) == enabled_flags:
                self._enabled_flags = enabled_flags

        if self._temp_entity_id:
            temp_state = self.hass.states.get(self._temp_entity_id)
            if temp_state and temp_state.state not in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
                self._async_update_temp(temp_state)

        await self.async_update_ha_state(True)
