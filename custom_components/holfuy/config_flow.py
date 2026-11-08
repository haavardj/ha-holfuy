"""Config flow to configure Holfuy component."""

from __future__ import annotations

import logging
from typing import Any

from holfuy import HolfuyAuthError, HolfuyConnectionError, HolfuyError, HolfuyService
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): str})

# Passed as a placeholder: hassfest rejects URLs inside translation strings.
API_URL = "https://api.holfuy.com/live/"


class HolfuyConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Holfuy component."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match({CONF_API_KEY: user_input[CONF_API_KEY]})

            service = HolfuyService(
                user_input[CONF_API_KEY], async_get_clientsession(self.hass)
            )
            try:
                await service.fetch_data()
            except HolfuyAuthError:
                errors["base"] = "invalid_auth"
            except HolfuyConnectionError:
                errors["base"] = "cannot_connect"
            except HolfuyError:
                _LOGGER.exception("Unexpected reply from the Holfuy API")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Holfuy API ({user_input[CONF_API_KEY][0:4]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA, user_input),
            errors=errors,
            description_placeholders={"api_url": API_URL},
        )
