"""The Holfuy component."""

from __future__ import annotations  # noqa: I001

import logging
from .pyholfuy import HolfuyService
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY,
    DOMAIN,
    UPDATE_INTERVAL_OBSERVATION,
)
from .coordinator import (
    HolfuyDataUpdateCoordinator,
    HolfuyWeatherConfigEntry,
    HolfuyWeatherData,
)

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: HolfuyWeatherConfigEntry
) -> bool:
    """Set up Holfuy as config entry."""

    api_key: str = config_entry.data[CONF_API_KEY]
    name: str = hex(hash(api_key)).capitalize

    websession = async_get_clientsession(hass)
    holfuy = HolfuyService(api_key, websession)

    coordinator = HolfuyDataUpdateCoordinator(
        hass, config_entry, holfuy, f"Holfuy {name}", UPDATE_INTERVAL_OBSERVATION
    )

    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = HolfuyWeatherData(coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    await cleanup_old_device(hass)

    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: HolfuyWeatherConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def async_update_entry(
    hass: HomeAssistant, config_entry: HolfuyWeatherConfigEntry
):
    """Reload Holfuy component when options changed."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def cleanup_old_device(hass: HomeAssistant) -> None:
    """Cleanup device without proper device identifier."""
    device_reg = dr.async_get(hass)
    device = device_reg.async_get_device(identifiers={(DOMAIN,)})  # type: ignore[arg-type]
    if device:
        _LOGGER.debug("Removing improper device %s", device.name)
        device_reg.async_remove_device(device.id)
