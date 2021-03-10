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
NONE = "ingen"
LOW = "få"
MODERATE = "moderat"
HIGH = "mange"

LOW_THRESHOLD = {
    'birk': 30,
    'bynke': 10,
    'elm': 10,
    'el': 10,
    'hassel': 5,
    'græs': 10,
    'alternaria': 20,
    'cladosporium': 2000,
}
HIGH_THRESHOLD = {
    'birk': 100,
    'bynke': 50,
    'elm': 50,
    'el': 50,
    'hassel': 15,
    'græs': 50,
    'alternaria': 100,
    'cladosporium': 6000,
}

NO_READING = "-"
SOURCE = "source"
DATE = "applicable_date"

NAME = "DMI Pollen"
ICON = "mdi:flower-poppy"

# Time between updates (Default: 15 minutes)
SCAN_INTERVAL = timedelta(seconds=600)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the sensor platform."""

    data = DMIpollenApi()
    data.update()

    city_list = []
    for city in data.readings:
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
        return f"{NAME} {self.city.capitalize()}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.data.readings[self.city][SEVERITY]

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attributes = dict(self.data.readings[self.city])
        attributes.update({JSON_FORECAST: self.data.forecasts[self.city]})
        attributes.update(self.data.attrs)
        return attributes

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.data.update()


class DMIpollenApi:

    def __init__(self):
        self.readings = {}
        self.attrs = {}
        self.forecasts = {}

    @staticmethod
    def calculate_severity(name, value):

        if 0 < value < LOW_THRESHOLD[name]:
            return LOW
        elif LOW_THRESHOLD[name] < value < HIGH_THRESHOLD[name]:
            return MODERATE
        elif HIGH_THRESHOLD[name] < value:
            return HIGH
        else:
            return NONE

    @staticmethod
    def convert_xml_to_json(xml):
        info_dict = xmltodict.parse(xml)

        json_string = json.dumps(info_dict)

        return json.loads(json_string)

    @staticmethod
    def request_new_data(endpoint):
        response = requests.get(endpoint)

        if response.status_code != HTTP_OK:
            _LOGGER.error("Error fetching data. Status code: {code} with text: {text}".format(
                code=response.status_code,
                text=response
            ))
            return

        return response.json()

    def format_readings(self, raw_readings):
        readings = {}

        for item in raw_readings:
            name = item.get(JSON_ATTRIBUTE_NAME).lower()
            value = int(item.get(JSON_ATTRIBUTE_VALUE)) if item.get(JSON_ATTRIBUTE_VALUE).isnumeric() else 0
            readings[name] = value

        maximum = max(readings, key=readings.get)
        readings[SEVERITY] = self.calculate_severity(maximum, readings[maximum])

        return readings

    def update(self):

        self.readings = {}
        self.attrs = {}
        self.forecasts = {}

        data = self.request_new_data(ENDPOINT)

        result = self.convert_xml_to_json(data[0][JSON_PRODUCTS][JSON_XMLTEXT])

        self.attrs = {
            DATE: result[JSON_POLLEN_INFO][JSON_FILE_INFO][JSON_DATE_DK][JSON_DATE_DK_STRING],
            SOURCE: result[JSON_POLLEN_INFO][JSON_SOURCE]
        }

        for city in result[JSON_POLLEN_INFO][JSON_REGION]:
            self.readings[city[JSON_ATTRIBUTE_NAME]] = self.format_readings(city[JSON_READINGS][JSON_READING])
            self.forecasts[city[JSON_ATTRIBUTE_NAME]] = city[JSON_FORECAST]
