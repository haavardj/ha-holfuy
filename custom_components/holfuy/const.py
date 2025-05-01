"""Constants for Holfy component."""

from datetime import timedelta  # noqa: I001
from homeassistant.components.weather import (
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_GUST_SPEED,
    ATTR_WEATHER_WIND_SPEED,
)


DOMAIN = "holfuy"
MANUFACTURER = "dagenborg.net"
ATTRIBUTION = "Weather observations from Holfuy.com by Dagenborg.net"

CONF_STATION_ID = "station_id"
CONF_API_KEY = "api_key"

SCAN_INTERVAL = timedelta(minutes=1)
UPDATE_INTERVAL_OBSERVATION = timedelta(minutes=1)

ATTR_MAP = {
    ATTR_WEATHER_HUMIDITY: "humidity",
    ATTR_WEATHER_PRESSURE: "pressure",
    ATTR_WEATHER_TEMPERATURE: "temperature",
    ATTR_WEATHER_WIND_BEARING: "wind_bearing",
    ATTR_WEATHER_WIND_SPEED: "wind_speed",
    ATTR_WEATHER_WIND_GUST_SPEED: "wind_gust",
}
