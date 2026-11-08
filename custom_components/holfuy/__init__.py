"""The Holfuy component."""

from __future__ import annotations  # noqa: I001

import logging
from typing import Any
from holfuy import HolfuyService
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
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

    websession = async_get_clientsession(hass)
    holfuy = HolfuyService(api_key, websession)

    coordinator = HolfuyDataUpdateCoordinator(
        hass,
        config_entry,
        holfuy,
        f"Holfuy API ({api_key[0:4]})",
        UPDATE_INTERVAL_OBSERVATION,
    )

    await coordinator.async_config_entry_first_refresh()

    _migrate_device_identifiers(hass, config_entry)
    await _migrate_unique_ids(hass, config_entry, coordinator)

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


def _migrate_device_identifiers(
    hass: HomeAssistant, config_entry: HolfuyWeatherConfigEntry
) -> None:
    """Convert int station IDs in device identifiers to str.

    Up to 0.2.0 the integration used the API's int station IDs, so devices were
    registered as ("holfuy", 142). Without this, the str IDs now used would
    create a second device for every station.
    """
    device_reg = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_reg, config_entry.entry_id):
        new_identifiers = {
            (domain, str(identifier)) if domain == DOMAIN else (domain, identifier)
            for domain, identifier in device.identifiers
        }
        if new_identifiers != device.identifiers:
            _LOGGER.debug("Migrating identifiers of device %s", device.name)
            device_reg.async_update_device(
                device.id,
                new_identifiers=new_identifiers,
                serial_number=next(
                    (i for d, i in new_identifiers if d == DOMAIN), device.serial_number
                ),
            )


async def _migrate_unique_ids(
    hass: HomeAssistant,
    config_entry: HolfuyWeatherConfigEntry,
    coordinator: HolfuyDataUpdateCoordinator,
) -> None:
    """Change unique IDs from "<station name>-<key>" to "<station id>-<key>".

    Up to 0.2.0 the unique ID was built from the station name, so renaming a
    station on Holfuy created new entities. Entities of a station that was
    renamed before this migration ran cannot be matched and are left as is.
    """
    station_ids = {
        str(station["Name"]).lower(): station_id
        for station_id, station in coordinator.data.items()
    }
    ent_reg = er.async_get(hass)

    @callback
    def _migrate(entity_entry: er.RegistryEntry) -> dict[str, Any] | None:
        name, sep, key = entity_entry.unique_id.rpartition("-")
        if not sep or name not in station_ids:
            return None
        new_unique_id = f"{station_ids[name]}-{key}"
        if ent_reg.async_get_entity_id(entity_entry.domain, DOMAIN, new_unique_id):
            _LOGGER.warning(
                "Cannot migrate %s: unique ID %s is already in use",
                entity_entry.entity_id,
                new_unique_id,
            )
            return None
        _LOGGER.debug("Migrating unique ID of %s", entity_entry.entity_id)
        return {"new_unique_id": new_unique_id}

    await er.async_migrate_entries(hass, config_entry.entry_id, _migrate)


async def cleanup_old_device(hass: HomeAssistant) -> None:
    """Cleanup device without proper device identifier."""
    device_reg = dr.async_get(hass)
    device = device_reg.async_get_device(identifiers={(DOMAIN,)})  # type: ignore[arg-type]
    if device:
        _LOGGER.debug("Removing improper device %s", device.name)
        device_reg.async_remove_device(device.id)
