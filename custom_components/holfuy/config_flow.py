"""Config flow to configure Holfuy component."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_API_KEY, DOMAIN

DATA_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): str})


class HolfuyConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Holfuy component."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._async_abort_entries_match({CONF_API_KEY: user_input[CONF_API_KEY]})
            return self.async_create_entry(
                title=f"Holfuy API ({user_input[CONF_API_KEY][0:4]})",
                data=user_input,
            )

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
