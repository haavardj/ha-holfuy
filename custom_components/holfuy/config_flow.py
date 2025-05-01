"""Config flow to configure Holfuy component."""

from __future__ import annotations  # noqa: I001

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_STATION_ID,
    CONF_API_KEY,
    DOMAIN,
)


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
                    title=user_input[CONF_NAME], data=user_input
                )
            errors[CONF_NAME] = "already_configured"

        return self.async_show_form(
            step_id="user",
            data_schema=_get_data_schema(self.hass),
            errors=errors,
        )


# @staticmethod
# @callback
# def async_get_options_flow(
#     config_entry: ConfigEntry,
# ) -> HolfuyOptionsFlowHandler:
#     """Get the options flow for Holfuy."""
#     return HolfuyOptionsFlowHandler()


# class HolfuyOptionsFlowHandler(OptionsFlow):
#     """Options flow for Holfuy component."""

#     async def async_step_init(
#         self, user_input: dict[str, Any] | None = None
#     ) -> ConfigFlowResult:
#         """Configure options for Holfuy."""

#         if user_input is not None:
#             # Update config entry with data from user input
#             self.hass.config_entries.async_update_entry(
#                 self.config_entry, data=user_input
#             )
#             return self.async_create_entry(
#                 title=self.config_entry.title, data=user_input
#             )

#         return self.async_show_form(
#             step_id="init",
#             data_schema=OPTIONS_SCHEMA,
#         )
