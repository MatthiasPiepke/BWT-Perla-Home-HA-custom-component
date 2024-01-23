import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

import requests
import urllib3
import json

from homeassistant.const import (
    UnitOfTime,
    CONF_NAME,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
)

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

urllib3.disable_warnings()

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
{
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_SCAN_INTERVAL): cv.time_period,
}
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Set up the sensor platform."""
    name = config[CONF_NAME]
    ip_address = config[CONF_IP_ADDRESS]
    password = config[CONF_PASSWORD]
    add_entities([DummySensor(name, ip_address, password)], True)
    SCAN_INTERVAL = config[CONF_SCAN_INTERVAL].total_seconds()

class DummySensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, name, ip_address, password) -> None:
        super().__init__()
        self._ip = ip_address
        self._password = password
        self._login_url = "https://"+ip_address+"/users/login"
        self._login_data = {"STLoginPWField":password}
        self._data_url = "https://"+ip_address+"/home/actualizedata"
        self._warning_url = "https://"+ip_address+"/home/warnings"
        self._name = name
        self._attr_name = name
        self._attr_native_unit_of_measurement = UnitOfTime.DAYS
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._flowToday = None
        self._flowMonth = None
        self._flowYear = None
        self._refillRegeneratingAgent = None
        self._remainingRegeneratingAgent = None

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        session = requests.Session()
        response = session.post(self._login_url, data=self._login_data, verify=False)

        response = session.get(self._data_url)
        json_response = json.loads(response.text)

        self._flowToday = json_response['durchflussHeute']
        self._flowMonth = json_response['durchflussMonat']
        self._flowYear = "{:.1f}".format(float(json_response['durchflussJahr'])/10)
        self._refillRegeneratingAgent = json_response['RegeneriemittelNachfuellenIn']
        self._remainingRegeneratingAgent = json_response['RegeneriemittelVerbleibend']
        self._attr_native_value = self._refillRegeneratingAgent
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            "flowToday" : self._flowToday,
            "flowMonth" : self._flowMonth,
            "flowYear" : self._flowYear,
            "refillRegeneratingAgent" : self._refillRegeneratingAgent,
            "remainingRegeneratingAgent" : self._remainingRegeneratingAgent,
        }
