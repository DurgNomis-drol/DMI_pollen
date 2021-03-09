"""DMI pollen sensor"""
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.const import HTTP_OK, STATE_UNKNOWN, STATE_ON, STATE_OFF
import json
import requests
import xmltodict
import voluptuous as vol
import logging
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

# API Endpoint
ENDPOINT = "https://www.dmi.dk/dmidk_byvejrWS/rest/texts/forecast/pollen/Danmark"

JSON_XMLTEXT = "text"
JSON_PRODUCTS = "products"
JSON_POLLEN_INFO = "pollen_info"
JSON_FILE_INFO = "file_info"
JSON_REGION = "region"
JSON_DATE_DK = "date_DK"
JSON_DATE_DK_STRING = "date_string"
JSON_FORECAST = "forecast"
JSON_SOURCE = "comment"

JSON_ATTRIBUTE_NAME = "name"
JSON_ATTRIBUTE_VALUE = "value"
JSON_READINGS = "readings"
JSON_READING = "reading"

SEVERITY = "severity"
MANY = "Mange"
FEW = "Få"
FEW_THRESHOLD = 25
NONE = "Ingen"
NONE_THRESHOLD = 5

NO_READING = "-"
SOURCE = "source"
DATE = "applicable_date"

NAME = "dmi_pollen"
ICON = "mdi:flower-poppy"

# Time between updates (Default: 1 hour)
SCAN_INTERVAL = timedelta(seconds=3600)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the sensor platform."""

    data = DMIpollenApi()
    data.get_data()

    city_list = []
    for city in data.data:
        city_list.append(PollenSensor(data, city))

    add_devices(city_list, True)


class PollenSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, data, city):
        """Initialize the sensor."""
        self.data = data
        self._state = None
        self.city = city

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{NAME}_{self.city}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.data.data[self.city][SEVERITY]

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self.data.data[self.city]

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.data.get_data()


class DMIpollenApi:

    def __init__(self):
        self.data = {}

    @staticmethod
    def format_readings(raw):
        readings = {}
        all_values = 0

        for item in raw:
            name = item.get(JSON_ATTRIBUTE_NAME).str.lower()
            value = item.get(JSON_ATTRIBUTE_VALUE)
            readings[name] = int(value) if value.isnumeric() else 0

            all_values += int(value) if value.isnumeric() else 0

        readings[SEVERITY] = MANY

        if all_values < NONE_THRESHOLD:
            readings[SEVERITY] = NONE

        if NONE_THRESHOLD < all_values < FEW_THRESHOLD:
            readings[SEVERITY] = FEW

        return readings

    def get_data(self):

        self.data = {}

        response = requests.get(ENDPOINT)

        if response.status_code != HTTP_OK:
            _LOGGER.error("Error fetching data. Status code: {code} with text: {text}".format(
                code=response.status_code,
                text=response
            ))
            return

        json_string = json.dumps(xmltodict.parse(response.json()[0][JSON_PRODUCTS][JSON_XMLTEXT]))

        data = json.loads(json_string)

        for city in data[JSON_POLLEN_INFO][JSON_REGION]:
            readings = self.format_readings(city[JSON_READINGS][JSON_READING])
            readings.update(
                {
                    JSON_FORECAST: city[JSON_FORECAST],
                    DATE: data[JSON_POLLEN_INFO][JSON_FILE_INFO][JSON_DATE_DK][JSON_DATE_DK_STRING],
                    SOURCE: data[JSON_POLLEN_INFO][JSON_SOURCE],
                }
            )
            self.data.update(
                {
                    city[JSON_ATTRIBUTE_NAME]: readings
                }
            )
