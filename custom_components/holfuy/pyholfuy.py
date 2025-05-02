"""Library to handle connection with met.no api."""

import asyncio
import datetime
import logging

from typing import Any

import aiohttp
import async_timeout


#  http://api.holfuy.com/live/?s=101&pw=pass&m=JSON&tu=C&su=m/s
#
# s: station(s) ID e.g. s=101 or you can get the data from more stations by one query as well (coma separated list) e.g. s=101,102,103 . If you would get all stations' data (to which you have access) by one single API call please use the "all" string -> s=all .
# pw: password for the API access (it could be sent by a POST "pw" parameter also)
# m:mode XML or CSV or JSON default: CSV
# avg:averaging "0": newest data from the station, "1" newest quarter hourly average, "2" newest hourly average (default = 0)
# su: wind speed unit: knots, km/h, m/s, mph, default: m/s
# tu: temperature unit C:Celsius , F: Fahrenheit default: Celsius
# batt: add this parameter to get the station's battery voltage (JSON only).
# cam: add this parameter to the URL for timestamp of the last picture from the camera. (JSON only, only for stations with a camera)
# daily: add this parameter to get daily Max-Min temperatures and precipitation since last midnight CE(S)T (JSON only, max 5 stations)
# loc: add this parameter to the URL to get the station's location in reply too (JSON only)
# utc: add this parameter to the URL for timestamps in UTC, otherwise times will be in CE(S)T
# Data: DateTime: time of the last data / average in ".date('T')." (Central European Time) or in UTC if utc param is set.


DEFAULT_API_URL = "http://api.holfuy.com/live/"

TIMEOUT = 30

_LOGGER = logging.getLogger(__name__)


class HolfuyService:
    """Representation of Holfuy weather data."""

    def __init__(self, api_key: str, websession=None, api_url=DEFAULT_API_URL) -> None:
        """Initialize the Weather object."""

        urlparams = {}
        urlparams["m"] = "JSON"
        urlparams["tu"] = "C"
        urlparams["su"] = "m/s"
        urlparams["daily"] = ""
        urlparams["batt"] = ""
        urlparams["avg"] = 1

        urlparams["s"] = "all"
        urlparams["pw"] = api_key

        self._urlparams = urlparams
        self._api_url = api_url

        if websession is None:

            async def _create_session():
                return aiohttp.ClientSession()

            loop = asyncio.get_event_loop()
            self._websession = loop.run_until_complete(_create_session())
        else:
            self._websession = websession

    async def fetch_data(
        self, stations: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Get the latest data from Holfuy."""

        if stations:
            self._urlparams["s"] = ",".join(map(str, stations))
        else:
            self._urlparams["s"] = "all"

        try:
            async with async_timeout.timeout(TIMEOUT):
                resp = await self._websession.get(self._api_url, params=self._urlparams)

            if resp.status >= 400:
                _LOGGER.error("%s returned %s", self._api_url, resp.status)
                return None

            result = await resp.json()

            # Make return value consistent.
            if stations and len(stations) == 1:
                result = {"measurements": result}

            return result  # noqa: TRY300

        except (TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error(
                "Access to %s returned error '%s'", self._api_url, type(err).__name__
            )
            return None
        except ValueError:
            _LOGGER.exception("Unable to parse json response from %s", self._api_url)
            return None


def parse_datetime(dt_str: str) -> datetime.datetime:
    """Parse datetime."""

    date_format = "%Y-%m-%dT%H:%M:%S %z"
    dt_str = dt_str.replace("Z", " +0000")
    return datetime.datetime.strptime(dt_str, date_format)
