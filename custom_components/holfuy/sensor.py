"""Support for Holfuy.no weather service."""

from __future__ import annotations  # noqa: I001

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Any, cast


from homeassistant.components.weather import (
    ATTR_WEATHER_CLOUD_COVERAGE,
    ATTR_WEATHER_DEW_POINT,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_UV_INDEX,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_GUST_SPEED,
    ATTR_WEATHER_WIND_SPEED,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)


from homeassistant.const import (
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback

from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import ATTRIBUTION, MANUFACTURER, DOMAIN
from .coordinator import HolfuyDataUpdateCoordinator, HolfuyWeatherConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class HolfuySensorDescription(SensorEntityDescription):
    """Class describing sensor entities."""

    value_fn: Callable[[dict[str, Any]], str | int | float | None]
    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] = lambda _: {}


SENSOR_TYPES: tuple[HolfuySensorDescription, ...] = (
    HolfuySensorDescription(
        key="RelativeHumidity",
        device_class=SensorDeviceClass.HUMIDITY,
        entity_registry_enabled_default=True,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: cast(int, data),
        translation_key="humidity",
    ),
    HolfuySensorDescription(
        key="Pressure",
        device_class=SensorDeviceClass.PRESSURE,
        entity_registry_enabled_default=True,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        native_unit_of_measurement=UnitOfPressure.HPA,
        value_fn=lambda data: cast(float, data),
        translation_key="pressure",
    ),
    HolfuySensorDescription(
        key="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_registry_enabled_default=True,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: cast(float, data),
        translation_key="temperature",
    ),
    HolfuySensorDescription(
        key="Wind",
        device_class=SensorDeviceClass.WIND_SPEED,
        entity_registry_enabled_default=True,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        value_fn=lambda data: cast(float, data),
        translation_key="wind_speed",
    ),
    HolfuySensorDescription(
        key="WindGust",
        name="Wind gust",
        device_class=SensorDeviceClass.WIND_SPEED,
        entity_registry_enabled_default=True,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        value_fn=lambda data: cast(float, data),
        translation_key="wind_gust_speed",
    ),
    HolfuySensorDescription(
        key="WindBearing",
        device_class=SensorDeviceClass.WIND_DIRECTION,
        entity_registry_enabled_default=True,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
        native_unit_of_measurement="°",
        value_fn=lambda data: cast(int, data),
        translation_key="wind_direction",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HolfuyWeatherConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a weather entity from a config_entry."""

    coordinator: HolfuyDataUpdateCoordinator = config_entry.runtime_data.coordinator
    entities: list[HolfuySensor] = []

    for key in coordinator.available_station_ids:
        entities.extend(
            [
                HolfuySensor(key, coordinator, description)
                for description in SENSOR_TYPES
            ]
        )

    async_add_entities(entities)


class HolfuySensor(CoordinatorEntity[HolfuyDataUpdateCoordinator], SensorEntity):
    """Implementation of a Holfuy sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    entity_description: HolfuySensorDescription

    def __init__(
        self,
        station_id: str,
        coordinator: HolfuyDataUpdateCoordinator,
        description: HolfuySensorDescription,
    ) -> None:
        """Initialise."""
        super().__init__(coordinator)

        self.entity_description = description

        self.station_id = station_id
        self.station_name = coordinator.get_station_name(station_id)

        self._sensor_data = self._get_sensor_data(
            coordinator.data, station_id, description.key
        )

        self._attr_unique_id = f"{self.station_name}-{description.key}".lower()

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, station_id)},  # type: ignore[arg-type]
            manufacturer=MANUFACTURER,
            model="Holfy API",
            name=self.station_name,
            configuration_url=f"https://holfuy.com/en/weather/{self.station_id}",
        )

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state."""
        return self.entity_description.value_fn(self._sensor_data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self.entity_description.attr_fn(self.coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""

        self._sensor_data = self._get_sensor_data(
            self.coordinator.data, self.station_id, self.entity_description.key
        )
        self.async_write_ha_state()

    @staticmethod
    def _get_sensor_data(
        sensors: dict[str, Any],
        station_id: str,
        kind: str,
    ) -> Any:
        """Get sensor data."""

        return sensors[station_id][kind]
