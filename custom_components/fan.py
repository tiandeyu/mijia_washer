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

SPEED_LIST = [
    'pause',
    'start',
    'dailywash',    # 日常洗
    'quick',        # 快速洗
    'delicate',     # 轻柔洗
    'intensive',    # 强力洗
    'heavy',        # 大件洗
    'washdry',      # 洗+烘
    'spin',         # 单脱水
    'dry',          # 单烘干
    'dryairwash',   # 空气洗
    'userdefine',   # 自定义
    'washdryquick', # 快洗烘
    'down',         # 羽绒服
    'drumclean',    # 桶自洁
    'rinse',        # 单漂洗
    'cotton',       # 棉麻洗
    'synthetic',    # 化纤洗
    'shirt',        # 衬衣洗
    'babycare',     # 婴童洗
    'jacket',       # 冲锋衣
    'underwear',    # 内衣洗
    'boiling',      # 高温洗
    'wool',         # 羊毛洗
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
        return self._state

    def start(self):
        if self._state_attrs != 'run':
            self._device.raw_command("set_startpause", ['true'])

    def pause(self):
        if self._state_attrs != 'pause':
            self._device.raw_command("set_startpause", ['false'])

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
            self._speed = values['cycle']
            self._state = values['state'] != 'off'
            self._state_attrs = values

        except DeviceException as ex:
            self._available = False
            _LOGGER.error("Got exception while fetching the state: %s", ex)


    @asyncio.coroutine
    def async_turn_on(self, speed: str = None) -> None:
        """Turn on the entity."""
        if not self._state:
            result = self._device.raw_command("set_power", ["on"])
            _LOGGER.debug("Turn on with result: %s" % result)
        self.set_speed(speed)

    @asyncio.coroutine
    def async_turn_off(self) -> None:
        """Turn off the entity."""
        result = self._device.raw_command("set_power", ["off"])
        _LOGGER.debug("Turn off with result: %s" % result)
        # yield from self.async_set_speed(STATE_OFF)

    def set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if self.supported_features & SUPPORT_SET_SPEED == 0:
            return
        _LOGGER.debug("Setting the operation mode to: %s", speed)
        if speed == 'pause':
            self.pause()
        elif speed == 'start':
            self.start()
        else:
            self._device.raw_command("set_cycle", [speed])

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return SPEED_LIST

    @property
    def speed(self):
        """Return the current speed."""
        if self._state:
            return self._speed

        return None






