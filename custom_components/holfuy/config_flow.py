"""Config flow to configure Holfuy component."""

from __future__ import annotations  # noqa: I001

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.const import (
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, callback

from .const import (
    CONF_STATION_ID,
    CONF_API_KEY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@callback
def configured_instances(hass: HomeAssistant) -> set[str]:
    """Return a set of configured Holfuy.no instances."""
    entries = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        entries.append(entry.data.get(CONF_STATION_ID))

    return set(entries)


def _get_data_schema(
    hass: HomeAssistant, config_entry: ConfigEntry | None = None
) -> vol.Schema:
    """Get a schema with default values."""

    return vol.Schema(
        {
            vol.Required(
                CONF_API_KEY,
                msg="API Key",
                description="The API key you received from Holfuy.",
            ): str,
        }
    )


class HolfuyConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Holfuy component."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            if user_input.get(CONF_STATION_ID) not in configured_instances(self.hass):
                return self.async_create_entry(
                    title=f"Holfy API ({user_input[CONF_API_KEY][0:4]})",
                    data=user_input,
                )
            errors[CONF_STATION_ID] = "already_configured"

        return self.async_show_form(
            step_id="user",
            data_schema=_get_data_schema(self.hass),
            errors=errors,
        )
