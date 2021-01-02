import logging
import voluptuous as vol
import asyncio
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_TOKEN,
)
from homeassistant.components.fan import (
    FanEntity,
    SUPPORT_SET_SPEED,
    PLATFORM_SCHEMA,
    DOMAIN,
)
from miio import DeviceException
from miio.device import Device

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
})

AVAILABLE_PROPERTIES = [
    "state",
    "process",
    "cycle",
    "time_remain",
    "child_lock",
    "volume",
]

ICON = 'mdi:washing-machine'

def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    # get config
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    token = config.get(CONF_TOKEN)
    # init sensor
    washer = MijiaWasher(name, host, token)
    add_devices_callback([washer])


class MijiaWasher(FanEntity):
    def __init__(self, name, host, token):
        self._name = name
        self._device = Device(ip=host, token=token)
        self._available = True
        self._speed = None
        self._speed_list = []
        self._state = False
        self._state_attrs = {}
        self._skip_update = False

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    @property
    def should_poll(self):
        """Poll the device."""
        return True

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def icon(self):
        """Return the icon for device by its type."""
        return ICON

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state != 'off'

    '''
    async def async_turn_on(self, speed: str = None, **kwargs) -> None:
        """Turn the device on."""
        if speed:
            # If operation mode was set the device must not be turned on.
            result = await self.async_set_speed(speed)
        else:
            result = await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        result = await self._try_command(
            "Turning the miio device off failed.", self._device.off
        )

        if result:
            self._state = False
            self._skip_update = True

    async def async_set_buzzer_on(self):
        """Turn the buzzer on."""
        if self._device_features & FEATURE_SET_BUZZER == 0:
            return

        await self._try_command(
            "Turning the buzzer of the miio device on failed.",
            self._device.set_buzzer,
            True,
        )
'''
    def update(self):
        try:
            values = {}
            for prop in AVAILABLE_PROPERTIES:
                values[prop] = self._device.get_properties(properties=[prop])[0]
            return values
        except Exception:
            _LOGGER.error('Update seating state error.', exc_info=True)

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            values = await self.hass.async_add_executor_job(self.update)
            _LOGGER.debug("Got new values: %s", values)

            self._available = True
            self._state = values['state']
            self._state_attrs = values

        except DeviceException as ex:
            self._available = False
            _LOGGER.error("Got exception while fetching the state: %s", ex)


    @asyncio.coroutine
    def async_turn_on(self, speed: str = None) -> None:
        """Turn on the entity."""
        result = self._device.raw_command("set_power", ["on"])
        _LOGGER.debug("Turn on with result: %s" % result)

    @asyncio.coroutine
    def async_turn_off(self) -> None:
        """Turn off the entity."""
        result = self._device.raw_command("set_power", ["off"])
        _LOGGER.debug("Turn off with result: %s" % result)
        # yield from self.async_set_speed(STATE_OFF)

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return self._speed_list

    @property
    def speed(self):
        """Return the current speed."""
        if self._state:
            return self._speed

        return None

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if self.supported_features & SUPPORT_SET_SPEED == 0:
            return

        _LOGGER.debug("Setting the operation mode to: %s", speed)
        '''
        await self._try_command(
            "Setting operation mode of the miio device failed.",
            self._device.set_mode,
            AirpurifierOperationMode[speed.title()],
        )
        '''



