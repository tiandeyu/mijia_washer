import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_TOKEN,
)
from homeassistant.components.fan import (
    FanEntity,
    SPEED_OFF,
    SUPPORT_SET_SPEED,
    SUPPORT_PRESET_MODE,
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

PRESET_MODES = [
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

PROCESS_VALUE = {
    'wash': '主洗',
    'rinse': '漂洗',
    'spin': '脱水',
    'dry': '烘干',
    'invalid': '',
}

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
        info = self._device.info()
        self._info = {
            'firmware_version': info.firmware_version,
            'hardware_version': info.hardware_version,
            'mac_address': info.mac_address,
            'model': info.model,
        }
        self._available = True
        self._speed = SPEED_OFF
        self._percentage = None
        self._speed_list = []
        self._preset_modes = PRESET_MODES
        self._preset_mode = None
        self._state_attrs = {}
        self._skip_update = False

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_PRESET_MODE

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
    def percentage(self) -> int:
        """Return the current speed."""
        return self._percentage

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(PRESET_MODES)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        self._percentage = percentage
        self._preset_mode = None
        self.async_write_ha_state()

    @property
    def preset_mode(self) -> str:
        """Return the current preset mode, e.g., auto, smart, interval, favorite."""
        return self._preset_mode

    @property
    def preset_modes(self) -> list:
        """Return a list of available preset modes."""
        return self._preset_modes

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.debug("Setting the operation mode to: %s", preset_mode)
        if preset_mode not in self.preset_modes:
            return
        if preset_mode == 'pause':
            self.pause()
        elif preset_mode == 'start':
            self.start()
        else:
            self._device.raw_command("set_cycle", [preset_mode])
        self._preset_mode = preset_mode
        self._percentage = None
        self.async_write_ha_state()

    async def async_turn_on(
            self,
            speed: str = None,
            percentage: int = None,
            preset_mode: str = None,
            **kwargs,
    ) -> None:
        """Turn on the entity."""
        if not self._state:
            result = self._device.raw_command("set_power", ["on"])
            _LOGGER.debug("Turn on with result: %s" % result)
        self._preset_mode = PRESET_MODES[2]
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the entity."""
        result = self._device.raw_command("set_power", ["off"])
        await self.async_set_percentage(0)
        _LOGGER.debug("Turn off with result: %s" % result)

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
            # split process
            process = values['process'].split(';')
            options = process[0].split(':')[1].split(',')
            processing = process[1].split(':')[1]
            values['options'] = [PROCESS_VALUE[x] if x in PROCESS_VALUE else x for x in options]
            values['process'] = PROCESS_VALUE[processing]
            values.update(self._info)
            self._state_attrs = values

        except DeviceException as ex:
            self._available = False
            _LOGGER.error("Got exception while fetching the state: %s", ex)




