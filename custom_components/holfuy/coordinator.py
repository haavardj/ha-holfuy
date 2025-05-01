"""DataUpdateCoordinator for Met.no integration."""

from __future__ import annotations  # noqa: I001

from asyncio import timeout
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import timedelta
import logging
from random import randrange
from typing import TYPE_CHECKING, Any, Self

import async_timeout

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .pyholfuy import HolfuyService

from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


from .const import DOMAIN, MANUFACTURER

# Dedicated Home Assistant endpoint - do not change!

URL = "http://api.holfuy.com/live/"


_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Unable to connect to the web site."""


@dataclass
class HolfuyWeatherData:
    """Keep data for Holfuy weather entities."""

    coordinator: HolfuyDataUpdateCoordinator


type HolfuyWeatherConfigEntry = ConfigEntry[HolfuyWeatherData]


class HolfuyDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Holfuy data."""

    config_entry: HolfuyWeatherConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: HolfuyWeatherConfigEntry,
        holfuy: HolfuyService,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize global Holfuy data updater."""

        self.holfuy = holfuy
        self.available_station_ids: list[str] = []

        # self.device_info = _get_device_info("299", name)

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{name}",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Holfuy."""
        try:
            async with async_timeout.timeout(10):
                resp: dict[str, Any] = await self.holfuy.fetch_data()
                val = {}
                for entry in resp["measurements"]:
                    idx: str = entry["stationId"]
                    val[idx] = {
                        "stationId": idx,
                        "Name": entry.get("stationName", idx),
                        "RelativeHumidity": entry.get("humidity", 0),
                        "Pressure": entry.get("pressure", 0),
                        "Temperature": entry.get("temperature", 0),
                        "Wind": entry["wind"].get("speed", 0),
                        "WindGust": entry["wind"].get("gust", 0),
                        "WindBearing": entry["wind"].get("direction", 0),
                    }

                self.available_station_ids = list(val.keys())
                return val

        except Exception as error:
            _LOGGER.error(error)
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_data_error",
                translation_placeholders={"error": repr(error)},
            ) from error

    def get_station_name(self, station_id: str) -> str:
        """Return the name of a station."""

        if not self.data:
            return station_id

        if not self.data.get(station_id):
            return station_id

        return self.data[station_id].get("Name", station_id)


def _get_device_info(station_id: str, name: str) -> DeviceInfo:
    """Device info."""

    return DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, station_id)},  # type: ignore[arg-type]
        manufacturer=MANUFACTURER,
        model="Holfy API",
        name=name,
        configuration_url="https://www.hofluy.com",
    )
